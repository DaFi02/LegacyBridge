"""
MVP - Software de Refactorización Automatizada de Código Legacy
Migración de Java 8 → Java 17+ y C++ Legacy → Rust

Uso:
    uv run python main.py --demo                        # Demo Java 8 → Java 17
    uv run python main.py --demo-rust                   # Demo C++ → Rust
    uv run python main.py examples/java8 output/java17
    uv run python main.py --cpp-to-rust examples/cpp_legacy output/rust
    uv run python main.py examples/java8/UserService.java
"""

import sys
from pathlib import Path

from src.migrator import MigrationEngine, CppToRustEngine


def print_diff(original: str, transformed: str, filename: str):
    """Print a colorized before/after comparison."""
    print(f"\n{'─' * 60}")
    print(f"📄 {filename}")
    print(f"{'─' * 60}")

    orig_lines = original.splitlines()
    trans_lines = transformed.splitlines()

    # Simple diff - show changed lines
    max_lines = max(len(orig_lines), len(trans_lines))
    changes_shown = 0

    for i in range(max_lines):
        orig = orig_lines[i] if i < len(orig_lines) else ""
        trans = trans_lines[i] if i < len(trans_lines) else ""

        if orig != trans:
            if changes_shown < 30:  # Limit output
                if orig:
                    print(f"  - {orig}")
                if trans:
                    print(f"  + {trans}")
            changes_shown += 1

    if changes_shown > 30:
        print(f"  ... y {changes_shown - 30} cambios más")


def run_demo():
    """Run the migration on the example files."""
    engine = MigrationEngine(target_version=17)
    examples_dir = Path("examples/java8")
    output_dir = Path("output/java17")

    if not examples_dir.exists():
        print("Error: No se encontró la carpeta examples/java8")
        sys.exit(1)

    print("🚀 MVP - Migración Automatizada Java 8 → Java 17+")
    print("=" * 60)

    all_results = engine.migrate_directory(examples_dir, output_dir)

    # Show diffs for each file
    for filename, results in all_results.items():
        if results:
            print_diff(
                results[0].original,
                results[-1].transformed,
                filename,
            )

    # Print summary
    print("\n")
    print(engine.get_summary(all_results))
    print(f"\n📁 Archivos migrados guardados en: {output_dir.resolve()}")


def run_demo_rust():
    """Run the C++ → Rust migration on example files."""
    engine = CppToRustEngine()
    examples_dir = Path("examples/cpp_legacy")
    output_dir = Path("output/rust")

    if not examples_dir.exists():
        print("Error: No se encontró la carpeta examples/cpp_legacy")
        sys.exit(1)

    print("🦀 MVP - Migración Automatizada C++ Legacy → Rust")
    print("=" * 60)

    all_results = engine.migrate_directory(examples_dir, output_dir)

    # Show diffs for each file
    for filename, results in all_results.items():
        if results:
            print_diff(
                results[0].original,
                results[-1].transformed,
                filename,
            )

    # Print summary
    print("\n")
    print(engine.get_summary(all_results))
    print(f"\n📁 Archivos migrados guardados en: {output_dir.resolve()}")


def migrate_file(filepath: str, output: str | None = None):
    """Migrate a single file."""
    engine = MigrationEngine(target_version=17)
    input_path = Path(filepath)

    if not input_path.exists():
        print(f"Error: No se encontró el archivo {filepath}")
        sys.exit(1)

    output_path = Path(output) if output else None
    results = engine.migrate_file(input_path, output_path)

    if results:
        actual_output = output_path or input_path.with_suffix(".migrated.java")
        print_diff(results[0].original, results[-1].transformed, input_path.name)
        print(f"\n✓ Archivo migrado: {actual_output}")
        for result in results:
            for change in result.changes_made:
                print(f"  • {change}")
    else:
        print(f"ℹ️  {input_path.name}: no se encontraron patrones para migrar")


def migrate_directory(input_dir: str, output_dir: str):
    """Migrate all Java files in a directory."""
    engine = MigrationEngine(target_version=17)
    results = engine.migrate_directory(Path(input_dir), Path(output_dir))
    print(engine.get_summary(results))
    print(f"\n📁 Archivos migrados guardados en: {Path(output_dir).resolve()}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--demo":
        run_demo()
    elif sys.argv[1] == "--demo-rust":
        run_demo_rust()
    elif sys.argv[1] == "--cpp-to-rust" and len(sys.argv) >= 4:
        engine = CppToRustEngine()
        results = engine.migrate_directory(Path(sys.argv[2]), Path(sys.argv[3]))
        print(engine.get_summary(results))
        print(f"\n📁 Archivos migrados guardados en: {Path(sys.argv[3]).resolve()}")
    elif len(sys.argv) == 2:
        migrate_file(sys.argv[1])
    elif len(sys.argv) == 3:
        input_path = Path(sys.argv[1])
        if input_path.is_dir():
            migrate_directory(sys.argv[1], sys.argv[2])
        else:
            migrate_file(sys.argv[1], sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
