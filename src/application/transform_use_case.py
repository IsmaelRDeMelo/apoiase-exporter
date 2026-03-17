"""Use case for transforming Apoia-se supporter data into summary artifacts."""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.domain.models import ApoiaSummary, Apoiador, RecompensaGroup
from src.domain.name_utils import format_display_name
from src.domain.ports import ArtifactWriterPort, DataReaderPort

# Status constants matching the CSV values
STATUS_ATIVO = "Ativo"
STATUS_DESATIVADO = "Desativado"
STATUS_INADIMPLENTE = "Inadimplente"
STATUS_AGUARDANDO = "Aguardando Confirmação"


class TransformApoiadoresUseCase:
    """Transforms raw supporter data into aggregated YAML and debug JSON."""

    def __init__(
        self,
        reader: DataReaderPort,
        yaml_writer: ArtifactWriterPort,
        json_writer: ArtifactWriterPort,
    ) -> None:
        """Initialize with injected ports.

        Args:
            reader: Port for reading supporter data.
            yaml_writer: Port for writing the YAML summary artifact.
            json_writer: Port for writing the JSON metadata artifact.
        """
        self._reader = reader
        self._yaml_writer = yaml_writer
        self._json_writer = json_writer

    def execute(
        self,
        csv_path: Path,
        output_dir: Path,
        reference_date: Optional[datetime] = None,
        days_filter: int = 30,
    ) -> tuple[Path, Path]:
        """Execute the full ETL pipeline.

        Args:
            csv_path: Path to the input CSV file.
            output_dir: Directory where artifacts will be saved.
            reference_date: Reference date for month calculations.
                Defaults to now.
            days_filter: Number of days for the "active recent" filter.
                Defaults to 30. Allowed: 10, 15, 30, 45, 60.

        Returns:
            Tuple of (yaml_path, json_path) for the generated artifacts.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
        """
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {csv_path}. "
                "Please place the Apoia-se export CSV in the data/ folder."
            )

        if reference_date is None:
            reference_date = datetime.now()

        apoiadores = self._reader.read(csv_path)
        summary = self._build_summary(apoiadores, reference_date, days_filter)

        # Build date-based output directory with serial number
        date_str = reference_date.strftime("%Y-%m-%d")
        date_dir = output_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        serial = self._next_serial(date_dir)
        yaml_path = date_dir / f"{serial:03d}.yaml"
        json_path = date_dir / f"{serial:03d}.json"

        yaml_data = self._summary_to_dict(summary)
        self._yaml_writer.write(yaml_data, yaml_path)

        metadata = self._build_metadata(apoiadores)
        self._json_writer.write(metadata, json_path)

        return yaml_path, json_path

    @staticmethod
    def _next_serial(date_dir: Path) -> int:
        """Determine the next serial number for artifacts in a date folder.

        Scans existing .yaml files and returns max + 1, starting at 1.

        Args:
            date_dir: The date-specific output directory.

        Returns:
            Next available serial number.
        """
        existing = list(date_dir.glob("*.yaml"))
        if not existing:
            return 1

        max_serial = 0
        for f in existing:
            try:
                serial = int(f.stem)
                max_serial = max(max_serial, serial)
            except ValueError:
                continue
        return max_serial + 1

    def _build_summary(
        self,
        apoiadores: list[Apoiador],
        reference_date: datetime,
        days_filter: int = 30,
    ) -> ApoiaSummary:
        """Build the aggregated summary from raw supporter data.

        Args:
            apoiadores: List of all supporters.
            reference_date: Date used to determine current/previous month.
            days_filter: Number of days for the active-recent filter.

        Returns:
            ApoiaSummary with all computed fields.
        """
        summary = ApoiaSummary(dias_filtro=days_filter)

        current_month = reference_date.month
        current_year = reference_date.year

        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year

        cutoff_date = reference_date - timedelta(days=days_filter)

        # Accumulate (name, date) tuples per recompensa+status for sorting
        recompensa_groups: dict[int, dict[str, list[tuple[str, datetime]]]] = (
            defaultdict(lambda: defaultdict(list))
        )

        # Separate accumulator for the "active recent" virtual status
        recent_by_recompensa: dict[int, list[tuple[str, datetime]]] = (
            defaultdict(list)
        )

        for ap in apoiadores:
            # Counts by status
            if ap.status == STATUS_ATIVO:
                summary.total_apoiadores += 1
            elif ap.status == STATUS_AGUARDANDO:
                summary.total_pendente += 1
            elif ap.status == STATUS_INADIMPLENTE:
                summary.total_inadimplente += 1

            # Monthly totals for active and pending
            if ap.status in (STATUS_ATIVO, STATUS_AGUARDANDO):
                if ap.data_ultima_mudanca is not None:
                    dt = ap.data_ultima_mudanca
                    if dt.month == current_month and dt.year == current_year:
                        summary.total_recebido_mes_atual += ap.valor
                    elif dt.month == prev_month and dt.year == prev_year:
                        summary.total_recebido_mes_anterior += ap.valor

            # Build recompensa groups (name, date) for date-based sorting
            display_name = format_display_name(ap.nome)
            status_key = self._status_to_key(ap.status)
            sort_date = ap.data_ultima_mudanca or datetime.max
            if status_key:
                recompensa_groups[ap.recompensa][status_key].append(
                    (display_name, sort_date)
                )

            # Active recent: Ativo always included; other statuses only within N days
            is_ativo = ap.status == STATUS_ATIVO
            within_period = (
                ap.data_ultima_mudanca is not None
                and ap.data_ultima_mudanca >= cutoff_date
            )
            if is_ativo or within_period:
                summary.total_ativos_recentes += 1
                recent_by_recompensa[ap.recompensa].append(
                    (display_name, sort_date)
                )

        # Sort by date (oldest first) and build RecompensaGroup objects
        all_recompensa_keys = set(recompensa_groups.keys()) | set(
            recent_by_recompensa.keys()
        )

        for recompensa_value in sorted(all_recompensa_keys):
            group = RecompensaGroup()

            # Standard status groups
            if recompensa_value in recompensa_groups:
                status_dict = recompensa_groups[recompensa_value]
                for status_key, name_date_pairs in status_dict.items():
                    sorted_pairs = sorted(name_date_pairs, key=lambda x: x[1])
                    sorted_names = [name for name, _ in sorted_pairs]
                    setattr(group, status_key, ", ".join(sorted_names))

            # Active recent group
            if recompensa_value in recent_by_recompensa:
                pairs = recent_by_recompensa[recompensa_value]
                sorted_pairs = sorted(pairs, key=lambda x: x[1])
                sorted_names = [name for name, _ in sorted_pairs]
                group.apoiadores_ativos_ultimos_n_dias = ", ".join(
                    sorted_names
                )

            summary.recompensas[recompensa_value] = group

        # Round monetary values
        summary.total_recebido_mes_atual = round(
            summary.total_recebido_mes_atual, 2
        )
        summary.total_recebido_mes_anterior = round(
            summary.total_recebido_mes_anterior, 2
        )

        return summary

    @staticmethod
    def _status_to_key(status: str) -> Optional[str]:
        """Map a CSV status value to a RecompensaGroup field name.

        Args:
            status: The raw status string from CSV.

        Returns:
            The corresponding field name, or None for unknown statuses.
        """
        mapping = {
            STATUS_ATIVO: "apoiadores_com_status_ativo",
            STATUS_AGUARDANDO: "apoiadores_com_status_pendente",
            STATUS_INADIMPLENTE: "apoiadores_com_status_inadimplente",
        }
        return mapping.get(status)

    @staticmethod
    def _summary_to_dict(summary: ApoiaSummary) -> dict:
        """Convert the summary dataclass to a nested dict for YAML output.

        Args:
            summary: The computed summary.

        Returns:
            Dictionary matching the YAML structure from the spec.
        """
        recompensas_dict: dict[str, dict[str, str]] = {}
        for recompensa_value, group in sorted(summary.recompensas.items()):
            pesetas_key = f"{recompensa_value}-pesetas"
            group_dict: dict[str, str] = {}
            if group.apoiadores_com_status_ativo:
                group_dict["apoiadores_com_status_ativo"] = (
                    group.apoiadores_com_status_ativo
                )
            if group.apoiadores_com_status_pendente:
                group_dict["apoiadores_com_status_pendente"] = (
                    group.apoiadores_com_status_pendente
                )
            if group.apoiadores_com_status_inadimplente:
                group_dict["apoiadores_com_status_inadimplente"] = (
                    group.apoiadores_com_status_inadimplente
                )
            if group.apoiadores_com_status_aguardando_confirmacao:
                group_dict["apoiadores_com_status_aguardando_confirmacao"] = (
                    group.apoiadores_com_status_aguardando_confirmacao
                )
            if group.apoiadores_ativos_ultimos_n_dias:
                group_dict["apoiadores_ativos_ultimos_n_dias"] = (
                    group.apoiadores_ativos_ultimos_n_dias
                )
            recompensas_dict[pesetas_key] = group_dict

        return {
            "apoia-se": {
                "total_apoiadores": summary.total_apoiadores,
                "total_pendente": summary.total_pendente,
                "total_inadimplente": summary.total_inadimplente,
                "total_recebido_mes_atual": summary.total_recebido_mes_atual,
                "total_recebido_mes_anterior": summary.total_recebido_mes_anterior,
                "total_ativos_recentes": summary.total_ativos_recentes,
                "dias_filtro": summary.dias_filtro,
                "recompensas": recompensas_dict,
            }
        }

    @staticmethod
    def _build_metadata(apoiadores: list[Apoiador]) -> list[dict[str, str]]:
        """Build the debugging metadata from all supporters.

        This JSON enables disambiguation of supporters with the same name
        by exposing their ID and email.

        Args:
            apoiadores: List of all supporters.

        Returns:
            List of dicts with id, nome, email for each supporter.
        """
        return [
            {"id": ap.id, "nome": ap.nome, "email": ap.email}
            for ap in apoiadores
        ]
