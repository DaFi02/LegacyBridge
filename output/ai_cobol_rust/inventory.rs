struct Product {
    prod_code: String,
    prod_name: String,
    prod_quantity: i32,
    prod_price: f64,
    prod_category: String,
}

struct Totals {
    total_products: i32,
    total_value: f64,
    low_stock_count: i32,
}

struct InventoryMgmt {
    ws_product: Option<Product>,
    ws_totals: Totals,
    ws_low_stock_limit: i32,
    ws_search_code: String,
    ws_found_flag: char,
}

impl InventoryMgmt {
    fn new() -> Self {
        Self {
            ws_product: None,
            ws_totals: Totals {
                total_products: 0,
                total_value: 0.0,
                low_stock_count: 0,
            },
            ws_low_stock_limit: 10,
            ws_search_code: String::new(),
            ws_found_flag: 'N',
        }
    }

    fn initialize_inventory(&mut self) {
        println!("==============================");
        println!("  SISTEMA DE INVENTARIO");
        println!("  Version Legacy COBOL");
        println!("==============================");
        self.ws_totals.total_products = 0;
        self.ws_totals.total_value = 0.0;
        self.ws_totals.low_stock_count = 0;
    }

    fn register_product(&mut self) {
        if let Some(ref prod) = self.ws_product {
            self.ws_totals.total_products += 1;
            self.ws_totals.total_value += (prod.prod_quantity as f64 * prod.prod_price);
            println!("  + Registrado: {}", prod.prod_name);
            println!("    Codigo: {}", prod.prod_code);
            println!("    Cantidad: {}", prod.prod_quantity);
            println!("    Precio: S/. {:.2}", prod.prod_price);
        }
    }

    fn add_sample_products(&mut self) {
        self.ws_product = Some(Product {
            prod_code: "PROD001".to_string(),
            prod_name: "Laptop HP EliteBook".to_string(),
            prod_quantity: 25,
            prod_price: 3500.00,
            prod_category: "Computadoras".to_string(),
        });
        self.register_product();

        self.ws_product = Some(Product {
            prod_code: "PROD002".to_string(),
            prod_name: "Mouse Logitech MX".to_string(),
            prod_quantity: 150,
            prod_price: 89.90,
            prod_category: "Perifericos".to_string(),
        });
        self.register_product();

        self.ws_product = Some(Product {
            prod_code: "PROD003".to_string(),
            prod_name: "Monitor 27 4K".to_string(),
            prod_quantity: 5,
            prod_price: 1200.00,
            prod_category: "Monitores".to_string(),
        });
        self.register_product();
    }

    fn check_low_stock(&mut self) {
        println!(" ");
        println!("--- ALERTA STOCK BAJO ---");
        if let Some(ref prod) = self.ws_product {
            if prod.prod_quantity < self.ws_low_stock_limit {
                self.ws_totals.low_stock_count += 1;
                println!("  ! BAJO STOCK: {}", prod.prod_name);
                println!("    Solo quedan: {} unidades", prod.prod_quantity);
            } else {
                println!("  Stock OK para ultimo producto verificado");
            }
        }
    }

    fn display_summary(&self) {
        println!(" ");
        println!("==============================");
        println!("  RESUMEN DE INVENTARIO");
        println!("  Productos: {}", self.ws_totals.total_products);
        println!("  Valor total: S/. {:.2}", self.ws_totals.total_value);
        println!("  Alertas stock bajo: {}", self.ws_totals.low_stock_count);
        println!("==============================");
    }

    pub fn run(&mut self) {
        self.initialize_inventory();
        self.add_sample_products();
        self.check_low_stock();
        self.display_summary();
    }
}

fn main() {
    let mut app = InventoryMgmt::new();
    app.run();
}