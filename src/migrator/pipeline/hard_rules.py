"""Reglas duras de transformación determinística.

Transformaciones que NO requieren IA - son mappings directos 1:1.
Se aplican ANTES de enviar a la IA para:
1. Reducir trabajo de la IA (menos que "pensar")
2. Garantizar consistencia (sin alucinaciones posibles)
3. Acelerar el pipeline (sin llamadas API para lo trivial)

La IA solo se encarga de la lógica compleja que estas reglas
no pueden resolver de forma determinística.
"""

import re
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class TransformResult:
    """Resultado de aplicar una regla dura."""
    code: str
    transformations_applied: list[str] = field(default_factory=list)
    lines_changed: int = 0


class HardRule(ABC):
    """Regla de transformación determinística."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def apply(self, code: str) -> TransformResult:
        ...


# ============================================================
# REGLAS COBOL → RUST
# ============================================================

class CobolTypesToRust(HardRule):
    """Convierte tipos de datos COBOL a tipos Rust equivalentes."""

    @property
    def name(self) -> str:
        return "cobol_types_to_rust"

    @property
    def description(self) -> str:
        return "PIC 9 → i32/i64, PIC X → String, PIC 9V99 → f64"

    # Mapeo directo de PIC patterns a tipos Rust
    TYPE_MAP = [
        # PIC S9(n) COMP → enteros con signo
        (r'PIC\s+S9\((\d+)\)\s+COMP', lambda m: f"i64" if int(m.group(1)) > 9 else "i32"),
        # PIC 9(n)V9(n) o PIC 9(n)V99 → f64
        (r'PIC\s+9+\(?(\d*)\)?V9+\(?(\d*)\)?', lambda m: "f64"),
        # PIC 9(n) → i32 o i64
        (r'PIC\s+9\((\d+)\)', lambda m: f"i64" if int(m.group(1)) > 9 else "i32"),
        # PIC 9 → i32
        (r'PIC\s+9+', lambda m: "i32"),
        # PIC X(n) → String
        (r'PIC\s+X\(\d+\)', lambda m: "String"),
        # PIC X+ → String
        (r'PIC\s+X+', lambda m: "String"),
    ]

    def apply(self, code: str) -> TransformResult:
        result = code
        applied = []
        changes = 0

        for pattern, replacement in self.TYPE_MAP:
            matches = re.findall(pattern, result, re.IGNORECASE)
            if matches:
                if callable(replacement):
                    for match in re.finditer(pattern, result, re.IGNORECASE):
                        old = match.group(0)
                        new = replacement(match)
                        result = result.replace(old, f"/* {old} */ {new}", 1)
                        changes += 1
                applied.append(f"{pattern}: {len(matches)} conversiones")

        return TransformResult(code=result, transformations_applied=applied, lines_changed=changes)


class CobolVerbsToRust(HardRule):
    """Convierte verbos COBOL a equivalentes Rust directos."""

    @property
    def name(self) -> str:
        return "cobol_verbs_to_rust"

    @property
    def description(self) -> str:
        return "DISPLAY→println!, MOVE→let/=, ADD→+=, SUBTRACT→-=, MULTIPLY→*=, STOP RUN→return"

    # Transformaciones directas de verbos COBOL
    VERB_PATTERNS = [
        # DISPLAY "text" → println!("text")
        (r'^\s*DISPLAY\s+"([^"]*)"\.?\s*$', r'    println!("\1");'),
        # DISPLAY "text" variable → println!("text {}", variable)  
        (r'^\s*DISPLAY\s+"([^"]*)"\s+([\w-]+)\.?\s*$', r'    println!("\1 {}", \2);'),
        # DISPLAY variable → println!("{}", variable)
        (r'^\s*DISPLAY\s+([\w-]+)\.?\s*$', r'    println!("{}", \1);'),
        # MOVE value TO variable → let variable = value / variable = value
        (r'^\s*MOVE\s+(\d+)\s+TO\s+([\w-]+)\.?\s*$', r'    \2 = \1;'),
        (r'^\s*MOVE\s+"([^"]*)"\s+TO\s+([\w-]+)\.?\s*$', r'    \2 = String::from("\1");'),
        (r'^\s*MOVE\s+([\w-]+)\s+TO\s+([\w-]+)\.?\s*$', r'    \2 = \1;'),
        # ADD n TO var → var += n
        (r'^\s*ADD\s+(\d+)\s+TO\s+([\w-]+)\.?\s*$', r'    \2 += \1;'),
        (r'^\s*ADD\s+([\w-]+)\s+TO\s+([\w-]+)\.?\s*$', r'    \2 += \1;'),
        # SUBTRACT n FROM var → var -= n
        (r'^\s*SUBTRACT\s+(\d+)\s+FROM\s+([\w-]+)\.?\s*$', r'    \2 -= \1;'),
        (r'^\s*SUBTRACT\s+([\w-]+)\s+FROM\s+([\w-]+)\.?\s*$', r'    \2 -= \1;'),
        # MULTIPLY var BY n GIVING result → result = var * n
        (r'^\s*MULTIPLY\s+([\w-]+)\s+BY\s+([\w-]+)\s+GIVING\s+([\w-]+)\.?\s*$', r'    \3 = \1 * \2;'),
        # COMPUTE var = expr → let var = expr (preservar la expresión)
        (r'^\s*COMPUTE\s+([\w-]+)\s*=\s*(.+?)\.?\s*$', r'    \1 = \2;'),
        # STOP RUN → return / process::exit(0)
        (r'^\s*STOP\s+RUN\.?\s*$', r'    return;'),
        # PERFORM paragraph → paragraph()
        (r'^\s*PERFORM\s+([\w-]+)\.?\s*$', r'    \1();'),
    ]

    def apply(self, code: str) -> TransformResult:
        lines = code.split('\n')
        result_lines = []
        applied = []
        changes = 0

        for line in lines:
            transformed = False
            for pattern, replacement in self.VERB_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    new_line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                    # Convertir nombres COBOL (con guiones) a snake_case
                    new_line = self._cobol_name_to_rust(new_line)
                    result_lines.append(new_line)
                    changes += 1
                    transformed = True
                    break

            if not transformed:
                result_lines.append(line)

        if changes > 0:
            applied.append(f"Verbos transformados: {changes}")

        return TransformResult(
            code='\n'.join(result_lines),
            transformations_applied=applied,
            lines_changed=changes,
        )

    def _cobol_name_to_rust(self, line: str) -> str:
        """Convierte nombres-cobol a nombres_rust en una línea."""
        # No tocar strings entre comillas
        parts = re.split(r'("[^"]*")', line)
        for i, part in enumerate(parts):
            if not part.startswith('"'):
                # Reemplazar guiones en identificadores por underscores
                parts[i] = re.sub(r'\b([\w]+-[\w-]+)\b', 
                                  lambda m: m.group(1).lower().replace('-', '_'), 
                                  part)
        return ''.join(parts)


class CobolControlFlowToRust(HardRule):
    """Convierte estructuras de control COBOL a Rust."""

    @property
    def name(self) -> str:
        return "cobol_control_flow_to_rust"

    @property
    def description(self) -> str:
        return "IF/ELSE/END-IF→if/else/{}, PERFORM UNTIL→while, EVALUATE→match"

    def apply(self, code: str) -> TransformResult:
        lines = code.split('\n')
        result_lines = []
        changes = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip().upper()

            # IF condition → if condition {
            if_match = re.match(r'^\s*IF\s+(.+?)\.?\s*$', line, re.IGNORECASE)
            if if_match and 'END-IF' not in stripped:
                condition = self._convert_condition(if_match.group(1))
                result_lines.append(f'    if {condition} {{')
                changes += 1
                i += 1
                continue

            # ELSE → } else {
            if stripped in ('ELSE', 'ELSE.'):
                result_lines.append('    } else {')
                changes += 1
                i += 1
                continue

            # END-IF → }
            if stripped in ('END-IF', 'END-IF.'):
                result_lines.append('    }')
                changes += 1
                i += 1
                continue

            # PERFORM ... UNTIL condition → while !condition {
            perform_until = re.match(
                r'^\s*PERFORM\s+([\w-]+)\s+UNTIL\s+(.+?)\.?\s*$', line, re.IGNORECASE
            )
            if perform_until:
                func_name = perform_until.group(1).lower().replace('-', '_')
                condition = self._convert_condition(perform_until.group(2))
                result_lines.append(f'    while !({condition}) {{')
                result_lines.append(f'        {func_name}();')
                result_lines.append(f'    }}')
                changes += 1
                i += 1
                continue

            # EVALUATE var → match var {
            eval_match = re.match(r'^\s*EVALUATE\s+([\w-]+)\.?\s*$', line, re.IGNORECASE)
            if eval_match:
                var = eval_match.group(1).lower().replace('-', '_')
                result_lines.append(f'    match {var} {{')
                changes += 1
                i += 1
                continue

            # WHEN value → value => {
            when_match = re.match(r'^\s*WHEN\s+"?([^"\s]+)"?\.?\s*$', line, re.IGNORECASE)
            if when_match:
                val = when_match.group(1)
                if val.upper() == 'OTHER':
                    result_lines.append(f'        _ => {{')
                else:
                    try:
                        int(val)
                        result_lines.append(f'        {val} => {{')
                    except ValueError:
                        result_lines.append(f'        "{val}" => {{')
                changes += 1
                i += 1
                continue

            # END-EVALUATE → }
            if stripped in ('END-EVALUATE', 'END-EVALUATE.'):
                result_lines.append('    }')
                changes += 1
                i += 1
                continue

            result_lines.append(line)
            i += 1

        applied = []
        if changes > 0:
            applied.append(f"Control de flujo: {changes} conversiones")

        return TransformResult(
            code='\n'.join(result_lines),
            transformations_applied=applied,
            lines_changed=changes,
        )

    def _convert_condition(self, cond: str) -> str:
        """Convierte condición COBOL a Rust."""
        result = cond.strip()
        # Operadores (orden importa: más específicos primero)
        result = re.sub(r'\bNOT\s+EQUAL\s+TO\b', '!=', result, flags=re.IGNORECASE)
        result = re.sub(r'\bGREATER\s+THAN\b', '>', result, flags=re.IGNORECASE)
        result = re.sub(r'\bLESS\s+THAN\b', '<', result, flags=re.IGNORECASE)
        result = re.sub(r'\bEQUAL\s+TO\b', '==', result, flags=re.IGNORECASE)
        result = re.sub(r'\bNOT\s*>', '<=', result, flags=re.IGNORECASE)
        result = re.sub(r'\bNOT\s*<', '>=', result, flags=re.IGNORECASE)
        result = re.sub(r'\bAND\b', '&&', result, flags=re.IGNORECASE)
        result = re.sub(r'\bOR\b', '||', result, flags=re.IGNORECASE)
        result = re.sub(r'\bNOT\b', '!', result, flags=re.IGNORECASE)
        # Nombres COBOL a snake_case
        result = re.sub(r'\b([\w]+-[\w-]+)\b', 
                        lambda m: m.group(1).lower().replace('-', '_'), result)
        return result


class CobolStructureToRust(HardRule):
    """Convierte estructura de programa COBOL a módulo Rust."""

    @property
    def name(self) -> str:
        return "cobol_structure_to_rust"

    @property
    def description(self) -> str:
        return "PROGRAM-ID→mod, WORKING-STORAGE→struct, paragraphs→fn"

    def apply(self, code: str) -> TransformResult:
        lines = code.split('\n')
        result_lines = []
        changes = 0
        in_data_division = False
        in_procedure = False
        struct_fields = []
        program_name = "program"

        for line in lines:
            stripped = line.strip()
            upper = stripped.upper()

            # PROGRAM-ID
            prog_match = re.match(r'^\s*PROGRAM-ID\.\s*([\w-]+)\.?\s*$', stripped, re.IGNORECASE)
            if prog_match:
                program_name = prog_match.group(1).lower().replace('-', '_')
                result_lines.append(f'// Migrado de COBOL: {prog_match.group(1)}')
                changes += 1
                continue

            # Skip division/section headers
            if re.match(r'^\s*\w[\w-]*\s+DIVISION', stripped, re.IGNORECASE):
                if 'DATA' in upper:
                    in_data_division = True
                    in_procedure = False
                elif 'PROCEDURE' in upper:
                    in_data_division = False
                    in_procedure = True
                    # Emit struct if we collected fields
                    if struct_fields:
                        result_lines.append(f'struct {program_name.title().replace("_", "")}State {{')
                        for fname, ftype in struct_fields:
                            result_lines.append(f'    {fname}: {ftype},')
                        result_lines.append('}')
                        result_lines.append('')
                        changes += 1
                continue

            if re.match(r'^\s*[\w-]+\s+SECTION', stripped, re.IGNORECASE):
                continue

            # WORKING-STORAGE variables (01 level)
            if in_data_division:
                var_match = re.match(
                    r'^\s*(?:01|77)\s+([\w-]+)\s+PIC\s+(.+?)\.?\s*$', stripped, re.IGNORECASE
                )
                if var_match:
                    var_name = var_match.group(1).lower().replace('-', '_')
                    pic = var_match.group(2).strip().rstrip('.')
                    rust_type = self._pic_to_type(pic)
                    struct_fields.append((var_name, rust_type))
                    changes += 1
                    continue

                # Group level (01 with sub-levels) - just capture the name
                group_match = re.match(r'^\s*01\s+([\w-]+)\.\s*$', stripped, re.IGNORECASE)
                if group_match:
                    result_lines.append(f'// Grupo: {group_match.group(1)}')
                    continue

            # Paragraphs → functions
            if in_procedure:
                para_match = re.match(r'^\s*([\w-]+)\.\s*$', stripped)
                if para_match:
                    name = para_match.group(1)
                    if not any(kw in name.upper() for kw in ('DIVISION', 'SECTION')):
                        fn_name = name.lower().replace('-', '_')
                        result_lines.append(f'fn {fn_name}() {{')
                        changes += 1
                        continue

            # Pass through other lines
            result_lines.append(line)

        applied = []
        if changes > 0:
            applied.append(f"Estructura convertida: {changes} elementos")

        return TransformResult(
            code='\n'.join(result_lines),
            transformations_applied=applied,
            lines_changed=changes,
        )

    def _pic_to_type(self, pic: str) -> str:
        """Convierte PIC clause a tipo Rust."""
        pic = pic.upper().strip()
        if 'V' in pic or '.' in pic:
            return "f64"
        if re.match(r'S?9', pic):
            # Contar dígitos
            count_match = re.search(r'9\((\d+)\)', pic)
            if count_match and int(count_match.group(1)) > 9:
                return "i64"
            return "i32"
        if re.match(r'X', pic):
            return "String"
        return "String"  # Default


# ============================================================
# REGLAS C++ → RUST
# ============================================================

class CppIncludesToRust(HardRule):
    """Convierte #include a use statements equivalentes."""

    @property
    def name(self) -> str:
        return "cpp_includes_to_rust"

    @property
    def description(self) -> str:
        return "#include <iostream> → use std::io, <vector> → Vec (built-in), etc."

    INCLUDE_MAP = {
        "iostream": "// use std::io; (println! no necesita import)",
        "vector": "// Vec is built-in",
        "string": "// String is built-in",
        "map": "use std::collections::HashMap;",
        "unordered_map": "use std::collections::HashMap;",
        "set": "use std::collections::HashSet;",
        "unordered_set": "use std::collections::HashSet;",
        "memory": "// Box, Rc, Arc are in std",
        "fstream": "use std::fs::File;\nuse std::io::{BufRead, BufReader, Write};",
        "algorithm": "// iterators have sort, find, etc.",
        "functional": "// closures are built-in",
        "numeric": "// iter().sum(), iter().product()",
        "cmath": "// use f64 methods: sqrt(), abs(), etc.",
        "math.h": "// use f64 methods",
        "stdio.h": "// use println!, eprintln!",
        "stdlib.h": "// use std::process",
        "cstdlib": "// use std::process",
        "cassert": "// use assert!, debug_assert!",
        "thread": "use std::thread;",
        "mutex": "use std::sync::Mutex;",
        "atomic": "use std::sync::atomic::{AtomicBool, AtomicI32, Ordering};",
    }

    def apply(self, code: str) -> TransformResult:
        lines = code.split('\n')
        result_lines = []
        changes = 0
        seen_uses = set()

        for line in lines:
            include_match = re.match(r'^\s*#include\s*[<"](\w+)(?:\.\w+)?[>"]', line)
            if include_match:
                header = include_match.group(1)
                rust_equiv = self.INCLUDE_MAP.get(header, f"// TODO: find Rust equivalent for {header}")
                if rust_equiv not in seen_uses:
                    result_lines.append(rust_equiv)
                    seen_uses.add(rust_equiv)
                changes += 1
            else:
                result_lines.append(line)

        applied = []
        if changes > 0:
            applied.append(f"Includes convertidos: {changes}")

        return TransformResult(
            code='\n'.join(result_lines),
            transformations_applied=applied,
            lines_changed=changes,
        )


