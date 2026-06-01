"""CLI profesional para ejecución en cliente.

Uso:
    # Ejecutar migración supervisada con config de cliente
    uv run python client_cli.py run --config legacybridge.toml

    # Ejecutar sin supervisión (automático)
    uv run python client_cli.py run --config legacybridge.toml --auto

    # Generar reporte desde estado guardado
    uv run python client_cli.py report --state output/delivery/.supervised_state.json

    # Iniciar API para dashboard
    uv run python client_cli.py dashboard --port 8787

    # Crear config de ejemplo
    uv run python client_cli.py init
"""

import sys
import argparse
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.migrator.supervised import SupervisedRunner, ClientConfig
from src.migrator.report_generator import ReportGenerator
from src.migrator.api_server import start_api_server


def cmd_run(args):
    """Ejecutar migración supervisada."""
    config = ClientConfig.from_toml(args.config)
    
    if args.auto:
        config.supervised = False
    
    runner = SupervisedRunner(config)
    
    # Iniciar API si se pide dashboard
    if args.dashboard:
        server = start_api_server(port=args.port, state_dir=str(Path(config.output_path).parent))
        print(f"  📊 Dashboard API en http://localhost:{args.port}")
        print(f"     Abre el dashboard React para monitorear en tiempo real")
        print()
    
    # Ejecutar
    report = runner.run(verbose=True)
    
    # Generar reporte HTML
    if config.generate_report and report.status in ("completed", "failed"):
        state_file = str(Path(config.output_path) / ".supervised_state.json")
        if Path(state_file).exists():
            gen = ReportGenerator()
            report_path = gen.generate(
                state_file, 
                output_path=str(Path(config.report_path) / "reporte_migracion.html")
            )
            print(f"\n  📄 Reporte generado: {report_path}")
    
    # Resumen final
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                   RESUMEN EJECUTIVO                      ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Estado: {report.status.upper():<47} ║")
    print(f"║  Archivos: {report.total_files:<45} ║")
    print(f"║  Líneas: {report.total_lines:<47} ║")
    print(f"║  Segmentos migrados: {report.segments_migrated}/{report.total_segments:<35} ║")
    print(f"║  Compilación: {report.compilation_rate:.0f}%{' ' * 42}║")
    print(f"║  Duración: {report.total_duration:.0f}s{' ' * 44}║")
    print("╚══════════════════════════════════════════════════════════╝")


def cmd_report(args):
    """Generar reporte HTML."""
    gen = ReportGenerator()
    output = args.output or str(Path(args.state).parent / "reporte_migracion.html")
    path = gen.generate(args.state, output_path=output)
    print(f"  📄 Reporte generado: {path}")
    print(f"     Abrir en navegador: file://{Path(path).resolve()}")


def cmd_dashboard(args):
    """Iniciar servidor de API para dashboard."""
    print(f"  📊 Iniciando API del dashboard en puerto {args.port}...")
    print(f"     URL: http://localhost:{args.port}")
    print(f"     Endpoints:")
    print(f"       GET /api/status    → Estado del último proyecto")
    print(f"       GET /api/projects  → Lista de proyectos")
    print(f"       GET /api/health    → Health check")
    print(f"")
    print(f"  Presiona Ctrl+C para detener")
    print()
    
    server = start_api_server(port=args.port, state_dir=args.state_dir)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido")
        server.shutdown()


def cmd_init(args):
    """Crear archivo de configuración de ejemplo."""
    dest = Path(args.output)
    src = Path("legacybridge.example.toml")
    
    if dest.exists():
        print(f"  ⚠️  Ya existe: {dest}")
        return
    
    shutil.copy(src, dest)
    print(f"  ✅ Configuración creada: {dest}")
    print(f"     Edita el archivo con los datos del cliente")


def main():
    parser = argparse.ArgumentParser(
        description="🌉 LegacyBridge — CLI para Clientes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # run
    p_run = subparsers.add_parser("run", help="Ejecutar migración supervisada")
    p_run.add_argument("--config", "-c", required=True, help="Archivo de configuración TOML")
    p_run.add_argument("--auto", action="store_true", help="Modo automático (sin confirmaciones)")
    p_run.add_argument("--dashboard", "-d", action="store_true", help="Iniciar API de dashboard")
    p_run.add_argument("--port", type=int, default=8787, help="Puerto para API dashboard")

    # report
    p_report = subparsers.add_parser("report", help="Generar reporte HTML")
    p_report.add_argument("--state", "-s", required=True, help="Ruta al .supervised_state.json")
    p_report.add_argument("--output", "-o", help="Ruta de salida del HTML")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Iniciar API para dashboard React")
    p_dash.add_argument("--port", "-p", type=int, default=8787, help="Puerto HTTP")
    p_dash.add_argument("--state-dir", default="output/", help="Directorio de estados")

    # init
    p_init = subparsers.add_parser("init", help="Crear configuración de ejemplo")
    p_init.add_argument("--output", "-o", default="legacybridge.toml", help="Archivo de salida")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "init":
        cmd_init(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
