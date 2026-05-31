"""Orquestador del pipeline de migración incremental.

Coordina todos los módulos:
1. Analyzer → extrae estructura
2. Segmenter → divide en partes
3. AI Migrator → migra cada parte (con reglas)
4. Podman Validator → compila
5. Assembler → une el resultado

Controla reintentos, limita alucinaciones y persiste estado.
"""

from pathlib import Path
from dataclasses import dataclass

from .state_machine import MigrationStateMachine, MigrationState, InvalidTransitionError
from .analyzer import CodeAnalyzer, FileAnalysis
from .segmenter import CodeSegmenter, CodeSegment
from .rules import RuleEngine, RuleResult
from .hard_rules import HardRuleEngine
from ..ai_migrator import AIMigrator, AIMigrationResult
from ..validation.compiler import PodmanValidator, ValidationResult


@dataclass
class MigrationReport:
    """Reporte final de una migración completa."""
    project_name: str
    source_language: str
    target_language: str
    total_segments: int
    segments_ok: int
    segments_failed: int
    compilation_passed: bool
    rule_violations: int
    output_dir: str
    event_log: list[dict]


class MigrationOrchestrator:
    """Orquesta la migración completa de un proyecto.
    
    Uso:
        orchestrator = MigrationOrchestrator(
            source_dir="examples/cobol/",
            output_dir="output/migrated/",
            source_lang="cobol",
            target_lang="rust",
        )
        report = orchestrator.run()
    """

    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        source_lang: str,
        target_lang: str,
        api_key: str | None = None,
        project_name: str = "migration",
        max_retries: int = 3,
    ):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_retries = max_retries

        # Componentes
        self.analyzer = CodeAnalyzer()
        self.segmenter = CodeSegmenter()
        self.rules = RuleEngine()
        self.hard_rules = HardRuleEngine(f"{source_lang}_to_{target_lang}")
        self.ai = AIMigrator(api_key=api_key)
        self.validator = PodmanValidator()

        # Estado persistido
        state_file = self.output_dir / ".migration_state.json"
        self.sm = MigrationStateMachine(state_file=state_file)
        self.sm.init_project(
            project_name=project_name,
            source_language=source_lang,
            target_language=target_lang,
            source_dir=str(self.source_dir),
            output_dir=str(self.output_dir),
        )

        # Almacenamiento intermedio
        self._analyses: list[FileAnalysis] = []
        self._segments: list[CodeSegment] = []
        self._migrated: dict[str, str] = {}  # segment_id → código migrado

    def run(self, verbose: bool = True) -> MigrationReport:
        """Ejecuta el pipeline completo."""
        try:
            self._phase_analyze(verbose)
            self._phase_segment(verbose)
            self._phase_migrate(verbose)
            self._phase_validate(verbose)
            self._phase_assemble(verbose)
        except InvalidTransitionError as e:
            if verbose:
                print(f"\n  ✗ Error de estado: {e}")
        except Exception as e:
            if verbose:
                print(f"\n  ✗ Error inesperado: {e}")
            self.sm.transition(MigrationState.FAILED, str(e))

        return self._build_report()

    def run_step(self, step: str, verbose: bool = True) -> dict:
        """Ejecuta un solo paso del pipeline (para control manual).
        
        Steps: analyze, segment, migrate, validate, assemble
        """
        steps = {
            "analyze": self._phase_analyze,
            "segment": self._phase_segment,
            "migrate": self._phase_migrate,
            "validate": self._phase_validate,
            "assemble": self._phase_assemble,
        }
        if step not in steps:
            return {"error": f"Paso desconocido: {step}. Opciones: {list(steps.keys())}"}

        steps[step](verbose)
        return self.sm.get_progress()

    # === FASES DEL PIPELINE ===

    def _phase_analyze(self, verbose: bool) -> None:
        """Fase 1: Analizar código fuente."""
        self.sm.transition(MigrationState.ANALYZING, "Iniciando análisis")
        if verbose:
            print("\n📊 FASE 1: Análisis de código fuente")
            print(f"   Directorio: {self.source_dir}")

        self._analyses = self.analyzer.analyze_directory(self.source_dir)

        # Actualizar contexto
        ctx = self.sm.context
        ctx.total_files = len(self._analyses)
        ctx.total_lines = sum(a.total_lines for a in self._analyses)
        ctx.total_symbols = sum(len(a.symbols) for a in self._analyses)
        ctx.file_analyses = {
            Path(a.filepath).name: a.to_dict() for a in self._analyses
        }

        if verbose:
            print(f"   Archivos: {ctx.total_files}")
            print(f"   Líneas: {ctx.total_lines}")
            print(f"   Símbolos: {ctx.total_symbols}")
            for a in self._analyses:
                print(f"   📄 {Path(a.filepath).name}: {len(a.symbols)} símbolos")
                for sym in a.symbols[:5]:
                    print(f"      • {sym.kind}: {sym.name} (complejidad: {sym.complexity})")

        self.sm.transition(MigrationState.ANALYZED, "Análisis completado")

    def _phase_segment(self, verbose: bool) -> None:
        """Fase 2: Segmentar código en partes migrables."""
        self.sm.transition(MigrationState.SEGMENTING, "Segmentando código")
        if verbose:
            print("\n✂️  FASE 2: Segmentación")

        self._segments = self.segmenter.segment_directory(
            self._analyses, self.source_dir
        )

        # Registrar segmentos en el estado
        ctx = self.sm.context
        ctx.total_segments = len(self._segments)
        for seg in self._segments:
            self.sm.update_segment(seg.segment_id, state="pending")

        if verbose:
            print(f"   Segmentos creados: {len(self._segments)}")
            for seg in self._segments:
                print(f"   📦 {seg.segment_id} ({seg.kind}, {seg.end_line - seg.start_line + 1} líneas, complejidad: {seg.complexity})")

        self.sm.transition(MigrationState.SEGMENTED, "Segmentación completada")

    def _phase_migrate(self, verbose: bool) -> None:
        """Fase 3: Migrar cada segmento con reglas duras + IA + validación."""
        self.sm.transition(MigrationState.MIGRATING, "Migrando segmentos")
        if verbose:
            print("\n🤖 FASE 3: Migración (Reglas Duras + IA)")
            print(f"   {self.hard_rules.summary()}")
            print()

        migration_type = f"{self.source_lang}_to_{self.target_lang}"
        total = len(self._segments)

        for i, segment in enumerate(self._segments, 1):
            sid = segment.segment_id
            seg_state = self.sm.context.segments.get(sid, {})

            # Skip si ya fue validado
            if seg_state.get("state") == "validated":
                continue

            attempts = seg_state.get("attempts", 0)
            if attempts >= self.max_retries:
                if verbose:
                    print(f"   ✗ [{i}/{total}] {sid} - max reintentos alcanzado")
                continue

            if verbose:
                print(f"   🔄 [{i}/{total}] Migrando: {sid} (intento {attempts + 1})")

            self.sm.update_segment(sid, state="migrating", attempts=attempts + 1)

            # PASO 1: Aplicar reglas duras (determinísticas, sin IA)
            hard_result = self.hard_rules.apply_all(segment.code)
            if verbose and hard_result.lines_changed > 0:
                print(f"      📐 Reglas duras: {hard_result.lines_changed} líneas transformadas")
                for t in hard_result.transformations_applied:
                    print(f"         • {t}")

            # PASO 2: Enviar a IA con el código pre-procesado
            # La IA recibe el código ya parcialmente transformado
            ai_input = segment.full_prompt_context()
            # Agregar hint de las transformaciones ya hechas
            if hard_result.lines_changed > 0:
                hint = (
                    f"\n// PRE-PROCESADO: Las siguientes transformaciones ya fueron aplicadas determinísticamente:\n"
                    f"// {', '.join(hard_result.transformations_applied)}\n"
                    f"// Completa la migración del siguiente código parcialmente convertido:\n\n"
                    f"{hard_result.code}"
                )
                ai_input = hint

            result = self.ai.migrate(
                source_code=ai_input,
                migration_type=migration_type,
            )

            if not result.success:
                self.sm.update_segment(sid, state="failed", last_error=result.error)
                if verbose:
                    print(f"      ✗ Error IA: {result.error}")
                continue

            # PASO 3: Aplicar reglas anti-alucinación
            context = {
                "source_language": self.source_lang,
                "target_language": self.target_lang,
                "segment_kind": segment.kind,
                "segment_name": segment.name,
            }
            rule_results = self.rules.validate(
                segment.code, result.migrated_code, context
            )

            # Verificar reglas
            blocking = self.rules.has_blocking_errors(rule_results)
            if blocking:
                violations = [r for r in rule_results if not r.passed]
                error_msg = "; ".join(r.message for r in violations)
                self.sm.update_segment(sid, state="failed", last_error=error_msg)
                for v in violations:
                    self.sm.add_rule_violation(v.rule_name, sid, v.message)
                if verbose:
                    print(f"      ✗ Reglas bloqueantes: {error_msg}")
                continue

            # Migración OK (puede tener warnings)
            self._migrated[sid] = result.migrated_code
            self.sm.update_segment(sid, state="migrated", migrated_code=result.migrated_code)
            if verbose:
                warnings = [r for r in rule_results if not r.passed]
                if warnings:
                    print(f"      ⚠️  Warnings: {', '.join(r.message for r in warnings)}")
                else:
                    print(f"      ✓ OK")

    def _phase_validate(self, verbose: bool) -> None:
        """Fase 4: Validar compilación en Podman."""
        self.sm.transition(MigrationState.VALIDATING, "Validando compilación")
        if verbose:
            print("\n🐳 FASE 4: Validación con Podman")

        # Primero ensamblar temporalmente para validar
        assembled = self._assemble_code()
        if not assembled:
            if verbose:
                print("   ✗ No hay código para validar")
            self.sm.transition(MigrationState.FAILED, "Sin código migrado")
            return

        # Escribir archivos temporales y validar
        self.output_dir.mkdir(parents=True, exist_ok=True)
        all_passed = True

        for filename, code in assembled.items():
            filepath = self.output_dir / filename
            filepath.write_text(code, encoding="utf-8")

            if verbose:
                print(f"   🔨 Compilando {filename}...")

            result = self.validator.validate_file(filepath)
            if not result.success:
                all_passed = False
                if verbose:
                    print(f"      ✗ {result.errors[:200]}")
                # Marcar segmentos del archivo como fallidos
                for seg in self._segments:
                    if Path(seg.source_file).stem in filename:
                        self.sm.update_segment(
                            seg.segment_id,
                            state="failed",
                            last_error=f"Compilación falló: {result.errors[:100]}",
                        )
            else:
                if verbose:
                    print(f"      ✓ Compila correctamente")
                # Marcar segmentos como validados
                for seg in self._segments:
                    if Path(seg.source_file).stem in filename:
                        self.sm.update_segment(seg.segment_id, state="validated", validation_passed=True)

        if all_passed:
            self.sm.transition(MigrationState.ASSEMBLING, "Validación exitosa")
        else:
            # Si hay segmentos fallidos que pueden reintentarse, volver a migrar
            pending = self.sm.get_pending_segments()
            if pending:
                if verbose:
                    print(f"\n   ↩️  {len(pending)} segmentos para reintentar...")
                self.sm.transition(MigrationState.MIGRATING, "Reintentando segmentos fallidos")
                self._phase_migrate(verbose)
                # Re-validar después del reintento
                self.sm.transition(MigrationState.VALIDATING, "Re-validando")
                self._phase_validate_final(verbose)
            else:
                self.sm.transition(MigrationState.ASSEMBLING, "Algunos errores, ensamblando parcial")

    def _phase_validate_final(self, verbose: bool) -> None:
        """Validación final sin reintentos."""
        assembled = self._assemble_code()
        for filename, code in assembled.items():
            filepath = self.output_dir / filename
            filepath.write_text(code, encoding="utf-8")
            result = self.validator.validate_file(filepath)
            if result.success:
                for seg in self._segments:
                    if Path(seg.source_file).stem in filename:
                        self.sm.update_segment(seg.segment_id, state="validated", validation_passed=True)

        self.sm.transition(MigrationState.ASSEMBLING, "Ensamblando resultado final")

    def _phase_assemble(self, verbose: bool) -> None:
        """Fase 5: Ensamblar resultado final."""
        if self.sm.state != MigrationState.ASSEMBLING:
            self.sm.transition(MigrationState.ASSEMBLING, "Ensamblando")

        if verbose:
            print("\n📦 FASE 5: Ensamblaje final")

        assembled = self._assemble_code()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for filename, code in assembled.items():
            filepath = self.output_dir / filename
            filepath.write_text(code, encoding="utf-8")
            if verbose:
                print(f"   💾 {filepath}")

        self.sm.transition(MigrationState.COMPLETED, "Migración completada")
        if verbose:
            progress = self.sm.get_progress()
            print(f"\n✅ MIGRACIÓN COMPLETADA")
            print(f"   Segmentos: {progress['completed']}/{progress['total_segments']} validados")
            print(f"   Violaciones de reglas: {progress['violations']}")
            print(f"   Output: {self.output_dir}")

    # === UTILIDADES ===

    def _assemble_code(self) -> dict[str, str]:
        """Ensambla segmentos migrados en archivos completos."""
        files: dict[str, list[tuple[int, str]]] = {}  # filename → [(order, code)]

        for segment in self._segments:
            sid = segment.segment_id
            code = self._migrated.get(sid)
            if not code:
                continue

            # Determinar nombre de archivo de salida
            source_stem = Path(segment.source_file).stem
            ext = ".rs" if self.target_lang == "rust" else f".{self.target_lang}"
            out_filename = f"{source_stem}{ext}"

            if out_filename not in files:
                files[out_filename] = []
            files[out_filename].append((segment.start_line, code))

        # Ordenar segmentos por línea original y concatenar
        result = {}
        for filename, parts in files.items():
            parts.sort(key=lambda x: x[0])
            result[filename] = "\n\n".join(code for _, code in parts)

        return result

    def _build_report(self) -> MigrationReport:
        """Construye el reporte final."""
        progress = self.sm.get_progress()
        return MigrationReport(
            project_name=self.sm.context.project_name,
            source_language=self.source_lang,
            target_language=self.target_lang,
            total_segments=progress["total_segments"],
            segments_ok=progress["completed"],
            segments_failed=progress["failed"],
            compilation_passed=progress["failed"] == 0,
            rule_violations=progress["violations"],
            output_dir=str(self.output_dir),
            event_log=self.sm.context.event_log,
        )

    def print_status(self) -> None:
        """Imprime estado actual del pipeline."""
        progress = self.sm.get_progress()
        print(f"\n{'═' * 60}")
        print(f"  ESTADO DEL PIPELINE: {progress['state'].upper()}")
        print(f"{'═' * 60}")
        print(f"  Segmentos: {progress['completed']} ✓ | {progress['failed']} ✗ | {progress['pending']} pendientes")
        print(f"  Progreso: {progress['progress_pct']:.1f}%")
        print(f"  Violaciones de reglas: {progress['violations']}")
        print(f"{'═' * 60}")
