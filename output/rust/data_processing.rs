use std::io::{self, Write};
// Vec<T> está en el prelude de Rust
// String y &str están en el prelude de Rust
use std::collections::HashMap;
use std::collections::HashSet;
// Rust usa iteradores y métodos de Iterator trait

// (namespaces manejados por mod/use en Rust)

// Clase con manejo de colecciones estilo C++ antiguo
#[derive(Debug, Clone)]
pub struct Config {
    pub key: string,
    pub value: string,
    pub priority: i32,
}

#[derive(Debug, Clone, PartialEq)]

pub enum LogLevel {

    Debug,

    Info,

    Warning,

    Error,

    Critical,

}

void processItems(vector<string>& items) {
    // Iteración con for clásico
    for (int i = 0; i < items.len(); i++) {
        println!("{}", items[i]);
    }
    
    // Range-based for (C++11)
    for item in &items {
        if (!item.is_empty()) {
            println!("{}", item);
        }
    }
}

string getLogPrefix(LogLevel level) {
    let prefix: String = String::from("UNKNOWN");
    
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
    let title: String = String::from("Data Processing Report");
    let separator: String = String::from("========================");
    
    println!("{}", title);
    println!("{}", separator);
    
    // Map con datos
    map<string, int> scores;
    scores["Alice"] = 95;
    scores["Bob"] = 87;
    scores["Charlie"] = 92;
    
    // Iteración sobre map
    for pair in &scores {
        std::string label = std::to_string(pair.second);
        println!("{}", pair.first);
    }
    
    // Strings con operaciones legacy
    let filename: String = String::from("report.txt");
    if (!filename.is_empty()) {
        let extension: String = filename.clone();
        println!("{}", filename.as_str());
    }
    
    // Null pointers
    int* result = None;
    Config* config = None;
    
    if (result == None) {
        println!("{}", No result available);
    }
    
    return 0;
}
