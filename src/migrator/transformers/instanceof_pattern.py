"""Transformer: instanceof pattern matching (Java 16+).

Converts:
    if (obj instanceof String) {
        String s = (String) obj;
        ...
    }

To:
    if (obj instanceof String s) {
        ...
    }
"""

import re

from .base import BaseTransformer, TransformResult


class InstanceofPatternTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Pattern Matching for instanceof"

    @property
    def description(self) -> str:
        return "Convierte instanceof + cast manual a pattern matching (Java 16+)"

    @property
    def java_version_target(self) -> int:
        return 16

    def transform(self, source_code: str) -> TransformResult:
        changes = []

        # Pattern: if (var instanceof Type) { Type name = (Type) var; ... }
        pattern = re.compile(
            r'(if\s*\(\s*(\w+)\s+instanceof\s+(\w+)\s*\))\s*\{'
            r'(\s*)'
            r'(\3)\s+(\w+)\s*=\s*\(\3\)\s*\2\s*;',
            re.MULTILINE
        )

        def replacer(match):
            full_if = match.group(1)
            var_name = match.group(2)
            type_name = match.group(3)
            whitespace = match.group(4)
            cast_var = match.group(6)

            changes.append(
                f"instanceof pattern matching: '{var_name} instanceof {type_name}' → variable '{cast_var}'"
            )

            # Replace the if condition and remove the cast line
            new_if = f"if ({var_name} instanceof {type_name} {cast_var}) {{"
            return new_if + whitespace

        transformed = pattern.sub(replacer, source_code)

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
