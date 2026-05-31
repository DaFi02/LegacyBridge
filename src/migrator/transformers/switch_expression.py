"""Transformer: Switch Expressions (Java 14+).

Converts traditional switch statements that assign to a variable:
    String result;
    switch (day) {
        case MONDAY:
        case FRIDAY:
            result = "Work";
            break;
        case SATURDAY:
        case SUNDAY:
            result = "Rest";
            break;
        default:
            result = "Unknown";
            break;
    }

To switch expressions:
    String result = switch (day) {
        case MONDAY, FRIDAY -> "Work";
        case SATURDAY, SUNDAY -> "Rest";
        default -> "Unknown";
    };
"""

import re

from .base import BaseTransformer, TransformResult


class SwitchExpressionTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Switch Expressions"

    @property
    def description(self) -> str:
        return "Convierte switch statements con asignación a switch expressions (Java 14+)"

    @property
    def java_version_target(self) -> int:
        return 14

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        original_code = source_code
        pattern = re.compile(
            r'(\s+)'                                    # indentation
            r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*;\s*\n'     # Type varName;
            r'\s*switch\s*\(([^)]+)\)\s*\{',           # switch (expr) {
            re.MULTILINE
        )

        for match in pattern.finditer(source_code):
            indent = match.group(1)
            var_type = match.group(2)
            var_name = match.group(3)
            switch_expr = match.group(4)

            # Find the full switch block
            switch_start = match.start()
            brace_start = source_code.index('{', match.end() - 1)
            brace_end = _find_matching_brace(source_code, brace_start)

            if brace_end == -1:
                continue

            switch_body = source_code[brace_start + 1:brace_end]

            # Parse case blocks and check if all assign to var_name
            cases = _parse_switch_cases(switch_body, var_name)
            if cases is None:
                continue

            # Build switch expression
            new_switch = f"{indent}{var_type} {var_name} = switch ({switch_expr}) {{\n"
            for case_labels, value in cases:
                labels_str = ", ".join(case_labels)
                if "default" in case_labels:
                    new_switch += f"{indent}    default -> {value};\n"
                else:
                    new_switch += f"{indent}    case {labels_str} -> {value};\n"
            new_switch += f"{indent}}};"

            full_original = source_code[switch_start:brace_end + 1]
            source_code = source_code[:switch_start] + new_switch + source_code[brace_end + 1:]

            changes.append(
                f"Switch expression: switch({switch_expr}) asignando a '{var_name}'"
            )

        return TransformResult(
            original=original_code,
            transformed=source_code,
            changes_made=changes,
            transformer_name=self.name,
        )


def _find_matching_brace(source: str, start: int) -> int:
    """Find the matching closing brace."""
    depth = 0
    for i in range(start, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1


def _parse_switch_cases(body: str, target_var: str) -> list[tuple[list[str], str]] | None:
    """Parse switch body and verify all cases assign to target_var.
    
    Returns list of (case_labels, assigned_value) or None if not convertible.
    """
    cases = []
    current_labels = []

    lines = body.strip().split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match case label
        case_match = re.match(r'case\s+(.+?)\s*:', line)
        default_match = re.match(r'default\s*:', line)

        if case_match:
            current_labels.append(case_match.group(1))
        elif default_match:
            current_labels.append("default")
        elif re.match(rf'{re.escape(target_var)}\s*=\s*(.+?)\s*;', line):
            # Assignment to target variable
            assign_match = re.match(rf'{re.escape(target_var)}\s*=\s*(.+?)\s*;', line)
            if assign_match and current_labels:
                cases.append((current_labels.copy(), assign_match.group(1)))
                current_labels = []
        elif line == 'break;' or line == '':
            pass
        elif line.startswith('//'):
            pass
        else:
            # Non-trivial statement - can't convert to expression
            if line and current_labels:
                return None

        i += 1

    if current_labels:
        # Dangling labels without assignment
        return None

    return cases if cases else None
