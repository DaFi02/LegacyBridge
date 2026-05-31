"""Pipeline de migración incremental con máquina de estados.

Controla el proceso de migración paso a paso:
1. ANALYZE - Analiza código fuente, extrae estructura
2. SEGMENT - Divide en segmentos migrables  
3. MIGRATE - Migra cada segmento con IA + reglas
4. VALIDATE - Compila en Podman para verificar
5. ASSEMBLE - Ensambla el resultado final

Incluye reglas anti-alucinación para detectar cuando
la IA genera código incorrecto o inventado.
"""

from .state_machine import MigrationState, MigrationStateMachine
from .analyzer import CodeAnalyzer, FileAnalysis, SymbolInfo
from .segmenter import CodeSegmenter, CodeSegment
from .rules import RuleEngine, Rule, RuleResult
from .hard_rules import HardRuleEngine, HardRule, TransformResult as HardTransformResult
from .orchestrator import MigrationOrchestrator

__all__ = [
    "MigrationState",
    "MigrationStateMachine",
    "CodeAnalyzer",
    "FileAnalysis",
    "SymbolInfo",
    "CodeSegmenter",
    "CodeSegment",
    "RuleEngine",
    "Rule",
    "RuleResult",
    "HardRuleEngine",
    "HardRule",
    "HardTransformResult",
    "MigrationOrchestrator",
]
