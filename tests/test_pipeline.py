"""Tests para el pipeline de migración incremental."""

import pytest
from pathlib import Path
from src.migrator.pipeline.state_machine import (
    MigrationStateMachine, MigrationState, InvalidTransitionError
)
from src.migrator.pipeline.analyzer import CodeAnalyzer, FileAnalysis
from src.migrator.pipeline.segmenter import CodeSegmenter
from src.migrator.pipeline.rules import RuleEngine, RuleResult, RuleSeverity


# === Tests de la Máquina de Estados ===

class TestStateMachine:
    def test_initial_state_is_idle(self):
        sm = MigrationStateMachine()
        assert sm.state == MigrationState.IDLE

    def test_valid_transition(self):
        sm = MigrationStateMachine()
        sm.init_project("test", "cobol", "rust", "/src", "/out")
        sm.transition(MigrationState.ANALYZING)
        assert sm.state == MigrationState.ANALYZING

    def test_invalid_transition_raises(self):
        sm = MigrationStateMachine()
        sm.init_project("test", "cobol", "rust", "/src", "/out")
        with pytest.raises(InvalidTransitionError):
            sm.transition(MigrationState.COMPLETED)

    def test_full_happy_path(self):
        sm = MigrationStateMachine()
        sm.init_project("test", "cobol", "rust", "/src", "/out")
        sm.transition(MigrationState.ANALYZING)
        sm.transition(MigrationState.ANALYZED)
        sm.transition(MigrationState.SEGMENTING)
        sm.transition(MigrationState.SEGMENTED)
        sm.transition(MigrationState.MIGRATING)
        sm.transition(MigrationState.VALIDATING)
        sm.transition(MigrationState.ASSEMBLING)
        sm.transition(MigrationState.COMPLETED)
        assert sm.state == MigrationState.COMPLETED

    def test_can_retry_from_failed(self):
        sm = MigrationStateMachine()
        sm.init_project("test", "cobol", "rust", "/src", "/out")
        sm.transition(MigrationState.ANALYZING)
        sm.transition(MigrationState.FAILED)
        sm.transition(MigrationState.ANALYZING)  # Retry
        assert sm.state == MigrationState.ANALYZING

    def test_segment_tracking(self):
        sm = MigrationStateMachine()
        sm.init_project("test", "cobol", "rust", "/src", "/out")
        sm.update_segment("seg1", state="pending")
        sm.update_segment("seg2", state="pending")
        sm.update_segment("seg1", state="validated")
        
        assert sm.context.segments_completed == 1
        assert sm.get_pending_segments() == ["seg2"]

    def test_persists_to_disk(self, tmp_path):
        state_file = tmp_path / "state.json"
        sm = MigrationStateMachine(state_file=state_file)
        sm.init_project("test", "cpp", "rust", "/src", "/out")
        sm.transition(MigrationState.ANALYZING)

        assert state_file.exists()
        
        # Cargar desde disco
        sm2 = MigrationStateMachine()
        sm2.load_state(state_file)
        assert sm2.state == MigrationState.ANALYZING

    def test_progress_report(self):
        sm = MigrationStateMachine()
        sm.init_project("test", "cobol", "rust", "/src", "/out")
        sm.context.total_segments = 4
        sm.update_segment("s1", state="validated")
        sm.update_segment("s2", state="validated")
        sm.update_segment("s3", state="failed", attempts=3, max_attempts=3)
        sm.update_segment("s4", state="pending")

        progress = sm.get_progress()
        assert progress["completed"] == 2
        assert progress["failed"] == 1
        assert progress["progress_pct"] == 50.0


# === Tests del Analizador ===

class TestAnalyzer:
    def setup_method(self):
        self.analyzer = CodeAnalyzer()

    def test_analyze_cpp_file(self, tmp_path):
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""
#include <iostream>
#include <vector>

struct Point {
    int x;
    int y;
};

int calculate(int a, int b) {
    if (a > b) {
        return a - b;
    }
    return a + b;
}

