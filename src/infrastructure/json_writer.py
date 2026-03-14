"""JSON metadata artifact writer adapter."""

import json
from pathlib import Path
from typing import Any

from src.domain.ports import ArtifactWriterPort


class JSONArtifactWriter(ArtifactWriterPort):
    """Writes data to a JSON artifact file for debugging."""

    def write(self, data: Any, path: Path) -> None:
        """Write data to a JSON file.

        Args:
            data: Data structure to serialize as JSON.
            path: Output file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
