"""Validador de código migrado usando Podman containers.

Compila el código generado en contenedores aislados para verificar
que la migración produce código funcional sin instalar compiladores localmente.
"""

import subprocess
import tempfile
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Resultado de la validación de compilación."""
    language: str
    file_name: str
    success: bool
    output: str
    errors: str
    container_image: str

    def __str__(self) -> str:
        status = "✓ COMPILA" if self.success else "✗ ERROR"
        result = f"[{status}] {self.file_name} ({self.language})"
        if not self.success and self.errors:
            result += f"\n    Errores:\n"
            for line in self.errors.strip().split("\n")[:10]:
                result += f"      {line}\n"
        return result


class PodmanValidator:
    """Valida código migrado compilándolo en contenedores Podman."""

    # Imágenes de contenedor por lenguaje
    IMAGES = {
        "java17": "docker.io/library/eclipse-temurin:17-jdk-alpine",
        "java21": "docker.io/library/eclipse-temurin:21-jdk-alpine",
        "rust": "docker.io/library/rust:1-alpine",
        "cpp": "docker.io/library/gcc:14",
    }

    def __init__(self):
        self._check_podman()

    def _check_podman(self):
        """Verify podman is available."""
        try:
            result = subprocess.run(
                ["podman", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("Podman no está disponible")
        except FileNotFoundError:
            raise RuntimeError("Podman no está instalado. Instálalo con: sudo dnf install podman")

    def _pull_image_if_needed(self, image: str) -> bool:
        """Pull container image if not already available."""
        check = subprocess.run(
            ["podman", "image", "exists", image],
            capture_output=True, timeout=30
        )
        if check.returncode != 0:
            print(f"  📥 Descargando imagen: {image}...")
            pull = subprocess.run(
                ["podman", "pull", image],
                capture_output=True, text=True, timeout=300
            )
            return pull.returncode == 0
        return True

    def validate_java(self, source_code: str, filename: str = "Main.java",
                      java_version: int = 17) -> ValidationResult:
        """Compile Java code in a container to validate it."""
        image_key = f"java{java_version}" if f"java{java_version}" in self.IMAGES else "java17"
        image = self.IMAGES[image_key]

        self._pull_image_if_needed(image)

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / filename
            src_path.write_text(source_code, encoding="utf-8")

            # Compile in container
            result = subprocess.run(
                [
                    "podman", "run", "--rm",
                    "-v", f"{tmpdir}:/code:Z",
                    "-w", "/code",
                    image,
                    "javac", filename
                ],
                capture_output=True, text=True, timeout=60
            )

            return ValidationResult(
                language=f"Java {java_version}",
                file_name=filename,
                success=result.returncode == 0,
                output=result.stdout,
                errors=result.stderr,
                container_image=image,
            )

    def validate_rust(self, source_code: str, filename: str = "main.rs") -> ValidationResult:
        """Compile Rust code in a container to validate it."""
        image = self.IMAGES["rust"]
        self._pull_image_if_needed(image)

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / filename
            src_path.write_text(source_code, encoding="utf-8")

            # Detect if it has a main function to choose crate type
            has_main = "fn main()" in source_code
            cmd = [
                "podman", "run", "--rm",
                "-v", f"{tmpdir}:/code:Z",
                "-w", "/code",
                image,
                "rustc", "--edition", "2021",
                filename,
                "-o", "/code/output"
            ]
            if not has_main:
                cmd.insert(-2, "--crate-type")
                cmd.insert(-2, "lib")

            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=60
            )

            # Filter: warnings-only means success
            has_errors = result.returncode != 0
            stderr_lines = result.stderr.strip()

            return ValidationResult(
                language="Rust",
                file_name=filename,
                success=not has_errors,
                output=result.stdout,
                errors=stderr_lines if has_errors else "",
                container_image=image,
            )

    def validate_cpp(self, source_code: str, filename: str = "main.cpp") -> ValidationResult:
        """Compile C++ code in a container to validate it (as reference)."""
        image = self.IMAGES["cpp"]
        self._pull_image_if_needed(image)

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / filename
            src_path.write_text(source_code, encoding="utf-8")

            result = subprocess.run(
                [
                    "podman", "run", "--rm",
                    "-v", f"{tmpdir}:/code:Z",
                    "-w", "/code",
                    image,
                    "g++", "-std=c++17", "-fsyntax-only", filename
                ],
                capture_output=True, text=True, timeout=60
            )

            return ValidationResult(
                language="C++17",
                file_name=filename,
                success=result.returncode == 0,
                output=result.stdout,
                errors=result.stderr,
                container_image=image,
            )

    def validate_file(self, filepath: Path) -> ValidationResult:
        """Auto-detect language and validate a file."""
        source_code = filepath.read_text(encoding="utf-8")
        suffix = filepath.suffix.lower()

        if suffix == ".java":
            return self.validate_java(source_code, filepath.name)
        elif suffix == ".rs":
            return self.validate_rust(source_code, filepath.name)
        elif suffix in (".cpp", ".cc", ".cxx", ".c"):
            return self.validate_cpp(source_code, filepath.name)
        else:
            return ValidationResult(
                language="Desconocido",
                file_name=filepath.name,
                success=False,
                output="",
                errors=f"Extensión no soportada: {suffix}",
                container_image="",
            )

    def validate_directory(self, dirpath: Path) -> list[ValidationResult]:
        """Validate all supported files in a directory."""
        results = []
        extensions = (".java", ".rs", ".cpp", ".cc", ".c")

        for f in sorted(dirpath.rglob("*")):
            if f.suffix.lower() in extensions:
                print(f"  🔨 Compilando {f.name}...")
                results.append(self.validate_file(f))

        return results

    @staticmethod
    def print_report(results: list["ValidationResult"]) -> None:
        """Print a validation report."""
        print("\n" + "=" * 60)
        print("REPORTE DE VALIDACIÓN - Compilación en Contenedores")
        print("=" * 60)

        passed = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        for r in results:
            print(f"\n  {r}")

        print(f"\n{'=' * 60}")
        print(f"  Resultados: {passed} compilaron ✓ | {failed} errores ✗")
        print(f"  Total archivos: {len(results)}")
        print("=" * 60)
