#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# LegacyBridge — Arranque de Demo para Video
# 
# Este script inicia todo lo necesario para la demo:
# 1. Dashboard React (puerto 5173)
# 2. Script de demo con API (puerto 8787)
#
# Uso:
#   chmod +x start_demo.sh
#   ./start_demo.sh
# ═══════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       🌉 LegacyBridge — Arranque de Demo                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar dependencias
if ! command -v pnpm &> /dev/null; then
    echo "  ✗ pnpm no instalado. Ejecuta: npm install -g pnpm"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "  ✗ uv no instalado. Ejecuta: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Instalar dependencias del dashboard si no existen
if [ ! -d "dashboard/node_modules" ]; then
    echo "  📦 Instalando dependencias del dashboard..."
    cd dashboard && pnpm install && cd ..
fi

echo "  🚀 Iniciando Dashboard React (http://localhost:5173)..."
cd dashboard && pnpm run dev &
DASHBOARD_PID=$!
cd ..

# Esperar que el dashboard arranque
sleep 2

echo ""
echo "  🚀 Iniciando script de demo..."
echo "  ─────────────────────────────────────────────────"
echo ""

# Ejecutar demo
uv run python demo_video.py

# Cleanup
kill $DASHBOARD_PID 2>/dev/null || true
echo "  👋 Todos los procesos cerrados."
