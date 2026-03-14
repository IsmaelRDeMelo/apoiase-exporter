"""Integration test: end-to-end pipeline with a CSV fixture."""

import json
from pathlib import Path

import yaml

from src.application.transform_use_case import TransformApoiadoresUseCase
from src.infrastructure.csv_reader import PolarsCSVReader
from src.infrastructure.json_writer import JSONArtifactWriter
from src.infrastructure.yaml_writer import YAMLArtifactWriter
from datetime import datetime

import pytest


@pytest.fixture
def integration_csv(tmp_path: Path) -> Path:
    """Create a realistic multi-status CSV fixture."""
    csv_content = (
        '"ID","Apoiador","Email","Valor","Recompensa","Apoios Efetuados",'
        '"Total Apoiado","Tipo","Status da Promessa","Visibilidade",'
        '"Data da Última Mudança no Status da Promessa","CEP","Rua","Número",'
        '"Complementos","Bairro","Cidade","UF","País","Endereço Completo"\n'
        # Active, current month, recompensa 5
        '"A001","Alice Santos da Silva","alice@test.com",10,5,5,50,'
        '"Cartão de crédito","Ativo","Público","2026-03-01 08:00",'
        ',,,,,,,,\n'
        # Active, previous month, recompensa 5
        '"A002","Bob Lima","bob@test.com",15,5,3,45,'
        '"Cartão de crédito","Ativo","Público","2026-02-15 10:00",'
        ',,,,,,,,\n'
        # Aguardando, current month, recompensa 18
        '"A003","Carol Ferreira Dias","carol@test.com",40,18,1,40,'
        '"Cartão de crédito","Aguardando Confirmação","Público","2026-03-05 12:00",'
        ',,,,,,,,\n'
        # Inadimplente, recompensa 5
        '"A004","Zé da Silva","ze@test.com",5,5,2,10,'
        '"Boleto","Inadimplente","Público","2026-01-10 09:00",'
        ',,,,,,,,\n'
        # Desativado (should not count in totals)
        '"A005","Marvin","marvin@test.com",20,5,10,200,'
        '"Cartão de crédito","Desativado","Público","2026-03-01 07:00",'
        ',,,,,,,,\n'
        # Active, current month, recompensa 18
        '"A006","Diana Gonçalves Costa","diana@test.com",40,18,2,80,'
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

        # Files exist
        assert yaml_path.exists()
        assert json_path.exists()

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

        # Recompensa 5 should have active: Alice Silva, Bob Lima
        r5 = apoia["recompensas"][5]
        assert "Alice Silva" in r5["apoiadores_com_status_ativo"]
        assert "Bob Lima" in r5["apoiadores_com_status_ativo"]
        assert "Zé Silva" in r5["apoiadores_com_status_inadimplente"]

        # Recompensa 18 should have active: Diana Costa + pending: Carol Dias
        r18 = apoia["recompensas"][18]
        assert "Diana Costa" in r18["apoiadores_com_status_ativo"]
        assert "Carol Dias" in r18["apoiadores_com_status_pendente"]

        # Validate JSON metadata
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        assert len(json_data) == 6
        ids = [entry["id"] for entry in json_data]
        assert "A001" in ids
        assert "A005" in ids  # Even desativado is in metadata

    def test_artifacts_in_correct_directory(
        self, integration_csv: Path, tmp_path: Path
    ) -> None:
        """Artifacts are created inside the specified output directory."""
        artifacts_dir = tmp_path / "my_artifacts"
        reader = PolarsCSVReader()
        yaml_writer = YAMLArtifactWriter()
        json_writer = JSONArtifactWriter()
        uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

        yaml_path, json_path = uc.execute(
            integration_csv, artifacts_dir, datetime(2026, 3, 14)
        )

        assert yaml_path.parent == artifacts_dir
        assert json_path.parent == artifacts_dir
