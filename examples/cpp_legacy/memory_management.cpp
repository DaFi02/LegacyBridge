#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <memory>
#include <algorithm>

using namespace std;

// Structs con estilo C++98
struct Point {
    int x;
    int y;
    double z;
};

struct Student {
    string name;
    int age;
    double gpa;
};

enum Color {
    RED,
    GREEN,
    BLUE,
    YELLOW
};

typedef unsigned int uint;
typedef long long int64;

// Función con punteros crudos y memory management manual
void processData(int* data, int size) {
    for (int i = 0; i < size; i++) {
        std::cout << data[i] << std::endl;
    }
}

int main() {
    // Memory management manual (C++ legacy)
    int* numbers = new int[100];
    int* single = new int(42);
    
    for (int i = 0; i < 100; i++) {
        numbers[i] = i * 2;
    }
    
    processData(numbers, 100);
    
    // Strings estilo C++
    std::string greeting = "Hello, World!";
    std::string name = "LegacyBridge";
    std::string fullMessage = greeting;
    fullMessage.append(" from ");
    fullMessage.append(name);
    
    std::cout << fullMessage << std::endl;
    std::cout << "Length: " << std::endl;
    
    // Punteros y referencias
    int value = 10;
    int* ptr = &value;
    const int* constPtr = &value;
    
    // Smart pointers (C++11, pero migrados a Rust)
    std::unique_ptr<int> smartPtr = std::make_unique<int>(99);
    std::shared_ptr<int> sharedPtr = std::make_shared<int>(77);
    
    // Limpieza manual
    delete single;
    delete[] numbers;
    
    return 0;
}
