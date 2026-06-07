<?php
/**
 * Sistema de Gestión de Empleados - PHP 5.4
 * Código legacy con patrones antiguos:
 * - Sin type hints
 * - mysql_* functions (deprecated)
 * - Sin namespaces
 * - Variables globales
 * - HTML mezclado con lógica
 */

// Simulación de datos (en legacy sería mysql_query)
$empleados = array(
    array("id" => 1, "nombre" => "María García", "cargo" => "Gerente", "salario" => 8500.00, "departamento" => "Administración"),
    array("id" => 2, "nombre" => "Carlos López", "cargo" => "Desarrollador", "salario" => 5200.00, "departamento" => "TI"),
    array("id" => 3, "nombre" => "Ana Rodríguez", "cargo" => "Diseñadora", "salario" => 4800.00, "departamento" => "Marketing"),
    array("id" => 4, "nombre" => "Pedro Sánchez", "cargo" => "Analista", "salario" => 5500.00, "departamento" => "TI"),
    array("id" => 5, "nombre" => "Laura Martínez", "cargo" => "Contadora", "salario" => 6000.00, "departamento" => "Finanzas"),
);

$departamentos = array("Administración", "TI", "Marketing", "Finanzas", "RRHH");

// Funciones globales sin type hints (PHP 5.4 style)
function calcular_nomina($empleados) {
    $total = 0;
    $detalles = array();
    
    for ($i = 0; $i < count($empleados); $i++) {
        $emp = $empleados[$i];
        $bruto = $emp["salario"];
        
        // Cálculos de nómina peruana
        $essalud = $bruto * 0.09;      // EsSalud 9%
        $afp = $bruto * 0.13;          // AFP 13%
        $impuesto = 0;
        
        if ($bruto > 7000) {
            $impuesto = ($bruto - 7000) * 0.08;  // IR simplificado
        }
        
        $neto = $bruto - $afp - $impuesto;
        $total += $neto;
        
        $detalles[] = array(
            "nombre" => $emp["nombre"],
            "cargo" => $emp["cargo"],
            "bruto" => $bruto,
            "afp" => $afp,
            "impuesto" => $impuesto,
            "neto" => $neto,
        );
    }
    
    return array("total" => $total, "detalles" => $detalles);
}

function buscar_empleado($empleados, $nombre) {
    $resultados = array();
    for ($i = 0; $i < count($empleados); $i++) {
        if (strpos(strtolower($empleados[$i]["nombre"]), strtolower($nombre)) !== false) {
            $resultados[] = $empleados[$i];
        }
    }
    return $resultados;
}

function generar_reporte($empleados) {
    $por_depto = array();
    
    foreach ($empleados as $emp) {
        $depto = $emp["departamento"];
        if (!isset($por_depto[$depto])) {
            $por_depto[$depto] = array("count" => 0, "total_salario" => 0);
        }
        $por_depto[$depto]["count"]++;
        $por_depto[$depto]["total_salario"] += $emp["salario"];
    }
    
    return $por_depto;
}

function formatear_moneda($monto) {
    return "S/. " . number_format($monto, 2, ".", ",");
}

// === EJECUCIÓN PRINCIPAL ===
echo "==============================================\n";
echo "  SISTEMA DE GESTIÓN DE EMPLEADOS v2.1\n";
echo "  PHP 5.4 Legacy System\n";
echo "==============================================\n\n";

// Calcular nómina
$nomina = calcular_nomina($empleados);
echo "--- NÓMINA DEL MES ---\n";
foreach ($nomina["detalles"] as $det) {
    echo "  " . str_pad($det["nombre"], 20) . " | ";
    echo str_pad($det["cargo"], 15) . " | ";
    echo "Bruto: " . formatear_moneda($det["bruto"]) . " | ";
    echo "AFP: " . formatear_moneda($det["afp"]) . " | ";
    echo "Neto: " . formatear_moneda($det["neto"]) . "\n";
}
echo "\n  TOTAL NÓMINA: " . formatear_moneda($nomina["total"]) . "\n\n";

// Reporte por departamento
echo "--- REPORTE POR DEPARTAMENTO ---\n";
$reporte = generar_reporte($empleados);
foreach ($reporte as $depto => $datos) {
    $promedio = $datos["total_salario"] / $datos["count"];
    echo "  " . str_pad($depto, 18) . " | ";
    echo "Empleados: " . $datos["count"] . " | ";
    echo "Gasto: " . formatear_moneda($datos["total_salario"]) . " | ";
    echo "Promedio: " . formatear_moneda($promedio) . "\n";
}

// Búsqueda
echo "\n--- BÚSQUEDA: 'garcía' ---\n";
$encontrados = buscar_empleado($empleados, "garcía");
if (count($encontrados) > 0) {
    foreach ($encontrados as $emp) {
        echo "  Encontrado: " . $emp["nombre"] . " - " . $emp["cargo"] . " (" . $emp["departamento"] . ")\n";
    }
} else {
    echo "  No se encontraron resultados\n";
}

echo "\n==============================================\n";
echo "  Fin del reporte - " . date("Y-m-d") . "\n";
echo "==============================================\n";
?>
