"""Port interfaces (hexagonal architecture) for the Apoia-se ETL pipeline."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.domain.models import Apoiador


class DataReaderPort(ABC):
    """Abstract port for reading supporter data from a source."""

    @abstractmethod
    def read(self, path: Path) -> list[Apoiador]:
        """Read supporter data from the given path.

        Args:
            path: Path to the data source.

        Returns:
            List of Apoiador domain objects.
        """


class ArtifactWriterPort(ABC):
    """Abstract port for writing output artifacts."""

    @abstractmethod
    def write(self, data: Any, path: Path) -> None:
        """Write data to an artifact file.

        Args:
            data: The data structure to write.
            path: Output file path.
        """
