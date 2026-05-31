struct Point {
    x: i32,
    y: i32,
    z: f64,
}

struct Student {
    name: String,
    age: i32,
    gpa: f64,
}

#[derive(Debug)]
enum Color {
    Red,
    Green,
    Blue,
    Yellow,
}

type Uint = u32;
type Int64 = i64;

fn process_data(data: &[i32]) {
    for item in data {
        println!("{}", item);
    }
}

fn main() {
    let mut numbers = vec![0; 100];
    let single = Box::new(42);

    for i in 0..100 {
        numbers[i] = i * 2;
    }

    process_data(&numbers);

    let greeting = String::from("Hello, World!");
    let name = String::from("LegacyBridge");
    let full_message = format!("{} from {}", greeting, name);

    println!("{}", full_message);
    println!("Length: ");

    let value = 10;
    let ptr = &value;
    let const_ptr = &value;

    let smart_ptr = Box::new(99);
    let shared_ptr = std::sync::Arc::new(77);

    drop(single);
    drop(numbers);
}