class CppTypesToRust(HardRule):
    """Convierte tipos C++ a equivalentes Rust."""

    @property
    def name(self) -> str:
        return "cpp_types_to_rust"

    @property
    def description(self) -> str:
        return "int→i32, double→f64, bool→bool, void→(), string→String, etc."

    TYPE_MAP = [
        (r'\bunsigned\s+long\s+long\b', 'u64'),
        (r'\blong\s+long\b', 'i64'),
        (r'\bunsigned\s+long\b', 'u64'),
        (r'\bunsigned\s+int\b', 'u32'),
        (r'\bunsigned\s+char\b', 'u8'),
        (r'\blong\s+double\b', 'f64'),
        (r'\blong\b', 'i64'),
        (r'\bdouble\b', 'f64'),
        (r'\bfloat\b', 'f32'),
        (r'\bchar\b', 'char'),
        (r'\bbool\b', 'bool'),
        (r'\bsize_t\b', 'usize'),
        (r'\bint\b', 'i32'),
        (r'\bvoid\b', '()'),
        (r'\bstd::string\b', 'String'),
        (r'\bstring\b', 'String'),
        (r'\bstd::vector<([^>]+)>', r'Vec<\1>'),
        (r'\bvector<([^>]+)>', r'Vec<\1>'),
        (r'\bstd::map<([^,]+),\s*([^>]+)>', r'HashMap<\1, \2>'),
        (r'\bstd::set<([^>]+)>', r'HashSet<\1>'),
        (r'\bnullptr\b', 'None'),
        (r'\bNULL\b', 'None'),
        (r'\btrue\b', 'true'),
        (r'\bfalse\b', 'false'),
    ]

    def apply(self, code: str) -> TransformResult:
        result = code
        changes = 0

        for pattern, replacement in self.TYPE_MAP:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                changes += result.count(re.findall(pattern, result)[0]) if re.findall(pattern, result) else 0
                result = new_result

        applied = []
        if changes > 0:
            applied.append(f"Tipos convertidos: {changes}")
        # Count actual differences
        actual_changes = sum(1 for a, b in zip(code.split('\n'), result.split('\n')) if a != b)

        return TransformResult(
            code=result,
            transformations_applied=applied,
            lines_changed=actual_changes,
        )


