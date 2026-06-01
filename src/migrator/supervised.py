"""Motor de ejecución supervisada para clientes.

Ejecuta el pipeline paso a paso con confirmación humana,
genera reportes y expone estado para el dashboard.
"""

import json
import time
import tomllib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .pipeline.orchestrator import MigrationOrchestrator, MigrationReport
from .pipeline.analyzer import CodeAnalyzer, FileAnalysis
from .pipeline.segmenter import CodeSegmenter, CodeSegment
from .pipeline.state_machine import MigrationStateMachine, MigrationState


@dataclass
class ClientConfig:
    """Configuración de proyecto de cliente."""
    # Client info
    client_name: str = "Cliente"
    client_contact: str = ""
    client_email: str = ""
    client_industry: str = ""
    
    # Project
    project_name: str = "Migración"
    project_description: str = ""
    
    # Source
    source_path: str = ""
    source_language: str = "cobol"
    
    # Target
    target_language: str = "rust"
    output_path: str = "output/delivery/"
    
    # Pipeline
    max_retries: int = 3
    supervised: bool = True
    generate_report: bool = True
    compile_validation: bool = True
    
    # Report
    report_path: str = "reports/"
    report_format: str = "html"
    include_source: bool = True
    include_metrics: bool = True

    @classmethod
    def from_toml(cls, path: str) -> "ClientConfig":
        """Carga configuración desde un archivo TOML."""
        with open(path, "rb") as f:
            data = tomllib.load(f)
        
        config = cls()
        
        # Client
        if "client" in data:
            config.client_name = data["client"].get("name", config.client_name)
            config.client_contact = data["client"].get("contact", "")
            config.client_email = data["client"].get("email", "")
            config.client_industry = data["client"].get("industry", "")
        
        # Project
        if "project" in data:
            config.project_name = data["project"].get("name", config.project_name)
            config.project_description = data["project"].get("description", "")
        
        # Source
        if "source" in data:
            config.source_path = data["source"].get("path", "")
            config.source_language = data["source"].get("language", "cobol")
        
        # Target
        if "target" in data:
            config.target_language = data["target"].get("language", "rust")
            config.output_path = data["target"].get("output_path", "output/delivery/")
        
        # Pipeline
        if "pipeline" in data:
            config.max_retries = data["pipeline"].get("max_retries", 3)
            config.supervised = data["pipeline"].get("supervised", True)
            config.generate_report = data["pipeline"].get("generate_report", True)
            config.compile_validation = data["pipeline"].get("compile_validation", True)
        
        # Report
        if "report" in data:
            config.report_path = data["report"].get("output_path", "reports/")
            config.report_format = data["report"].get("format", "html")
            config.include_source = data["report"].get("include_source", True)
            config.include_metrics = data["report"].get("include_metrics", True)
        
        return config


@dataclass
class PhaseResult:
    """Resultado de una fase del pipeline."""
    phase: str
    status: str  # "success" | "failed" | "skipped"
    duration_seconds: float
    details: dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass 
class SupervisedReport:
    """Reporte completo de una ejecución supervisada."""
    config: ClientConfig
    phases: list[PhaseResult] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    total_duration: float = 0.0
    status: str = "in_progress"  # in_progress | completed | failed
    
    # Métricas
    total_files: int = 0
    total_lines: int = 0
    total_segments: int = 0
    segments_migrated: int = 0
    segments_compiled: int = 0
    compilation_rate: float = 0.0
    
    def to_dict(self) -> dict:
        """Serializa a dict para JSON/dashboard."""
        return {
            "client": {
                "name": self.config.client_name,
                "contact": self.config.client_contact,
                "industry": self.config.client_industry,
            },
            "project": {
                "name": self.config.project_name,
                "description": self.config.project_description,
                "source_language": self.config.source_language,
                "target_language": self.config.target_language,
            },
            "execution": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total_duration": self.total_duration,
                "status": self.status,
            },
            "metrics": {
                "total_files": self.total_files,
                "total_lines": self.total_lines,
                "total_segments": self.total_segments,
                "segments_migrated": self.segments_migrated,
                "segments_compiled": self.segments_compiled,
                "compilation_rate": self.compilation_rate,
            },
            "phases": [asdict(p) for p in self.phases],
        }


