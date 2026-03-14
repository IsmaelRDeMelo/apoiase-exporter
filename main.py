"""Main entry point for the Apoia-se ETL pipeline."""

from pathlib import Path

from src.application.transform_use_case import TransformApoiadoresUseCase
from src.infrastructure.csv_reader import PolarsCSVReader
from src.infrastructure.json_writer import JSONArtifactWriter
from src.infrastructure.yaml_writer import YAMLArtifactWriter

# Project paths
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "base-apoiadores-mf.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


def main() -> None:
    """Run the ETL pipeline: CSV -> YAML summary + JSON metadata."""
    reader = PolarsCSVReader()
    yaml_writer = YAMLArtifactWriter()
    json_writer = JSONArtifactWriter()

    use_case = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)
    yaml_path, json_path = use_case.execute(CSV_PATH, ARTIFACTS_DIR)

    print(f"YAML artifact: {yaml_path}")
    print(f"JSON artifact: {json_path}")


if __name__ == "__main__":
    main()
