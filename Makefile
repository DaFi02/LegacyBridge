# ============================================================
# LegacyBridge - Makefile
# ============================================================
# Comandos rápidos para desarrollo y uso del producto
# ============================================================

.PHONY: help install setup test lint demo run validate clean

# --- Default ---
help: ## Mostrar esta ayuda
	@echo ""
	@echo "🌉 LegacyBridge — Comandos disponibles"
	@echo "============================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --- Setup ---
install: ## Instalar dependencias del proyecto
	@echo "📦 Instalando dependencias..."
	uv sync
	@echo "✅ Dependencias instaladas"

setup: install ## Setup completo para nuevos developers
	@echo ""
	@echo "⚙️  Configurando entorno..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📋 .env creado desde .env.example"; \
		echo "⚠️  Edita .env con tu NVIDIA_API_KEY"; \
	else \
		echo "✅ .env ya existe"; \
	fi
	@echo ""
	@echo "🐳 Descargando imágenes de contenedores..."
	podman pull docker.io/library/rust:1-alpine 2>/dev/null || true
	podman pull docker.io/library/eclipse-temurin:17-jdk-alpine 2>/dev/null || true
	@echo ""
	@echo "🧪 Ejecutando tests..."
	uv run pytest tests/ -q
	@echo ""
	@echo "════════════════════════════════════════════"
	@echo "  ✅ Setup completo!"
	@echo "  Siguiente paso: edita .env con tu API key"
	@echo "  Luego ejecuta: make demo"
	@echo "════════════════════════════════════════════"

# --- Testing ---
test: ## Ejecutar todos los tests (119)
	uv run pytest tests/ -v

test-quick: ## Tests rápidos (sin verbose)
	uv run pytest tests/ -q

test-pipeline: ## Tests solo del pipeline
	uv run pytest tests/test_pipeline.py -v

test-rules: ## Tests solo de reglas duras
	uv run pytest tests/test_hard_rules.py -v

# --- Demo ---
demo: ## Ejecutar demo interactivo del pipeline
	uv run python pipeline_cli.py demo

# --- Migración ---
run-cobol: ## Migrar COBOL → Rust (requiere API key)
	uv run python pipeline_cli.py run \
		--source examples/cobol/ \
		--output output/cobol_to_rust/ \
		--from cobol --to rust \
		--retries 2

run-cpp: ## Migrar C++ → Rust (requiere API key)
	uv run python pipeline_cli.py run \
		--source examples/cpp_legacy/ \
		--output output/cpp_to_rust/ \
		--from cpp --to rust \
		--retries 2

run-java: ## Migrar Java 8 → Java 17 (regex, sin IA)
	uv run python main.py --demo

# --- Análisis ---
analyze-cobol: ## Analizar estructura COBOL
	uv run python pipeline_cli.py analyze --source examples/cobol/ --context

analyze-cpp: ## Analizar estructura C++
	uv run python pipeline_cli.py analyze --source examples/cpp_legacy/ --context

segment-cobol: ## Segmentar código COBOL
	uv run python pipeline_cli.py segment --source examples/cobol/

# --- Validación ---
validate: ## Validar compilación de output/ con Podman
	@echo "¿Qué directorio validar?"
	@echo "  make validate DIR=output/cobol_to_rust/"
	@echo ""
	@if [ -n "$(DIR)" ]; then \
		uv run python migrate_ai.py --validate $(DIR); \
	fi

validate-cobol: ## Validar migración COBOL → Rust
	uv run python migrate_ai.py --validate output/cobol_to_rust/

validate-cpp: ## Validar migración C++ → Rust
	uv run python migrate_ai.py --validate output/cpp_to_rust/

# --- Utilidades ---
status: ## Ver estado del pipeline (último run)
	@latest=$$(ls -td output/*/  2>/dev/null | head -1); \
	if [ -n "$$latest" ]; then \
		uv run python pipeline_cli.py status --output "$$latest"; \
	else \
		echo "No hay ejecuciones previas en output/"; \
	fi

clean: ## Limpiar outputs generados
	rm -rf output/cobol_to_rust/ output/cpp_to_rust/
	rm -rf output/pipeline_*/ 
	@echo "🧹 Outputs limpiados"

clean-all: clean ## Limpiar todo (outputs + cache)
	rm -rf .pytest_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "🧹 Todo limpio"
