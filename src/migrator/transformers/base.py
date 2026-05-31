"""Base class for all code transformers."""

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
    """Base class for Java 8 → Java 17+ transformers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the transformation."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this transformer does."""
        ...

    @property
    @abstractmethod
    def java_version_target(self) -> int:
        """Minimum Java version required for this transformation."""
        ...

    @abstractmethod
    def transform(self, source_code: str) -> TransformResult:
        """Apply the transformation to the source code."""
        ...
