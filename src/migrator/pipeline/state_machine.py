"""Máquina de estados para el pipeline de migración.

Define los estados posibles y las transiciones válidas.
Persiste el estado en un archivo JSON para permitir
reanudar migraciones interrumpidas.
"""

import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


class MigrationState(Enum):
    """Estados del pipeline de migración."""
    IDLE = "idle"                    # Sin proyecto cargado
    ANALYZING = "analyzing"          # Analizando código fuente
    ANALYZED = "analyzed"            # Análisis completo
    SEGMENTING = "segmenting"        # Dividiendo en segmentos
    SEGMENTED = "segmented"          # Segmentación completa
    MIGRATING = "migrating"          # Migrando segmentos
    VALIDATING = "validating"        # Validando en Podman
    ASSEMBLING = "assembling"        # Ensamblando resultado
    COMPLETED = "completed"          # Migración exitosa
    FAILED = "failed"                # Fallo (requiere revisión)
    PAUSED = "paused"                # Pausado por el usuario


# Transiciones válidas entre estados
VALID_TRANSITIONS: dict[MigrationState, list[MigrationState]] = {
    MigrationState.IDLE: [MigrationState.ANALYZING],
    MigrationState.ANALYZING: [MigrationState.ANALYZED, MigrationState.FAILED],
    MigrationState.ANALYZED: [MigrationState.SEGMENTING],
    MigrationState.SEGMENTING: [MigrationState.SEGMENTED, MigrationState.FAILED],
    MigrationState.SEGMENTED: [MigrationState.MIGRATING],
    MigrationState.MIGRATING: [
        MigrationState.VALIDATING,
        MigrationState.FAILED,
        MigrationState.PAUSED,
    ],
    MigrationState.VALIDATING: [
        MigrationState.MIGRATING,   # Volver a migrar si falló validación
        MigrationState.ASSEMBLING,
        MigrationState.FAILED,
    ],
    MigrationState.ASSEMBLING: [MigrationState.COMPLETED, MigrationState.FAILED],
    MigrationState.COMPLETED: [MigrationState.IDLE],
    MigrationState.FAILED: [MigrationState.IDLE, MigrationState.MIGRATING, MigrationState.ANALYZING],
    MigrationState.PAUSED: [MigrationState.MIGRATING, MigrationState.IDLE],
}


@dataclass
class SegmentStatus:
    """Estado de un segmento individual."""
    segment_id: str
    state: str = "pending"          # pending, migrating, migrated, validated, failed
    attempts: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    migrated_code: str | None = None
    validation_passed: bool = False


@dataclass
class PipelineContext:
    """Contexto completo del pipeline - se persiste a disco."""
    project_name: str
    source_language: str
    target_language: str
    state: str = MigrationState.IDLE.value
    source_dir: str = ""
    output_dir: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Resultado del análisis
    total_files: int = 0
    total_symbols: int = 0
    total_lines: int = 0
    file_analyses: dict = field(default_factory=dict)  # filename -> analysis summary
    
    # Segmentos
    segments: dict[str, dict] = field(default_factory=dict)  # segment_id -> SegmentStatus
    total_segments: int = 0
    segments_completed: int = 0
    segments_failed: int = 0
    
    # Reglas aplicadas
    rules_violations: list[dict] = field(default_factory=list)
    
    # Log de eventos
    event_log: list[dict] = field(default_factory=list)


