"""Use case for transforming Apoia-se supporter data into summary artifacts."""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.domain.models import (
    TIER_PREMIUM_THRESHOLD,
    ApoiaSummary,
    Apoiador,
    RecompensaGroup,
)
from src.domain.name_utils import format_display_name
from src.domain.ports import ArtifactWriterPort, DataReaderPort

# Status constants matching the CSV values
STATUS_ATIVO = "Ativo"
STATUS_DESATIVADO = "Desativado"
STATUS_INADIMPLENTE = "Inadimplente"
STATUS_AGUARDANDO = "Aguardando Confirmação"

# Tier keys used in YAML output
TIER_LOW_KEY = "0-59-pesetas"
TIER_PREMIUM_KEY = "60-pesetas"


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

    @staticmethod
    def _is_premium(recompensa: int) -> bool:
        """Return True if the recompensa value belongs to the premium tier (≥60)."""
        return recompensa >= TIER_PREMIUM_THRESHOLD

    def _build_summary(
        self,
        apoiadores: list[Apoiador],
        reference_date: datetime,
        days_filter: int = 30,
    ) -> ApoiaSummary:
        """Build the aggregated summary from raw supporter data.

        Supporters are bucketed into two tiers:
        - tier_baixo:   recompensa 0–59
        - tier_premium: recompensa 60+

        Within each tier, names are deduplicated by display name. The
        ``apoiadores_ativos_ultimos_n_dias`` list contains only non-ATIVO
        supporters who changed status within the last *days_filter* days.

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

        # Per-tier accumulators: tier_key -> status_key -> list[(name, date)]
        # Using ordered insertion; dedup happens at flush time.
        tier_status: dict[str, dict[str, list[tuple[str, datetime]]]] = {
            TIER_LOW_KEY: defaultdict(list),
            TIER_PREMIUM_KEY: defaultdict(list),
        }
        # Per-tier recently-active (non-ATIVO within window)
        tier_recent: dict[str, list[tuple[str, datetime]]] = {
            TIER_LOW_KEY: [],
            TIER_PREMIUM_KEY: [],
        }
        # Seen-name sets for dedup — (tier_key, status_key) -> set[name]
        seen_status: dict[tuple[str, str], set[str]] = defaultdict(set)
        # Seen-name set for recently-active dedup — tier_key -> set[name]
        seen_recent: dict[str, set[str]] = {
            TIER_LOW_KEY: set(),
            TIER_PREMIUM_KEY: set(),
        }

        for ap in apoiadores:
            # --- Global counters by status ---
            if ap.status == STATUS_ATIVO:
                summary.total_apoiadores += 1
            elif ap.status == STATUS_AGUARDANDO:
                summary.total_pendente += 1
            elif ap.status == STATUS_INADIMPLENTE:
                summary.total_inadimplente += 1

            # --- Monthly monetary totals ---
            if ap.status in (STATUS_ATIVO, STATUS_AGUARDANDO):
                if ap.data_ultima_mudanca is not None:
                    dt = ap.data_ultima_mudanca
                    if dt.month == current_month and dt.year == current_year:
                        summary.total_recebido_mes_atual += ap.valor
                    elif dt.month == prev_month and dt.year == prev_year:
                        summary.total_recebido_mes_anterior += ap.valor

            display_name = format_display_name(ap.nome)
            sort_date = ap.data_ultima_mudanca or datetime.max
            tier_key = TIER_PREMIUM_KEY if self._is_premium(ap.recompensa) else TIER_LOW_KEY

            # --- Status groups (with dedup) ---
            status_key = self._status_to_key(ap.status)
            if status_key:
                seen_key = (tier_key, status_key)
                if display_name not in seen_status[seen_key]:
                    seen_status[seen_key].add(display_name)
                    tier_status[tier_key][status_key].append((display_name, sort_date))

            # --- Active-recent counter (ATIVO always counted) ---
            is_ativo = ap.status == STATUS_ATIVO
            within_period = (
                ap.data_ultima_mudanca is not None
                and ap.data_ultima_mudanca >= cutoff_date
            )
            if is_ativo or within_period:
                summary.total_ativos_recentes += 1

            # --- Recently-active list: non-ATIVO only within window (with dedup) ---
            if not is_ativo and within_period:
                if display_name not in seen_recent[tier_key]:
                    seen_recent[tier_key].add(display_name)
                    tier_recent[tier_key].append((display_name, sort_date))

        # --- Build RecompensaGroup for each tier ---
        for tier_key, status_dict in tier_status.items():
            group = self._build_group(status_dict, tier_recent[tier_key])
            if tier_key == TIER_LOW_KEY:
                summary.tier_baixo = group
            else:
                summary.tier_premium = group

        # --- Build sumario fields ---
        summary = self._build_sumario(summary)

        # Round monetary values
        summary.total_recebido_mes_atual = round(summary.total_recebido_mes_atual, 2)
        summary.total_recebido_mes_anterior = round(summary.total_recebido_mes_anterior, 2)

        return summary

    @staticmethod
    def _build_group(
        status_dict: dict[str, list[tuple[str, datetime]]],
        recent_pairs: list[tuple[str, datetime]],
    ) -> RecompensaGroup:
        """Build a RecompensaGroup from pre-bucketed (name, date) pairs.

        Args:
            status_dict: Mapping from status field name to (name, date) pairs.
            recent_pairs: (name, date) pairs for the recently-active list.

        Returns:
            Populated RecompensaGroup.
        """
        group = RecompensaGroup()

        # Ativo names
        ativo_pairs = sorted(
            status_dict.get("apoiadores_com_status_ativo", []), key=lambda x: x[1]
        )
        group.apoiadores_com_status_ativo = ", ".join(n for n, _ in ativo_pairs)

        # Other statuses merged into one field
        other_pairs: list[tuple[str, datetime]] = []
        seen_other: set[str] = set()
        for key in ("apoiadores_com_status_pendente", "apoiadores_com_status_inadimplente"):
            for name, date in status_dict.get(key, []):
                if name not in seen_other:
                    seen_other.add(name)
                    other_pairs.append((name, date))
        other_pairs_sorted = sorted(other_pairs, key=lambda x: x[1])
        group.apoiadores_com_outros_status = ", ".join(n for n, _ in other_pairs_sorted)

        # nomes_unicos = union of ativo + outros, deduped, sorted by date
        all_pairs: list[tuple[str, datetime]] = []
        seen_all: set[str] = set()
        for name, date in (ativo_pairs + other_pairs_sorted):
            if name not in seen_all:
                seen_all.add(name)
                all_pairs.append((name, date))
        all_sorted = sorted(all_pairs, key=lambda x: x[1])
        group.nomes_unicos = ", ".join(n for n, _ in all_sorted)

        # Recently active
        recent_sorted = sorted(recent_pairs, key=lambda x: x[1])
        group.apoiadores_ativos_ultimos_n_dias = ", ".join(n for n, _ in recent_sorted)

        return group

    @staticmethod
    def _build_sumario(summary: ApoiaSummary) -> ApoiaSummary:
        """Populate the sumario fields by combining both tiers.

        Args:
            summary: ApoiaSummary with tier_baixo and tier_premium already built.

        Returns:
            The same summary object with sumario fields filled.
        """
        # Unique ativos from both tiers (preserve order: baixo first)
        seen: set[str] = set()
        ativos: list[str] = []
        for name in [
            n.strip()
            for src in (
                summary.tier_baixo.apoiadores_com_status_ativo,
                summary.tier_premium.apoiadores_com_status_ativo,
            )
            for n in src.split(", ")
            if src
        ]:
            if name and name not in seen:
                seen.add(name)
                ativos.append(name)
        summary.sumario_ativos = ", ".join(ativos)

        # Unique recently-active from both tiers
        seen_r: set[str] = set()
        recentes: list[str] = []
        for name in [
            n.strip()
            for src in (
                summary.tier_baixo.apoiadores_ativos_ultimos_n_dias,
                summary.tier_premium.apoiadores_ativos_ultimos_n_dias,
            )
            for n in src.split(", ")
            if src
        ]:
            if name and name not in seen_r:
                seen_r.add(name)
                recentes.append(name)
        summary.sumario_ativos_recentes = ", ".join(recentes)

        # lista_completa = union(ativos + recentes), deduped
        seen_l: set[str] = set(ativos)
        lista = list(ativos)
        for name in recentes:
            if name and name not in seen_l:
                seen_l.add(name)
                lista.append(name)
        summary.sumario_lista_completa = ", ".join(lista)

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
            Dictionary matching the new two-tier YAML structure.
        """
        def _group_to_dict(group: RecompensaGroup) -> dict:
            d: dict[str, str] = {}
            if group.nomes_unicos:
                d["nomes_unicos"] = group.nomes_unicos
            if group.apoiadores_com_status_ativo:
                d["apoiadores_com_status_ativo"] = group.apoiadores_com_status_ativo
            if group.apoiadores_com_outros_status:
                d["apoiadores_com_outros_status"] = group.apoiadores_com_outros_status
            if group.apoiadores_ativos_ultimos_n_dias:
                d["apoiadores_ativos_ultimos_n_dias"] = group.apoiadores_ativos_ultimos_n_dias
            return d

        recompensas_dict: dict[str, dict] = {
            TIER_LOW_KEY: _group_to_dict(summary.tier_baixo),
            TIER_PREMIUM_KEY: _group_to_dict(summary.tier_premium),
        }

        sumario_dict: dict[str, str] = {}
        if summary.sumario_ativos:
            sumario_dict["ativos"] = summary.sumario_ativos
        if summary.sumario_ativos_recentes:
            sumario_dict["ativos_recentes"] = summary.sumario_ativos_recentes
        if summary.sumario_lista_completa:
            sumario_dict["lista_completa"] = summary.sumario_lista_completa

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
                "sumario": sumario_dict,
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
