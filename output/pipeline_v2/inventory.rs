// inventory.rs
pub mod inventory {
    use std::collections::HashMap;

    pub struct Inventory {
        products: HashMap<i32, Product>,
    }

    #[derive(Debug)]
    pub struct Product {
        id: i32,
        name: String,
        stock: i32,
    }

    impl Inventory {
        pub fn new() -> Self {
            Self {
                products: HashMap::new(),
            }
        }

        pub fn register_product(&mut self, id: i32, name: String, stock: i32) {
            self.products.insert(id, Product { id, name, stock });
        }

        pub fn check_low_stock(&self) -> Vec<&Product> {
            self.products.values().filter(|p| p.stock < 5).collect()
        }

        pub fn display_summary(&self) {
            println!("Inventory Summary:");
            for product in self.products.values() {
                println!("ID: {}, Name: {}, Stock: {}", product.id, product.name, product.stock);
            }
        }
    }

    pub fn initialize_inventory() -> Inventory {
        Inventory::new()
    }

    pub fn add_sample_products(inventory: &mut Inventory) {
        inventory.register_product(1, "Sample Product 1".to_string(), 10);
        inventory.register_product(2, "Sample Product 2".to_string(), 3);
    }

    pub fn main_program() {
        let mut inventory = initialize_inventory();
        add_sample_products(&mut inventory);
        let low_stock = inventory.check_low_stock();
        if !low_stock.is_empty() {
            println!("Low stock products:");
            for product in low_stock {
                println!("ID: {}, Name: {}, Stock: {}", product.id, product.name, product.stock);
            }
        }
        inventory.display_summary();
    }
}

// payroll.rs
pub mod payroll {
    use std::collections::HashMap;
    use std::io;

    pub struct Employee {
        id: i32,
        name: String,
        salary: f64,
    }

    pub struct Payroll {
        employees: HashMap<i32, Employee>,
    }

    impl Payroll {
        pub fn new() -> Self {
            Self {
                employees: HashMap::new(),
            }
        }

        pub fn process_employees(&mut self) -> io::Result<()> {
            // Simulating file read for demonstration
            // In a real scenario, read from a file or database
            self.employees.insert(1, Employee { id: 1, name: "John Doe".to_string(), salary: 50000.0 });
            self.employees.insert(2, Employee { id: 2, name: "Jane Doe".to_string(), salary: 60000.0 });
            Ok(())
        }

        pub fn calculate_pay(&self, id: i32) -> Option<f64> {
            self.employees.get(&id).map(|e| e.salary)
        }

        pub fn generate_report_line(&self, id: i32) -> Option<String> {
            self.employees.get(&id).map(|e| format!("ID: {}, Name: {}, Salary: {}", e.id, e.name, e.salary))
        }

        pub fn finalize_process(&self) {
            println!("Payroll process finalized.");
        }
    }

    pub fn file_control() -> io::Result<()> {
        // Simulating file control for demonstration
        Ok(())
    }

    pub fn main_program() -> io::Result<()> {
        file_control()?;
        let mut payroll = Payroll::new();
        payroll.process_employees()?;
        let pay = payroll.calculate_pay(1);
        match pay {
            Some(salary) => println!("Salary for ID 1: {}", salary),
            None => println!("Employee not found"),
        }
        if let Some(line) = payroll.generate_report_line(2) {
            println!("{}", line);
        }
        payroll.finalize_process();
        Ok(())
    }
}

fn main() {
    inventory::main_program();
    match payroll::main_program() {
        Ok(_) => println!("Payroll processed successfully"),
        Err(e) => eprintln!("Error processing payroll: {}", e),
    }
}

mod inventory {
    pub struct Inventory {
        products: Vec<Product>,
    }

    impl Inventory {
        pub fn new() -> Self {
            Self { products: Vec::new() }
        }

        pub fn add_product(&mut self, product: Product) {
            self.products.push(product);
        }

        pub fn check_low_stock(&self) -> Vec<&Product> {
            self.products.iter().filter(|p| p.quantity < 5).collect()
        }

        pub fn display_summary(&self) {
            println!("Summary:");
            for product in &self.products {
                println!("{}: {}", product.name, product.quantity);
            }
        }
    }

    pub struct Product {
        pub name: String,
        pub quantity: i32,
    }

