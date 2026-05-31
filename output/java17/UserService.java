package com.example.legacy;

import java.util.*;

/**
 * Ejemplo de servicio Java 8 con patrones legacy que pueden modernizarse.
 * Este archivo demuestra: Arrays.asList, instanceof + cast, concatenación de strings.
 */
public class UserService {

    private List<String> defaultRoles = List.of("USER", "VIEWER");
    private Set<String> adminEmails = Set.of();
    private Map<String, String> config = Map.of();

    public List<String> getActiveUsers() {
        List<String> users = List.of("admin", "user1", "user2");
        return users;
    }

    public String processEntity(Object entity) {
        if (entity instanceof String s) {
            
            return s.toUpperCase();
        }
        if (entity instanceof Integer num) {
            
            return String.valueOf(num * 2);
        }
        if (entity instanceof List list) {
            
            return "List size: " + list.size();
        }
        return "unknown";
    }

    public String buildQuery(String table, String condition) {
        String sql = "SELECT *\n" +
                     "FROM " + table + "\n" +
                     "WHERE " + condition + "\n" +
                     "ORDER BY id\n" +
                     "LIMIT 100";
        return sql;
    }

    public String buildHtmlReport(String title, String content) {
        String html = "<html>\n" +
                      "  <head>\n" +
                      "    <title>" + title + "</title>\n" +
                      "  </head>\n" +
                      "  <body>\n" +
                      "    <p>" + content + "</p>\n" +
                      "  </body>\n" +
                      "</html>";
        return html;
    }

    public void createCollections() {
        var names = new ArrayList<String>();
        var scores = new HashMap<String, Integer>();
        var queue = new LinkedList<String>();
        HashSet<String> tags = Set.of("java", "legacy", "migration");
    }
}
