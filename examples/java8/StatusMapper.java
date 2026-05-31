package com.example.legacy;

import java.util.*;

/**
 * Ejemplo de Java 8 con switch statements verbose que pueden ser switch expressions.
 */
public class StatusMapper {

    public String getStatusLabel(int code) {
        String label;
        switch (code) {
            case 200:
                label = "OK";
                break;
            case 201:
                label = "Created";
                break;
            case 400:
                label = "Bad Request";
                break;
            case 401:
                label = "Unauthorized";
                break;
            case 403:
                label = "Forbidden";
                break;
            case 404:
                label = "Not Found";
                break;
            case 500:
                label = "Internal Server Error";
                break;
            default:
                label = "Unknown";
                break;
        }
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
        List<String> headers = Arrays.asList("Content-Type", "X-Request-Id");
        List<String> emptyHeaders = Collections.emptyList();
        return headers;
    }
}