class CppOutputToRust(HardRule):
    """Convierte cout/printf a println!"""

    @property
    def name(self) -> str:
        return "cpp_output_to_rust"

    @property
    def description(self) -> str:
        return "cout << x << endl → println!(\"{}\", x), printf → println!"

    def apply(self, code: str) -> TransformResult:
        lines = code.split('\n')
        result_lines = []
        changes = 0

        for line in lines:
            # std::cout << "text" << var << std::endl;
            cout_match = re.match(r'^(\s*)(?:std::)?cout\s*<<\s*(.+?)\s*;', line)
            if cout_match:
                indent = cout_match.group(1)
                parts = re.split(r'\s*<<\s*', cout_match.group(2))
                # Build println! call
                fmt_parts = []
                args = []
                for part in parts:
                    part = part.strip()
                    if part in ('std::endl', 'endl', '"\\n"', "'\\n'"):
                        continue  # println! adds newline
                    elif part.startswith('"') and part.endswith('"'):
                        fmt_parts.append(part[1:-1])
                    else:
                        fmt_parts.append('{}')
                        args.append(part)

                fmt_str = ''.join(fmt_parts)
                if args:
                    result_lines.append(f'{indent}println!("{fmt_str}", {", ".join(args)});')
                else:
                    result_lines.append(f'{indent}println!("{fmt_str}");')
                changes += 1
                continue

            # printf("format", args)
            printf_match = re.match(r'^(\s*)printf\s*\(\s*"([^"]*)"(?:\s*,\s*(.+?))?\s*\)\s*;', line)
            if printf_match:
                indent = printf_match.group(1)
                fmt = printf_match.group(2)
                args_str = printf_match.group(3)
                # Convert C format specifiers to Rust
                fmt = fmt.replace('%d', '{}').replace('%i', '{}')
                fmt = fmt.replace('%f', '{:.2}').replace('%lf', '{:.2}')
                fmt = fmt.replace('%s', '{}').replace('%c', '{}')
                fmt = fmt.replace('%ld', '{}').replace('%lu', '{}')
                fmt = fmt.replace('\\n', '')  # println! adds newline
                if args_str:
                    result_lines.append(f'{indent}println!("{fmt}", {args_str});')
                else:
                    result_lines.append(f'{indent}println!("{fmt}");')
                changes += 1
                continue

            result_lines.append(line)

        applied = []
        if changes > 0:
            applied.append(f"Output convertido: {changes}")

        return TransformResult(
            code='\n'.join(result_lines),
            transformations_applied=applied,
            lines_changed=changes,
        )


