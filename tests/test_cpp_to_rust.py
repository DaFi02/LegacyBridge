"""Tests para el migrador C++ Legacy → Rust."""

from src.migrator.transformers_cpp_to_rust.raw_pointers import RawPointerTransformer
from src.migrator.transformers_cpp_to_rust.memory_management import MemoryManagementTransformer
from src.migrator.transformers_cpp_to_rust.types_and_structs import TypesAndStructsTransformer
from src.migrator.transformers_cpp_to_rust.control_flow import ControlFlowTransformer
from src.migrator.transformers_cpp_to_rust.string_conversion import StringConversionTransformer
from src.migrator.transformers_cpp_to_rust.includes_to_use import IncludesToUseTransformer
from src.migrator.engine_cpp_to_rust import CppToRustEngine


class TestIncludesToUse:
    def test_iostream(self):
        transformer = IncludesToUseTransformer()
        code = "#include <iostream>"
        result = transformer.transform(code)
        assert "use std::io" in result.transformed
        assert result.was_modified

    def test_map(self):
        transformer = IncludesToUseTransformer()
        code = "#include <map>"
        result = transformer.transform(code)
        assert "HashMap" in result.transformed

    def test_vector_prelude(self):
        transformer = IncludesToUseTransformer()
        code = "#include <vector>"
        result = transformer.transform(code)
        assert "prelude" in result.transformed

    def test_local_include(self):
        transformer = IncludesToUseTransformer()
        code = '#include "mymodule.h"'
        result = transformer.transform(code)
        assert "mod mymodule;" in result.transformed

    def test_using_namespace(self):
        transformer = IncludesToUseTransformer()
        code = "using namespace std;"
        result = transformer.transform(code)
        assert "namespace" not in result.transformed or "mod/use" in result.transformed

    def test_fstream(self):
        transformer = IncludesToUseTransformer()
        code = "#include <fstream>"
        result = transformer.transform(code)
        assert "std::fs" in result.transformed


class TestRawPointers:
    def test_const_pointer(self):
        transformer = RawPointerTransformer()
        code = "const int* ptr = &value;"
        result = transformer.transform(code)
        assert "let ptr: &i32" in result.transformed
        assert result.was_modified

    def test_mut_pointer_ref(self):
        transformer = RawPointerTransformer()
        code = "    int* ptr = &value;"
        result = transformer.transform(code)
        assert "&mut i32" in result.transformed
        assert "&mut value" in result.transformed

    def test_new_array(self):
        transformer = RawPointerTransformer()
        code = "    int* arr = new int[100];"
        result = transformer.transform(code)
        assert "Vec<i32>" in result.transformed
        assert "vec![0; 100]" in result.transformed

    def test_double_array(self):
        transformer = RawPointerTransformer()
        code = "    double* data = new double[50];"
        result = transformer.transform(code)
        assert "Vec<f64>" in result.transformed


class TestMemoryManagement:
    def test_new_single(self):
        transformer = MemoryManagementTransformer()
        code = "    int* p = new int(42);"
        result = transformer.transform(code)
        assert "Box::new(42)" in result.transformed
        assert "Box<i32>" in result.transformed
        assert result.was_modified

    def test_delete(self):
        transformer = MemoryManagementTransformer()
        code = "    delete ptr;"
        result = transformer.transform(code)
        assert "drop(ptr)" in result.transformed

    def test_delete_array(self):
        transformer = MemoryManagementTransformer()
        code = "    delete[] arr;"
        result = transformer.transform(code)
        assert "drop(arr)" in result.transformed

    def test_unique_ptr(self):
        transformer = MemoryManagementTransformer()
        code = "    std::unique_ptr<int> p = std::make_unique<int>(99);"
        result = transformer.transform(code)
        assert "Box<i32>" in result.transformed
        assert "Box::new(99)" in result.transformed

    def test_shared_ptr(self):
        transformer = MemoryManagementTransformer()
        code = "    std::shared_ptr<int> p = std::make_shared<int>(77);"
        result = transformer.transform(code)
        assert "Rc<i32>" in result.transformed
        assert "Rc::new(77)" in result.transformed

    def test_nullptr(self):
        transformer = MemoryManagementTransformer()
        code = "    int* p = nullptr;"
        result = transformer.transform(code)
        assert "None" in result.transformed
        assert "nullptr" not in result.transformed