class SupervisedRunner:
    """Ejecutor supervisado para proyectos de cliente.
    
    Ejecuta la migración fase por fase, pidiendo confirmación
    en modo supervisado y generando métricas para el dashboard.
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self.report = SupervisedReport(config=config)
        self._state_file = Path(config.output_path) / ".supervised_state.json"
        
        # Pipeline components
        self.orchestrator = MigrationOrchestrator(
            source_dir=config.source_path,
            output_dir=config.output_path,
            source_lang=config.source_language,
            target_lang=config.target_language,
            project_name=config.project_name,
            max_retries=config.max_retries,
        )

    def run(self, verbose: bool = True) -> SupervisedReport:
        """Ejecuta el pipeline completo con supervisión."""
        self.report.start_time = datetime.now().isoformat()
        start = time.time()

        if verbose:
            self._print_header()

        try:
            # Fase 1: Análisis
            if not self._run_phase("analyze", "Análisis de Código Fuente", verbose):
                return self._finalize("failed", start)

            # Fase 2: Segmentación
            if not self._run_phase("segment", "Segmentación Incremental", verbose):
                return self._finalize("failed", start)

            # Fase 3: Migración
            if not self._run_phase("migrate", "Migración (Reglas Duras + IA)", verbose):
                return self._finalize("failed", start)

            # Fase 4: Validación
            if self.config.compile_validation:
                if not self._run_phase("validate", "Validación de Compilación", verbose):
                    return self._finalize("failed", start)

            # Fase 5: Ensamblaje
            self._run_phase("assemble", "Ensamblaje Final", verbose)

        except KeyboardInterrupt:
            if verbose:
                print("\n\n  ⏸️  Pipeline pausado por el usuario")
            return self._finalize("paused", start)
        except Exception as e:
            if verbose:
                print(f"\n  ✗ Error: {e}")
            return self._finalize("failed", start)

        return self._finalize("completed", start)

    def _run_phase(self, step: str, label: str, verbose: bool) -> bool:
        """Ejecuta una fase con supervisión opcional."""
        if verbose:
            print(f"\n{'═' * 60}")
            print(f"  📋 FASE: {label}")
            print(f"{'═' * 60}")

        # Supervisión: pedir confirmación
        if self.config.supervised and verbose:
            response = input(f"\n  ¿Continuar con '{label}'? [S/n/saltar] → ").strip().lower()
            if response == "n":
                self.report.phases.append(PhaseResult(
                    phase=step, status="cancelled", duration_seconds=0,
                    details={"reason": "Cancelado por el usuario"}
                ))
                return False
            elif response == "saltar":
                self.report.phases.append(PhaseResult(
                    phase=step, status="skipped", duration_seconds=0,
                    details={"reason": "Saltado por el usuario"}
                ))
                if verbose:
                    print(f"  ⏭️  Fase saltada")
                return True

        # Ejecutar fase
        phase_start = time.time()
        try:
            result = self.orchestrator.run_step(step, verbose=verbose)
            duration = time.time() - phase_start

            phase_result = PhaseResult(
                phase=step,
                status="success",
                duration_seconds=round(duration, 2),
                details=result or {},
            )
            self.report.phases.append(phase_result)
            
            # Actualizar métricas
            self._update_metrics(step, result)
            
            # Guardar estado intermedio
            self._save_state()

            if verbose:
                print(f"\n  ✅ {label} completado ({duration:.1f}s)")

            return True

        except Exception as e:
            duration = time.time() - phase_start
            self.report.phases.append(PhaseResult(
                phase=step, status="failed", duration_seconds=round(duration, 2),
                details={"error": str(e)}
            ))
            if verbose:
                print(f"\n  ✗ {label} falló: {e}")
            return False

    def _update_metrics(self, step: str, result: dict | None):
        """Actualiza métricas del reporte según la fase completada."""
        if not result:
            return
            
        if step == "analyze":
            self.report.total_files = result.get("files", 0)
            self.report.total_lines = result.get("lines", 0)
        elif step == "segment":
            self.report.total_segments = result.get("segments", 0)
        elif step == "migrate":
            self.report.segments_migrated = result.get("migrated", 0)
        elif step == "validate":
            self.report.segments_compiled = result.get("compiled", 0)
            if self.report.total_segments > 0:
                self.report.compilation_rate = (
                    self.report.segments_compiled / self.report.total_segments * 100
                )

    def _finalize(self, status: str, start: float) -> SupervisedReport:
        """Finaliza el reporte."""
        self.report.end_time = datetime.now().isoformat()
        self.report.total_duration = round(time.time() - start, 2)
        self.report.status = status
        self._save_state()
        return self.report

    def _save_state(self):
        """Guarda estado para el dashboard."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._state_file, "w") as f:
            json.dump(self.report.to_dict(), f, indent=2, ensure_ascii=False)

    def get_live_state(self) -> dict:
        """Retorna estado actual para el dashboard (API)."""
        return self.report.to_dict()

    def _print_header(self):
        """Imprime header profesional."""
        print("")
        print("╔══════════════════════════════════════════════════════════╗")
        print("║       🌉 LegacyBridge — Migración Supervisada          ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  Cliente: {self.config.client_name:<46} ║")
        print(f"║  Proyecto: {self.config.project_name:<45} ║")
        print(f"║  Migración: {self.config.source_language} → {self.config.target_language:<38} ║")
        print(f"║  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M'):<48} ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  Modo: SUPERVISADO (confirmación en cada fase)          ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print("")
