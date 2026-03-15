"""Import tab — CSV file picker and processing trigger."""

import threading
from pathlib import Path
from tkinter import filedialog
from typing import Any, Callable

import customtkinter as ctk

from src.application.transform_use_case import TransformApoiadoresUseCase
from src.infrastructure.csv_reader import PolarsCSVReader
from src.infrastructure.json_writer import JSONArtifactWriter
from src.infrastructure.yaml_writer import YAMLArtifactWriter


class ImportTab:
    """Tab for importing and processing a CSV file."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        colors: dict[str, str],
        on_done: Callable[[dict, list[dict]], None],
    ) -> None:
        """Initialize the import tab.

        Args:
            parent: Parent frame from the TabView.
            colors: Color palette dict.
            on_done: Callback with (yaml_data, metadata) when processing completes.
        """
        self._colors = colors
        self._on_done = on_done
        self._csv_path: Path | None = None

        parent.configure(fg_color=colors["bg_dark"])

        # -- Center container --
        container = ctk.CTkFrame(parent, fg_color=colors["bg_dark"])
        container.place(relx=0.5, rely=0.45, anchor="center")

        # -- Icon / title --
        icon_label = ctk.CTkLabel(
            container,
            text="📄",
            font=ctk.CTkFont(size=48),
        )
        icon_label.pack(pady=(0, 8))

        title = ctk.CTkLabel(
            container,
            text="Importar base de apoiadores",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=colors["text_primary"],
        )
        title.pack(pady=(0, 4))

        desc = ctk.CTkLabel(
            container,
            text="Selecione o arquivo CSV exportado do Apoia-se",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=colors["text_secondary"],
        )
        desc.pack(pady=(0, 24))

        # -- File picker row --
        picker_frame = ctk.CTkFrame(container, fg_color=colors["bg_card"], corner_radius=12)
        picker_frame.pack(fill="x", padx=20, pady=(0, 8))

        self._file_label = ctk.CTkLabel(
            picker_frame,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_muted"],
            anchor="w",
        )
        self._file_label.pack(side="left", padx=16, pady=14, fill="x", expand=True)

        browse_btn = ctk.CTkButton(
            picker_frame,
            text="Escolher arquivo",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color="#0D0D0D",
            corner_radius=8,
            width=160,
            command=self._browse_file,
        )
        browse_btn.pack(side="right", padx=12, pady=10)

        # -- File info --
        self._info_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=colors["text_secondary"],
        )
        self._info_label.pack(pady=(0, 20))

        # -- Process button --
        self._process_btn = ctk.CTkButton(
            container,
            text="⚡  Processar",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color="#0D0D0D",
            corner_radius=10,
            height=48,
            width=280,
            state="disabled",
            command=self._process,
        )
        self._process_btn.pack(pady=(0, 12))

        # -- Status --
        self._status_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["text_secondary"],
        )
        self._status_label.pack(pady=(0, 8))

    def _browse_file(self) -> None:
        """Open a file dialog to select a CSV file."""
        path = filedialog.askopenfilename(
            title="Selecionar arquivo CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._csv_path = Path(path)
            name = self._csv_path.name
            self._file_label.configure(
                text=f"📄  {name}",
                text_color=self._colors["text_primary"],
            )

            # Count lines for preview
            try:
                with open(self._csv_path, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f) - 1  # exclude header
                self._info_label.configure(
                    text=f"{line_count:,} apoiadores encontrados no arquivo"
                )
            except Exception:
                self._info_label.configure(text="")

            self._process_btn.configure(state="normal")
            self._status_label.configure(text="")

    def _process(self) -> None:
        """Run the ETL pipeline in a background thread."""
        if self._csv_path is None:
            return

        self._process_btn.configure(state="disabled", text="⏳  Processando...")
        self._status_label.configure(
            text="Analisando dados...",
            text_color=self._colors["accent"],
        )

        def _run() -> None:
            try:
                reader = PolarsCSVReader()
                yaml_writer = YAMLArtifactWriter()
                json_writer = JSONArtifactWriter()
                uc = TransformApoiadoresUseCase(reader, yaml_writer, json_writer)

                # We need the yaml_data and metadata without writing to disk
                # So we read, build summary, and convert — reusing use case internals
                apoiadores = reader.read(self._csv_path)  # type: ignore
                from datetime import datetime

                ref = datetime.now()
                summary = uc._build_summary(apoiadores, ref)
                yaml_data = uc._summary_to_dict(summary)
                metadata = uc._build_metadata(apoiadores)

                # Also save artifacts to disk
                from pathlib import Path as P

                artifacts_dir = self._csv_path.parent / "artifacts"
                uc.execute(self._csv_path, artifacts_dir, ref)  # type: ignore

                # Callback on main thread
                self._process_btn.after(0, lambda: self._finish_ok(yaml_data, metadata))

            except FileNotFoundError as e:
                self._process_btn.after(
                    0, lambda: self._finish_error(str(e))
                )
            except Exception as e:
                self._process_btn.after(
                    0, lambda: self._finish_error(f"Erro inesperado: {e}")
                )

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _finish_ok(self, yaml_data: dict, metadata: list[dict]) -> None:
        """Handle successful processing."""
        self._process_btn.configure(state="normal", text="⚡  Processar")
        self._status_label.configure(
            text="✅  Processamento concluído com sucesso!",
            text_color=self._colors["success"],
        )
        self._on_done(yaml_data, metadata)

    def _finish_error(self, msg: str) -> None:
        """Handle processing error."""
        self._process_btn.configure(state="normal", text="⚡  Processar")
        self._status_label.configure(
            text=f"❌  {msg}",
            text_color=self._colors["error"],
        )