class CppMemoryToRust(HardRule):
    """Convierte patrones de memoria C++ a ownership Rust."""

    @property
    def name(self) -> str:
        return "cpp_memory_to_rust"

    @property
    def description(self) -> str:
        return "new T → Box::new(T), delete → drop(), T* → &T, unique_ptr → Box"

    def apply(self, code: str) -> TransformResult:
        result = code
        changes = 0

        # new Type(...) → Box::new(Type::new(...))
        new_result = re.sub(
            r'\bnew\s+(\w+)\(([^)]*)\)',
            r'Box::new(\1::new(\2))',
            result
        )
        if new_result != result:
            changes += len(re.findall(r'\bnew\s+\w+\(', result))
            result = new_result

        # new Type[n] → vec![Default::default(); n]
        new_arr = re.sub(
            r'\bnew\s+(\w+)\[([^\]]+)\]',
            r'vec![0; \2]',
            result
        )
        if new_arr != result:
            changes += 1
            result = new_arr

        # delete ptr; / delete[] ptr; → drop(ptr);
        del_result = re.sub(r'\bdelete\s*(?:\[\])?\s*(\w+)\s*;', r'drop(\1);', result)
        if del_result != result:
            changes += len(re.findall(r'\bdelete\b', result))
            result = del_result

        # unique_ptr<T> → Box<T>
        result = re.sub(r'\bstd::unique_ptr<(\w+)>', r'Box<\1>', result)
        # shared_ptr<T> → Arc<T>
        result = re.sub(r'\bstd::shared_ptr<(\w+)>', r'Arc<\1>', result)
        # make_unique<T>(...) → Box::new(T::new(...))
        result = re.sub(r'\bstd::make_unique<(\w+)>\(([^)]*)\)', r'Box::new(\1::new(\2))', result)
        # make_shared<T>(...) → Arc::new(T::new(...))
        result = re.sub(r'\bstd::make_shared<(\w+)>\(([^)]*)\)', r'Arc::new(\1::new(\2))', result)

        applied = []
        if changes > 0:
            applied.append(f"Memoria convertida: {changes}")

        return TransformResult(
            code=result,
            transformations_applied=applied,
            lines_changed=changes,
        )


