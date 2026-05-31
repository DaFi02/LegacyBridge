"""Transformer: C++ control flow → Rust control flow.

Converts:
    for (int i = 0; i < n; i++)     →  for i in 0..n
    while (condition) { ... }        →  while condition { ... }
    for (auto& item : collection)    →  for item in &collection
    if (condition) { ... }           →  if condition { ... }
    condition ? a : b                →  if condition { a } else { b }
"""

import re

from .base import BaseTransformer, TransformResult


class ControlFlowTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Control Flow → Rust Syntax"

    @property
    def description(self) -> str:
        return "Convierte bucles y condicionales de C++ a sintaxis Rust (for..in, while, if sin paréntesis)"

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # Classic for: for (int i = 0; i < N; i++) → for i in 0..N
        pattern_for_classic = re.compile(
            r'for\s*\(\s*(?:int|size_t|unsigned)\s+(\w+)\s*=\s*(\w+)\s*;\s*\1\s*<\s*(\w+)\s*;\s*\1\s*\+\+\s*\)'
        )

        def replace_for_classic(match):
            var = match.group(1)
            start = match.group(2)
            end = match.group(3)
            changes.append(f"for ({var}=0; {var}<{end}; {var}++) → for {var} in {start}..{end}")
            if start == "0":
                return f"for {var} in 0..{end}"
            return f"for {var} in {start}..{end}"

        transformed = pattern_for_classic.sub(replace_for_classic, transformed)

        # Range-based for: for (auto& item : collection) → for item in &collection
        pattern_for_range = re.compile(
            r'for\s*\(\s*(?:const\s+)?(?:auto|(\w+))\s*&\s*(\w+)\s*:\s*(\w+)\s*\)'
        )

        def replace_for_range(match):
            var_name = match.group(2)
            collection = match.group(3)
            changes.append(f"for (auto& {var_name} : {collection}) → for {var_name} in &{collection}")
            return f"for {var_name} in &{collection}"

        transformed = pattern_for_range.sub(replace_for_range, transformed)

        # Range-based for with auto (value): for (auto item : collection) → for item in collection
        pattern_for_range_val = re.compile(
            r'for\s*\(\s*(?:const\s+)?auto\s+(\w+)\s*:\s*(\w+)\s*\)'
        )

        def replace_for_range_val(match):
            var_name = match.group(1)
            collection = match.group(2)
            changes.append(f"for (auto {var_name} : {collection}) → for {var_name} in {collection}")
            return f"for {var_name} in {collection}"

        transformed = pattern_for_range_val.sub(replace_for_range_val, transformed)

        # while (condition) → while condition
        pattern_while = re.compile(r'while\s*\(\s*(.+?)\s*\)\s*\{')

        def replace_while(match):
            condition = match.group(1)
            changes.append(f"while ({condition}) → while {condition}")
            return f"while {condition} {{"

        transformed = pattern_while.sub(replace_while, transformed)

        # std::cout << expr << std::endl; → println!("{}", expr);
        pattern_cout = re.compile(
            r'std::cout\s*<<\s*(.+?)\s*<<\s*std::endl\s*;'
        )

        def replace_cout(match):
            expr = match.group(1).strip()
            # Handle chained << operators
            parts = [p.strip().strip('"') for p in re.split(r'\s*<<\s*', expr)]
            if len(parts) == 1:
                if parts[0].startswith('"') or parts[0].startswith("'"):
                    changes.append(f"std::cout → println!()")
                    return f'println!("{parts[0]}");'
                else:
                    changes.append(f"std::cout → println!()")
                    return f'println!("{{}}", {parts[0]});'
            else:
                format_parts = []
                args = []
                for p in parts:
                    if p.startswith('"') or p.startswith("'"):
                        format_parts.append(p.strip('"').strip("'"))
                    else:
                        format_parts.append("{}")
                        args.append(p)
                fmt_str = "".join(format_parts)
                args_str = ", ".join(args) if args else ""
                changes.append(f"std::cout → println!()")
                if args_str:
                    return f'println!("{fmt_str}", {args_str});'
                return f'println!("{fmt_str}");'

        transformed = pattern_cout.sub(replace_cout, transformed)

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
