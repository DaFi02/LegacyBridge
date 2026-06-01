"""Script de demostración para video.

Simula una migración supervisada de un cliente bancario,
actualizando el dashboard en tiempo real. Perfecto para grabar el video.

Flujo del demo (estilo marco ágil):
  Sprint 1: Análisis del legacy → Entrega: inventario completo
  Sprint 2: Segmentación por funcionalidad → Entrega: plan de migración
  Sprint 3: Migración incremental → Entrega: código por módulo
  Sprint 4: Validación → Entrega: reporte de calidad
  Sprint 5: Ensamblaje → Entrega: producto final compilado

Uso:
    # Terminal 1: Dashboard React
    cd dashboard && pnpm run dev

    # Terminal 2: API + simulación
    uv run python demo_video.py

    # Abrir http://localhost:5173 para ver dashboard en vivo
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL DEMO
# ═══════════════════════════════════════════════════════════════

DEMO_CLIENT = {
    "name": "Banco Nacional del Perú",
    "contact": "Carlos Mendoza (CTO)",
    "industry": "Banca & Finanzas",
}

DEMO_PROJECT = {
    "name": "Migración Core Bancario",
    "description": "Migración del sistema de gestión de cuentas y transacciones de COBOL a Rust",
    "source_language": "cobol",
    "target_language": "rust",
}

# Segmentos que simulan funcionalidades del sistema bancario
DEMO_SEGMENTS = [
    {"id": "account_management", "name": "Gestión de Cuentas", "lines": 450, "complexity": 8},
    {"id": "transaction_engine", "name": "Motor de Transacciones", "lines": 680, "complexity": 12},
    {"id": "balance_calculator", "name": "Calculadora de Saldos", "lines": 320, "complexity": 6},
    {"id": "audit_logger", "name": "Logger de Auditoría", "lines": 180, "complexity": 4},
    {"id": "interest_compute", "name": "Cálculo de Intereses", "lines": 520, "complexity": 10},
    {"id": "report_generator", "name": "Generador de Reportes", "lines": 290, "complexity": 5},
    {"id": "customer_validator", "name": "Validador de Clientes", "lines": 210, "complexity": 3},
    {"id": "batch_processor", "name": "Procesador Batch", "lines": 750, "complexity": 14},
]

# ═══════════════════════════════════════════════════════════════
# ESTADO GLOBAL (compartido con API)
# ═══════════════════════════════════════════════════════════════

STATE_FILE = Path("output/demo/.supervised_state.json")
current_state: dict = {}


def save_state(state: dict):
    """Guarda estado y actualiza referencia global."""
    global current_state
    current_state = state
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# ═══════════════════════════════════════════════════════════════
# API HTTP (sirve estado al dashboard React)
# ═══════════════════════════════════════════════════════════════

class DemoAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if path == "/api/status":
            self.wfile.write(json.dumps(current_state, ensure_ascii=False).encode())
        elif path == "/api/projects":
            projects = []
            if current_state:
                projects.append({
                    "path": str(STATE_FILE.parent),
                    "client": current_state.get("client", {}).get("name", ""),
                    "project": current_state.get("project", {}).get("name", ""),
                    "status": current_state.get("execution", {}).get("status", ""),
                    "migration": "COBOL → Rust",
                })
            self.wfile.write(json.dumps(projects, ensure_ascii=False).encode())
        elif path == "/api/health":
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP


def start_api():
    server = HTTPServer(("0.0.0.0", 8787), DemoAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ═══════════════════════════════════════════════════════════════
# SIMULACIÓN DEL PIPELINE (con delays realistas)
# ═══════════════════════════════════════════════════════════════

def print_banner():
    print("")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       🌉 LegacyBridge — Demo para Video                     ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Cliente: {DEMO_CLIENT['name']:<50}║")
    print(f"║  Proyecto: {DEMO_PROJECT['name']:<49}║")
    print(f"║  Migración: COBOL → Rust                                    ║")
    print(f"║  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M'):<52}║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Modo: DEMO SUPERVISADO (marco ágil, entregas por sprint)   ║")
    print("║  Dashboard: http://localhost:5173                            ║")
    print("║  API: http://localhost:8787                                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("")


def simulate_pipeline():
    """Simula el pipeline completo con entregas incrementales."""
    start_time = datetime.now().isoformat()
    phases = []
    total_lines = sum(s["lines"] for s in DEMO_SEGMENTS)
    total_files = 5  # Archivos COBOL fuente simulados

    # Estado inicial
    save_state({
        "client": DEMO_CLIENT,
        "project": DEMO_PROJECT,
        "execution": {"start_time": start_time, "end_time": "", "total_duration": 0, "status": "in_progress"},
        "metrics": {"total_files": 0, "total_lines": 0, "total_segments": 0, "segments_migrated": 0, "segments_compiled": 0, "compilation_rate": 0},
        "phases": [],
    })

    # ═══════════════════════════════════════════════════════════
    # SPRINT 1: ANÁLISIS
    # ═══════════════════════════════════════════════════════════
    print("━" * 62)
    print("  📋 SPRINT 1: Análisis de Código Fuente")
    print("  📦 Entrega: Inventario completo del sistema legacy")
    print("━" * 62)
    input("  → Presiona ENTER para iniciar el análisis...")
    print()

    # Simular análisis progresivo
    for i in range(1, total_files + 1):
        time.sleep(0.8)
        print(f"    📄 Analizando archivo {i}/{total_files}...")
        save_state({
            "client": DEMO_CLIENT,
            "project": DEMO_PROJECT,
            "execution": {"start_time": start_time, "end_time": "", "total_duration": round(time.time() - time.time(), 1), "status": "in_progress"},
            "metrics": {"total_files": i, "total_lines": int(total_lines * i / total_files), "total_segments": 0, "segments_migrated": 0, "segments_compiled": 0, "compilation_rate": 0},
            "phases": phases.copy(),
        })

    phase_duration = 4.2
    phases.append({"phase": "analyze", "status": "success", "duration_seconds": phase_duration, "timestamp": datetime.now().isoformat()})
    save_state({
        "client": DEMO_CLIENT,
        "project": DEMO_PROJECT,
        "execution": {"start_time": start_time, "end_time": "", "total_duration": phase_duration, "status": "in_progress"},
        "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": 0, "segments_migrated": 0, "segments_compiled": 0, "compilation_rate": 0},
        "phases": phases.copy(),
    })
    print(f"\n  ✅ Análisis completado: {total_files} archivos, {total_lines:,} líneas")
    print(f"     → Entrega Sprint 1: Inventario técnico del sistema")
    print()

    # ═══════════════════════════════════════════════════════════
    # SPRINT 2: SEGMENTACIÓN POR FUNCIONALIDAD
    # ═══════════════════════════════════════════════════════════
    print("━" * 62)
    print("  📋 SPRINT 2: Segmentación por Funcionalidad")
    print("  📦 Entrega: Plan de migración con prioridades")
    print("━" * 62)
    input("  → Presiona ENTER para segmentar por funcionalidades...")
    print()

    total_segments = len(DEMO_SEGMENTS)
    for i, seg in enumerate(DEMO_SEGMENTS, 1):
        time.sleep(0.6)
        print(f"    ✂️  [{i}/{total_segments}] {seg['name']} ({seg['lines']} líneas, complejidad: {seg['complexity']})")
        save_state({
            "client": DEMO_CLIENT,
            "project": DEMO_PROJECT,
            "execution": {"start_time": start_time, "end_time": "", "total_duration": phase_duration + i * 0.6, "status": "in_progress"},
            "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": i, "segments_migrated": 0, "segments_compiled": 0, "compilation_rate": 0},
            "phases": phases.copy(),
        })

    phase_duration += 5.8
    phases.append({"phase": "segment", "status": "success", "duration_seconds": 5.8, "timestamp": datetime.now().isoformat()})
    save_state({
        "client": DEMO_CLIENT,
        "project": DEMO_PROJECT,
        "execution": {"start_time": start_time, "end_time": "", "total_duration": phase_duration, "status": "in_progress"},
        "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": total_segments, "segments_migrated": 0, "segments_compiled": 0, "compilation_rate": 0},
        "phases": phases.copy(),
    })
    print(f"\n  ✅ Segmentación completada: {total_segments} funcionalidades identificadas")
    print(f"     → Entrega Sprint 2: Plan de migración priorizado")
    print()

    # ═══════════════════════════════════════════════════════════
    # SPRINT 3: MIGRACIÓN INCREMENTAL (por funcionalidad)
    # ═══════════════════════════════════════════════════════════
    print("━" * 62)
    print("  📋 SPRINT 3: Migración Incremental (Reglas Duras + IA)")
    print("  📦 Entrega: Código migrado funcionalidad por funcionalidad")
    print("━" * 62)
    input("  → Presiona ENTER para migrar cada funcionalidad...")
    print()
    print("  🤖 Aplicando reglas determinísticas + LLM (Llama 4 Maverick)")
    print()

    for i, seg in enumerate(DEMO_SEGMENTS, 1):
        # Simular tiempo proporcional a complejidad
        delay = 1.0 + seg["complexity"] * 0.3
        time.sleep(delay)

        # Simular resultado (98% éxito)
        status_icon = "✓" if i != 6 else "⚠️"  # Un warning para realismo
        rules_applied = 2 + seg["complexity"] // 3
        
        print(f"    {status_icon} [{i}/{total_segments}] {seg['name']}")
        print(f"       📐 {rules_applied} reglas duras aplicadas → IA completa migración")
        
        if i == 6:
            print(f"       ⚠️  Warning: unsafe pointer detectado, corregido automáticamente")

        save_state({
            "client": DEMO_CLIENT,
            "project": DEMO_PROJECT,
            "execution": {"start_time": start_time, "end_time": "", "total_duration": phase_duration + i * delay, "status": "in_progress"},
            "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": total_segments, "segments_migrated": i, "segments_compiled": 0, "compilation_rate": 0},
            "phases": phases.copy(),
        })

    migrate_duration = sum(1.0 + s["complexity"] * 0.3 for s in DEMO_SEGMENTS)
    phase_duration += migrate_duration
    phases.append({"phase": "migrate", "status": "success", "duration_seconds": round(migrate_duration, 1), "timestamp": datetime.now().isoformat()})
    save_state({
        "client": DEMO_CLIENT,
        "project": DEMO_PROJECT,
        "execution": {"start_time": start_time, "end_time": "", "total_duration": round(phase_duration, 1), "status": "in_progress"},
        "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": total_segments, "segments_migrated": total_segments, "segments_compiled": 0, "compilation_rate": 0},
        "phases": phases.copy(),
    })
    print(f"\n  ✅ Migración completada: {total_segments}/{total_segments} funcionalidades migradas")
    print(f"     → Entrega Sprint 3: Módulos individuales en Rust")
    print()

    # ═══════════════════════════════════════════════════════════
    # SPRINT 4: VALIDACIÓN DE COMPILACIÓN
    # ═══════════════════════════════════════════════════════════
    print("━" * 62)
    print("  📋 SPRINT 4: Validación de Compilación")
    print("  📦 Entrega: Reporte de calidad y cobertura")
    print("━" * 62)
    input("  → Presiona ENTER para validar compilación (Podman + Rust)...")
    print()
    print("  🐳 Compilando en contenedor aislado (rust:1-alpine)")
    print()

    compiled = 0
    for i, seg in enumerate(DEMO_SEGMENTS, 1):
        time.sleep(1.2)
        # 7 de 8 compilan (87.5%)
        compiles = i != 4  # batch_processor falla primero
        if compiles:
            compiled += 1
            print(f"    ✓ [{i}/{total_segments}] {seg['name']} → COMPILA")
        else:
            print(f"    ✗ [{i}/{total_segments}] {seg['name']} → ERROR (reintentando...)")
            time.sleep(2.0)
            compiled += 1
            print(f"    ✓ [{i}/{total_segments}] {seg['name']} → COMPILA (intento 2)")

        rate = round(compiled / i * 100, 0)
        save_state({
            "client": DEMO_CLIENT,
            "project": DEMO_PROJECT,
            "execution": {"start_time": start_time, "end_time": "", "total_duration": round(phase_duration + i * 1.5, 1), "status": "in_progress"},
            "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": total_segments, "segments_migrated": total_segments, "segments_compiled": compiled, "compilation_rate": rate},
            "phases": phases.copy(),
        })

    phase_duration += 14.0
    phases.append({"phase": "validate", "status": "success", "duration_seconds": 14.0, "timestamp": datetime.now().isoformat()})
    final_rate = 100.0  # Todos compilan al final
    save_state({
        "client": DEMO_CLIENT,
        "project": DEMO_PROJECT,
        "execution": {"start_time": start_time, "end_time": "", "total_duration": round(phase_duration, 1), "status": "in_progress"},
        "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": total_segments, "segments_migrated": total_segments, "segments_compiled": total_segments, "compilation_rate": final_rate},
        "phases": phases.copy(),
    })
    print(f"\n  ✅ Validación completada: {total_segments}/{total_segments} compilan (100%)")
    print(f"     → Entrega Sprint 4: Certificación de compilación")
    print()

    # ═══════════════════════════════════════════════════════════
    # SPRINT 5: ENSAMBLAJE FINAL
    # ═══════════════════════════════════════════════════════════
    print("━" * 62)
    print("  📋 SPRINT 5: Ensamblaje Final")
    print("  📦 Entrega: Sistema completo migrado + reporte ejecutivo")
    print("━" * 62)
    input("  → Presiona ENTER para ensamblar el producto final...")
    print()

    time.sleep(2.0)
    print("    📦 Unificando módulos en proyecto Rust...")
    time.sleep(1.5)
    print("    📝 Generando Cargo.toml...")
    time.sleep(1.0)
    print("    📄 Generando reporte HTML ejecutivo...")
    time.sleep(1.5)
    print("    ✓ Producto final listo")

    phase_duration += 6.0
    phases.append({"phase": "assemble", "status": "success", "duration_seconds": 6.0, "timestamp": datetime.now().isoformat()})

    # Estado final
    end_time = datetime.now().isoformat()
    save_state({
        "client": DEMO_CLIENT,
        "project": DEMO_PROJECT,
        "execution": {"start_time": start_time, "end_time": end_time, "total_duration": round(phase_duration, 1), "status": "completed"},
        "metrics": {"total_files": total_files, "total_lines": total_lines, "total_segments": total_segments, "segments_migrated": total_segments, "segments_compiled": total_segments, "compilation_rate": final_rate},
        "phases": phases,
    })

    # ═══════════════════════════════════════════════════════════
    # RESUMEN EJECUTIVO
    # ═══════════════════════════════════════════════════════════
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                  ✅ MIGRACIÓN COMPLETADA                     ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Cliente: {DEMO_CLIENT['name']:<50}║")
    print(f"║  Proyecto: {DEMO_PROJECT['name']:<49}║")
    print(f"║  Archivos migrados: {total_files:<40}║")
    print(f"║  Líneas de código: {total_lines:,}{' ' * (40 - len(f'{total_lines:,}'))}║")
    print(f"║  Funcionalidades: {total_segments:<42}║")
    print(f"║  Tasa de compilación: 100%{' ' * 34}║")
    print(f"║  Duración total: {phase_duration:.0f}s{' ' * (41 - len(f'{phase_duration:.0f}s'))}║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  📄 Reporte: output/demo/reporte_migracion.html             ║")
    print("║  📊 Dashboard: http://localhost:5173                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Generar reporte HTML
    _generate_demo_report(start_time, end_time, phase_duration, total_files, total_lines, total_segments, phases)

    print("  💡 El dashboard sigue activo. Presiona Ctrl+C para cerrar.")
    print()


def _generate_demo_report(start_time, end_time, duration, files, lines, segments, phases):
    """Genera reporte HTML demo."""
    from src.migrator.report_generator import ReportGenerator
    
    # El ReportGenerator lee del state file
    gen = ReportGenerator()
    report_path = gen.generate(
        str(STATE_FILE),
        output_path="output/demo/reporte_migracion.html"
    )
    print(f"  📄 Reporte HTML generado: {report_path}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print_banner()
    
    # Iniciar API en background
    print("  🚀 Iniciando API del dashboard en puerto 8787...")
    start_api()
    print("  ✓ API lista")
    print()
    print("  📌 Instrucciones para el video:")
    print("     1. Abre otra terminal: cd dashboard && pnpm run dev")
    print("     2. Abre el navegador en http://localhost:5173")
    print("     3. Graba la pantalla con ambas ventanas visibles")
    print("     4. Presiona ENTER en cada sprint para avanzar")
    print()
    input("  → Presiona ENTER cuando estés listo para empezar la demo...")
    print()

    try:
        simulate_pipeline()
        # Mantener API viva para que el dashboard siga mostrando datos
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  👋 Demo finalizado. ¡Buen video!")
