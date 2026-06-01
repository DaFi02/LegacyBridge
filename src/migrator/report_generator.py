"""Generador de reportes HTML profesionales para clientes.

Genera un reporte visual con métricas, progreso y detalles
de la migración para entregar al cliente.
"""

import json
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """Genera reportes HTML profesionales de migración."""

    def generate(self, state_file: str, output_path: str | None = None) -> str:
        """Genera reporte HTML desde el estado guardado.
        
        Args:
            state_file: Ruta al .supervised_state.json
            output_path: Ruta donde guardar el HTML (opcional)
            
        Returns:
            Ruta al archivo HTML generado
        """
        with open(state_file) as f:
            data = json.load(f)

        html = self._render(data)
        
        if not output_path:
            output_path = str(Path(state_file).parent / "reporte_migracion.html")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def _render(self, data: dict) -> str:
        """Renderiza el HTML del reporte."""
        client = data.get("client", {})
        project = data.get("project", {})
        execution = data.get("execution", {})
        metrics = data.get("metrics", {})
        phases = data.get("phases", [])

        status_color = {
            "completed": "#10b981",
            "failed": "#ef4444",
            "in_progress": "#f59e0b",
            "paused": "#6b7280",
        }.get(execution.get("status", ""), "#6b7280")

        status_label = {
            "completed": "✓ COMPLETADO",
            "failed": "✗ FALLIDO",
            "in_progress": "⟳ EN PROGRESO",
            "paused": "⏸ PAUSADO",
        }.get(execution.get("status", ""), "DESCONOCIDO")

        # Generar filas de fases
        phases_html = ""
        for p in phases:
            p_status = p.get("status", "")
            p_icon = {"success": "✓", "failed": "✗", "skipped": "⏭", "cancelled": "✗"}.get(p_status, "?")
            p_color = {"success": "#10b981", "failed": "#ef4444", "skipped": "#6b7280", "cancelled": "#ef4444"}.get(p_status, "#6b7280")
            phases_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{p.get('phase', '').upper()}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; color: {p_color}; font-weight: 600;">{p_icon} {p_status.upper()}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{p.get('duration_seconds', 0):.1f}s</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">{p.get('timestamp', '')[:19]}</td>
            </tr>"""

        compilation_rate = metrics.get("compilation_rate", 0)
        rate_color = "#10b981" if compilation_rate >= 80 else "#f59e0b" if compilation_rate >= 50 else "#ef4444"

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Migración — {client.get('name', 'Cliente')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 40px; border-radius: 16px; margin-bottom: 32px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header p {{ opacity: 0.8; font-size: 14px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 32px; }}
        .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h3 {{ font-size: 13px; text-transform: uppercase; color: #64748b; margin-bottom: 8px; letter-spacing: 0.5px; }}
        .card .value {{ font-size: 32px; font-weight: 700; color: #1e293b; }}
        .card .sub {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
        .section {{ background: white; border-radius: 12px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }}
        .section h2 {{ font-size: 18px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e5e7eb; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 12px; background: #f1f5f9; font-size: 12px; text-transform: uppercase; color: #64748b; }}
        .progress-bar {{ width: 100%; height: 12px; background: #e5e7eb; border-radius: 6px; overflow: hidden; }}
        .progress-fill {{ height: 100%; border-radius: 6px; transition: width 0.5s; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .info-item {{ padding: 8px 0; }}
        .info-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; }}
        .info-value {{ font-size: 15px; font-weight: 500; }}
        .footer {{ text-align: center; padding: 32px; color: #94a3b8; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h1>🌉 Reporte de Migración</h1>
                    <p>{project.get('name', 'Proyecto de Migración')}</p>
                </div>
                <span class="badge" style="background: {status_color}; color: white;">{status_label}</span>
            </div>
        </div>

        <!-- Métricas principales -->
        <div class="grid">
            <div class="card">
                <h3>Archivos Analizados</h3>
                <div class="value">{metrics.get('total_files', 0)}</div>
                <div class="sub">{metrics.get('total_lines', 0):,} líneas de código</div>
            </div>
            <div class="card">
                <h3>Segmentos Migrados</h3>
                <div class="value">{metrics.get('segments_migrated', 0)}/{metrics.get('total_segments', 0)}</div>
                <div class="sub">fragmentos de código</div>
            </div>
            <div class="card">
                <h3>Compilación Exitosa</h3>
                <div class="value" style="color: {rate_color};">{compilation_rate:.0f}%</div>
                <div class="sub">{metrics.get('segments_compiled', 0)} segmentos compilan</div>
            </div>
            <div class="card">
                <h3>Tiempo Total</h3>
                <div class="value">{execution.get('total_duration', 0):.0f}s</div>
                <div class="sub">{self._format_duration(execution.get('total_duration', 0))}</div>
            </div>
        </div>

        <!-- Barra de progreso -->
        <div class="section">
            <h2>Progreso de Compilación</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {compilation_rate}%; background: {rate_color};"></div>
            </div>
            <p style="margin-top: 8px; font-size: 13px; color: #64748b;">
                {metrics.get('segments_compiled', 0)} de {metrics.get('total_segments', 0)} segmentos compilan correctamente
            </p>
        </div>

        <!-- Info del proyecto -->
        <div class="section">
            <h2>Información del Proyecto</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Cliente</div>
                    <div class="info-value">{client.get('name', '-')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Industria</div>
                    <div class="info-value">{client.get('industry', '-')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Lenguaje Origen</div>
                    <div class="info-value">{project.get('source_language', '-').upper()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Lenguaje Destino</div>
                    <div class="info-value">{project.get('target_language', '-').upper()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Contacto</div>
                    <div class="info-value">{client.get('contact', '-')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Fecha de Ejecución</div>
                    <div class="info-value">{execution.get('start_time', '')[:10]}</div>
                </div>
            </div>
        </div>

        <!-- Fases -->
        <div class="section">
            <h2>Detalle de Fases</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fase</th>
                        <th>Estado</th>
                        <th>Duración</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {phases_html}
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Generado por <strong>LegacyBridge</strong> — {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p style="margin-top: 4px;">Migración automatizada con IA + validación en contenedores</p>
        </div>
    </div>
</body>
</html>"""

    def _format_duration(self, seconds: float) -> str:
        """Formatea duración en formato legible."""
        if seconds < 60:
            return f"{seconds:.0f} segundos"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"
