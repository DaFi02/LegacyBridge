"""Segmentador de código fuente.

Divide el código en segmentos migrables individualmente.
Cada segmento es una unidad lógica (función, struct, módulo)
que puede ser migrada por la IA con contexto reducido.

Estrategia de segmentación:
- Cada función/método es un segmento
- Structs/clases con sus métodos son un segmento
- Headers/imports son un segmento separado
- Variables globales/constantes son un segmento
"""

from dataclasses import dataclass, field
from pathlib import Path

from .analyzer import FileAnalysis, SymbolInfo


@dataclass
class CodeSegment:
    """Un segmento de código listo para migrar."""
    segment_id: str             # Identificador único: "archivo::nombre"
    source_file: str            # Archivo de origen
    kind: str                   # header, struct, function, globals, main
    name: str                   # Nombre del símbolo principal
    code: str                   # Código fuente del segmento
    start_line: int
    end_line: int
    dependencies: list[str] = field(default_factory=list)  # IDs de otros segmentos que necesita
    context_summary: str = ""   # Resumen del proyecto para la IA
    complexity: int = 1

    def full_prompt_context(self) -> str:
        """Genera el contexto completo para enviar a la IA."""
        lines = []
        if self.context_summary:
            lines.append(self.context_summary)
            lines.append("")
        lines.append(f"// Segmento: {self.name} ({self.kind})")
        lines.append(f"// Dependencias: {', '.join(self.dependencies) if self.dependencies else 'ninguna'}")
        lines.append("")
        lines.append(self.code)
        return "\n".join(lines)


