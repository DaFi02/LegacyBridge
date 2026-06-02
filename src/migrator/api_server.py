"""API HTTP simple para el dashboard de métricas.

Expone el estado del pipeline vía HTTP para el frontend React.
Usa solo la stdlib (http.server) para no agregar dependencias.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


class DashboardAPIHandler(BaseHTTPRequestHandler):
    """Handler HTTP para la API del dashboard."""

    # Se setea desde fuera
    state_dir: str = "output/"
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        # CORS headers
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        if path == "/api/status":
            self._serve_status()
        elif path == "/api/projects":
            self._serve_projects()
        elif path == "/api/code":
            self._serve_code()
        elif path == "/api/health":
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_status(self):
        """Devuelve el estado del último proyecto activo."""
        state_file = self._find_latest_state()
        if state_file:
            with open(state_file) as f:
                data = json.load(f)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        else:
            self.wfile.write(json.dumps({"status": "no_projects"}).encode())

    def _serve_projects(self):
        """Lista todos los proyectos con estado."""
        projects = []
        output_dir = Path(self.state_dir)
        
        for state_file in output_dir.rglob(".supervised_state.json"):
            try:
                with open(state_file) as f:
                    data = json.load(f)
                projects.append({
                    "path": str(state_file.parent),
                    "client": data.get("client", {}).get("name", "?"),
                    "project": data.get("project", {}).get("name", "?"),
                    "status": data.get("execution", {}).get("status", "?"),
                    "migration": f"{data.get('project', {}).get('source_language', '?')} → {data.get('project', {}).get('target_language', '?')}",
                })
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        # También buscar .migration_state.json (pipeline normal)
        for state_file in output_dir.rglob(".migration_state.json"):
            try:
                with open(state_file) as f:
                    data = json.load(f)
                ctx = data.get("context", {})
                projects.append({
                    "path": str(state_file.parent),
                    "client": "Pipeline directo",
                    "project": ctx.get("project_name", "?"),
                    "status": data.get("current_state", "?"),
                    "migration": f"{ctx.get('source_language', '?')} → {ctx.get('target_language', '?')}",
                })
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        self.wfile.write(json.dumps(projects, ensure_ascii=False).encode())

    def _find_latest_state(self) -> str | None:
        """Encuentra el archivo de estado más reciente."""
        output_dir = Path(self.state_dir)
        state_files = list(output_dir.rglob(".supervised_state.json"))
        if not state_files:
            state_files = list(output_dir.rglob(".migration_state.json"))
        if state_files:
            return str(max(state_files, key=lambda f: f.stat().st_mtime))
        return None

    def _serve_code(self):
        """Sirve pares de código fuente/migrado para comparación visual."""
        base = Path(self.state_dir).parent  # raíz del proyecto
        pairs = []

        # Buscar archivos fuente y su equivalente migrado
        source_dirs = {
            "examples/cobol": ("cobol", "output/ai_cobol_rust", ".cob", ".rs"),
            "examples/cpp_legacy": ("cpp", "output/cpp_to_rust", ".cpp", ".rs"),
        }

        for src_dir, (lang, out_dir, src_ext, tgt_ext) in source_dirs.items():
            src_path = base / src_dir
            out_path = base / out_dir
            if not src_path.exists():
                continue
            for src_file in sorted(src_path.glob(f"*{src_ext}")):
                tgt_file = out_path / (src_file.stem + tgt_ext)
                source_code = src_file.read_text(encoding="utf-8", errors="replace")
                target_code = ""
                if tgt_file.exists():
                    target_code = tgt_file.read_text(encoding="utf-8", errors="replace")
                pairs.append({
                    "source_file": src_file.name,
                    "target_file": tgt_file.name if tgt_file.exists() else f"{src_file.stem}{tgt_ext}",
                    "source_language": lang,
                    "target_language": "rust",
                    "source_code": source_code,
                    "target_code": target_code,
                    "status": "migrated" if target_code else "pending",
                })

        self.wfile.write(json.dumps(pairs, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        """Silenciar logs HTTP normales."""
        pass


def start_api_server(port: int = 8787, state_dir: str = "output/") -> HTTPServer:
    """Inicia el servidor API para el dashboard.
    
    Returns:
        HTTPServer instance (ya corriendo en un thread)
    """
    DashboardAPIHandler.state_dir = state_dir
    server = HTTPServer(("0.0.0.0", port), DashboardAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
