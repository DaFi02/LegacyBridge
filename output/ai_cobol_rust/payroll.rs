use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};

struct EmployeeRecord {
    emp_id: i32,
    emp_name: String,
    emp_dept: String,
    emp_salary: f64,
    emp_hours: i32,
    emp_status: char,
}

struct PayrollSystem {
    ws_gross_pay: f64,
    ws_tax: f64,
    ws_net_pay: f64,
    ws_overtime_hours: i32,
    ws_overtime_pay: f64,
    ws_tax_rate: f64,
    ws_overtime_rate: f64,
    ws_standard_hours: i32,
    ws_total_payroll: f64,
    ws_emp_count: i32,
}

impl PayrollSystem {
    fn new() -> Self {
        Self {
            ws_gross_pay: 0.0,
            ws_tax: 0.0,
            ws_net_pay: 0.0,
            ws_overtime_hours: 0,
            ws_overtime_pay: 0.0,
            ws_tax_rate: 0.30,
            ws_overtime_rate: 1.50,
            ws_standard_hours: 160,
            ws_total_payroll: 0.0,
            ws_emp_count: 0,
        }
    }

    fn calculate_pay(&mut self, emp: &EmployeeRecord) {
        self.ws_overtime_pay = 0.0;
        if emp.emp_hours > self.ws_standard_hours {
            self.ws_overtime_hours = emp.emp_hours - self.ws_standard_hours;
            self.ws_overtime_pay = (self.ws_overtime_hours as f64) 
                * (emp.emp_salary / self.ws_standard_hours as f64) 
                * self.ws_overtime_rate;
        }
        self.ws_gross_pay = emp.emp_salary + self.ws_overtime_pay;
        self.ws_tax = self.ws_gross_pay * self.ws_tax_rate;
        self.ws_net_pay = self.ws_gross_pay - self.ws_tax;
    }

    fn generate_report_line(&self, emp: &EmployeeRecord) {
        println!("Empleado: {}", emp.emp_name);
        println!("  ID: {}", emp.emp_id);
        println!("  Depto: {}", emp.emp_dept);
        println!("  Salario Bruto: S/. {:.2}", self.ws_gross_pay);
        println!("  Impuesto: S/. {:.2}", self.ws_tax);
        println!("  Pago Neto: S/. {:.2}", self.ws_net_pay);
        println!("-----------------------------------");
    }

    fn finalize_process(&self) {
        println!("\n===================================");
        println!("  RESUMEN DE NOMINA");
        println!("  Empleados procesados: {}", self.ws_emp_count);
        println!("  Total nómina: S/. {:.2}", self.ws_total_payroll);
        println!("===================================");
    }
}

fn parse_employee_record(line: &str) -> Option<EmployeeRecord> {
    if line.len() < 47 { return None; }
    
    let emp_id = line[0..6].trim().parse::<i32>().ok()?;
    let emp_name = line[6..36].trim().to_string();
    let emp_dept = line[36..46].trim().to_string();
    let emp_salary = line[46..54].trim().parse::<f64>().ok()?;
    let emp_hours = line[54..57].trim().parse::<i32>().ok()?;
    let emp_status = line[57..58].chars().next()?;

    Some(EmployeeRecord {
        emp_id,
        emp_name,
        emp_dept,
        emp_salary,
        emp_hours,
        emp_status,
    })
}

fn main() -> io::Result<()> {
    let mut payroll = PayrollSystem::new();
    
    println!("===================================");
    println!("  SISTEMA DE NOMINA - TECHCORP");
    println!("===================================");

    let input_file = File::open("EMPFILE.DAT")?;
    let reader = BufReader::new(input_file);
    let mut output_file = File::create("PAYROLL.RPT")?;

    for line in reader.lines() {
        let line = line?;
        if let Some(emp) = parse_employee_record(&line) {
            if emp.emp_status == 'A' {
                payroll.calculate_pay(&emp);
                payroll.generate_report_line(&emp);
                
                let report_line = format!(
                    "Empleado: {} ID: {} Neto: {:.2}\n", 
                    emp.emp_name, emp.emp_id, payroll.ws_net_pay
                );
                output_file.write_all(report_line.as_bytes())?;

                payroll.ws_emp_count += 1;
                payroll.ws_total_payroll += payroll.ws_net_pay;
            }
        }
    }

    payroll.finalize_process();
    Ok(())
}