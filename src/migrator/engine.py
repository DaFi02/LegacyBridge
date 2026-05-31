"""Motor principal de migración de código Java 8 a Java 17+."""

from pathlib import Path

from .transformers.base import TransformResult
from .transformers import (
    InstanceofPatternTransformer,
    TextBlockTransformer,
    CollectionFactoryTransformer,
    VarKeywordTransformer,
    SwitchExpressionTransformer,
)


class MigrationEngine:
    """Engine that applies all Java 8 → Java 17+ transformations."""

    def __init__(self, target_version: int = 17):
        self.target_version = target_version
        self.transformers = [
            CollectionFactoryTransformer(),
            VarKeywordTransformer(),
            InstanceofPatternTransformer(),
            TextBlockTransformer(),
            SwitchExpressionTransformer(),
        ]

    def migrate_code(self, source_code: str) -> list[TransformResult]:
        """Apply all applicable transformations to the source code."""
        results = []
        current_code = source_code

        for transformer in self.transformers:
            if transformer.java_version_target <= self.target_version:
                result = transformer.transform(current_code)
                if result.was_modified:
                    results.append(result)
                    current_code = result.transformed

        return results

    def migrate_file(self, input_path: Path, output_path: Path | None = None) -> list[TransformResult]:
        """Migrate a single Java file."""
        source_code = input_path.read_text(encoding="utf-8")
        results = self.migrate_code(source_code)

        if results:
            final_code = results[-1].transformed
        else:
            final_code = source_code

        if output_path is None:
            output_path = input_path.with_suffix(".migrated.java")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_code, encoding="utf-8")

        return results

    def migrate_directory(self, input_dir: Path, output_dir: Path) -> dict[str, list[TransformResult]]:
        """Migrate all Java files in a directory."""
        all_results = {}

        for java_file in input_dir.rglob("*.java"):
            relative = java_file.relative_to(input_dir)
            output_file = output_dir / relative
            results = self.migrate_file(java_file, output_file)
            all_results[str(relative)] = results

        return all_results

    def get_summary(self, all_results: dict[str, list[TransformResult]]) -> str:
        """Generate a human-readable summary of the migration."""
        lines = []
        lines.append("=" * 60)
        lines.append("RESUMEN DE MIGRACIÓN - Java 8 → Java 17+")
        lines.append("=" * 60)

        total_changes = 0
        for filename, results in all_results.items():
            if results:
                lines.append(f"\n📄 {filename}")
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
