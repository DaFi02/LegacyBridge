"""Transformer: Text Blocks (Java 15+).

Converts multi-line string concatenation:
    String sql = "SELECT *\\n" +
                 "FROM users\\n" +
                 "WHERE active = true";

To text blocks:
    String sql = \"\"\"
            SELECT *
            FROM users
            WHERE active = true\"\"\";
"""

import re

from .base import BaseTransformer, TransformResult


class TextBlockTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Text Blocks"

    @property
    def description(self) -> str:
        return "Convierte concatenación de strings multilínea a text blocks (Java 15+)"

    @property
    def java_version_target(self) -> int:
        return 15

    def transform(self, source_code: str) -> TransformResult:
        changes = []

        # Pattern: multi-line string concatenation with \n
        # Matches: "line1\n" + "line2\n" + "line3"  (at least 2 concatenated parts)
        pattern = re.compile(
            r'(\w+\s+\w+\s*=\s*)'  # Type varName =
            r'("(?:[^"\\]|\\.)*"'   # First string literal
            r'(?:\s*\+\s*\n?\s*"(?:[^"\\]|\\.)*"){2,})'  # + "..." repeated 2+ times
            r'\s*;',
            re.MULTILINE
        )

        def replacer(match):
            assignment = match.group(1)
            concat_str = match.group(2)

            # Extract individual string parts
            parts = re.findall(r'"((?:[^"\\]|\\.)*)"', concat_str)

            # Check if they contain \n (multiline intent)
            has_newlines = any('\\n' in part for part in parts)
            if not has_newlines or len(parts) < 3:
                return match.group(0)

            # Build text block content
            lines = []
            for part in parts:
                line = part.replace('\\n', '').replace('\\t', '\t')
                lines.append(line)

            # Determine indentation
            indent = " " * (len(assignment) + 4)
            text_block_content = ("\n" + indent).join(lines)

            changes.append(f"Text block: concatenación de {len(parts)} strings → text block")

            return f'{assignment}"""\n{indent}{text_block_content}""";'

        transformed = pattern.sub(replacer, source_code)

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
