"""Transformer: C++ types, structs, classes → Rust structs/enums.

Converts:
    struct Point { int x; int y; };       →  struct Point { x: i32, y: i32 }
    class Animal { public: ... };         →  struct Animal { ... } impl Animal { ... }
    enum Color { RED, GREEN, BLUE };      →  enum Color { Red, Green, Blue }
    typedef unsigned int uint;            →  type Uint = u32;
"""

import re

from .base import BaseTransformer, TransformResult
from .raw_pointers import cpp_type_to_rust


class TypesAndStructsTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Types & Structs → Rust Structs"

    @property
    def description(self) -> str:
        return "Convierte structs, clases y typedefs de C++ a structs/enums de Rust"

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # typedef OldType NewType; → type NewType = RustType;
        pattern_typedef = re.compile(
            r'^(\s*)typedef\s+(.+?)\s+(\w+);',
            re.MULTILINE
        )

        def replace_typedef(match):
            indent = match.group(1)
            old_type = match.group(2).strip()
            new_name = match.group(3)
            rust_type = cpp_type_to_rust(old_type)
            # Capitalize first letter for Rust convention
            rust_name = new_name[0].upper() + new_name[1:] if new_name else new_name
            changes.append(f"typedef {old_type} {new_name} → type {rust_name} = {rust_type}")
            return f"{indent}type {rust_name} = {rust_type};"

        transformed = pattern_typedef.sub(replace_typedef, transformed)

        # Simple struct: struct Name { Type field; ... };
        pattern_struct = re.compile(
            r'^(\s*)struct\s+(\w+)\s*\{([^}]+)\};',
            re.MULTILINE
        )

        def replace_struct(match):
            indent = match.group(1)
            name = match.group(2)
            body = match.group(3)

            # Parse fields
            fields = []
            field_pattern = re.compile(r'(\w[\w\s]*?)\s+(\w+);')
            for field_match in field_pattern.finditer(body):
                field_type = field_match.group(1).strip()
                field_name = field_match.group(2)
                rust_type = cpp_type_to_rust(field_type)
                fields.append(f"{indent}    pub {field_name}: {rust_type},")

            if not fields:
                return match.group(0)

            fields_str = "\n".join(fields)
            changes.append(f"struct {name} → Rust struct con {len(fields)} campos")
            return f"{indent}#[derive(Debug, Clone)]\n{indent}pub struct {name} {{\n{fields_str}\n{indent}}}"

        transformed = pattern_struct.sub(replace_struct, transformed)

        # Simple enum: enum Name { A, B, C }; → enum Name { A, B, C }
        pattern_enum = re.compile(
            r'^(\s*)enum\s+(\w+)\s*\{([^}]+)\};',
            re.MULTILINE
        )

        def replace_enum(match):
            indent = match.group(1)
            name = match.group(2)
            body = match.group(3)

            # Parse enum values
            values = [v.strip() for v in body.split(',') if v.strip()]
            # Remove any = value assignments for now
            clean_values = []
            for v in values:
                v_name = v.split('=')[0].strip()
                if v_name:
                    # Convert to PascalCase
                    rust_name = v_name.replace('_', ' ').title().replace(' ', '')
                    clean_values.append(f"{indent}    {rust_name},")

            if not clean_values:
                return match.group(0)

            values_str = "\n".join(clean_values)
            changes.append(f"enum {name} → Rust enum con {len(clean_values)} variantes")
            return f"{indent}#[derive(Debug, Clone, PartialEq)]\n{indent}pub enum {name} {{\n{values_str}\n{indent}}}"

        transformed = pattern_enum.sub(replace_enum, transformed)

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
