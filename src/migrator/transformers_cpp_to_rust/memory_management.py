"""Transformer: C++ manual memory management → Rust ownership.

Converts:
    int* p = new int(42);     →  let p: Box<i32> = Box::new(42);
    delete p;                 →  drop(p);  // or just remove
    int* arr = new int[10];   →  let mut arr: Vec<i32> = vec![0; 10];
    delete[] arr;             →  drop(arr);
    std::shared_ptr<T> p      →  Rc<T> / Arc<T>
    std::unique_ptr<T> p      →  Box<T>
"""

import re

from .base import BaseTransformer, TransformResult
from .raw_pointers import cpp_type_to_rust


class MemoryManagementTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Memory Management → Ownership"

    @property
    def description(self) -> str:
        return "Convierte new/delete y smart pointers de C++ al sistema de ownership de Rust"

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # Type* var = new Type(args); → let var = Box::new(args);
        pattern_new_single = re.compile(
            r'^(\s*)(\w+)\s*\*\s*(\w+)\s*=\s*new\s+\w+\(([^)]*)\);',
            re.MULTILINE
        )

        def replace_new_single(match):
            indent = match.group(1)
            cpp_type = match.group(2)
            var_name = match.group(3)
            args = match.group(4)
            rust_type = cpp_type_to_rust(cpp_type)
            changes.append(f"new {cpp_type}({args}) → Box::new({args})")
            return f"{indent}let {var_name}: Box<{rust_type}> = Box::new({args});"

        transformed = pattern_new_single.sub(replace_new_single, transformed)

        # delete ptr; → drop(ptr);
        pattern_delete = re.compile(r'^(\s*)delete\s+(\w+);', re.MULTILINE)

        def replace_delete(match):
            indent = match.group(1)
            var_name = match.group(2)
            changes.append(f"delete {var_name} → drop({var_name})")
            return f"{indent}drop({var_name});"

        transformed = pattern_delete.sub(replace_delete, transformed)

        # delete[] arr; → drop(arr);
        pattern_delete_arr = re.compile(r'^(\s*)delete\s*\[\]\s*(\w+);', re.MULTILINE)

        def replace_delete_arr(match):
            indent = match.group(1)
            var_name = match.group(2)
            changes.append(f"delete[] {var_name} → drop({var_name})")
            return f"{indent}drop({var_name});"

        transformed = pattern_delete_arr.sub(replace_delete_arr, transformed)

        # std::unique_ptr<Type> var = std::make_unique<Type>(args);
        # → let var: Box<Type> = Box::new(args);
        pattern_unique = re.compile(
            r'^(\s*)std::unique_ptr<(\w+)>\s+(\w+)\s*=\s*std::make_unique<\w+>\(([^)]*)\);',
            re.MULTILINE
        )

        def replace_unique(match):
            indent = match.group(1)
            cpp_type = match.group(2)
            var_name = match.group(3)
            args = match.group(4)
            rust_type = cpp_type_to_rust(cpp_type)
            changes.append(f"std::unique_ptr<{cpp_type}> → Box<{rust_type}>")
            return f"{indent}let {var_name}: Box<{rust_type}> = Box::new({args});"

        transformed = pattern_unique.sub(replace_unique, transformed)

        # std::shared_ptr<Type> var = std::make_shared<Type>(args);
        # → let var: Rc<Type> = Rc::new(args);
        pattern_shared = re.compile(
            r'^(\s*)std::shared_ptr<(\w+)>\s+(\w+)\s*=\s*std::make_shared<\w+>\(([^)]*)\);',
            re.MULTILINE
        )

        def replace_shared(match):
            indent = match.group(1)
            cpp_type = match.group(2)
            var_name = match.group(3)
            args = match.group(4)
            rust_type = cpp_type_to_rust(cpp_type)
            changes.append(f"std::shared_ptr<{cpp_type}> → Rc<{rust_type}>")
            return f"{indent}let {var_name}: Rc<{rust_type}> = Rc::new({args});"

        transformed = pattern_shared.sub(replace_shared, transformed)

        # nullptr → None (when used with Option)
        pattern_nullptr = re.compile(r'\bnullptr\b')
        if pattern_nullptr.search(transformed):
            count = len(pattern_nullptr.findall(transformed))
            transformed = pattern_nullptr.sub('None', transformed)
            changes.append(f"nullptr → None ({count} ocurrencia(s))")

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
