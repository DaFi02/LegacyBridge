import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Date;
import java.text.SimpleDateFormat;

/**
 * Sistema de Gestión de Tienda - Java 7
 * Código legacy que usa patrones antiguos:
 * - Sin lambdas, sin streams
 * - Raw types en colecciones
 * - Manejo manual de iteradores
 * - Sin try-with-resources
 */
public class TiendaManager {

    private ArrayList productos = new ArrayList();
    private HashMap inventario = new HashMap();
    private ArrayList ventas = new ArrayList();
    private double totalVentas = 0.0;

    public static void main(String[] args) {
        TiendaManager tienda = new TiendaManager();
        tienda.inicializar();
        tienda.registrarVentas();
        tienda.mostrarReporte();
    }

    public void inicializar() {
        System.out.println("==============================================");
        System.out.println("  SISTEMA DE GESTION DE TIENDA v1.0");
        System.out.println("  Java 7 - Legacy System");
        System.out.println("==============================================");

        // Agregar productos (sin diamond operator en Java 7 style)
        HashMap prod1 = new HashMap();
        prod1.put("codigo", "SKU001");
        prod1.put("nombre", "Arroz Extra 5kg");
        prod1.put("precio", "18.50");
        prod1.put("categoria", "Abarrotes");
        productos.add(prod1);

        HashMap prod2 = new HashMap();
        prod2.put("codigo", "SKU002");
        prod2.put("nombre", "Aceite Vegetal 1L");
        prod2.put("precio", "12.90");
        prod2.put("categoria", "Abarrotes");
        productos.add(prod2);

        HashMap prod3 = new HashMap();
        prod3.put("codigo", "SKU003");
        prod3.put("nombre", "Detergente Bolsa 2kg");
        prod3.put("precio", "24.00");
        prod3.put("categoria", "Limpieza");
        productos.add(prod3);

        HashMap prod4 = new HashMap();
        prod4.put("codigo", "SKU004");
        prod4.put("nombre", "Leche Evaporada x6");
        prod4.put("precio", "22.80");
        prod4.put("categoria", "Lacteos");
        productos.add(prod4);

        // Inicializar inventario
        inventario.put("SKU001", new Integer(150));
        inventario.put("SKU002", new Integer(200));
        inventario.put("SKU003", new Integer(80));
        inventario.put("SKU004", new Integer(120));

        System.out.println("  Productos cargados: " + productos.size());
        System.out.println("  Inventario inicializado");
        System.out.println();
    }

    public void registrarVentas() {
        System.out.println("--- REGISTRANDO VENTAS DEL DIA ---");

        registrarVenta("SKU001", 3);
        registrarVenta("SKU002", 5);
        registrarVenta("SKU003", 2);
        registrarVenta("SKU001", 10);
        registrarVenta("SKU004", 4);
        registrarVenta("SKU002", 8);

        System.out.println();
    }

    private void registrarVenta(String codigo, int cantidad) {
        // Buscar producto con iterador (Java 7 style)
        Iterator it = productos.iterator();
        HashMap productoEncontrado = null;

        while (it.hasNext()) {
            HashMap prod = (HashMap) it.next();
            if (prod.get("codigo").equals(codigo)) {
                productoEncontrado = prod;
                break;
            }
        }

        if (productoEncontrado != null) {
            double precio = Double.parseDouble((String) productoEncontrado.get("precio"));
            double subtotal = precio * cantidad;
            totalVentas += subtotal;

            // Actualizar inventario
            Integer stock = (Integer) inventario.get(codigo);
            if (stock != null) {
                inventario.put(codigo, new Integer(stock.intValue() - cantidad));
            }

            // Registrar venta
            HashMap venta = new HashMap();
            venta.put("codigo", codigo);
            venta.put("producto", productoEncontrado.get("nombre"));
            venta.put("cantidad", String.valueOf(cantidad));
            venta.put("subtotal", String.valueOf(subtotal));
            venta.put("fecha", new SimpleDateFormat("yyyy-MM-dd HH:mm").format(new Date()));
            ventas.add(venta);

            System.out.println("  + Venta: " + cantidad + "x " + productoEncontrado.get("nombre") + " = S/." + String.format("%.2f", subtotal));
        }
    }

    public void mostrarReporte() {
        System.out.println("==============================================");
        System.out.println("  REPORTE DE VENTAS");
        System.out.println("==============================================");
        System.out.println("  Total ventas del dia: S/." + String.format("%.2f", totalVentas));
        System.out.println("  Transacciones: " + ventas.size());
        System.out.println();

        // Alertas de stock bajo
        System.out.println("--- ALERTAS DE INVENTARIO ---");
        Iterator entries = inventario.entrySet().iterator();
        int alertas = 0;
        while (entries.hasNext()) {
            HashMap.Entry entry = (HashMap.Entry) entries.next();
            Integer stock = (Integer) entry.getValue();
            if (stock.intValue() < 100) {
                alertas++;
                System.out.println("  ! STOCK BAJO: " + entry.getKey() + " (quedan: " + stock + " unidades)");
            }
        }

        if (alertas == 0) {
            System.out.println("  Todos los productos con stock suficiente");
        }

        System.out.println();
        System.out.println("==============================================");
        System.out.println("  Fin del reporte - " + new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
        System.out.println("==============================================");
    }
}
