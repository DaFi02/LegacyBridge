"""Transformer: var keyword for local variables (Java 10+).

Converts:
    ArrayList<String> list = new ArrayList<String>();
    HashMap<String, Integer> map = new HashMap<>();
    BufferedReader reader = new BufferedReader(new FileReader(file));

To:
    var list = new ArrayList<String>();
    var map = new HashMap<String, Integer>();
    var reader = new BufferedReader(new FileReader(file));
"""

import re

from .base import BaseTransformer, TransformResult


class VarKeywordTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Local Variable Type Inference (var)"

    @property
    def description(self) -> str:
        return "Usa 'var' para variables locales con tipo obvio por el constructor (Java 10+)"

    @property
    def java_version_target(self) -> int:
        return 10

    def transform(self, source_code: str) -> TransformResult:
        changes = []

        # Pattern: Type<...> varName = new Type<...>(...);
        # Only when the type on the left matches the constructor type
        pattern = re.compile(
            r'^(\s+)'                           # indentation (must be indented = local var)
            r'(\w+(?:<[^>]+>)?)\s+'             # Type (with optional generics)
            r'(\w+)\s*=\s*'                     # varName =
            r'new\s+(\w+)(<[^>]*>)?\s*\([^)]*\)\s*;',  # new Type<...>(...);
            re.MULTILINE
        )

        def replacer(match):
            indent = match.group(1)
            declared_type = match.group(2)
            var_name = match.group(3)
            constructor_type = match.group(4)
            constructor_generics = match.group(5) or ""

            # Get base type name (without generics) for comparison
            base_declared = re.match(r'(\w+)', declared_type).group(1)

            # Only apply var when the declared type matches or is a parent of constructor type
            # Common cases: ArrayList matches ArrayList, HashMap matches HashMap, etc.
            if base_declared == constructor_type or _is_common_subtype(base_declared, constructor_type):
                # Reconstruct the new expression with full generics
                new_expr = match.group(0)[len(indent):]
                # Replace the type declaration with var
                new_line = re.sub(
                    r'^(\w+(?:<[^>]+>)?)\s+',
                    'var ',
                    new_expr
                )
                # If diamond operator was used, fill in the generics
                if constructor_generics == "<>" and "<" in declared_type:
                    generics = re.search(r'(<[^>]+>)', declared_type)
                    if generics:
                        new_line = new_line.replace(
                            f"new {constructor_type}<>",
                            f"new {constructor_type}{generics.group(1)}"
                        )

                changes.append(f"var: '{declared_type} {var_name}' → 'var {var_name}'")
                return indent + new_line

            return match.group(0)

        transformed = pattern.sub(replacer, source_code)

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )


def _is_common_subtype(interface_type: str, impl_type: str) -> bool:
    """Check common interface→implementation mappings."""
    common_mappings = {
        "List": ["ArrayList", "LinkedList", "CopyOnWriteArrayList"],
        "Map": ["HashMap", "TreeMap", "LinkedHashMap", "ConcurrentHashMap"],
        "Set": ["HashSet", "TreeSet", "LinkedHashSet"],
        "Queue": ["LinkedList", "PriorityQueue", "ArrayDeque"],
        "Deque": ["ArrayDeque", "LinkedList"],
    }
    return impl_type in common_mappings.get(interface_type, [])
