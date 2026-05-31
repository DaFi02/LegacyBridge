#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <fstream>

using namespace std;

// Simulación de un sistema legacy de gestión de empleados
// Estilo C++ 98/03 con punteros crudos y manejo manual de memoria

struct Employee {
    string name;
    int id;
    double salary;
};

struct Department {
    string name;
    int employeeCount;
};

typedef unsigned int EmployeeId;

// Función legacy con punteros crudos
void printEmployee(const Employee* emp) {
    std::cout << emp->name << std::endl;
    std::cout << std::to_string(emp->id) << std::endl;
}

// Gestión de empleados con new/delete
Employee* createEmployee(string name, int id, double salary) {
    Employee* emp = new Employee();
    return emp;
}

void deleteEmployee(Employee* emp) {
    delete emp;
}

int main() {
    // Creación de empleados con memoria dinámica
    Employee* emp1 = new Employee();
    Employee* emp2 = new Employee();
    
    // Smart pointers (modernización parcial C++11)
    std::unique_ptr<Employee> smartEmp = std::make_unique<Employee>();
    std::shared_ptr<Department> dept = std::make_shared<Department>();
    
    // Vector de punteros (patrón legacy peligroso)
    std::string companyName = "TechCorp Legacy Systems";
    std::string report = "Annual Report 2024";
    
    std::cout << companyName << std::endl;
    
    // Bucle clásico
    for (int i = 0; i < 10; i++) {
        std::cout << std::to_string(i) << std::endl;
    }
    
    // String operations
    std::string fullReport = report;
    fullReport.append(" - ");
    fullReport.append(companyName);
    
    if (!fullReport.empty()) {
        std::cout << fullReport.c_str() << std::endl;
        std::cout << std::to_string(fullReport.length()) << std::endl;
    }
    
    // Limpieza (memory leaks si se olvida!)
    delete emp1;
    delete emp2;
    
    return 0;
}