class CodeSegmenter:
    """Divide código analizado en segmentos migrables.
    
    Usa el resultado del CodeAnalyzer para hacer cortes inteligentes.
    """

    def segment_file(self, analysis: FileAnalysis, source_content: str) -> list[CodeSegment]:
        """Segmenta un archivo basándose en su análisis."""
        lines = source_content.split("\n")
        segments: list[CodeSegment] = []
        file_stem = Path(analysis.filepath).stem

        # 1. Segmento de headers/imports
        header_segment = self._extract_header(analysis, lines, file_stem)
        if header_segment:
            segments.append(header_segment)

        # 2. Segmento de variables globales
        globals_segment = self._extract_globals(analysis, lines, file_stem)
        if globals_segment:
            segments.append(globals_segment)

        # 3. Segmentos por símbolo (funciones, structs, clases)
        # Agrupar: structs/clases con sus métodos
        grouped = self._group_symbols(analysis.symbols)
        for group_name, symbols in grouped.items():
            segment = self._create_symbol_segment(
                symbols, lines, file_stem, group_name, analysis
            )
            if segment:
                segments.append(segment)

        return segments

    def segment_directory(
        self, analyses: list[FileAnalysis], base_dir: Path
    ) -> list[CodeSegment]:
        """Segmenta todos los archivos de un directorio."""
        all_segments = []
        project_summary = self._build_project_summary(analyses)

        for analysis in analyses:
            filepath = Path(analysis.filepath)
            content = filepath.read_text(encoding="utf-8", errors="replace")
            segments = self.segment_file(analysis, content)
            
            # Agregar contexto del proyecto a cada segmento
            for seg in segments:
                seg.context_summary = project_summary

            all_segments.extend(segments)

        return all_segments

    def _extract_header(
        self, analysis: FileAnalysis, lines: list[str], file_stem: str
    ) -> CodeSegment | None:
        """Extrae el segmento de imports/includes."""
        if not analysis.imports:
            return None

        # Encontrar las líneas de imports
        header_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if any(kw in stripped for kw in ('#include', 'import ', 'use ', 'COPY ', 'package ')):
                header_lines.append(line)
            elif stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                header_lines.append(line)  # Incluir comments del header
            elif header_lines and not stripped:
                header_lines.append(line)  # Líneas vacías entre includes
            elif header_lines and stripped and not any(
                kw in stripped for kw in ('#include', 'import ', 'use ', 'COPY ')
            ):
                break  # Ya pasamos la zona de imports

        if not header_lines:
            return None

        return CodeSegment(
            segment_id=f"{file_stem}::header",
            source_file=analysis.filepath,
            kind="header",
            name="imports/includes",
            code="\n".join(header_lines),
            start_line=1,
            end_line=len(header_lines),
            complexity=1,
        )

    def _extract_globals(
        self, analysis: FileAnalysis, lines: list[str], file_stem: str
    ) -> CodeSegment | None:
        """Extrae variables globales/constantes."""
        if not analysis.global_vars:
            return None

        # Buscar líneas con las variables globales
        global_lines = []
        for i, line in enumerate(lines):
            for var in analysis.global_vars:
                if var in line and '=' in line:
                    global_lines.append((i + 1, line))
                    break

        if not global_lines:
            return None

        code = "\n".join(line for _, line in global_lines)
        return CodeSegment(
            segment_id=f"{file_stem}::globals",
            source_file=analysis.filepath,
            kind="globals",
            name="variables_globales",
            code=code,
            start_line=global_lines[0][0],
            end_line=global_lines[-1][0],
            complexity=1,
        )

    def _group_symbols(self, symbols: list[SymbolInfo]) -> dict[str, list[SymbolInfo]]:
        """Agrupa símbolos: structs/clases con funciones contenidas."""
        groups: dict[str, list[SymbolInfo]] = {}
        containers = [s for s in symbols if s.kind in ("struct", "class")]
        functions = [s for s in symbols if s.kind == "function"]
        enums = [s for s in symbols if s.kind == "enum"]

        # Funciones dentro de un struct/class
        assigned_functions = set()
        for container in containers:
            group_name = container.name
            groups[group_name] = [container]
            for func in functions:
                if container.start_line <= func.start_line <= container.end_line:
                    groups[group_name].append(func)
                    assigned_functions.add(func.name)

        # Funciones independientes (no dentro de struct/class)
        for func in functions:
            if func.name not in assigned_functions:
                groups[func.name] = [func]

        # Enums como grupo propio
        for enum in enums:
            groups[enum.name] = [enum]

        return groups

    def _create_symbol_segment(
        self,
        symbols: list[SymbolInfo],
        lines: list[str],
        file_stem: str,
        group_name: str,
        analysis: FileAnalysis,
    ) -> CodeSegment | None:
        """Crea un segmento a partir de un grupo de símbolos."""
        if not symbols:
            return None

        # Rango de líneas del grupo
        start_line = min(s.start_line for s in symbols)
        end_line = max(s.end_line for s in symbols)

        # Extraer código (1-indexed → 0-indexed)
        code = "\n".join(lines[start_line - 1:end_line])
        if not code.strip():
            return None

        # Determinar tipo del segmento
        primary = symbols[0]
        kind = primary.kind

        # Dependencias: otros símbolos referenciados
        deps = []
        for sym in symbols:
            deps.extend(sym.dependencies)

        complexity = max(s.complexity for s in symbols)

        return CodeSegment(
            segment_id=f"{file_stem}::{group_name}",
            source_file=analysis.filepath,
            kind=kind,
            name=group_name,
            code=code,
            start_line=start_line,
            end_line=end_line,
            dependencies=list(set(deps)),
            complexity=complexity,
        )

    def _build_project_summary(self, analyses: list[FileAnalysis]) -> str:
        """Construye un resumen compacto del proyecto."""
        lines = ["// === CONTEXTO DEL PROYECTO ==="]
        for a in analyses:
            lines.append(f"// Archivo: {Path(a.filepath).name} ({a.total_lines} líneas)")
            for sym in a.symbols[:10]:  # Max 10 symbols por archivo
                lines.append(f"//   {sym.kind}: {sym.name}")
        return "\n".join(lines)
