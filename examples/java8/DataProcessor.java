package com.example.legacy;

import java.io.*;
import java.util.*;

/**
 * Ejemplo de código Java 8 con patrones de manejo de datos legacy.
 * Demuestra: variables locales con tipo explícito, instanceof, colecciones.
 */
public class DataProcessor {

    public Map<String, List<String>> processFile(String filename) {
        HashMap<String, List<String>> result = new HashMap<>();
        ArrayList<String> errors = new ArrayList<String>();
        ArrayList<String> warnings = new ArrayList<String>();
        
        result.put("errors", errors);
        result.put("warnings", warnings);
        
        return result;
    }

    public String formatRecord(Object record) {
        if (record instanceof Map) {
            Map map = (Map) record;
            return "Map with " + map.size() + " entries";
        }
        if (record instanceof List) {
            List list = (List) record;
            return "List with " + list.size() + " items";
        }
        if (record instanceof String) {
            String str = (String) record;
            return "String: " + str.trim();
        }
        return record.toString();
    }

    public String generateInsertSQL(String table, List<String> columns) {
        String columnList = String.join(", ", columns);
        String placeholders = String.join(", ", Collections.nCopies(columns.size(), "?"));
        
        String sql = "INSERT INTO " + table + "\n" +
                     "(" + columnList + ")\n" +
                     "VALUES\n" +
                     "(" + placeholders + ")";
        return sql;
    }

    public List<String> getDefaultColumns() {
        return Arrays.asList("id", "name", "email", "created_at", "updated_at");
    }

    public Set<String> getReservedWords() {
        HashSet<String> reserved = new HashSet<>(Arrays.asList(
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE"
        ));
        return reserved;
    }

    public void initializeCache() {
        HashMap<String, Object> cache = new HashMap<>();
        ArrayList<String> keys = new ArrayList<String>();
        TreeMap<String, Integer> sortedScores = new TreeMap<String, Integer>();
        
        List<String> defaultKeys = Collections.singletonList("default");
        Map<String, String> emptyConfig = Collections.emptyMap();
    }
}
