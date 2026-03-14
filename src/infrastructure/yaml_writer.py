"""YAML artifact writer adapter."""

from pathlib import Path
from typing import Any

import yaml

from src.domain.ports import ArtifactWriterPort


class YAMLArtifactWriter(ArtifactWriterPort):
    """Writes data to a YAML artifact file."""

    def write(self, data: Any, path: Path) -> None:
        """Write data to a YAML file.

        Args:
            data: Dictionary to serialize as YAML.
            path: Output file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
