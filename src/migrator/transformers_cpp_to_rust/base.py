"""Base class for C++ → Rust transformers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TransformResult:
    """Result of a transformation applied to code."""
    original: str
    transformed: str
    changes_made: list[str]
    transformer_name: str

    @property
    def was_modified(self) -> bool:
        return self.original != self.transformed


class BaseTransformer(ABC):
    """Base class for C++ → Rust transformers."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def transform(self, source_code: str) -> TransformResult:
        ...