int main() {
    Point p;
    p.x = 10;
    std::cout << calculate(p.x, 5) << std::endl;
    return 0;
}
""")
        result = self.analyzer.analyze_file(cpp_file)
        assert result.language == "cpp"
        assert "iostream" in result.imports
        assert "vector" in result.imports
        assert any(s.name == "Point" for s in result.symbols)
        assert any(s.name == "calculate" for s in result.symbols)
        assert any(s.name == "main" for s in result.symbols)

    def test_analyze_cobol_file(self, tmp_path):
        cob_file = tmp_path / "test.cob"
        cob_file.write_text("""       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEST-PROG.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-COUNTER         PIC 9(3).
       01  WS-TOTAL           PIC 9(5)V99.
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM INITIALIZE-DATA
           PERFORM CALCULATE-TOTAL
           STOP RUN.
       INITIALIZE-DATA.
           MOVE 0 TO WS-COUNTER
           MOVE 0 TO WS-TOTAL.
       CALCULATE-TOTAL.
           ADD 1 TO WS-COUNTER
           COMPUTE WS-TOTAL = WS-COUNTER * 10.
""")
        result = self.analyzer.analyze_file(cob_file)
        assert result.language == "cobol"
        assert "WS-COUNTER" in result.global_vars
        assert "WS-TOTAL" in result.global_vars
        # Paragraphs detectados como funciones
        func_names = [s.name for s in result.symbols]
        assert "MAIN-LOGIC" in func_names or "INITIALIZE-DATA" in func_names

    def test_analyze_java_file(self, tmp_path):
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
import java.util.List;
import java.util.ArrayList;

public class Calculator {
    private int value;

    public int add(int a, int b) {
        return a + b;
    }

    public int multiply(int a, int b) {
        return a * b;
    }
}
""")
        result = self.analyzer.analyze_file(java_file)
        assert result.language == "java"
        assert "java.util.List" in result.imports
        assert any(s.name == "Calculator" and s.kind == "class" for s in result.symbols)

    def test_summary_output(self, tmp_path):
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""
#include <stdio.h>
void hello() { printf("hi"); }
""")
        result = self.analyzer.analyze_file(cpp_file)
        summary = result.summary()
        assert "test.cpp" in summary
        assert "hello" in summary

    def test_complexity_estimation(self, tmp_path):
        cpp_file = tmp_path / "complex.cpp"
        cpp_file.write_text("""
int complex_func(int x) {
    if (x > 0) {
        for (int i = 0; i < x; i++) {
            if (i % 2 == 0) {
                while (x > i) {
                    x--;
                }
            }
        }
    } else if (x < 0) {
        switch(x) {
            case -1: return 1;
            case -2: return 2;
        }
    }
    return x;
}
""")
        result = self.analyzer.analyze_file(cpp_file)
        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1
        assert funcs[0].complexity > 3  # Alta complejidad


# === Tests del Segmentador ===

class TestSegmenter:
    def setup_method(self):
        self.analyzer = CodeAnalyzer()
        self.segmenter = CodeSegmenter()

    def test_segments_cpp_file(self, tmp_path):
        cpp_file = tmp_path / "app.cpp"
        content = """#include <iostream>
#include <vector>

struct Config {
    int width;
    int height;
};

void initialize(Config& cfg) {
    cfg.width = 800;
    cfg.height = 600;
}

int main() {
    Config c;
    initialize(c);
    std::cout << c.width << std::endl;
    return 0;
}
"""
        cpp_file.write_text(content)
        analysis = self.analyzer.analyze_file(cpp_file)
        segments = self.segmenter.segment_file(analysis, content)

        assert len(segments) >= 2  # Al menos header + funciones
        kinds = [s.kind for s in segments]
        assert "header" in kinds

    def test_segment_has_context(self, tmp_path):
        cpp_file = tmp_path / "test.cpp"
        content = "void foo() { }\n"
        cpp_file.write_text(content)
        analysis = self.analyzer.analyze_file(cpp_file)
        
        analyses = [analysis]
        segments = self.segmenter.segment_directory(analyses, tmp_path)
        
        # Cada segmento debe tener contexto del proyecto
        for seg in segments:
            assert seg.context_summary != "" or seg.kind == "header"

    def test_segment_id_format(self, tmp_path):
        cpp_file = tmp_path / "myfile.cpp"
        content = """
