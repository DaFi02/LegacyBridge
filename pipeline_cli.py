"""CLI del pipeline de migración incremental.

Uso:
    # Pipeline completo (analiza → segmenta → migra → valida → ensambla)
    uv run python pipeline_cli.py run --source examples/cobol/ --output output/pipeline_cobol/ --from cobol --to rust

    # Solo análisis (ver estructura del proyecto)
    uv run python pipeline_cli.py analyze --source examples/cobol/

    # Solo segmentación (ver cómo se divide)
    uv run python pipeline_cli.py segment --source examples/cpp_legacy/

    # Paso a paso con control manual
    uv run python pipeline_cli.py step analyze --source examples/cobol/ --output output/pipeline/
    uv run python pipeline_cli.py step segment --source examples/cobol/ --output output/pipeline/
    uv run python pipeline_cli.py step migrate --source examples/cobol/ --output output/pipeline/

    # Ver estado actual
    uv run python pipeline_cli.py status --output output/pipeline/

    # Demo completa
    uv run python pipeline_cli.py demo
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.migrator.pipeline.analyzer import CodeAnalyzer
from src.migrator.pipeline.segmenter import CodeSegmenter
from src.migrator.pipeline.rules import RuleEngine
from src.migrator.pipeline.state_machine import MigrationStateMachine
from src.migrator.pipeline.orchestrator import MigrationOrchestrator


def cmd_analyze(args):
    """Analiza código fuente y muestra estructura."""
    source_dir = Path(args.source)
    if not source_dir.exists():
        print(f"✗ Directorio no encontrado: {source_dir}")
        return 1

    print(f"📊 Analizando: {source_dir}")
    print("=" * 60)

    analyzer = CodeAnalyzer()
    analyses = analyzer.analyze_directory(source_dir)

    total_lines = 0
    total_symbols = 0

    for analysis in analyses:
        total_lines += analysis.total_lines
        total_symbols += len(analysis.symbols)
        
        print(f"\n📄 {Path(analysis.filepath).name} ({analysis.language}, {analysis.total_lines} líneas)")
        
        if analysis.imports:
            print(f"   Imports: {', '.join(analysis.imports[:5])}")
        if analysis.global_vars:
            print(f"   Globales: {', '.join(analysis.global_vars[:5])}")
        
        for sym in analysis.symbols:
            params = f"({', '.join(sym.params[:3])})" if sym.params else ""
            ret = f" → {sym.return_type}" if sym.return_type else ""
            print(f"   {'├' if sym != analysis.symbols[-1] else '└'} {sym.kind}: {sym.name}{params}{ret} [L{sym.start_line}-{sym.end_line}, C:{sym.complexity}]")

    print(f"\n{'=' * 60}")
    print(f"  Total: {len(analyses)} archivos, {total_lines} líneas, {total_symbols} símbolos")
    print(f"{'=' * 60}")

    # Mostrar resumen para IA
    if args.context:
        print("\n📋 CONTEXTO PARA IA:")
        print("-" * 40)
        print(analyzer.project_summary(analyses))

    return 0


def cmd_segment(args):
    """Muestra cómo se segmentaría el código."""
    source_dir = Path(args.source)
    if not source_dir.exists():
        print(f"✗ Directorio no encontrado: {source_dir}")
        return 1

    print(f"✂️  Segmentando: {source_dir}")
    print("=" * 60)

    analyzer = CodeAnalyzer()
    segmenter = CodeSegmenter()
    analyses = analyzer.analyze_directory(source_dir)
    segments = segmenter.segment_directory(analyses, source_dir)

    for seg in segments:
        code_preview = seg.code[:80].replace('\n', ' ').strip()
        deps = f" ← [{', '.join(seg.dependencies)}]" if seg.dependencies else ""
        print(f"\n  📦 {seg.segment_id}")
        print(f"     Tipo: {seg.kind} | Líneas: {seg.start_line}-{seg.end_line} | Complejidad: {seg.complexity}")
        print(f"     Código: {code_preview}...{deps}")

    print(f"\n{'=' * 60}")
    print(f"  Total segmentos: {len(segments)}")
    
    by_complexity = sorted(segments, key=lambda s: s.complexity, reverse=True)
    if by_complexity:
        print(f"  Más complejo: {by_complexity[0].segment_id} (C:{by_complexity[0].complexity})")
    print(f"{'=' * 60}")

    return 0


def cmd_run(args):
    """Ejecuta el pipeline completo."""
    source_dir = Path(args.source)
    output_dir = Path(args.output)

    if not source_dir.exists():
        print(f"✗ Directorio no encontrado: {source_dir}")
        return 1

    print(f"🚀 PIPELINE DE MIGRACIÓN INCREMENTAL")
    print(f"   {args.source_lang} → {args.target_lang}")
    print(f"   Fuente: {source_dir}")
    print(f"   Salida: {output_dir}")
    print("=" * 60)

    orchestrator = MigrationOrchestrator(
        source_dir=str(source_dir),
        output_dir=str(output_dir),
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        project_name=source_dir.name,
        max_retries=args.retries,
    )

    report = orchestrator.run(verbose=True)

    print(f"\n{'═' * 60}")
    print(f"  REPORTE FINAL")
    print(f"{'═' * 60}")
    print(f"  Proyecto: {report.project_name}")
    print(f"  Migración: {report.source_language} → {report.target_language}")
    print(f"  Segmentos: {report.segments_ok} ✓ | {report.segments_failed} ✗ / {report.total_segments}")
    print(f"  Compilación: {'✓ PASA' if report.compilation_passed else '✗ ERRORES'}")
    print(f"  Violaciones reglas: {report.rule_violations}")
    print(f"  Output: {report.output_dir}")
    print(f"{'═' * 60}")

    return 0 if report.compilation_passed else 1


def cmd_status(args):
    """Muestra estado de un pipeline en progreso."""
    output_dir = Path(args.output)
    state_file = output_dir / ".migration_state.json"

    if not state_file.exists():
        print(f"✗ No hay estado guardado en: {output_dir}")
        return 1

    sm = MigrationStateMachine()
    sm.load_state(state_file)
    
    progress = sm.get_progress()
    ctx = sm.context
    
    print(f"\n{'═' * 60}")
    print(f"  ESTADO DEL PIPELINE")
    print(f"{'═' * 60}")
    print(f"  Proyecto: {ctx.project_name}")
    print(f"  Estado: {progress['state'].upper()}")
    print(f"  Migración: {ctx.source_language} → {ctx.target_language}")
    print(f"  Archivos: {ctx.total_files} | Líneas: {ctx.total_lines}")
    print(f"  Segmentos: {progress['completed']} ✓ | {progress['failed']} ✗ | {progress['pending']} pendientes")
    print(f"  Progreso: {progress['progress_pct']:.1f}%")
    print(f"  Violaciones: {progress['violations']}")
    
    if ctx.rules_violations:
        print(f"\n  ⚠️  Últimas violaciones:")
        for v in ctx.rules_violations[-5:]:
            print(f"     • [{v['rule']}] {v['segment_id']}: {v['details'][:60]}")

    print(f"\n  📋 Últimos eventos:")
    for ev in ctx.event_log[-8:]:
        print(f"     {ev['type']}: {ev['detail']}")

    print(f"{'═' * 60}")
    return 0


def cmd_demo(args):
    """Demo completa del pipeline."""
    print("🎯 DEMO: Pipeline de Migración Incremental con Control de Estado")
    print("=" * 60)
    print()
    print("Este demo muestra cómo LegacyBridge migra código de forma controlada:")
    print("  1. Analiza la estructura del código fuente")
    print("  2. Segmenta en partes migrables")
    print("  3. Migra cada parte con IA (con reglas anti-alucinación)")
    print("  4. Valida compilación en contenedores Podman")
    print("  5. Ensambla el resultado final")
    print()

    # Primero: mostrar análisis
    source_dir = Path("examples/cobol")
    if not source_dir.exists():
        source_dir = Path("examples/cpp_legacy")

    print(f"📊 Paso 1: Analizando {source_dir}...")
    print("-" * 40)
    analyzer = CodeAnalyzer()
    analyses = analyzer.analyze_directory(source_dir)
    for a in analyses:
        print(f"  📄 {Path(a.filepath).name}: {len(a.symbols)} símbolos, {a.total_lines} líneas")
        for sym in a.symbols[:3]:
            print(f"     • {sym.kind}: {sym.name} (complejidad: {sym.complexity})")

    # Segundo: segmentar
    print(f"\n✂️  Paso 2: Segmentando...")
    print("-" * 40)
    segmenter = CodeSegmenter()
    segments = segmenter.segment_directory(analyses, source_dir)
    print(f"  Creados {len(segments)} segmentos:")
    for seg in segments[:6]:
        print(f"  📦 {seg.segment_id} ({seg.kind}, C:{seg.complexity})")

    # Tercero: reglas
    print(f"\n📋 Paso 3: Motor de Reglas Anti-Alucinación")
    print("-" * 40)
    engine = RuleEngine()
    print(f"  {len(engine.rules)} reglas activas:")
    for rule in engine.rules:
        print(f"     • {rule.name} [{rule.category.value}] (severidad: {rule.severity.value})")

    # Ejemplo de validación
    source = 'PERFORM CALCULATE-PAY\n  COMPUTE WS-TOTAL = WS-SALARY + WS-BONUS'
    migrated = 'fn calculate_pay() {\n    let total = salary + bonus;\n}'
    ctx = {"source_language": "cobol", "target_language": "rust"}
    results = engine.validate(source, migrated, ctx)
    print(f"\n  Ejemplo validación COBOL→Rust:")
    print(f"  {engine.summary(results)}")

    # Cuarto: estados
    print(f"\n🔄 Paso 4: Máquina de Estados")
    print("-" * 40)
    print("  Estados del pipeline:")
    print("  IDLE → ANALYZING → ANALYZED → SEGMENTING → SEGMENTED")
    print("       → MIGRATING → VALIDATING → ASSEMBLING → COMPLETED")
    print("                  ↘ FAILED (retry) ↗")
    print()
    print("  Cada transición es validada. Estado persiste a disco.")
    print("  Se puede pausar y reanudar en cualquier momento.")

    print(f"\n{'═' * 60}")
    print(f"  Para ejecutar migración completa:")
    print(f"  uv run python pipeline_cli.py run --source examples/cobol/ \\")
    print(f"       --output output/pipeline/ --from cobol --to rust")
    print(f"{'═' * 60}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="LegacyBridge - Pipeline de Migración Incremental",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analizar estructura del código")
    p_analyze.add_argument("--source", "-s", required=True, help="Directorio fuente")
    p_analyze.add_argument("--context", "-c", action="store_true", help="Mostrar contexto para IA")

    # segment
    p_segment = subparsers.add_parser("segment", help="Segmentar código")
    p_segment.add_argument("--source", "-s", required=True, help="Directorio fuente")

    # run
    p_run = subparsers.add_parser("run", help="Ejecutar pipeline completo")
    p_run.add_argument("--source", "-s", required=True, help="Directorio fuente")
    p_run.add_argument("--output", "-o", required=True, help="Directorio de salida")
    p_run.add_argument("--from", dest="source_lang", required=True, help="Lenguaje fuente")
    p_run.add_argument("--to", dest="target_lang", required=True, help="Lenguaje destino")
    p_run.add_argument("--retries", type=int, default=3, help="Max reintentos por segmento")

    # status
    p_status = subparsers.add_parser("status", help="Ver estado del pipeline")
    p_status.add_argument("--output", "-o", required=True, help="Directorio del pipeline")

    # demo
    subparsers.add_parser("demo", help="Demo del pipeline")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "analyze": cmd_analyze,
        "segment": cmd_segment,
        "run": cmd_run,
        "status": cmd_status,
        "demo": cmd_demo,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
