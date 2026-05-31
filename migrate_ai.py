"""
CLI para migración con IA + validación con Podman.

Uso:
    uv run python migrate_ai.py --type cpp_to_rust examples/cpp_legacy/memory_management.cpp
    uv run python migrate_ai.py --type cobol_to_rust examples/cobol/payroll.cob
    uv run python migrate_ai.py --type cobol_to_java examples/cobol/inventory.cob
    uv run python migrate_ai.py --demo-cobol-rust
    uv run python migrate_ai.py --demo-cpp-rust
    uv run python migrate_ai.py --validate output/ai_rust/
"""

import sys
import os
from pathlib import Path

from src.migrator.ai_migrator import AIMigrator, AIMigrationResult
from src.migrator.validation import PodmanValidator


# API Key de NVIDIA NIM (configurar variable de entorno)
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

# Extensiones de salida por target
TARGET_EXTENSIONS = {
    "rust": ".rs",
    "java": ".java",
    "java17": ".java",
}


def print_migration_result(result: AIMigrationResult, output_path: Path | None = None):
    """Print the AI migration result."""
    if result.success:
        print(f"  ✓ Migración exitosa: {result.source_language} → {result.target_language}")
        print(f"  📦 Modelo: {result.model}")
        if output_path:
            print(f"  📄 Guardado en: {output_path}")
        print(f"\n{'─' * 60}")
        print("  CÓDIGO GENERADO POR IA:")
        print(f"{'─' * 60}")
        # Show first 50 lines
        lines = result.migrated_code.split("\n")
        for i, line in enumerate(lines[:50]):
            print(f"  {line}")
        if len(lines) > 50:
            print(f"  ... ({len(lines) - 50} líneas más)")
        print(f"{'─' * 60}")
    else:
        print(f"  ✗ Error en migración: {result.error}")


def migrate_single_file(filepath: str, migration_type: str, output_dir: str = "output/ai_migrated"):
    """Migrate a single file using AI."""
    input_path = Path(filepath)
    if not input_path.exists():
        print(f"Error: No se encontró {filepath}")
        sys.exit(1)

    target_lang = migration_type.split("_to_")[-1]
    ext = TARGET_EXTENSIONS.get(target_lang, ".txt")
    output_path = Path(output_dir) / (input_path.stem + ext)

    print(f"\n🤖 Migrando con IA: {input_path.name}")
    print(f"   Tipo: {migration_type}")
    print(f"   Modelo: meta/llama-4-maverick-17b-128e-instruct (NVIDIA NIM)")
    print()

    migrator = AIMigrator(api_key=NVIDIA_API_KEY)
    result = migrator.migrate_file(input_path, output_path, migration_type)
    print_migration_result(result, output_path if result.success else None)

    return result, output_path


def validate_output(directory: str):
    """Validate compiled output using Podman."""
    dirpath = Path(directory)
    if not dirpath.exists():
        print(f"Error: No se encontró {directory}")
        sys.exit(1)

    print(f"\n🐳 Validando compilación con Podman...")
    print(f"   Directorio: {dirpath}")
    print()

    validator = PodmanValidator()
    results = validator.validate_directory(dirpath)
    validator.print_report(results)
    return results


