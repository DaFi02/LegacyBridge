"""Tests para el motor de migración Java 8 → Java 17+."""

from src.migrator.transformers.collection_factory import CollectionFactoryTransformer
from src.migrator.transformers.instanceof_pattern import InstanceofPatternTransformer
from src.migrator.transformers.var_keyword import VarKeywordTransformer
from src.migrator.transformers.text_blocks import TextBlockTransformer
from src.migrator.transformers.switch_expression import SwitchExpressionTransformer
from src.migrator import MigrationEngine


class TestCollectionFactory:
    def test_arrays_aslist_to_list_of(self):
        transformer = CollectionFactoryTransformer()
        code = 'List<String> names = Arrays.asList("a", "b", "c");'
        result = transformer.transform(code)
        assert 'List.of("a", "b", "c")' in result.transformed
        assert result.was_modified

    def test_empty_list(self):
        transformer = CollectionFactoryTransformer()
        code = "List<String> empty = Collections.emptyList();"
        result = transformer.transform(code)
        assert "List.of()" in result.transformed

    def test_empty_map(self):
        transformer = CollectionFactoryTransformer()
        code = "Map<String, String> m = Collections.emptyMap();"
        result = transformer.transform(code)
        assert "Map.of()" in result.transformed

    def test_singleton_list(self):
        transformer = CollectionFactoryTransformer()
        code = 'List<String> single = Collections.singletonList("only");'
        result = transformer.transform(code)
        assert 'List.of("only")' in result.transformed

    def test_no_change_for_regular_code(self):
        transformer = CollectionFactoryTransformer()
        code = 'String name = "hello";'
        result = transformer.transform(code)
        assert not result.was_modified


class TestInstanceofPattern:
    def test_basic_instanceof_cast(self):
        transformer = InstanceofPatternTransformer()
        code = '''    if (obj instanceof String) {
        String s = (String) obj;
        return s.length();
    }'''
        result = transformer.transform(code)
        assert "instanceof String s" in result.transformed
        assert "(String) obj" not in result.transformed
        assert result.was_modified

    def test_integer_instanceof(self):
        transformer = InstanceofPatternTransformer()
        code = '''    if (value instanceof Integer) {
        Integer num = (Integer) value;
        return num.intValue();
    }'''
        result = transformer.transform(code)
        assert "instanceof Integer num" in result.transformed

    def test_no_change_without_cast(self):
        transformer = InstanceofPatternTransformer()
        code = '''    if (obj instanceof String) {
        return "is string";
    }'''
        result = transformer.transform(code)
        assert not result.was_modified


class TestVarKeyword:
    def test_same_type_constructor(self):
        transformer = VarKeywordTransformer()
        code = "    ArrayList<String> names = new ArrayList<String>();"
        result = transformer.transform(code)
        assert "var names" in result.transformed
        assert result.was_modified

    def test_diamond_operator(self):
        transformer = VarKeywordTransformer()
        code = "    HashMap<String, Integer> scores = new HashMap<>();"
        result = transformer.transform(code)
        assert "var scores" in result.transformed

    def test_interface_to_impl(self):
        transformer = VarKeywordTransformer()
        code = "    List<String> items = new ArrayList<String>();"
        result = transformer.transform(code)
        assert "var items" in result.transformed

    def test_no_change_for_field(self):
        """Fields (no indentation) should not be converted to var."""
        transformer = VarKeywordTransformer()
        code = "ArrayList<String> names = new ArrayList<String>();"
        result = transformer.transform(code)
        assert not result.was_modified


class TestTextBlocks:
    def test_multiline_string_concat(self):
        transformer = TextBlockTransformer()
        code = '''    String sql = "SELECT *\\n" +
                     "FROM users\\n" +
                     "WHERE active = true\\n" +
                     "ORDER BY name";'''
        result = transformer.transform(code)
        assert '"""' in result.transformed
        assert result.was_modified

    def test_short_concat_not_converted(self):
        """Only 2 parts - should not convert."""
        transformer = TextBlockTransformer()
        code = '''    String s = "hello\\n" +
                   "world";'''
        result = transformer.transform(code)
        assert not result.was_modified


class TestSwitchExpression:
    def test_simple_switch_to_expression(self):
        transformer = SwitchExpressionTransformer()
        code = '''    String result;
    switch (code) {
        case 200:
            result = "OK";
            break;
        case 404:
            result = "Not Found";
            break;
        default:
            result = "Unknown";
            break;
    }'''
        result = transformer.transform(code)
        assert "->" in result.transformed
        assert result.was_modified

    def test_multi_label_switch(self):
        transformer = SwitchExpressionTransformer()
        code = '''    String type;
    switch (day) {
        case "MONDAY":
        case "FRIDAY":
            type = "Work";
            break;
        case "SATURDAY":
        case "SUNDAY":
            type = "Rest";
            break;
        default:
            type = "Unknown";
            break;
    }'''
        result = transformer.transform(code)
        assert "->" in result.transformed


class TestMigrationEngine:
    def test_full_migration(self):
        engine = MigrationEngine(target_version=17)
        code = '''public class Test {
    public void method() {
        List<String> items = Arrays.asList("a", "b", "c");
        ArrayList<String> names = new ArrayList<String>();
        if (obj instanceof String) {
            String s = (String) obj;
            System.out.println(s);
        }
    }
}'''
        results = engine.migrate_code(code)
        assert len(results) > 0

        final_code = results[-1].transformed
        assert "List.of(" in final_code
        assert "var names" in final_code
        assert "instanceof String s" in final_code

    def test_target_version_limits(self):
        """Engine with Java 9 target should only apply Java 9 transformations."""
        engine = MigrationEngine(target_version=9)
        code = '''public class Test {
    public void method() {
        List<String> items = Arrays.asList("a", "b");
        ArrayList<String> names = new ArrayList<String>();
    }
}'''
        results = engine.migrate_code(code)
        # Collection factory (Java 9) should be applied
        if results:
            final_code = results[-1].transformed
            assert "List.of(" in final_code
            # var (Java 10) should NOT be applied
            assert "var names" not in final_code