    impl Product {
        pub fn new(name: String, quantity: i32) -> Self {
            Self { name, quantity }
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut inventory = inventory::Inventory::new();
    initialize_inventory(&mut inventory)?;
    add_sample_products(&mut inventory)?;
    check_low_stock(&inventory)?;
    inventory.display_summary();
    Ok(())
}

fn initialize_inventory(inventory: &mut inventory::Inventory) -> Result<(), Box<dyn std::error::Error>> {
    // TO DO: implement initialization logic
    Ok(())
}

fn add_sample_products(inventory: &mut inventory::Inventory) -> Result<(), Box<dyn std::error::Error>> {
    inventory.add_product(inventory::Product::new("Product 1".to_string(), 10));
    inventory.add_product(inventory::Product::new("Product 2".to_string(), 3));
    Ok(())
}

fn check_low_stock(inventory: &inventory::Inventory) -> Result<(), Box<dyn std::error::Error>> {
    let low_stock = inventory.check_low_stock();
    if !low_stock.is_empty() {
        println!("Low stock products:");
        for product in low_stock {
            println!("{}: {}", product.name, product.quantity);
        }
    }
    Ok(())
}

struct InventorySystem {
    total_products: i32,
    total_value: i32,
    low_stock_count: i32,
}

impl InventorySystem {
    fn initialize_inventory(&mut self) {
        println!("==============================");
        println!("  SISTEMA DE INVENTARIO");
        println!("  Version Legacy COBOL");
        println!("==============================");
        self.total_products = 0;
        self.total_value = 0;
        self.low_stock_count = 0;
    }
}

struct Product {
    prod_code: String,
    prod_name: String,
    prod_quantity: i32,
    prod_price: f64,
    prod_category: String,
}

impl Product {
    fn new(code: String, name: String, quantity: i32, price: f64, category: String) -> Self {
        Product {
            prod_code: code,
            prod_name: name,
            prod_quantity: quantity,
            prod_price: price,
            prod_category: category,
        }
    }

    fn register_product(&self) -> Result<(), String> {
        // Assuming register_product logic is implemented here
        Ok(())
    }
}

fn add_sample_products() {
    let products = vec![
        Product::new(String::from("PROD001"), String::from("Laptop HP EliteBook"), 25, 3500.00, String::from("Computadoras")),
        Product::new(String::from("PROD002"), String::from("Mouse Logitech MX"), 150, 89.90, String::from("Perifericos")),
        Product::new(String::from("PROD003"), String::from("Monitor 27 4K"), 5, 1200.00, String::from("Monitores")),
    ];

    for product in products {
        match product.register_product() {
            Ok(_) => println!("Product {} registered successfully", product.prod_code),
            Err(e) => println!("Error registering product {}: {}", product.prod_code, e),
        }
    }
}

fn main() {
    add_sample_products();
}

pub struct ProductRegister {
    total_products: i32,
    total_value: f64,
    prod_name: String,
    prod_code: String,
    prod_quantity: i32,
    prod_price: f64,
}

impl ProductRegister {
    pub fn register_product(&mut self) -> Result<(), String> {
        self.total_products += 1;
        self.total_value += (self.prod_quantity as f64) * self.prod_price;
        println!("  + Registrado:  {}", self.prod_name);
        println!("    Codigo:  {}", self.prod_code);
        println!("    Cantidad:  {}", self.prod_quantity);
        println!("    Precio: S/.  {}", self.prod_price);
        Ok(())
    }
}

pub struct InventoryChecker {
    prod_quantity: i32,
    ws_low_stock_limit: i32,
    low_stock_count: i32,
    prod_name: String,
}

impl InventoryChecker {
    pub fn check_low_stock(&mut self) -> () {
        println!(" ");
        println!("--- ALERTA STOCK BAJO ---");
        if self.prod_quantity < self.ws_low_stock_limit {
            self.low_stock_count += 1;
            println!("  ! BAJO STOCK:  {}", self.prod_name);
            println!("    Solo quedan: {} unidades", self.prod_quantity);
        } else {
            println!("  Stock OK para ultimo producto verificado");
        }
    }
}

// No COBOL code was provided for migration.

pub struct InventorySummary {
    total_products: i32,
    total_value: i32,
    low_stock_count: i32,
}

impl InventorySummary {
    pub fn display_summary(&self) {
        println!(" ");
        println!("==============================");
        println!("  RESUMEN DE INVENTARIO");
        println!("  Productos:  {}", self.total_products);
        println!("  Valor total: S/.  {}", self.total_value);
        println!("  Alertas stock bajo:  {}", self.low_stock_count);
        println!("==============================");
    }
}