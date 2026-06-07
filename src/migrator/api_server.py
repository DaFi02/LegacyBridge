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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        if path == "/api/status":
            self._serve_status()
        elif path == "/api/projects":
            self._serve_projects()
        elif path == "/api/code":
            self._serve_code()
        elif path == "/api/output":
            self._serve_output()
        elif path == "/api/examples":
            self._serve_examples()
        elif path == "/api/health":
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        path = urlparse(self.path).path
        
        # CORS headers
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        if path == "/api/migrate":
            self._handle_migrate(body)
        elif path == "/api/browse":
            self._handle_browse(body)
        elif path == "/api/load-folder":
            self._handle_load_folder(body)
        else:
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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

    def _serve_output(self):
        """Sirve el resultado de ejecutar el binario migrado."""
        import subprocess

        base = Path(self.state_dir).parent
        rust_dir = (base / "output" / "ai_cobol_rust").resolve()

        results = []
        if rust_dir.exists():
            for rs_file in sorted(rust_dir.glob("*.rs")):
                try:
                    # Compilar y ejecutar en Podman
                    cmd = [
                        "podman", "run", "--rm",
                        "-v", f"{rust_dir}:/code:Z",
                        "rust:1-alpine",
                        "sh", "-c",
                        f"cd /code && rustc {rs_file.name} -o /tmp/prog 2>/dev/null && /tmp/prog 2>&1 || echo '[ERROR DE COMPILACIÓN]'"
                    ]
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    output = proc.stdout.strip() or proc.stderr.strip()
                    results.append({
                        "file": rs_file.name,
                        "source_file": rs_file.stem + ".cob",
                        "output": output,
                        "success": "[ERROR" not in output,
                        "compiled": True,
                    })
                except subprocess.TimeoutExpired:
                    results.append({
                        "file": rs_file.name,
                        "source_file": rs_file.stem + ".cob",
                        "output": "[TIMEOUT - excedió 30s]",
                        "success": False,
                        "compiled": False,
                    })
                except FileNotFoundError:
                    results.append({
                        "file": rs_file.name,
                        "source_file": rs_file.stem + ".cob",
                        "output": "[Podman no disponible]",
                        "success": False,
                        "compiled": False,
                    })

        self.wfile.write(json.dumps(results, ensure_ascii=False).encode())

    def _serve_examples(self):
        """Lista archivos de ejemplo disponibles para migrar."""
        base = Path(self.state_dir).parent
        examples_dir = base / "examples"
        
        examples = []
        example_configs = {
            "java7_tienda": {"source_lang": "java7", "target_lang": "python", "label": "Java 7 → Python"},
            "php_legacy": {"source_lang": "php", "target_lang": "python", "label": "PHP → Python"},
            "html_legacy": {"source_lang": "html", "target_lang": "react", "label": "HTML/JS → React+Tailwind"},
            "cobol": {"source_lang": "cobol", "target_lang": "rust", "label": "COBOL → Rust"},
            "cpp_legacy": {"source_lang": "cpp", "target_lang": "rust", "label": "C++ → Rust"},
        }
        
        for folder, config in example_configs.items():
            folder_path = examples_dir / folder
            if folder_path.exists():
                for f in sorted(folder_path.iterdir()):
                    if f.is_file() and not f.name.startswith("."):
                        examples.append({
                            "folder": folder,
                            "file": f.name,
                            "path": str(f.relative_to(base)),
                            "source_lang": config["source_lang"],
                            "target_lang": config["target_lang"],
                            "label": config["label"],
                            "code": f.read_text(encoding="utf-8", errors="replace"),
                            "lines": len(f.read_text(encoding="utf-8", errors="replace").splitlines()),
                        })
        
        self.wfile.write(json.dumps(examples, ensure_ascii=False).encode())

    def _handle_migrate(self, body: str):
        """Ejecuta migración con IA."""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.wfile.write(json.dumps({"error": "JSON inválido"}).encode())
            return

        source_code = data.get("source_code", "")
        migration_type = data.get("migration_type", "")
        
        if not source_code or not migration_type:
            self.wfile.write(json.dumps({"error": "Faltan campos: source_code, migration_type"}).encode())
            return

        from src.migrator.ai_migrator import AIMigrator
        
        api_key = os.environ.get("NVIDIA_API_KEY", "")
        if not api_key:
            self.wfile.write(json.dumps({"error": "NVIDIA_API_KEY no configurada en .env"}).encode())
            return

        migrator = AIMigrator(api_key=api_key)
        result = migrator.migrate(source_code, migration_type)
        
        response = {
            "success": result.success,
            "source_language": result.source_language,
            "target_language": result.target_language,
            "migrated_code": result.migrated_code,
            "model": result.model,
            "error": result.error,
        }
        
        # Guardar resultado si fue exitoso
        if result.success:
            base = Path(self.state_dir).parent
            output_dir = base / "output" / f"ai_{result.source_language}_to_{result.target_language}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre de archivo
            ext_map = {"python": ".py", "rust": ".rs", "java": ".java", "react": ".tsx"}
            ext = ext_map.get(result.target_language, ".txt")
            filename = data.get("filename", "migrated") 
            if "." in filename:
                filename = filename.rsplit(".", 1)[0]
            output_file = output_dir / (filename + ext)
            output_file.write_text(result.migrated_code, encoding="utf-8")
            response["output_path"] = str(output_file)
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

    def _handle_browse(self, body: str):
        """Lista contenido de un directorio para el file browser."""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.wfile.write(json.dumps({"error": "JSON inválido"}).encode())
            return

        target_path = Path(data.get("path", str(Path.home()))).expanduser()
        
        if not target_path.exists():
            self.wfile.write(json.dumps({"error": "Directorio no existe", "path": str(target_path)}).encode())
            return
        if not target_path.is_dir():
            self.wfile.write(json.dumps({"error": "No es un directorio"}).encode())
            return

        items = []
        try:
            for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                # Skip hidden files/dirs and common non-useful dirs
                if item.name.startswith(".") or item.name in ("node_modules", "__pycache__", ".git", "venv", ".venv"):
                    continue
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "path": str(item),
                    "size": item.stat().st_size if item.is_file() else None,
                })
        except PermissionError:
            pass

        self.wfile.write(json.dumps({
            "current": str(target_path),
            "parent": str(target_path.parent) if target_path != target_path.parent else None,
            "items": items,
        }, ensure_ascii=False).encode())

    def _handle_load_folder(self, body: str):
        """Carga todos los archivos de código de una carpeta seleccionada."""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.wfile.write(json.dumps({"error": "JSON inválido"}).encode())
            return

        folder_path = Path(data.get("path", ""))
        if not folder_path.exists() or not folder_path.is_dir():
            self.wfile.write(json.dumps({"error": "Carpeta no existe"}).encode())
            return

        # Code file extensions we support
        code_extensions = {
            ".java", ".php", ".html", ".htm", ".js", ".cpp", ".c", ".h",
            ".cob", ".cbl", ".py", ".rb", ".cs", ".vb", ".pl", ".pas",
        }

        # Detect language from extensions found
        lang_map = {
            ".java": "java7", ".php": "php", ".html": "html", ".htm": "html",
            ".js": "html", ".cpp": "cpp", ".c": "cpp", ".h": "cpp",
            ".cob": "cobol", ".cbl": "cobol", ".py": "python",
        }

        files = []
        detected_lang = None
        for f in sorted(folder_path.rglob("*")):
            if f.is_file() and f.suffix.lower() in code_extensions:
                # Skip very large files
                if f.stat().st_size > 100_000:
                    continue
                try:
                    code = f.read_text(encoding="utf-8", errors="replace")
                    files.append({
                        "name": f.name,
                        "path": str(f),
                        "relative": str(f.relative_to(folder_path)),
                        "code": code,
                        "lines": len(code.splitlines()),
                        "extension": f.suffix.lower(),
                    })
                    if not detected_lang:
                        detected_lang = lang_map.get(f.suffix.lower())
                except Exception:
                    continue

        # Suggest migration type
        target_map = {
            "java7": "python", "php": "python", "html": "react",
            "cpp": "rust", "cobol": "rust",
        }
        suggested_target = target_map.get(detected_lang, "python")

        self.wfile.write(json.dumps({
            "folder": str(folder_path),
            "folder_name": folder_path.name,
            "files": files,
            "total_files": len(files),
            "total_lines": sum(f["lines"] for f in files),
            "detected_language": detected_lang,
            "suggested_migration": f"{detected_lang}_to_{suggested_target}" if detected_lang else None,
        }, ensure_ascii=False).encode())

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
