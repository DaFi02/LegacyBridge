package com.example.legacy;

import java.util.*;

/**
 * Ejemplo de Java 8 con switch statements verbose que pueden ser switch expressions.
 */
public class StatusMapper {

    public String getStatusLabel(int code) {
        String label = switch (code) {

            case 200 -> "OK";

            case 201 -> "Created";

            case 400 -> "Bad Request";

            case 401 -> "Unauthorized";

            case 403 -> "Forbidden";

            case 404 -> "Not Found";

            case 500 -> "Internal Server Error";

            default -> "Unknown";

        };
        return label;
    }

    public String getDayType(String day) {
        String type;
        switch (day) {
            case "MONDAY":
            case "TUESDAY":
            case "WEDNESDAY":
            case "THURSDAY":
            case "FRIDAY":
                type = "Weekday";
                break;
            case "SATURDAY":
            case "SUNDAY":
                type = "Weekend";
                break;
            default:
                type = "Invalid";
                break;
        }
        return type;
    }

    public List<String> getResponseHeaders(int statusCode) {
        List<String> headers = List.of("Content-Type", "X-Request-Id");
        List<String> emptyHeaders = List.of();
        return headers;
    }
}
