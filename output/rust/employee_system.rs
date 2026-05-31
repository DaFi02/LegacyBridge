use std::io::{self, Write};
// String y &str están en el prelude de Rust
// Vec<T> está en el prelude de Rust
use std::rc::Rc;
use std::sync::Arc;
use std::fs;

// (namespaces manejados por mod/use en Rust)

// Simulación de un sistema legacy de gestión de empleados
// Estilo C++ 98/03 con punteros crudos y manejo manual de memoria

#[derive(Debug, Clone)]

pub struct Employee {

    pub name: string,

    pub id: i32,

    pub salary: f64,

}

#[derive(Debug, Clone)]

pub struct Department {

    pub name: string,

    pub employeeCount: i32,

}

type EmployeeId = u32;

// Función legacy con punteros crudos
void printEmployee(const Employee* emp) {
    println!("{}", emp->name);
    println!("{}", std::to_string(emp->id));
}

// Gestión de empleados con new/delete
Employee* createEmployee(string name, int id, double salary) {
    let emp: Box<Employee> = Box::new();
    return emp;
}

void deleteEmployee(Employee* emp) {
    drop(emp);
}

int main() {
    // Creación de empleados con memoria dinámica
    let emp1: Box<Employee> = Box::new();
    let emp2: Box<Employee> = Box::new();
    
    // Smart pointers (modernización parcial C++11)
    let smartEmp: Box<Employee> = Box::new();
    let dept: Rc<Department> = Rc::new();
    
    // Vector de punteros (patrón legacy peligroso)
    let companyName: String = String::from("TechCorp Legacy Systems");
    let report: String = String::from("Annual Report 2024");
    
    println!("{}", companyName);
    
    // Bucle clásico
    for i in 0..10 {
        println!("{}", i.to_string());
    }
    
    // String operations
    let fullReport: String = report.clone();
    fullReport.push_str(" - ");
    fullReport.push_str(companyName);
    
    if (!fullReport.is_empty()) {
        println!("{}", fullReport.as_str());
        println!("{}", std::to_string(fullReport.len()));
    }
    
    // Limpieza (memory leaks si se olvida!)
    drop(emp1);
    drop(emp2);
    
    return 0;
}
