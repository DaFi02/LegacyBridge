"""Motor de reglas anti-alucinación.

Define reglas que el código migrado debe cumplir.
Si la IA genera código que viola estas reglas, se detecta
y se puede pedir re-migración o marcar como fallo.

Categorías de reglas:
- STRUCTURAL: El código debe tener estructura equivalente
- SEMANTIC: Debe preservar la lógica del original
- SYNTACTIC: Debe ser sintácticamente válido
- COMPILATION: Debe compilar en Podman
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class RuleCategory(Enum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    SYNTACTIC = "syntactic"
    COMPILATION = "compilation"


class RuleSeverity(Enum):
    ERROR = "error"          # Bloquea la migración
    WARNING = "warning"      # Se reporta pero continúa
    INFO = "info"            # Solo informativo


@dataclass
class RuleResult:
    """Resultado de aplicar una regla."""
    rule_name: str
    passed: bool
    category: RuleCategory
    severity: RuleSeverity
    message: str
    details: str = ""


class Rule(ABC):
    """Regla base que todo código migrado debe cumplir."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def category(self) -> RuleCategory:
        ...

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.ERROR

    @abstractmethod
    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        """Verifica la regla. context tiene metadata del segmento."""
        ...


# === REGLAS ESTRUCTURALES ===

class FunctionCountRule(Rule):
    """El código migrado debe tener al menos tantas funciones como el original."""

    @property
    def name(self) -> str:
        return "function_count"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.STRUCTURAL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        source_lang = context.get("source_language", "")
        target_lang = context.get("target_language", "")

        source_count = self._count_functions(source_code, source_lang)
        target_count = self._count_functions(migrated_code, target_lang)

        passed = target_count >= source_count * 0.7  # Tolerancia 30%
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message=f"Funciones: original={source_count}, migrado={target_count}",
            details="" if passed else
                f"El código migrado tiene significativamente menos funciones "
                f"({target_count} vs {source_count}). La IA puede haber omitido lógica.",
        )

    def _count_functions(self, code: str, lang: str) -> int:
        patterns = {
            "cpp": r'\b\w+\s+\w+\s*\([^)]*\)\s*{',
            "c": r'\b\w+\s+\w+\s*\([^)]*\)\s*{',
            "cobol": r'^\s{6}\s+[\w-]+\.\s*$',
            "java": r'(?:public|private|protected)\s+.*\w+\s*\([^)]*\)\s*{',
            "rust": r'\bfn\s+\w+',
        }
        pattern = patterns.get(lang, patterns["rust"])
        return len(re.findall(pattern, code, re.MULTILINE))


class StructCountRule(Rule):
    """El código migrado debe preservar los tipos de datos."""

    @property
    def name(self) -> str:
        return "struct_count"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.STRUCTURAL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        source_lang = context.get("source_language", "")

        source_types = self._count_types(source_code, source_lang)
        target_types = self._count_types(migrated_code, "rust")

        passed = target_types >= source_types * 0.5
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message=f"Tipos de datos: original={source_types}, migrado={target_types}",
            details="" if passed else
                "El código migrado perdió tipos de datos del original.",
        )

    def _count_types(self, code: str, lang: str) -> int:
        patterns = {
            "cpp": r'\b(?:struct|class|enum)\s+\w+',
            "c": r'\b(?:struct|enum|typedef)\s+',
            "cobol": r'^\s{6}\s+01\s+',
            "java": r'\bclass\s+\w+',
            "rust": r'\b(?:struct|enum)\s+\w+',
        }
        pattern = patterns.get(lang, patterns["rust"])
        return len(re.findall(pattern, code, re.MULTILINE))


# === REGLAS SEMÁNTICAS ===

class NoEmptyOutputRule(Rule):
    """El código migrado no puede estar vacío."""

    @property
    def name(self) -> str:
        return "no_empty_output"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.SEMANTIC

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        non_empty = migrated_code.strip()
        passed = len(non_empty) > 10
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message="Código migrado no vacío" if passed else "Código migrado vacío o trivial",
        )


class SizeRatioRule(Rule):
    """El código migrado debe tener tamaño razonable respecto al original."""

    @property
    def name(self) -> str:
        return "size_ratio"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.SEMANTIC

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        source_lines = len(source_code.strip().split('\n'))
        target_lines = len(migrated_code.strip().split('\n'))

        if source_lines == 0:
            return RuleResult(
                rule_name=self.name, passed=False,
                category=self.category, severity=self.severity,
                message="Código fuente vacío",
            )

        ratio = target_lines / source_lines
        # El código migrado puede ser 0.3x a 4x del original
        passed = 0.3 <= ratio <= 4.0
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message=f"Ratio de tamaño: {ratio:.2f}x ({source_lines} → {target_lines} líneas)",
            details="" if passed else
                f"El ratio {ratio:.2f}x está fuera de rango [0.3, 4.0]. "
                f"La IA puede haber generado código excesivo o incompleto.",
        )


class NoHallucinatedImportsRule(Rule):
    """Detecta imports de crates/módulos que no existen en Rust estándar."""

    # Crates/modules legítimos en Rust std + comunes
    KNOWN_RUST_MODULES = {
        "std", "core", "alloc", "collections", "io", "fs", "fmt",
        "sync", "thread", "net", "path", "env", "process",
        "serde", "tokio", "anyhow", "thiserror", "clap",
    }

    @property
    def name(self) -> str:
        return "no_hallucinated_imports"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.SEMANTIC

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        target_lang = context.get("target_language", "")
        if target_lang != "rust":
            return RuleResult(
                rule_name=self.name, passed=True,
                category=self.category, severity=self.severity,
                message="No aplica (target no es Rust)",
            )

        suspicious = []
        for match in re.finditer(r'^use\s+(\w+)', migrated_code, re.MULTILINE):
            root_crate = match.group(1)
            if root_crate not in self.KNOWN_RUST_MODULES and root_crate != "crate":
                suspicious.append(root_crate)

        passed = len(suspicious) == 0
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message="Sin imports sospechosos" if passed else
                f"Imports posiblemente alucinados: {suspicious}",
            details="" if passed else
                f"Los crates {suspicious} no son parte de std ni crates comunes. "
                f"Verificar que existen antes de usar.",
        )


