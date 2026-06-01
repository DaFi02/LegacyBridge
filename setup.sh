#!/usr/bin/env bash
# ============================================================
# LegacyBridge — Setup automático para nuevos developers
# ============================================================
# Uso: curl -sSL <repo-url>/setup.sh | bash
#   o: ./setup.sh
# ============================================================

set -e

echo ""
echo "🌉 LegacyBridge — Setup Automático"
echo "════════════════════════════════════════════════════════"
echo ""

# --- Verificar dependencias ---
echo "🔍 Verificando dependencias del sistema..."

check_cmd() {
    if command -v "$1" &> /dev/null; then
        echo "  ✅ $1 $(command -v "$1")"
        return 0
    else
        echo "  ❌ $1 no encontrado"
        return 1
    fi
}

MISSING=0
check_cmd python3 || MISSING=1
check_cmd uv || MISSING=1
check_cmd podman || MISSING=1
check_cmd git || MISSING=1

echo ""

if [ $MISSING -eq 1 ]; then
    echo "⚠️  Dependencias faltantes. Instalando..."
    echo ""

    # UV
    if ! command -v uv &> /dev/null; then
        echo "📦 Instalando UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # Podman (Linux)
    if ! command -v podman &> /dev/null; then
        echo "🐳 Instala Podman manualmente:"
        echo "   Fedora/RHEL: sudo dnf install podman"
        echo "   Ubuntu:      sudo apt install podman"
        echo "   macOS:       brew install podman"
        echo ""
    fi
fi

# --- Instalar dependencias Python ---
echo "📦 Instalando dependencias del proyecto..."
uv sync
echo ""

# --- Configurar .env ---
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📋 Archivo .env creado desde .env.example"
    echo ""
    echo "┌─────────────────────────────────────────────────┐"
    echo "│  ⚠️  ACCIÓN REQUERIDA:                          │"
    echo "│  Edita .env y agrega tu NVIDIA API Key:         │"
    echo "│                                                 │"
    echo "│  NVIDIA_API_KEY=nvapi-tu-key-aqui               │"
    echo "│                                                 │"
    echo "│  Obtén una en: https://build.nvidia.com/        │"
    echo "└─────────────────────────────────────────────────┘"
    echo ""
else
    echo "✅ .env ya configurado"
fi

# --- Descargar imágenes de contenedores ---
echo "🐳 Pre-descargando imágenes de compilación..."
podman pull docker.io/library/rust:1-alpine 2>/dev/null && echo "  ✅ rust:1-alpine" || echo "  ⏭️  rust:1-alpine (se descargará al usar)"
podman pull docker.io/library/eclipse-temurin:17-jdk-alpine 2>/dev/null && echo "  ✅ eclipse-temurin:17" || echo "  ⏭️  eclipse-temurin:17 (se descargará al usar)"
echo ""

# --- Ejecutar tests ---
echo "🧪 Verificando instalación con tests..."
uv run pytest tests/ -q
echo ""

# --- Resultado ---
echo "════════════════════════════════════════════════════════"
echo "  ✅ ¡Setup completado!"
echo ""
echo "  Comandos disponibles:"
echo "    make help          → Ver todos los comandos"
echo "    make demo          → Demo del pipeline (sin API key)"
echo "    make test          → Ejecutar tests"
echo "    make run-cobol     → Migrar COBOL → Rust"
echo "    make run-cpp       → Migrar C++ → Rust"
echo ""
echo "  Primer paso:"
echo "    1. Edita .env con tu NVIDIA_API_KEY"
echo "    2. Ejecuta: make demo"
echo "════════════════════════════════════════════════════════"
