from dataclasses import dataclass
from datetime import date
from typing import List, Dict

@dataclass
class Empleado:
    id: int
    nombre: str
    cargo: str
    salario: float
    departamento: str

@dataclass
class DetalleNomina:
    nombre: str
    cargo: str
    bruto: float
    afp: float
    impuesto: float
    neto: float

def calcular_nomina(empleados: List[Empleado]) -> Dict[str, float | List[DetalleNomina]]:
    detalles = [
        DetalleNomina(
            nombre=emp.nombre,
            cargo=emp.cargo,
            bruto=emp.salario,
            afp=emp.salario * 0.13,
            impuesto=max(0, emp.salario - 7000) * 0.08,
            neto=emp.salario - (emp.salario * 0.13) - max(0, emp.salario - 7000) * 0.08
        ) for emp in empleados
    ]
    total = sum(d.neto for d in detalles)
    return {"total": total, "detalles": detalles}

def buscar_empleado(empleados: List[Empleado], nombre: str) -> List[Empleado]:
    return [emp for emp in empleados if nombre.lower() in emp.nombre.lower()]

def generar_reporte(empleados: List[Empleado]) -> Dict[str, Dict[str, int | float]]:
    reporte = {}
    for emp in empleados:
        if emp.departamento not in reporte:
            reporte[emp.departamento] = {"count": 0, "total_salario": 0}
        reporte[emp.departamento]["count"] += 1
        reporte[emp.departamento]["total_salario"] += emp.salario
    return reporte

def formatear_moneda(monto: float) -> str:
    return f"S/. {monto:,.2f}"

def main():
    empleados = [
        Empleado(1, "María García", "Gerente", 8500.00, "Administración"),
        Empleado(2, "Carlos López", "Desarrollador", 5200.00, "TI"),
        Empleado(3, "Ana Rodríguez", "Diseñadora", 4800.00, "Marketing"),
        Empleado(4, "Pedro Sánchez", "Analista", 5500.00, "TI"),
        Empleado(5, "Laura Martínez", "Contadora", 6000.00, "Finanzas"),
    ]

    print("==============================================")
    print("  SISTEMA DE GESTIÓN DE EMPLEADOS v2.1")
    print("  Python 3.12 Modern System")
    print("==============================================\n")

    nomina = calcular_nomina(empleados)
    print("--- NÓMINA DEL MES ---")
    for det in nomina["detalles"]:
        print(f"  {det.nombre:<20} | {det.cargo:<15} | Bruto: {formatear_moneda(det.bruto)} | AFP: {formatear_moneda(det.afp)} | Neto: {formatear_moneda(det.neto)}")
    print(f"\n  TOTAL NÓMINA: {formatear_moneda(nomina['total'])}\n")

    reporte = generar_reporte(empleados)
    print("--- REPORTE POR DEPARTAMENTO ---")
    for depto, datos in reporte.items():
        promedio = datos["total_salario"] / datos["count"]
        print(f"  {depto:<18} | Empleados: {datos['count']} | Gasto: {formatear_moneda(datos['total_salario'])} | Promedio: {formatear_moneda(promedio)}")

    encontrados = buscar_empleado(empleados, "garcía")
    print("\n--- BÚSQUEDA: 'garcía' ---")
    if encontrados:
        for emp in encontrados:
            print(f"  Encontrado: {emp.nombre} - {emp.cargo} ({emp.departamento})")
    else:
        print("  No se encontraron resultados")

    print(f"\n==============================================")
    print(f"  Fin del reporte - {date.today()}")
    print("==============================================")

if __name__ == "__main__":
    main()