class PreservesLogicPatternsRule(Rule):
    """Verifica que patrones lógicos del original se preservan."""

    @property
    def name(self) -> str:
        return "preserves_logic"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.SEMANTIC

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        # Verificar que strings literales del original aparecen en el migrado
        source_strings = set(re.findall(r'"([^"]{4,})"', source_code))
        target_strings = set(re.findall(r'"([^"]{4,})"', migrated_code))

        if not source_strings:
            return RuleResult(
                rule_name=self.name, passed=True,
                category=self.category, severity=self.severity,
                message="Sin strings para comparar",
            )

        preserved = source_strings & target_strings
        ratio = len(preserved) / len(source_strings) if source_strings else 1.0
        passed = ratio >= 0.3  # Al menos 30% de strings preservados

        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message=f"Strings preservados: {len(preserved)}/{len(source_strings)} ({ratio:.0%})",
            details="" if passed else
                "Muchos strings literales del original no aparecen en el migrado. "
                "La IA puede haber cambiado la lógica de negocio.",
        )


# === REGLAS SINTÁCTICAS ===

class ValidRustSyntaxRule(Rule):
    """Verifica sintaxis básica de Rust sin compilar."""

    @property
    def name(self) -> str:
        return "valid_rust_syntax"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.SYNTACTIC

    def check(self, source_code: str, migrated_code: str, context: dict) -> RuleResult:
        target_lang = context.get("target_language", "")
        if target_lang != "rust":
            return RuleResult(
                rule_name=self.name, passed=True,
                category=self.category, severity=self.severity,
                message="No aplica (target no es Rust)",
            )

        issues = []

        # Verificar balance de llaves
        opens = migrated_code.count('{')
        closes = migrated_code.count('}')
        if opens != closes:
            issues.append(f"Llaves desbalanceadas: {{ ={opens}, }} ={closes}")

        # Verificar que no hay código C/C++ residual
        cpp_markers = [
            (r'\bNULL\b', "NULL (usar None)"),
            (r'#include\s*<', "#include (no es Rust)"),
            (r'\bcout\s*<<', "cout (no es Rust)"),
            (r'\bprintf\s*\(', "printf (usar println!/format!)"),
            (r'\bnew\s+\w+\s*\(', "new (usar Box::new o constructor)"),
            (r'\bdelete\s+', "delete (no existe en Rust)"),
            (r'\bvoid\s+\w+\s*\(', "void (usar -> () en Rust)"),
        ]
        for pattern, msg in cpp_markers:
            if re.search(pattern, migrated_code):
                issues.append(f"Código C++ residual: {msg}")

        passed = len(issues) == 0
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            category=self.category,
            severity=self.severity,
            message="Sintaxis Rust válida" if passed else f"{len(issues)} problemas sintácticos",
            details="\n".join(issues) if issues else "",
        )


# === MOTOR DE REGLAS ===

class RuleEngine:
    """Ejecuta todas las reglas sobre el código migrado.
    
    Usage:
        engine = RuleEngine()
        results = engine.validate(source, migrated, context)
        if engine.has_blocking_errors(results):
            # Re-intentar migración
    """

    def __init__(self):
        self._rules: list[Rule] = [
            # Structural
            FunctionCountRule(),
            StructCountRule(),
            # Semantic
            NoEmptyOutputRule(),
            SizeRatioRule(),
            NoHallucinatedImportsRule(),
            PreservesLogicPatternsRule(),
            # Syntactic
            ValidRustSyntaxRule(),
        ]

    @property
    def rules(self) -> list[Rule]:
        return self._rules

    def add_rule(self, rule: Rule) -> None:
        """Agrega una regla personalizada."""
        self._rules.append(rule)

    def validate(self, source_code: str, migrated_code: str, context: dict) -> list[RuleResult]:
        """Ejecuta todas las reglas y retorna resultados."""
        results = []
        for rule in self._rules:
            try:
                result = rule.check(source_code, migrated_code, context)
                results.append(result)
            except Exception as e:
                results.append(RuleResult(
                    rule_name=rule.name,
                    passed=False,
                    category=rule.category,
                    severity=RuleSeverity.WARNING,
                    message=f"Error ejecutando regla: {e}",
                ))
        return results

    def has_blocking_errors(self, results: list[RuleResult]) -> bool:
        """Verifica si hay errores que bloquean la migración."""
        return any(
            not r.passed and r.severity == RuleSeverity.ERROR
            for r in results
        )

    def summary(self, results: list[RuleResult]) -> str:
        """Genera un resumen legible de los resultados."""
        lines = ["📋 VALIDACIÓN DE REGLAS:"]
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        lines.append(f"   {passed} ✓ | {failed} ✗ (de {len(results)} reglas)")

        for r in results:
            icon = "✓" if r.passed else "✗"
            sev = f"[{r.severity.value}]" if not r.passed else ""
            lines.append(f"   {icon} {r.rule_name}: {r.message} {sev}")
            if r.details:
                for detail_line in r.details.split('\n'):
                    lines.append(f"     → {detail_line}")

        return "\n".join(lines)
