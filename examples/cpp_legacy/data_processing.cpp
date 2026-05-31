#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <set>
#include <algorithm>

using namespace std;

// Clase con manejo de colecciones estilo C++ antiguo
struct Config {
    string key;
    string value;
    int priority;
};

enum LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL
};

void processItems(vector<string>& items) {
    // Iteración con for clásico
    for (int i = 0; i < items.size(); i++) {
        std::cout << items[i] << std::endl;
    }
    
    // Range-based for (C++11)
    for (auto& item : items) {
        if (!item.empty()) {
            std::cout << item << std::endl;
        }
    }
}

string getLogPrefix(LogLevel level) {
    std::string prefix = "UNKNOWN";
    
    if (level == DEBUG) {
        prefix = "DEBUG";
    } else if (level == INFO) {
        prefix = "INFO";
    } else if (level == WARNING) {
        prefix = "WARN";
    } else if (level == ERROR) {
        prefix = "ERROR";
    }
    
    return prefix;
}

int main() {
    // Vectores y strings
    std::string title = "Data Processing Report";
    std::string separator = "========================";
    
    std::cout << title << std::endl;
    std::cout << separator << std::endl;
    
    // Map con datos
    map<string, int> scores;
    scores["Alice"] = 95;
    scores["Bob"] = 87;
    scores["Charlie"] = 92;
    
    // Iteración sobre map
    for (auto& pair : scores) {
        std::string label = std::to_string(pair.second);
        std::cout << pair.first << std::endl;
    }
    
    // Strings con operaciones legacy
    std::string filename = "report.txt";
    if (!filename.empty()) {
        std::string extension = filename;
        std::cout << filename.c_str() << std::endl;
    }
    
    // Null pointers
    int* result = nullptr;
    Config* config = nullptr;
    
    if (result == nullptr) {
        std::cout << "No result available" << std::endl;
    }
    
    return 0;
}