def demo_cobol_to_rust():
    """Demo: Migrate COBOL files to Rust using AI and validate."""
    print("=" * 60)
    print("🚀 DEMO: Migración COBOL → Rust con IA + Validación")
    print("=" * 60)

    output_dir = Path("output/ai_rust")
    output_dir.mkdir(parents=True, exist_ok=True)

    migrator = AIMigrator(api_key=NVIDIA_API_KEY)
    cobol_files = list(Path("examples/cobol").glob("*.cob"))

    if not cobol_files:
        print("Error: No se encontraron archivos COBOL en examples/cobol/")
        sys.exit(1)

    migration_results = []

    for cobol_file in cobol_files:
        output_path = output_dir / (cobol_file.stem + ".rs")
        print(f"\n🤖 Migrando: {cobol_file.name} → {output_path.name}")
        print(f"   Enviando a Gemma 4 31B...")

        result = migrator.migrate_file(cobol_file, output_path, "cobol_to_rust")
        migration_results.append((result, output_path))
        print_migration_result(result, output_path if result.success else None)

    # Validate with Podman
    successful = [r for r, _ in migration_results if r.success]
    if successful:
        print(f"\n\n{'=' * 60}")
        print("🐳 FASE 2: Validación de compilación con Podman")
        print("=" * 60)

        validator = PodmanValidator()
        validation_results = validator.validate_directory(output_dir)
        validator.print_report(validation_results)

        # Final summary
        print(f"\n{'=' * 60}")
        print("📊 RESUMEN COMPLETO DEL PIPELINE IA + VALIDACIÓN")
        print("=" * 60)
        print(f"  Archivos COBOL procesados: {len(cobol_files)}")
        print(f"  Migraciones IA exitosas: {len(successful)}/{len(cobol_files)}")
        compiled = sum(1 for r in validation_results if r.success)
        print(f"  Archivos que compilan: {compiled}/{len(validation_results)}")
        print("=" * 60)


def demo_cpp_to_rust():
    """Demo: Migrate C++ files to Rust using AI and validate."""
    print("=" * 60)
    print("🚀 DEMO: Migración C++ → Rust con IA + Validación")
    print("=" * 60)

    output_dir = Path("output/ai_cpp_to_rust")
    output_dir.mkdir(parents=True, exist_ok=True)

    migrator = AIMigrator(api_key=NVIDIA_API_KEY)
    cpp_files = list(Path("examples/cpp_legacy").glob("*.cpp"))

    if not cpp_files:
        print("Error: No se encontraron archivos C++ en examples/cpp_legacy/")
        sys.exit(1)

    migration_results = []

    for cpp_file in cpp_files:
        output_path = output_dir / (cpp_file.stem + ".rs")
        print(f"\n🤖 Migrando: {cpp_file.name} → {output_path.name}")
        print(f"   Enviando a Gemma 4 31B...")

        result = migrator.migrate_file(cpp_file, output_path, "cpp_to_rust")
        migration_results.append((result, output_path))
        print_migration_result(result, output_path if result.success else None)

    # Validate with Podman
    successful = [r for r, _ in migration_results if r.success]
    if successful:
        print(f"\n\n{'=' * 60}")
        print("🐳 FASE 2: Validación de compilación con Podman")
        print("=" * 60)

        validator = PodmanValidator()
        validation_results = validator.validate_directory(output_dir)
        validator.print_report(validation_results)

        # Final summary
        print(f"\n{'=' * 60}")
        print("📊 RESUMEN COMPLETO DEL PIPELINE IA + VALIDACIÓN")
        print("=" * 60)
        print(f"  Archivos C++ procesados: {len(cpp_files)}")
        print(f"  Migraciones IA exitosas: {len(successful)}/{len(cpp_files)}")
        compiled = sum(1 for r in validation_results if r.success)
        print(f"  Archivos que compilan: {compiled}/{len(validation_results)}")
        print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--demo-cobol-rust":
        demo_cobol_to_rust()
    elif sys.argv[1] == "--demo-cpp-rust":
        demo_cpp_to_rust()
    elif sys.argv[1] == "--validate" and len(sys.argv) >= 3:
        validate_output(sys.argv[2])
    elif sys.argv[1] == "--type" and len(sys.argv) >= 4:
        migration_type = sys.argv[2]
        filepath = sys.argv[3]
        output_dir = sys.argv[4] if len(sys.argv) > 4 else "output/ai_migrated"
        result, output_path = migrate_single_file(filepath, migration_type, output_dir)

        # Auto-validate if migration was successful
        if result.success:
            print(f"\n🐳 Validando con Podman...")
            validator = PodmanValidator()
            val_result = validator.validate_file(output_path)
            print(f"\n  {val_result}")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
