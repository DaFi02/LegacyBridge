"""Transformer: Raw pointers → Rust ownership/references.

Converts C++ raw pointer patterns to Rust safe references:
    int* ptr = &value;        →  let ptr: &i32 = &value;
    const char* name = ...;   →  let name: &str = ...;
    int* arr = new int[10];   →  let arr: Vec<i32> = vec![0; 10];
    void foo(int* data)       →  fn foo(data: &mut i32)
"""

import re

from .base import BaseTransformer, TransformResult


# C++ type → Rust type mapping
TYPE_MAP = {
    "int": "i32",
    "long": "i64",
    "short": "i16",
    "char": "char",
    "float": "f32",
    "double": "f64",
    "bool": "bool",
    "unsigned int": "u32",
    "unsigned long": "u64",
    "unsigned short": "u16",
    "unsigned char": "u8",
    "size_t": "usize",
    "void": "()",
}


def cpp_type_to_rust(cpp_type: str) -> str:
    """Convert a C++ type to its Rust equivalent."""
    cpp_type = cpp_type.strip()
    return TYPE_MAP.get(cpp_type, cpp_type)


class RawPointerTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Raw Pointers → Safe References"

    @property
    def description(self) -> str:
        return "Convierte punteros crudos de C++ a referencias seguras de Rust"

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # const Type* var = &expr; → let var: &Type = &expr;
        pattern_const_ptr = re.compile(
            r'const\s+(\w+)\s*\*\s*(\w+)\s*=\s*(.+?);'
        )

        def replace_const_ptr(match):
            cpp_type = match.group(1)
            var_name = match.group(2)
            value = match.group(3).strip()
            rust_type = cpp_type_to_rust(cpp_type)
            changes.append(f"const {cpp_type}* {var_name} → let {var_name}: &{rust_type}")
            return f"let {var_name}: &{rust_type} = {value};"

        transformed = pattern_const_ptr.sub(replace_const_ptr, transformed)

        # Type* var = &expr; → let var: &mut Type = &mut expr;
        pattern_mut_ptr_ref = re.compile(
            r'^(\s*)(\w+)\s*\*\s*(\w+)\s*=\s*&(\w+);',
            re.MULTILINE
        )

        def replace_mut_ptr_ref(match):
            indent = match.group(1)
            cpp_type = match.group(2)
            var_name = match.group(3)
            ref_var = match.group(4)
            rust_type = cpp_type_to_rust(cpp_type)
            changes.append(f"{cpp_type}* {var_name} = &{ref_var} → let {var_name}: &mut {rust_type}")
            return f"{indent}let {var_name}: &mut {rust_type} = &mut {ref_var};"

        transformed = pattern_mut_ptr_ref.sub(replace_mut_ptr_ref, transformed)

        # Type* arr = new Type[N]; → let mut arr: Vec<Type> = vec![Default; N];
        pattern_new_array = re.compile(
            r'^(\s*)(\w+)\s*\*\s*(\w+)\s*=\s*new\s+\w+\[(.+?)\];',
            re.MULTILINE
        )

        def replace_new_array(match):
            indent = match.group(1)
            cpp_type = match.group(2)
            var_name = match.group(3)
            size = match.group(4)
            rust_type = cpp_type_to_rust(cpp_type)
            default_val = "0" if rust_type in ("i32", "i64", "i16", "f32", "f64", "u32", "u64", "u16", "u8", "usize") else "Default::default()"
            changes.append(f"new {cpp_type}[{size}] → Vec<{rust_type}> con vec![{default_val}; {size}]")
            return f"{indent}let mut {var_name}: Vec<{rust_type}> = vec![{default_val}; {size}];"

        transformed = pattern_new_array.sub(replace_new_array, transformed)

        # Function params: void foo(Type* param) → fn foo(param: &mut Type)
        pattern_func_ptr_param = re.compile(
            r'(\w+)\s*\*\s*(\w+)(?=\s*[,\)])'
        )
        # This is applied only within function signatures - more complex, skip for now
        # and handle in function-level transformer

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