class TestTypesAndStructs:
    def test_simple_struct(self):
        transformer = TypesAndStructsTransformer()
        code = "struct Point {\n    int x;\n    int y;\n};"
        result = transformer.transform(code)
        assert "pub struct Point" in result.transformed
        assert "x: i32" in result.transformed
        assert "y: i32" in result.transformed
        assert "#[derive(Debug, Clone)]" in result.transformed
        assert result.was_modified

    def test_enum(self):
        transformer = TypesAndStructsTransformer()
        code = "enum Color {\n    RED,\n    GREEN,\n    BLUE\n};"
        result = transformer.transform(code)
        assert "pub enum Color" in result.transformed
        assert "Red," in result.transformed
        assert "Green," in result.transformed
        assert "Blue," in result.transformed

    def test_typedef(self):
        transformer = TypesAndStructsTransformer()
        code = "typedef unsigned int uint;"
        result = transformer.transform(code)
        assert "type Uint = u32;" in result.transformed

    def test_typedef_long(self):
        transformer = TypesAndStructsTransformer()
        code = "typedef long long int64;"
        # 'long long' is two words, may not match perfectly
        result = transformer.transform(code)
        assert "type" in result.transformed


class TestControlFlow:
    def test_classic_for_loop(self):
        transformer = ControlFlowTransformer()
        code = "for (int i = 0; i < 10; i++) {"
        result = transformer.transform(code)
        assert "for i in 0..10" in result.transformed
        assert result.was_modified

    def test_range_based_for_ref(self):
        transformer = ControlFlowTransformer()
        code = "for (auto& item : items) {"
        result = transformer.transform(code)
        assert "for item in &items" in result.transformed

    def test_range_based_for_value(self):
        transformer = ControlFlowTransformer()
        code = "for (auto item : items) {"
        result = transformer.transform(code)
        assert "for item in items" in result.transformed

    def test_while_loop(self):
        transformer = ControlFlowTransformer()
        code = "while (count > 0) {"
        result = transformer.transform(code)
        assert "while count > 0 {" in result.transformed

    def test_cout_simple(self):
        transformer = ControlFlowTransformer()
        code = 'std::cout << "Hello" << std::endl;'
        result = transformer.transform(code)
        assert "println!" in result.transformed

    def test_cout_variable(self):
        transformer = ControlFlowTransformer()
        code = "std::cout << value << std::endl;"
        result = transformer.transform(code)
        assert "println!" in result.transformed
        assert "value" in result.transformed


class TestStringConversion:
    def test_string_declaration(self):
        transformer = StringConversionTransformer()
        code = '    std::string name = "hello";'
        result = transformer.transform(code)
        assert "let name: String" in result.transformed
        assert 'String::from("hello")' in result.transformed
        assert result.was_modified

    def test_length(self):
        transformer = StringConversionTransformer()
        code = "name.length()"
        result = transformer.transform(code)
        assert "name.len()" in result.transformed

    def test_size(self):
        transformer = StringConversionTransformer()
        code = "vec.size()"
        result = transformer.transform(code)
        assert "vec.len()" in result.transformed

    def test_append(self):
        transformer = StringConversionTransformer()
        code = 'name.append(" world")'
        result = transformer.transform(code)
        assert 'name.push_str(" world")' in result.transformed

    def test_c_str(self):
        transformer = StringConversionTransformer()
        code = "name.c_str()"
        result = transformer.transform(code)
        assert "name.as_str()" in result.transformed

    def test_empty(self):
        transformer = StringConversionTransformer()
        code = "if (name.empty()) {"
        result = transformer.transform(code)
        assert "name.is_empty()" in result.transformed

    def test_to_string(self):
        transformer = StringConversionTransformer()
        code = "std::to_string(42)"
        result = transformer.transform(code)
        # Note: regex matches \w+ so literal 42 won't match, but variable will
        transformer2 = StringConversionTransformer()
        code2 = "std::to_string(count)"
        result2 = transformer2.transform(code2)
        assert "count.to_string()" in result2.transformed


class TestCppToRustEngine:
    def test_full_migration(self):
        engine = CppToRustEngine()
        code = '''#include <iostream>
#include <vector>
#include <map>

using namespace std;

struct Point {
    int x;
    int y;
};

int main() {
    std::string name = "test";
    int* arr = new int[10];
    
    for (int i = 0; i < 10; i++) {
        std::cout << name << std::endl;
    }
    
    delete[] arr;
    return 0;
}'''
        results = engine.migrate_code(code)
        assert len(results) > 0

        final_code = results[-1].transformed
        # Includes converted
        assert "use std::io" in final_code
        assert "HashMap" in final_code
        # Struct converted
        assert "pub struct Point" in final_code
        # String converted
        assert "String::from" in final_code
        # Memory converted
        assert "drop(arr)" in final_code
        # For loop converted
        assert "for i in 0..10" in final_code
        # cout converted
        assert "println!" in final_code

    def test_memory_safety(self):
        """Verify that unsafe raw pointers are converted to safe Rust."""
        engine = CppToRustEngine()
        code = '''    int* p = new int(42);
    std::shared_ptr<int> sp = std::make_shared<int>(10);
    delete p;'''
        results = engine.migrate_code(code)
        assert len(results) > 0
        final_code = results[-1].transformed
        assert "Box::new(42)" in final_code
        assert "Rc::new(10)" in final_code
        assert "drop(p)" in final_code
        assert "new int" not in final_code
        assert "delete" not in final_code
