from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict

@dataclass
class Producto:
    codigo: str
    nombre: str
    precio: float
    categoria: str

class TiendaManager:
    def __init__(self):
        self.productos: List[Producto] = []
        self.inventario: Dict[str, int] = {}
        self.ventas: List[Dict] = []
        self.total_ventas: float = 0.0

    def inicializar(self):
        print("==============================================")
        print("  SISTEMA DE GESTION DE TIENDA v1.0")
        print("  Python 3.12")
        print("==============================================")

        productos_data = [
            {"codigo": "SKU001", "nombre": "Arroz Extra 5kg", "precio": 18.50, "categoria": "Abarrotes"},
            {"codigo": "SKU002", "nombre": "Aceite Vegetal 1L", "precio": 12.90, "categoria": "Abarrotes"},
            {"codigo": "SKU003", "nombre": "Detergente Bolsa 2kg", "precio": 24.00, "categoria": "Limpieza"},
            {"codigo": "SKU004", "nombre": "Leche Evaporada x6", "precio": 22.80, "categoria": "Lacteos"},
        ]

        for prod_data in productos_data:
            self.productos.append(Producto(**prod_data))

        self.inventario = {
            "SKU001": 150,
            "SKU002": 200,
            "SKU003": 80,
            "SKU004": 120,
        }

        print(f"  Productos cargados: {len(self.productos)}")
        print("  Inventario inicializado")
        print()

    def registrar_ventas(self):
        print("--- REGISTRANDO VENTAS DEL DIA ---")

        ventas_data = [
            ("SKU001", 3),
            ("SKU002", 5),
            ("SKU003", 2),
            ("SKU001", 10),
            ("SKU004", 4),
            ("SKU002", 8),
        ]

        for codigo, cantidad in ventas_data:
            self.registrar_venta(codigo, cantidad)

        print()

    def registrar_venta(self, codigo: str, cantidad: int):
        producto = next((p for p in self.productos if p.codigo == codigo), None)
        if producto:
            subtotal = producto.precio * cantidad
            self.total_ventas += subtotal

            self.inventario[codigo] -= cantidad

            venta = {
                "codigo": codigo,
                "producto": producto.nombre,
                "cantidad": cantidad,
                "subtotal": subtotal,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            self.ventas.append(venta)

            print(f"  + Venta: {cantidad}x {producto.nombre} = S/. {subtotal:.2f}")

    def mostrar_reporte(self):
        print("==============================================")
        print("  REPORTE DE VENTAS")
        print("==============================================")
        print(f"  Total ventas del dia: S/. {self.total_ventas:.2f}")
        print(f"  Transacciones: {len(self.ventas)}")
        print()

        print("--- ALERTAS DE INVENTARIO ---")
        alertas = [f"  ! STOCK BAJO: {codigo} (quedan: {stock} unidades)" 
                   for codigo, stock in self.inventario.items() if stock < 100]

        if alertas:
            for alerta in alertas:
                print(alerta)
        else:
            print("  Todos los productos con stock suficiente")

        print()
        print("==============================================")
        print(f"  Fin del reporte - {datetime.now().strftime('%Y-%m-%d')}")
        print("==============================================")

def main():
    tienda = TiendaManager()
    tienda.inicializar()
    tienda.registrar_ventas()
    tienda.mostrar_reporte()

if __name__ == "__main__":
    main()