# ============================================================
# REGLAS JAVA 8 → JAVA 17
# ============================================================

class JavaCollectionsToModern(HardRule):
    """Convierte colecciones Java 8 a factory methods modernos."""

    @property
    def name(self) -> str:
        return "java_collections_modern"

    @property
    def description(self) -> str:
        return "Arrays.asList→List.of, Collections.empty*→*.of()"

    PATTERNS = [
        (r'Arrays\.asList\(([^)]*)\)', r'List.of(\1)'),
        (r'Collections\.emptyList\(\)', 'List.of()'),
        (r'Collections\.emptyMap\(\)', 'Map.of()'),
        (r'Collections\.emptySet\(\)', 'Set.of()'),
        (r'Collections\.singletonList\(([^)]+)\)', r'List.of(\1)'),
        (r'Collections\.singleton\(([^)]+)\)', r'Set.of(\1)'),
    ]

    def apply(self, code: str) -> TransformResult:
        result = code
        changes = 0
        for pattern, replacement in self.PATTERNS:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                changes += len(re.findall(pattern, result))
                result = new_result

        applied = []
        if changes > 0:
            applied.append(f"Colecciones modernizadas: {changes}")

        return TransformResult(code=result, transformations_applied=applied, lines_changed=changes)


# ============================================================
# MOTOR DE REGLAS DURAS
# ============================================================

