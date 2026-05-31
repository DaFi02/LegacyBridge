"""Analizador de código fuente.

Extrae la estructura del código sin ejecutarlo:
- Funciones/métodos (nombre, parámetros, líneas)
- Structs/clases
- Dependencias (imports/includes)
- Variables globales
- Complejidad estimada

Esto permite a la IA tener contexto reducido de todo el proyecto
antes de migrar cada segmento.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SymbolInfo:
    """Información de un símbolo encontrado en el código."""
    name: str
    kind: str                   # function, struct, class, enum, global, constant, typedef
    start_line: int
    end_line: int
    params: list[str] = field(default_factory=list)
    return_type: str = ""
    dependencies: list[str] = field(default_factory=list)  # Otros símbolos que usa
    complexity: int = 1         # Estimación de complejidad (1-10)
    docstring: str = ""


@dataclass
class FileAnalysis:
    """Análisis completo de un archivo fuente."""
    filepath: str
    language: str
    total_lines: int
    symbols: list[SymbolInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    global_vars: list[str] = field(default_factory=list)
    
    def summary(self) -> str:
        """Resumen compacto para dar contexto a la IA."""
        lines = [f"// Archivo: {Path(self.filepath).name} ({self.language}, {self.total_lines} líneas)"]
        lines.append(f"// Imports: {', '.join(self.imports[:10]) if self.imports else 'ninguno'}")
        lines.append("// Símbolos:")
        for sym in self.symbols:
            params_str = f"({', '.join(sym.params)})" if sym.params else "()"
            ret = f" -> {sym.return_type}" if sym.return_type else ""
            lines.append(f"//   {sym.kind}: {sym.name}{params_str}{ret} [L{sym.start_line}-{sym.end_line}]")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serializa para persistir en el estado."""
        return {
            "filepath": self.filepath,
            "language": self.language,
            "total_lines": self.total_lines,
            "imports": self.imports,
            "global_vars": self.global_vars,
            "symbols": [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "start_line": s.start_line,
                    "end_line": s.end_line,
                    "params": s.params,
                    "return_type": s.return_type,
                    "dependencies": s.dependencies,
                    "complexity": s.complexity,
                }
                for s in self.symbols
            ],
        }


