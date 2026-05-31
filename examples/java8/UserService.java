package com.example.legacy;

import java.util.*;

/**
 * Ejemplo de servicio Java 8 con patrones legacy que pueden modernizarse.
 * Este archivo demuestra: Arrays.asList, instanceof + cast, concatenación de strings.
 */
public class UserService {

    private List<String> defaultRoles = Collections.unmodifiableList(Arrays.asList("USER", "VIEWER"));
    private Set<String> adminEmails = Collections.emptySet();
    private Map<String, String> config = Collections.emptyMap();

    public List<String> getActiveUsers() {
        List<String> users = Arrays.asList("admin", "user1", "user2");
        return users;
    }

    public String processEntity(Object entity) {
        if (entity instanceof String) {
            String s = (String) entity;
            return s.toUpperCase();
        }
        if (entity instanceof Integer) {
            Integer num = (Integer) entity;
            return String.valueOf(num * 2);
        }
        if (entity instanceof List) {
            List list = (List) entity;
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
        ArrayList<String> names = new ArrayList<String>();
        HashMap<String, Integer> scores = new HashMap<>();
        LinkedList<String> queue = new LinkedList<String>();
        HashSet<String> tags = new HashSet<>(Arrays.asList("java", "legacy", "migration"));
    }
}