# Registros de reglas por tipo de migración
HARD_RULES_REGISTRY: dict[str, list[type[HardRule]]] = {
    "cobol_to_rust": [
        CobolStructureToRust,
        CobolTypesToRust,
        CobolVerbsToRust,
        CobolControlFlowToRust,
    ],
    "cpp_to_rust": [
        CppIncludesToRust,
        CppTypesToRust,
        CppOutputToRust,
        CppMemoryToRust,
    ],
    "java8_to_java17": [
        JavaCollectionsToModern,
    ],
}


class HardRuleEngine:
    """Motor de reglas duras determinísticas.
    
    Se ejecuta ANTES de la IA para:
    - Resolver transformaciones triviales sin LLM
    - Darle a la IA código pre-procesado más fácil de completar
    - Garantizar consistencia en patrones conocidos
    
    Usage:
        engine = HardRuleEngine("cobol_to_rust")
        result = engine.apply_all(source_code)
        # result.code tiene las transformaciones determinísticas
        # Solo enviar a IA lo que no se pudo resolver aquí
    """

    def __init__(self, migration_type: str):
        self.migration_type = migration_type
        rule_classes = HARD_RULES_REGISTRY.get(migration_type, [])
        self._rules: list[HardRule] = [cls() for cls in rule_classes]

    @property
    def rules(self) -> list[HardRule]:
        return self._rules

    def apply_all(self, code: str) -> TransformResult:
        """Aplica todas las reglas en orden."""
        current = code
        all_applied = []
        total_changes = 0

        for rule in self._rules:
            result = rule.apply(current)
            current = result.code
            all_applied.extend(result.transformations_applied)
            total_changes += result.lines_changed

        return TransformResult(
            code=current,
            transformations_applied=all_applied,
            lines_changed=total_changes,
        )

    def apply_single(self, code: str, rule_name: str) -> TransformResult:
        """Aplica una sola regla por nombre."""
        for rule in self._rules:
            if rule.name == rule_name:
                return rule.apply(code)
        return TransformResult(code=code)

    def summary(self) -> str:
        """Lista las reglas disponibles."""
        lines = [f"Reglas duras para {self.migration_type}:"]
        for rule in self._rules:
            lines.append(f"  • {rule.name}: {rule.description}")
        return '\n'.join(lines)
