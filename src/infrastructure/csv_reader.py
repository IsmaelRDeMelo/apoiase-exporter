"""Polars-based CSV reader adapter for the Apoia-se data."""

from datetime import datetime
from pathlib import Path

import polars as pl

from src.domain.models import Apoiador
from src.domain.ports import DataReaderPort

# Columns we need from the CSV
REQUIRED_COLUMNS = [
    "ID",
    "Apoiador",
    "Email",
    "Valor",
    "Recompensa",
    "Apoios Efetuados",
    "Total Apoiado",
    "Status da Promessa",
    "Data da Última Mudança no Status da Promessa",
]


class PolarsCSVReader(DataReaderPort):
    """Reads supporter data from a CSV file using Polars."""

    def read(self, path: Path) -> list[Apoiador]:
        """Read and parse the CSV file into domain objects.

        Args:
            path: Path to the CSV file.

        Returns:
            List of Apoiador domain objects.
        """
        df = pl.read_csv(
            path,
            columns=REQUIRED_COLUMNS,
            schema_overrides={
                "Valor": pl.Float64,
                "Apoios Efetuados": pl.Int64,
                "Total Apoiado": pl.Float64,
            },
        )
        # Cast Recompensa to Int64 explicitly after fill to avoid NaN→float promotion
        df = df.with_columns(
            pl.col("Recompensa").cast(pl.Float64).fill_null(0).cast(pl.Int64)
        )

        apoiadores: list[Apoiador] = []
        for row in df.iter_rows(named=True):
            data_str = row["Data da Última Mudança no Status da Promessa"]
            data_dt = None
            if data_str:
                try:
                    data_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    data_dt = None

            apoiador = Apoiador(
                id=str(row["ID"]),
                nome=str(row["Apoiador"]),
                email=str(row["Email"]),
                valor=float(row["Valor"]),
                recompensa=int(row["Recompensa"]),
                apoios_efetuados=int(row["Apoios Efetuados"]),
                total_apoiado=float(row["Total Apoiado"]),
                status=str(row["Status da Promessa"]),
                data_ultima_mudanca=data_dt,
            )
            apoiadores.append(apoiador)

        return apoiadores