struct Data { int x; };
void process() { }
"""
        cpp_file.write_text(content)
        analysis = self.analyzer.analyze_file(cpp_file)
        segments = self.segmenter.segment_file(analysis, content)

        for seg in segments:
            assert "::" in seg.segment_id
            assert "myfile" in seg.segment_id


# === Tests del Motor de Reglas ===

class TestRuleEngine:
    def setup_method(self):
        self.engine = RuleEngine()
        self.context = {
            "source_language": "cpp",
            "target_language": "rust",
        }

    def test_empty_output_fails(self):
        results = self.engine.validate("int main() { }", "", self.context)
        blocking = self.engine.has_blocking_errors(results)
        assert blocking  # Código vacío es error bloqueante

    def test_valid_migration_passes(self):
        source = """
void process(int* data, int size) {
    for (int i = 0; i < size; i++) {
        printf("%d\\n", data[i]);
    }
}
"""
        migrated = """
fn process(data: &[i32]) {
    for item in data {
        println!("{}", item);
    }
}
"""
        results = self.engine.validate(source, migrated, self.context)
        blocking = self.engine.has_blocking_errors(results)
        assert not blocking

    def test_detects_cpp_residual(self):
        source = "void hello() { cout << \"hi\"; }"
        migrated = """
fn hello() {
    cout << "hi";
}
"""
        results = self.engine.validate(source, migrated, self.context)
        # Should detect cout as C++ residual
        syntax_results = [r for r in results if r.rule_name == "valid_rust_syntax"]
        assert any(not r.passed for r in syntax_results)

    def test_detects_hallucinated_imports(self):
        source = "void foo() { }"
        migrated = """
use fake_quantum_crate::magic;
use nonexistent_lib::thing;

fn foo() { }
"""
        results = self.engine.validate(source, migrated, self.context)
        import_results = [r for r in results if r.rule_name == "no_hallucinated_imports"]
        assert any(not r.passed for r in import_results)

    def test_size_ratio_extreme(self):
        source = "int x = 1;"
        migrated = "\n".join([f"let x{i} = {i};" for i in range(200)])
        results = self.engine.validate(source, migrated, self.context)
        size_results = [r for r in results if r.rule_name == "size_ratio"]
        assert any(not r.passed for r in size_results)

    def test_summary_output(self):
        source = "struct Point { int x; int y; };"
        migrated = "struct Point { x: i32, y: i32 }"
        results = self.engine.validate(source, migrated, self.context)
        summary = self.engine.summary(results)
        assert "VALIDACIÓN DE REGLAS" in summary

    def test_preserves_logic_strings(self):
        source = 'printf("Hello World"); printf("Error: invalid input");'
        migrated = 'println!("Hello World"); println!("Error: invalid input");'
        results = self.engine.validate(source, migrated, self.context)
        logic_results = [r for r in results if r.rule_name == "preserves_logic"]
        assert all(r.passed for r in logic_results)

    def test_cobol_context(self):
        context = {"source_language": "cobol", "target_language": "rust"}
        source = """       MAIN-LOGIC.
           PERFORM INIT
           PERFORM CALC
           STOP RUN.
       INIT.
           MOVE 0 TO WS-X.
       CALC.
           ADD 1 TO WS-X.
"""
        migrated = """
fn main() {
    init();
    calc();
}

fn init() {
    // ws_x = 0
}

fn calc() {
    // ws_x += 1
}
"""
        results = self.engine.validate(source, migrated, context)
        blocking = self.engine.has_blocking_errors(results)
        assert not blocking
