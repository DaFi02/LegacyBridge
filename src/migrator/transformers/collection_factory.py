"""Transformer: Collection Factory Methods (Java 9+).

Converts:
    List<String> list = Arrays.asList("a", "b", "c");
    List<String> list = Collections.unmodifiableList(Arrays.asList("a", "b"));
    Set<String> set = new HashSet<>(Arrays.asList("a", "b"));
    Map<String, Integer> map = new HashMap<>(); map.put("a", 1); ...

To:
    List<String> list = List.of("a", "b", "c");
    Set<String> set = Set.of("a", "b");
    Map<String, Integer> map = Map.of("a", 1, ...);
"""

import re

from .base import BaseTransformer, TransformResult


class CollectionFactoryTransformer(BaseTransformer):

    @property
    def name(self) -> str:
        return "Collection Factory Methods"

    @property
    def description(self) -> str:
        return "Convierte Arrays.asList/Collections.unmodifiable* a List.of/Set.of/Map.of (Java 9+)"

    @property
    def java_version_target(self) -> int:
        return 9

    def transform(self, source_code: str) -> TransformResult:
        changes = []
        transformed = source_code

        # Arrays.asList(...) → List.of(...)
        pattern_aslist = re.compile(r'Arrays\.asList\(([^)]*)\)')
        if pattern_aslist.search(transformed):
            count = len(pattern_aslist.findall(transformed))
            transformed = pattern_aslist.sub(r'List.of(\1)', transformed)
            changes.append(f"Arrays.asList() → List.of() ({count} ocurrencia(s))")

        # Collections.unmodifiableList(Arrays.asList(...)) → List.of(...)
        # This should already be handled by the above, but catch wrapper
        pattern_unmod_list = re.compile(
            r'Collections\.unmodifiableList\(\s*List\.of\(([^)]*)\)\s*\)'
        )
        if pattern_unmod_list.search(transformed):
            count = len(pattern_unmod_list.findall(transformed))
            transformed = pattern_unmod_list.sub(r'List.of(\1)', transformed)
            changes.append(f"Collections.unmodifiableList() simplificado ({count})")

        # Collections.unmodifiableSet(new HashSet<>(List.of(...))) → Set.of(...)
        pattern_unmod_set = re.compile(
            r'Collections\.unmodifiableSet\(\s*new\s+HashSet<[^>]*>\(List\.of\(([^)]*)\)\)\s*\)'
        )
        if pattern_unmod_set.search(transformed):
            count = len(pattern_unmod_set.findall(transformed))
            transformed = pattern_unmod_set.sub(r'Set.of(\1)', transformed)
            changes.append(f"Collections.unmodifiableSet() → Set.of() ({count})")

        # new HashSet<>(Arrays.asList(...)) → Set.of(...) (already converted asList above)
        pattern_hashset = re.compile(
            r'new\s+HashSet<[^>]*>\(\s*List\.of\(([^)]*)\)\s*\)'
        )
        if pattern_hashset.search(transformed):
            count = len(pattern_hashset.findall(transformed))
            transformed = pattern_hashset.sub(r'Set.of(\1)', transformed)
            changes.append(f"new HashSet<>(List.of()) → Set.of() ({count})")

        # Collections.emptyList() → List.of()
        pattern_empty_list = re.compile(r'Collections\.emptyList\(\)')
        if pattern_empty_list.search(transformed):
            count = len(pattern_empty_list.findall(transformed))
            transformed = pattern_empty_list.sub('List.of()', transformed)
            changes.append(f"Collections.emptyList() → List.of() ({count})")

        # Collections.emptySet() → Set.of()
        pattern_empty_set = re.compile(r'Collections\.emptySet\(\)')
        if pattern_empty_set.search(transformed):
            count = len(pattern_empty_set.findall(transformed))
            transformed = pattern_empty_set.sub('Set.of()', transformed)
            changes.append(f"Collections.emptySet() → Set.of() ({count})")

        # Collections.emptyMap() → Map.of()
        pattern_empty_map = re.compile(r'Collections\.emptyMap\(\)')
        if pattern_empty_map.search(transformed):
            count = len(pattern_empty_map.findall(transformed))
            transformed = pattern_empty_map.sub('Map.of()', transformed)
            changes.append(f"Collections.emptyMap() → Map.of() ({count})")

        # Collections.singletonList(x) → List.of(x)
        pattern_singleton = re.compile(r'Collections\.singletonList\(([^)]*)\)')
        if pattern_singleton.search(transformed):
            count = len(pattern_singleton.findall(transformed))
            transformed = pattern_singleton.sub(r'List.of(\1)', transformed)
            changes.append(f"Collections.singletonList() → List.of() ({count})")

        return TransformResult(
            original=source_code,
            transformed=transformed,
            changes_made=changes,
            transformer_name=self.name,
        )
