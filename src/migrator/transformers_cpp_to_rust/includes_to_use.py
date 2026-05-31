"""Transformer: C++ #include → Rust use statements.

Converts:
    #include <iostream>     →  use std::io;
    #include <vector>       →  // Vec is in prelude
    #include <string>       →  // String is in prelude
    #include <map>          →  use std::collections::HashMap;
    #include <set>          →  use std::collections::HashSet;
    #include <algorithm>    →  // iterators in Rust
    #include <memory>       →  use std::rc::Rc;
    #include <fstream>      →  use std::fs;
    #include "myheader.h"   →  mod myheader;
"""

import re

from .base import BaseTransformer, TransformResult


# Mapping of C++ includes to Rust use statements
INCLUDE_MAP = {
    "iostream": "use std::io::{self, Write};",
    "fstream": "use std::fs;",
    "sstream": "use std::fmt;",
    "vector": "// Vec<T> está en el prelude de Rust",
    "string": "// String y &str están en el prelude de Rust",
    "map": "use std::collections::HashMap;",
    "unordered_map": "use std::collections::HashMap;",
    "set": "use std::collections::HashSet;",
    "unordered_set": "use std::collections::HashSet;",
    "algorithm": "// Rust usa iteradores y métodos de Iterator trait",
    "memory": "use std::rc::Rc;\nuse std::sync::Arc;",
    "cmath": "// Rust: use f64 methods directly",
    "math.h": "// Rust: use f64 methods directly",
    "cstdlib": "use std::process;",
    "cstdio": "use std::io::{self, Write};",
    "cassert": "// Rust: use assert!() macro",
    "mutex": "use std::sync::Mutex;",
    "thread": "use std::thread;",
    "functional": "// Rust: closures are native",
    "optional": "// Rust: Option<T> está en el prelude",
    "variant": "// Rust: use enum para variantes",
    "array": "// Rust: arrays [T; N] son nativos",
    "deque": "use std::collections::VecDeque;",
    "queue": "use std::collections::VecDeque;",
    "stack": "// Rust: use Vec<T> como stack (push/pop)",
    "utility": "// Rust: tuples son nativos",
}


class IncludesToUseTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "#include → use statements"

    @property
    def description(self) -> str:
        return "Convierte #include de C++ a declaraciones use de Rust"

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # #include <header>
        pattern_system = re.compile(r'^(\s*)#include\s*<(\w+)>', re.MULTILINE)

        def replace_system_include(match):
            indent = match.group(1)
            header = match.group(2)
            rust_equiv = INCLUDE_MAP.get(header, f"// TODO: buscar equivalente Rust de <{header}>")
            changes.append(f"#include <{header}> → {rust_equiv.split(chr(10))[0]}")
            return f"{indent}{rust_equiv}"

        transformed = pattern_system.sub(replace_system_include, transformed)

        # #include "header.h" → mod header;
        pattern_local = re.compile(r'^(\s*)#include\s*"(\w+)\.h(?:pp)?"', re.MULTILINE)

        def replace_local_include(match):
            indent = match.group(1)
            module_name = match.group(2)
            changes.append(f'#include "{module_name}.h" → mod {module_name}')
            return f"{indent}mod {module_name};"

        transformed = pattern_local.sub(replace_local_include, transformed)

        # Remove using namespace std; (no equivalent in Rust)
        pattern_using = re.compile(r'^(\s*)using\s+namespace\s+\w+;.*$', re.MULTILINE)
        if pattern_using.search(transformed):
            transformed = pattern_using.sub(r'\1// (namespaces manejados por mod/use en Rust)', transformed)
            changes.append("using namespace → comentario (Rust usa mod/use)")

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
