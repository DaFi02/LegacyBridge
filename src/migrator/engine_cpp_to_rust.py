"""Motor de migración C++ Legacy → Rust."""

from pathlib import Path

from .transformers_cpp_to_rust.base import TransformResult
from .transformers_cpp_to_rust import (
    IncludesToUseTransformer,
    RawPointerTransformer,
    MemoryManagementTransformer,
    TypesAndStructsTransformer,
    ControlFlowTransformer,
    StringConversionTransformer,
)


class CppToRustEngine:
    """Engine that applies C++ → Rust transformations."""

    def __init__(self):
        self.transformers = [
            IncludesToUseTransformer(),
            TypesAndStructsTransformer(),
            StringConversionTransformer(),
            MemoryManagementTransformer(),
            RawPointerTransformer(),
            ControlFlowTransformer(),
        ]

    def migrate_code(self, source_code: str) -> list[TransformResult]:
        """Apply all transformations to the source code."""
        results = []
        current_code = source_code

        for transformer in self.transformers:
            result = transformer.transform(current_code)
            if result.was_modified:
                results.append(result)
                current_code = result.transformed

        return results

    def migrate_file(self, input_path: Path, output_path: Path | None = None) -> list[TransformResult]:
        """Migrate a single C++ file to Rust."""
        source_code = input_path.read_text(encoding="utf-8")
        results = self.migrate_code(source_code)

        if results:
            final_code = results[-1].transformed
        else:
            final_code = source_code

        if output_path is None:
            output_path = input_path.with_suffix(".rs")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_code, encoding="utf-8")

        return results

    def migrate_directory(self, input_dir: Path, output_dir: Path) -> dict[str, list[TransformResult]]:
        """Migrate all C/C++ files in a directory to Rust."""
        all_results = {}

        for ext in ("*.cpp", "*.cxx", "*.cc", "*.c", "*.hpp", "*.h"):
            for cpp_file in input_dir.rglob(ext):
                relative = cpp_file.relative_to(input_dir)
                output_file = output_dir / relative.with_suffix(".rs")
                results = self.migrate_file(cpp_file, output_file)
                all_results[str(relative)] = results

        return all_results

    def get_summary(self, all_results: dict[str, list[TransformResult]]) -> str:
        """Generate a human-readable summary of the migration."""
        lines = []
        lines.append("=" * 60)
        lines.append("RESUMEN DE MIGRACIÓN - C++ Legacy → Rust")
        lines.append("=" * 60)

        total_changes = 0
        for filename, results in all_results.items():
            if results:
                lines.append(f"\n📄 {filename} → {filename.rsplit('.', 1)[0]}.rs")
                for result in results:
                    for change in result.changes_made:
                        lines.append(f"   ✓ {change}")
                        total_changes += 1
            else:
                lines.append(f"\n📄 {filename} (sin cambios)")

        lines.append(f"\n{'=' * 60}")
        lines.append(f"Total de transformaciones aplicadas: {total_changes}")
        lines.append(f"Archivos procesados: {len(all_results)}")
        lines.append(f"Archivos modificados: {sum(1 for r in all_results.values() if r)}")
        lines.append("=" * 60)

        return "\n".join(lines)
