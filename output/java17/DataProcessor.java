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
        var errors = new ArrayList<String>();
        var warnings = new ArrayList<String>();
        
        result.put("errors", errors);
        result.put("warnings", warnings);
        
        return result;
    }

    public String formatRecord(Object record) {
        if (record instanceof Map map) {
            
            return "Map with " + map.size() + " entries";
        }
        if (record instanceof List list) {
            
            return "List with " + list.size() + " items";
        }
        if (record instanceof String str) {
            
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
        return List.of("id", "name", "email", "created_at", "updated_at");
    }

    public Set<String> getReservedWords() {
        HashSet<String> reserved = Set.of(
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE"
        );
        return reserved;
    }

    public void initializeCache() {
        var cache = new HashMap<String, Object>();
        var keys = new ArrayList<String>();
        var sortedScores = new TreeMap<String, Integer>();
        
        List<String> defaultKeys = List.of("default");
        Map<String, String> emptyConfig = Map.of();
    }
}
