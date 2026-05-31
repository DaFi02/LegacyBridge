"""Transformer: C++ strings → Rust strings.

Converts:
    std::string name = "hello";        →  let name: String = String::from("hello");
    const char* msg = "world";         →  let msg: &str = "world";
    str.length() / str.size()          →  str.len()
    str.substr(pos, len)               →  &str[pos..pos+len]
    str.find("x")                      →  str.find("x")  (similar in Rust)
    str.append("x") / str += "x"      →  str.push_str("x")
    str.c_str()                        →  str.as_str()
    to_string(x)                       →  x.to_string()
"""

import re

from .base import BaseTransformer, TransformResult


class StringConversionTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Strings → Rust Strings"

    @property
    def description(self) -> str:
        return "Convierte std::string y operaciones de string de C++ a String/&str de Rust"

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # std::string var = "value"; → let var: String = String::from("value");
        pattern_string_decl = re.compile(
            r'^(\s*)std::string\s+(\w+)\s*=\s*("(?:[^"\\]|\\.)*");',
            re.MULTILINE
        )

        def replace_string_decl(match):
            indent = match.group(1)
            var_name = match.group(2)
            value = match.group(3)
            changes.append(f"std::string {var_name} → let {var_name}: String")
            return f'{indent}let {var_name}: String = String::from({value});'

        transformed = pattern_string_decl.sub(replace_string_decl, transformed)

        # std::string var = other_string; → let var: String = other.clone();
        pattern_string_copy = re.compile(
            r'^(\s*)std::string\s+(\w+)\s*=\s*(\w+);',
            re.MULTILINE
        )

        def replace_string_copy(match):
            indent = match.group(1)
            var_name = match.group(2)
            source = match.group(3)
            changes.append(f"std::string {var_name} = {source} → let {var_name} = {source}.clone()")
            return f'{indent}let {var_name}: String = {source}.clone();'

        transformed = pattern_string_copy.sub(replace_string_copy, transformed)

        # .length() and .size() → .len()
        pattern_length = re.compile(r'\.(?:length|size)\(\)')
        if pattern_length.search(transformed):
            count = len(pattern_length.findall(transformed))
            transformed = pattern_length.sub('.len()', transformed)
            changes.append(f".length()/.size() → .len() ({count} ocurrencia(s))")

        # .append("str") → .push_str("str")
        pattern_append = re.compile(r'\.append\(([^)]+)\)')
        if pattern_append.search(transformed):
            count = len(pattern_append.findall(transformed))
            transformed = pattern_append.sub(r'.push_str(\1)', transformed)
            changes.append(f".append() → .push_str() ({count} ocurrencia(s))")

        # .c_str() → .as_str()
        pattern_cstr = re.compile(r'\.c_str\(\)')
        if pattern_cstr.search(transformed):
            count = len(pattern_cstr.findall(transformed))
            transformed = pattern_cstr.sub('.as_str()', transformed)
            changes.append(f".c_str() → .as_str() ({count} ocurrencia(s))")

        # .empty() → .is_empty()
        pattern_empty = re.compile(r'\.empty\(\)')
        if pattern_empty.search(transformed):
            count = len(pattern_empty.findall(transformed))
            transformed = pattern_empty.sub('.is_empty()', transformed)
            changes.append(f".empty() → .is_empty() ({count} ocurrencia(s))")

        # std::to_string(x) → x.to_string()
        pattern_to_string = re.compile(r'std::to_string\((\w+)\)')
        if pattern_to_string.search(transformed):
            count = len(pattern_to_string.findall(transformed))
            transformed = pattern_to_string.sub(r'\1.to_string()', transformed)
            changes.append(f"std::to_string(x) → x.to_string() ({count} ocurrencia(s))")

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
