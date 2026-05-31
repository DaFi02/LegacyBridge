"""Tests para las reglas duras de transformación determinística."""

import pytest
from src.migrator.pipeline.hard_rules import (
    HardRuleEngine,
    CobolVerbsToRust,
    CobolControlFlowToRust,
    CobolStructureToRust,
    CppIncludesToRust,
    CppTypesToRust,
    CppOutputToRust,
    CppMemoryToRust,
)


# === Tests COBOL → Rust ===

class TestCobolVerbsToRust:
    def setup_method(self):
        self.rule = CobolVerbsToRust()

    def test_display_string(self):
        code = '           DISPLAY "Hello World".'
        result = self.rule.apply(code)
        assert 'println!("Hello World")' in result.code

    def test_display_variable(self):
        code = '           DISPLAY WS-COUNTER.'
        result = self.rule.apply(code)
        assert 'println!("{}", ws_counter)' in result.code

    def test_move_number(self):
        code = '           MOVE 0 TO WS-TOTAL.'
        result = self.rule.apply(code)
        assert 'ws_total = 0' in result.code

    def test_move_string(self):
        code = '           MOVE "PROD001" TO PROD-CODE.'
        result = self.rule.apply(code)
        assert 'String::from("PROD001")' in result.code

    def test_add(self):
        code = '           ADD 1 TO WS-COUNTER.'
        result = self.rule.apply(code)
        assert 'ws_counter += 1' in result.code

    def test_subtract(self):
        code = '           SUBTRACT 5 FROM TOTAL-AMOUNT.'
        result = self.rule.apply(code)
        assert 'total_amount -= 5' in result.code

    def test_perform(self):
        code = '           PERFORM CALCULATE-PAY.'
        result = self.rule.apply(code)
        assert 'calculate_pay()' in result.code

    def test_stop_run(self):
        code = '           STOP RUN.'
        result = self.rule.apply(code)
        assert 'return;' in result.code

    def test_compute(self):
        code = '           COMPUTE WS-TOTAL = WS-PRICE * WS-QTY.'
        result = self.rule.apply(code)
        assert 'ws_total = ws_price * ws_qty' in result.code

    def test_names_converted_to_snake_case(self):
        code = '           PERFORM INITIALIZE-INVENTORY.'
        result = self.rule.apply(code)
        assert 'initialize_inventory()' in result.code


class TestCobolControlFlowToRust:
    def setup_method(self):
        self.rule = CobolControlFlowToRust()

    def test_if_simple(self):
        code = '           IF WS-COUNTER GREATER THAN 10'
        result = self.rule.apply(code)
        assert 'if ws_counter > 10 {' in result.code

    def test_else(self):
        code = '           ELSE'
        result = self.rule.apply(code)
        assert '} else {' in result.code

    def test_end_if(self):
        code = '           END-IF.'
        result = self.rule.apply(code)
        assert '}' in result.code

    def test_condition_operators(self):
        code = '           IF A LESS THAN B'
        result = self.rule.apply(code)
        assert '< B' in result.code or '< b' in result.code

    def test_not_equal(self):
        code = '           IF STATUS NOT EQUAL TO "ACTIVE"'
        result = self.rule.apply(code)
        assert '!=' in result.code

    def test_perform_until(self):
        code = '           PERFORM READ-RECORD UNTIL EOF-FLAG = "Y".'
        result = self.rule.apply(code)
        assert 'while' in result.code
        assert 'read_record()' in result.code


class TestCobolStructureToRust:
    def setup_method(self):
        self.rule = CobolStructureToRust()

    def test_program_id(self):
        code = '       PROGRAM-ID. INVENTORY-MGMT.'
        result = self.rule.apply(code)
        assert 'Migrado de COBOL' in result.code

    def test_paragraph_to_fn(self):
        code = """       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY "Hello".
       CALC-TOTAL.
           ADD 1 TO X."""
        result = self.rule.apply(code)
        assert 'fn main_logic()' in result.code
        assert 'fn calc_total()' in result.code


# === Tests C++ → Rust ===

class TestCppIncludesToRust:
    def setup_method(self):
        self.rule = CppIncludesToRust()

    def test_iostream(self):
        code = '#include <iostream>'
        result = self.rule.apply(code)
        assert 'println!' in result.code

    def test_map(self):
        code = '#include <map>'
        result = self.rule.apply(code)
        assert 'HashMap' in result.code

    def test_fstream(self):
        code = '#include <fstream>'
        result = self.rule.apply(code)
        assert 'std::fs::File' in result.code

    def test_vector_builtin(self):
        code = '#include <vector>'
        result = self.rule.apply(code)
        assert 'Vec' in result.code