class CodeAnalyzer:
    """Analiza código fuente y extrae su estructura.
    
    Soporta: C/C++, COBOL, Java, Rust (como referencia).
    """

    # Extensiones soportadas por lenguaje
    LANGUAGE_MAP = {
        ".c": "c", ".h": "c",
        ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
        ".cob": "cobol", ".cbl": "cobol",
        ".java": "java",
        ".rs": "rust",
    }

    def analyze_file(self, filepath: Path) -> FileAnalysis:
        """Analiza un archivo y retorna su estructura."""
        suffix = filepath.suffix.lower()
        language = self.LANGUAGE_MAP.get(suffix, "unknown")
        content = filepath.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        analysis = FileAnalysis(
            filepath=str(filepath),
            language=language,
            total_lines=len(lines),
        )

        if language in ("c", "cpp"):
            self._analyze_cpp(content, lines, analysis)
        elif language == "cobol":
            self._analyze_cobol(content, lines, analysis)
        elif language == "java":
            self._analyze_java(content, lines, analysis)
        elif language == "rust":
            self._analyze_rust(content, lines, analysis)

        return analysis

    def analyze_directory(self, dirpath: Path) -> list[FileAnalysis]:
        """Analiza todos los archivos soportados en un directorio."""
        results = []
        for f in sorted(dirpath.rglob("*")):
            if f.suffix.lower() in self.LANGUAGE_MAP:
                results.append(self.analyze_file(f))
        return results

    def project_summary(self, analyses: list[FileAnalysis]) -> str:
        """Genera un resumen del proyecto completo para contexto de IA."""
        lines = ["// === RESUMEN DEL PROYECTO ==="]
        lines.append(f"// Archivos: {len(analyses)}")
        total_lines = sum(a.total_lines for a in analyses)
        total_symbols = sum(len(a.symbols) for a in analyses)
        lines.append(f"// Total líneas: {total_lines}")
        lines.append(f"// Total símbolos: {total_symbols}")
        lines.append("//")
        for a in analyses:
            lines.append(a.summary())
            lines.append("//")
        return "\n".join(lines)

    # --- Analizadores por lenguaje ---

    def _analyze_cpp(self, content: str, lines: list[str], analysis: FileAnalysis) -> None:
        """Extrae estructura de código C/C++."""
        # Includes
        for match in re.finditer(r'#include\s*[<"]([^>"]+)[>"]', content):
            analysis.imports.append(match.group(1))

        # Funciones
        func_pattern = re.compile(
            r'^(?:static\s+|inline\s+|virtual\s+|extern\s+)*'
            r'([\w:*&<>]+(?:\s*[*&])?)\s+'
            r'([\w:]+)\s*\(([^)]*)\)\s*(?:const\s*)?(?:override\s*)?[{;]',
            re.MULTILINE
        )
        for match in func_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            params = [p.strip() for p in match.group(3).split(',') if p.strip()]
            analysis.symbols.append(SymbolInfo(
                name=match.group(2),
                kind="function",
                start_line=start_line,
                end_line=end_line,
                params=params,
                return_type=match.group(1).strip(),
                complexity=self._estimate_complexity(lines[start_line-1:end_line]),
            ))

        # Structs/Classes
        struct_pattern = re.compile(
            r'^(?:typedef\s+)?(?:struct|class)\s+(\w+)\s*[{:]', re.MULTILINE
        )
        for match in struct_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            analysis.symbols.append(SymbolInfo(
                name=match.group(1),
                kind="struct" if "struct" in match.group(0) else "class",
                start_line=start_line,
                end_line=end_line,
                complexity=self._estimate_complexity(lines[start_line-1:end_line]),
            ))

        # Enums
        enum_pattern = re.compile(r'^(?:typedef\s+)?enum\s+(\w+)\s*{', re.MULTILINE)
        for match in enum_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            analysis.symbols.append(SymbolInfo(
                name=match.group(1),
                kind="enum",
                start_line=start_line,
                end_line=end_line,
            ))

        # Globals/Constants
        global_pattern = re.compile(
            r'^(?:const\s+|static\s+)?([\w:]+)\s+(\w+)\s*=', re.MULTILINE
        )
        for match in global_pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Skip if inside a function
            if not self._is_inside_function(line_num, analysis.symbols):
                analysis.global_vars.append(match.group(2))

    def _analyze_cobol(self, content: str, lines: list[str], analysis: FileAnalysis) -> None:
        """Extrae estructura de código COBOL."""
        # Divisions y Sections como imports/estructura
        for match in re.finditer(r'^\s{6}\s+(\w[\w-]*)\s+DIVISION', content, re.MULTILINE):
            analysis.imports.append(f"{match.group(1)} DIVISION")

        # COPY statements (imports de COBOL)
        for match in re.finditer(r'COPY\s+([\w-]+)', content, re.IGNORECASE):
            analysis.imports.append(f"COPY {match.group(1)}")

        # Variables de WORKING-STORAGE (niveles 01 y 77)
        ws_pattern = re.compile(
            r'^\s{6}\s+(?:01|77)\s+([\w-]+)', re.MULTILINE
        )
        for match in ws_pattern.finditer(content):
            name = match.group(1).strip()
            if name.upper() not in ('FILLER',):
                analysis.global_vars.append(name)

        # Paragraphs (funciones de COBOL)
        para_pattern = re.compile(r'^\s{6}\s+([\w-]+)\.\s*$', re.MULTILINE)
        paragraphs = list(para_pattern.finditer(content))
        
        for i, match in enumerate(paragraphs):
            start_line = content[:match.start()].count('\n') + 1
            # El párrafo termina donde empieza el siguiente
            if i + 1 < len(paragraphs):
                end_line = content[:paragraphs[i+1].start()].count('\n')
            else:
                end_line = len(lines)
            
            name = match.group(1).strip()
            # Filtrar divisiones/secciones
            if any(kw in name.upper() for kw in ('DIVISION', 'SECTION', 'STORAGE')):
                continue

            analysis.symbols.append(SymbolInfo(
                name=name,
                kind="function",  # Paragraphs son las "funciones" de COBOL
                start_line=start_line,
                end_line=end_line,
                complexity=self._estimate_complexity(lines[start_line-1:end_line]),
            ))

    def _analyze_java(self, content: str, lines: list[str], analysis: FileAnalysis) -> None:
        """Extrae estructura de código Java."""
        # Imports
        for match in re.finditer(r'^import\s+([\w.]+);', content, re.MULTILINE):
            analysis.imports.append(match.group(1))

        # Package
        pkg_match = re.search(r'^package\s+([\w.]+);', content, re.MULTILINE)
        if pkg_match:
            analysis.imports.insert(0, f"package:{pkg_match.group(1)}")

        # Classes
        class_pattern = re.compile(
            r'(?:public|private|protected)?\s*(?:abstract\s+|final\s+)?class\s+(\w+)'
            r'(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*{',
            re.MULTILINE
        )
        for match in class_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            deps = []
            if match.group(2):
                deps.append(match.group(2))
            if match.group(3):
                deps.extend(i.strip() for i in match.group(3).split(','))
            analysis.symbols.append(SymbolInfo(
                name=match.group(1),
                kind="class",
                start_line=start_line,
                end_line=end_line,
                dependencies=deps,
                complexity=self._estimate_complexity(lines[start_line-1:end_line]),
            ))

        # Methods
        method_pattern = re.compile(
            r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?'
            r'([\w<>\[\]]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s]+)?\s*{',
            re.MULTILINE
        )
        for match in method_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            params = [p.strip() for p in match.group(3).split(',') if p.strip()]
            analysis.symbols.append(SymbolInfo(
                name=match.group(2),
                kind="function",
                start_line=start_line,
                end_line=end_line,
                params=params,
                return_type=match.group(1).strip(),
                complexity=self._estimate_complexity(lines[start_line-1:end_line]),
            ))

    def _analyze_rust(self, content: str, lines: list[str], analysis: FileAnalysis) -> None:
        """Extrae estructura de código Rust (para referencia/validación)."""
        # Use statements
        for match in re.finditer(r'^use\s+([\w:{}*,\s]+);', content, re.MULTILINE):
            analysis.imports.append(match.group(1).strip())

        # Functions
        fn_pattern = re.compile(
            r'^(?:pub\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?:->\s*([\w<>&\[\]]+))?\s*{',
            re.MULTILINE
        )
        for match in fn_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            params = [p.strip() for p in match.group(2).split(',') if p.strip()]
            analysis.symbols.append(SymbolInfo(
                name=match.group(1),
                kind="function",
                start_line=start_line,
                end_line=end_line,
                params=params,
                return_type=match.group(3) or "",
                complexity=self._estimate_complexity(lines[start_line-1:end_line]),
            ))

        # Structs
        struct_pattern = re.compile(r'^(?:pub\s+)?struct\s+(\w+)', re.MULTILINE)
        for match in struct_pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(lines, start_line - 1)
            analysis.symbols.append(SymbolInfo(
                name=match.group(1),
                kind="struct",
                start_line=start_line,
                end_line=end_line,
            ))

    # --- Utilidades ---

    def _find_block_end(self, lines: list[str], start_idx: int) -> int:
        """Encuentra el final de un bloque delimitado por llaves."""
        depth = 0
        found_open = False
        for i in range(start_idx, len(lines)):
            for ch in lines[i]:
                if ch == '{':
                    depth += 1
                    found_open = True
                elif ch == '}':
                    depth -= 1
                    if found_open and depth == 0:
                        return i + 1  # Línea 1-indexed
        return min(start_idx + 20, len(lines))  # Fallback

    def _estimate_complexity(self, block_lines: list[str]) -> int:
        """Estima complejidad ciclomática simplificada (1-10)."""
        text = "\n".join(block_lines)
        complexity = 1
        # Cada branch/loop suma complejidad
        patterns = [
            r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
            r'\bswitch\b', r'\bcase\b', r'\bcatch\b',
            r'\bPERFORM\b', r'\bIF\b', r'\bEVALUATE\b',  # COBOL
            r'\bmatch\b',  # Rust
            r'&&', r'\|\|',
        ]
        for pat in patterns:
            complexity += len(re.findall(pat, text))
        return min(complexity, 10)

    def _is_inside_function(self, line_num: int, symbols: list[SymbolInfo]) -> bool:
        """Verifica si una línea está dentro de alguna función."""
        for sym in symbols:
            if sym.kind == "function" and sym.start_line <= line_num <= sym.end_line:
                return True
        return False