class MigrationStateMachine:
    """Máquina de estados para controlar el flujo de migración.
    
    Garantiza que:
    - Solo se ejecutan transiciones válidas
    - El estado se persiste a disco (para reanudar)
    - Se registra un log de todos los eventos
    """

    def __init__(self, state_file: Path | None = None):
        self._state_file = state_file
        self._context: PipelineContext | None = None

    @property
    def state(self) -> MigrationState:
        if self._context is None:
            return MigrationState.IDLE
        return MigrationState(self._context.state)

    @property
    def context(self) -> PipelineContext:
        if self._context is None:
            raise RuntimeError("No hay contexto de pipeline. Llama a init_project() primero.")
        return self._context

    def init_project(
        self,
        project_name: str,
        source_language: str,
        target_language: str,
        source_dir: str,
        output_dir: str,
    ) -> PipelineContext:
        """Inicializa un nuevo proyecto de migración."""
        self._context = PipelineContext(
            project_name=project_name,
            source_language=source_language,
            target_language=target_language,
            source_dir=source_dir,
            output_dir=output_dir,
        )
        self._log_event("project_initialized", f"{source_language} → {target_language}")
        self._save_state()
        return self._context

    def transition(self, new_state: MigrationState, reason: str = "") -> bool:
        """Intenta transicionar a un nuevo estado.
        
        Returns:
            True si la transición fue exitosa
        Raises:
            InvalidTransitionError si la transición no es válida
        """
        current = self.state
        valid_next = VALID_TRANSITIONS.get(current, [])

        if new_state not in valid_next:
            raise InvalidTransitionError(
                f"Transición inválida: {current.value} → {new_state.value}. "
                f"Transiciones válidas: {[s.value for s in valid_next]}"
            )

        old_state = current.value
        self._context.state = new_state.value
        self._context.updated_at = datetime.now().isoformat()
        self._log_event(
            "state_transition",
            f"{old_state} → {new_state.value}" + (f" ({reason})" if reason else "")
        )
        self._save_state()
        return True

    def update_segment(self, segment_id: str, **kwargs) -> None:
        """Actualiza el estado de un segmento."""
        if segment_id not in self._context.segments:
            self._context.segments[segment_id] = asdict(SegmentStatus(segment_id=segment_id))

        for key, value in kwargs.items():
            if key in self._context.segments[segment_id]:
                self._context.segments[segment_id][key] = value

        # Recalcular contadores
        self._context.segments_completed = sum(
            1 for s in self._context.segments.values() if s["state"] == "validated"
        )
        self._context.segments_failed = sum(
            1 for s in self._context.segments.values() if s["state"] == "failed"
        )
        self._save_state()

    def add_rule_violation(self, rule_name: str, segment_id: str, details: str) -> None:
        """Registra una violación de regla (posible alucinación)."""
        violation = {
            "rule": rule_name,
            "segment_id": segment_id,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self._context.rules_violations.append(violation)
        self._log_event("rule_violation", f"{rule_name} en {segment_id}: {details}")
        self._save_state()

    def get_pending_segments(self) -> list[str]:
        """Retorna IDs de segmentos pendientes de migración."""
        return [
            sid for sid, s in self._context.segments.items()
            if s["state"] in ("pending", "failed") and s["attempts"] < s["max_attempts"]
        ]

    def get_progress(self) -> dict:
        """Retorna progreso actual del pipeline."""
        total = self._context.total_segments
        return {
            "state": self.state.value,
            "total_segments": total,
            "completed": self._context.segments_completed,
            "failed": self._context.segments_failed,
            "pending": total - self._context.segments_completed - self._context.segments_failed,
            "progress_pct": (self._context.segments_completed / total * 100) if total > 0 else 0,
            "violations": len(self._context.rules_violations),
        }

    def _log_event(self, event_type: str, detail: str) -> None:
        """Registra un evento en el log."""
        if self._context is not None:
            self._context.event_log.append({
                "type": event_type,
                "detail": detail,
                "timestamp": datetime.now().isoformat(),
            })

    def _save_state(self) -> None:
        """Persiste el estado a disco."""
        if self._state_file and self._context:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            data = asdict(self._context)
            self._state_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def load_state(self, state_file: Path) -> PipelineContext:
        """Carga un estado previo desde disco."""
        self._state_file = state_file
        data = json.loads(state_file.read_text(encoding="utf-8"))
        self._context = PipelineContext(**{
            k: v for k, v in data.items()
            if k in PipelineContext.__dataclass_fields__
        })
        self._log_event("state_loaded", f"Reanudado desde {self._context.state}")
        return self._context


class InvalidTransitionError(Exception):
    """Se intenta una transición de estado no permitida."""
    pass