class TestCppTypesToRust:
    def setup_method(self):
        self.rule = CppTypesToRust()

    def test_int_to_i32(self):
        code = 'int x = 5;'
        result = self.rule.apply(code)
        assert 'i32' in result.code

    def test_double_to_f64(self):
        code = 'double pi = 3.14;'
        result = self.rule.apply(code)
        assert 'f64' in result.code

    def test_string(self):
        code = 'std::string name = "hello";'
        result = self.rule.apply(code)
        assert 'String' in result.code

    def test_vector(self):
        code = 'std::vector<int> numbers;'
        result = self.rule.apply(code)
        assert 'Vec<' in result.code

    def test_nullptr(self):
        code = 'int* ptr = nullptr;'
        result = self.rule.apply(code)
        assert 'None' in result.code

    def test_size_t(self):
        code = 'size_t count = 0;'
        result = self.rule.apply(code)
        assert 'usize' in result.code


class TestCppOutputToRust:
    def setup_method(self):
        self.rule = CppOutputToRust()

    def test_cout_string(self):
        code = '    std::cout << "Hello" << std::endl;'
        result = self.rule.apply(code)
        assert 'println!("Hello")' in result.code

    def test_cout_variable(self):
        code = '    cout << "Value: " << x << endl;'
        result = self.rule.apply(code)
        assert 'println!' in result.code
        assert '{}' in result.code

    def test_printf(self):
        code = '    printf("Count: %d\\n", count);'
        result = self.rule.apply(code)
        assert 'println!' in result.code
        assert 'count' in result.code


class TestCppMemoryToRust:
    def setup_method(self):
        self.rule = CppMemoryToRust()

    def test_new_to_box(self):
        code = 'auto p = new Point(1, 2);'
        result = self.rule.apply(code)
        assert 'Box::new' in result.code

    def test_delete_to_drop(self):
        code = 'delete ptr;'
        result = self.rule.apply(code)
        assert 'drop(ptr)' in result.code

    def test_new_array(self):
        code = 'int* arr = new int[100];'
        result = self.rule.apply(code)
        assert 'vec!' in result.code

    def test_unique_ptr(self):
        code = 'std::unique_ptr<Widget> w;'
        result = self.rule.apply(code)
        assert 'Box<Widget>' in result.code

    def test_shared_ptr(self):
        code = 'std::shared_ptr<Config> cfg;'
        result = self.rule.apply(code)
        assert 'Arc<Config>' in result.code


# === Tests del Motor Completo ===

class TestHardRuleEngine:
    def test_cobol_engine_has_rules(self):
        engine = HardRuleEngine("cobol_to_rust")
        assert len(engine.rules) == 4

    def test_cpp_engine_has_rules(self):
        engine = HardRuleEngine("cpp_to_rust")
        assert len(engine.rules) == 4

    def test_unknown_type_empty(self):
        engine = HardRuleEngine("python_to_go")
        assert len(engine.rules) == 0

    def test_apply_all_cobol(self):
        engine = HardRuleEngine("cobol_to_rust")
        code = """       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY "Sistema Iniciado".
           ADD 1 TO WS-COUNTER.
           IF WS-COUNTER GREATER THAN 5
               DISPLAY "Limite alcanzado"
           END-IF.
           STOP RUN."""
        result = engine.apply_all(code)
        assert result.lines_changed > 0
        assert 'println!' in result.code
        assert 'ws_counter += 1' in result.code

    def test_apply_all_cpp(self):
        engine = HardRuleEngine("cpp_to_rust")
        code = """#include <iostream>
#include <vector>

int main() {
    std::vector<int> nums;
    int* ptr = new int[10];
    std::cout << "Hello" << std::endl;
    delete[] ptr;
    return 0;
}"""
        result = engine.apply_all(code)
        assert result.lines_changed > 0
        assert 'Vec' in result.code or 'vec!' in result.code
        assert 'println!' in result.code
        assert 'drop(' in result.code

    def test_summary(self):
        engine = HardRuleEngine("cobol_to_rust")
        summary = engine.summary()
        assert "cobol_to_rust" in summary
        assert "DISPLAY" in summary or "println" in summary
