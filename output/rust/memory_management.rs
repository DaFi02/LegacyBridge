use std::io::{self, Write};
// Vec<T> está en el prelude de Rust
// String y &str están en el prelude de Rust
use std::collections::HashMap;
use std::rc::Rc;
use std::sync::Arc;
// Rust usa iteradores y métodos de Iterator trait

// (namespaces manejados por mod/use en Rust)

// Structs con estilo C++98
#[derive(Debug, Clone)]
pub struct Point {
    pub x: i32,
    pub y: i32,
    pub z: f64,
}

#[derive(Debug, Clone)]

pub struct Student {

    pub name: string,

    pub age: i32,

    pub gpa: f64,

}

#[derive(Debug, Clone, PartialEq)]

pub enum Color {

    Red,

    Green,

    Blue,

    Yellow,

}

type Uint = u32;
type Int64 = long long;

// Función con punteros crudos y memory management manual
void processData(int* data, int size) {
    for i in 0..size {
        println!("{}", data[i]);
    }
}

int main() {
    // Memory management manual (C++ legacy)
    let mut numbers: Vec<i32> = vec![0; 100];
    let single: Box<i32> = Box::new(42);
    
    for i in 0..100 {
        numbers[i] = i * 2;
    }
    
    processData(numbers, 100);
    
    // Strings estilo C++
    let greeting: String = String::from("Hello, World!");
    let name: String = String::from("LegacyBridge");
    let fullMessage: String = greeting.clone();
    fullMessage.push_str(" from ");
    fullMessage.push_str(name);
    
    println!("{}", fullMessage);
    println!("{}", Length: );
    
    // Punteros y referencias
    int value = 10;
    let ptr: &mut i32 = &mut value;
    let constPtr: &i32 = &value;
    
    // Smart pointers (C++11, pero migrados a Rust)
    let smartPtr: Box<i32> = Box::new(99);
    let sharedPtr: Rc<i32> = Rc::new(77);
    
    // Limpieza manual
    drop(single);
    drop(numbers);
    
    return 0;
}
