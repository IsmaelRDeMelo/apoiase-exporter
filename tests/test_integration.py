"""Integration test: end-to-end pipeline with a CSV fixture."""

import json
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from src.application.transform_use_case import TransformApoiadoresUseCase
from src.infrastructure.csv_reader import PolarsCSVReader
from src.infrastructure.json_writer import JSONArtifactWriter
from src.infrastructure.yaml_writer import YAMLArtifactWriter


@pytest.fixture
def integration_csv(tmp_path: Path) -> Path:
    """Create a realistic multi-status CSV fixture."""
    csv_content = (
        '"ID","Apoiador","Email","Valor","Recompensa","Apoios Efetuados",'
        '"Total Apoiado","Tipo","Status da Promessa","Visibilidade",'
        '"Data da Última Mudança no Status da Promessa","CEP","Rua","Número",'
        '"Complementos","Bairro","Cidade","UF","País","Endereço Completo"\n'
        # Active, current month, recompensa 5
        '"A001","alice santos da silva","alice@test.com",10,5,5,50,'
        '"Cartão de crédito","Ativo","Público","2026-03-01 08:00",'
        ',,,,,,,,\n'
        # Active, previous month, recompensa 5
        '"A002","BOB LIMA","bob@test.com",15,5,3,45,'
        '"Cartão de crédito","Ativo","Público","2026-02-15 10:00",'
        ',,,,,,,,\n'
        # Aguardando, current month, recompensa 18
        '"A003","Carol Ferreira Dias","carol@test.com",40,18,1,40,'
        '"Cartão de crédito","Aguardando Confirmação","Público","2026-03-05 12:00",'
        ',,,,,,,,\n'
        # Inadimplente, recompensa 5
        '"A004","zé da silva","ze@test.com",5,5,2,10,'
        '"Boleto","Inadimplente","Público","2026-01-10 09:00",'
        ',,,,,,,,\n'
        # Desativado (should not count in totals)
        '"A005","Marvin","marvin@test.com",20,5,10,200,'
        '"Cartão de crédito","Desativado","Público","2026-03-01 07:00",'
        ',,,,,,,,\n'
        # Active, current month, recompensa 18
        '"A006","DIANA GONÇALVES COSTA","diana@test.com",40,18,2,80,'
        '"Cartão de crédito","Ativo","Público","2026-03-10 14:00",'
        ',,,,,,,,\n'
    )
    csv_path = tmp_path / "integration_test.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline(
        self, integration_csv: Path, tmp_path: Path
    ) -> None:
        """Run the full pipeline and validate all outputs."""
        artifacts_dir = tmp_path / "artifacts"
        ref_date = datetime(2026, 3, 14)

        reader = PolarsCSVReader()
        yaml_writer = YAMLArtifactWriter()
        json_writer = JSONArtifactWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        yaml_path, json_path = uc.execute(
            integration_csv, artifacts_dir, ref_date
        )

        # Files exist under date directory
        assert yaml_path.exists()
        assert json_path.exists()
        assert yaml_path.parent.name == "2026-03-14"
        assert yaml_path.name == "001.yaml"

        # Validate YAML
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        apoia = yaml_data["apoia-se"]
        assert apoia["total_apoiadores"] == 3  # A001, A002, A006
        assert apoia["total_pendente"] == 1  # A003
        assert apoia["total_inadimplente"] == 1  # A004

        # Current month: A001 (10) + A003 (40) + A006 (40) = 90
        assert apoia["total_recebido_mes_atual"] == 90.0

        # Previous month: A002 (15) = 15
        assert apoia["total_recebido_mes_anterior"] == 15.0

        # New two-tier structure
        assert "0-59-pesetas" in apoia["recompensas"]
        assert "60-pesetas" in apoia["recompensas"]

        # All recompensas 5 and 18 land in tier_baixo (both < 60)
        low = apoia["recompensas"]["0-59-pesetas"]
        assert "Alice S. Silva" in low["apoiadores_com_status_ativo"]
        assert "Bob Lima" in low["apoiadores_com_status_ativo"]
        assert "Diana G. Costa" in low["apoiadores_com_status_ativo"]
        # Inadimplente and Aguardando are in outros_status
        assert "Zé Silva" in low["apoiadores_com_outros_status"]
        assert "Carol F. Dias" in low["apoiadores_com_outros_status"]

        # nomes_unicos combines all
        nomes = low["nomes_unicos"]
        assert "Alice S. Silva" in nomes
        assert "Bob Lima" in nomes

        # sumario section
        assert "sumario" in apoia
        sumario = apoia["sumario"]
        assert "Alice S. Silva" in sumario["ativos"]
        assert "Bob Lima" in sumario["ativos"]

        # Validate JSON metadata
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert len(json_data) == 6
        ids = [entry["id"] for entry in json_data]
        assert "A001" in ids
        assert "A005" in ids  # Even desativado is in metadata


    def test_artifacts_in_date_directory(
        self, integration_csv: Path, tmp_path: Path
    ) -> None:
        """Artifacts are created inside a date-stamped subdirectory."""
        artifacts_dir = tmp_path / "my_artifacts"
        ref = datetime(2026, 3, 14)
        reader = PolarsCSVReader()
        yaml_writer = YAMLArtifactWriter()
        json_writer = JSONArtifactWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        yaml_path, json_path = uc.execute(integration_csv, artifacts_dir, ref)

        assert yaml_path.parent == artifacts_dir / "2026-03-14"
        assert json_path.parent == artifacts_dir / "2026-03-14"

    def test_csv_validation_in_integration(self, tmp_path: Path) -> None:
        """FileNotFoundError raised for missing CSV in a real setup."""
        reader = PolarsCSVReader()
        yaml_writer = YAMLArtifactWriter()
        json_writer = JSONArtifactWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        missing = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            uc.execute(missing, tmp_path, datetime(2026, 3, 14))
