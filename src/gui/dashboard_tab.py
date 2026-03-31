"""Dashboard tab — two-tier panels (0–59 / 60+) with sumário, copy buttons."""

import customtkinter as ctk

TIER_LOW_KEY = "0-59-pesetas"
TIER_PREMIUM_KEY = "60-pesetas"


class DashboardTab:
    """Tab showing the YAML summary as a visual dashboard."""

    def __init__(self, parent: ctk.CTkFrame, colors: dict[str, str]) -> None:
        """Initialize the dashboard tab.

        Args:
            parent: Parent frame from the TabView.
            colors: Color palette dict.
        """
        self._colors = colors
        self._parent = parent
        parent.configure(fg_color=colors["bg_dark"])

        # -- Persistent wrapper that holds either placeholder or content --
        self._wrapper = ctk.CTkFrame(parent, fg_color=colors["bg_dark"])
        self._wrapper.pack(fill="both", expand=True)

        # -- Placeholder --
        self._placeholder = ctk.CTkLabel(
            self._wrapper,
            text="Importe um CSV primeiro para ver os resultados",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=colors["text_muted"],
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _clear_wrapper(self) -> None:
        """Destroy all children inside the wrapper frame."""
        for child in self._wrapper.winfo_children():
            child.pack_forget()
            child.place_forget()
            child.destroy()

    def populate(self, yaml_data: dict) -> None:
        """Populate the dashboard with processed data.

        Args:
            yaml_data: The YAML summary dict from the use case.
        """
        self._clear_wrapper()

        content = ctk.CTkScrollableFrame(
            self._wrapper,
            fg_color=self._colors["bg_dark"],
            corner_radius=0,
        )
        content.pack(fill="both", expand=True, padx=0, pady=0)

        apoia = yaml_data.get("apoia-se", {})

        # -- Stats cards --
        self._build_stats_row(content, apoia)

        self._divider(content)

        # -- Section title: Recompensas --
        self._section_label(content, "Recompensas por categoria")

        recompensas = apoia.get("recompensas", {})

        # Tier baixo (0–59)
        low = recompensas.get(TIER_LOW_KEY, {})
        self._build_tier_card(
            content,
            title="🥈  Tier Baixo  (0 – 59 pesetas)",
            groups=low,
            accent="#64B5F6",
        )

        # Tier premium (60+)
        premium = recompensas.get(TIER_PREMIUM_KEY, {})
        self._build_tier_card(
            content,
            title="🏆  Tier Premium  (60+ pesetas)",
            groups=premium,
            accent=self._colors["accent"],
        )

        self._divider(content)

        # -- Sumário --
        self._section_label(content, "Sumário")
        sumario = apoia.get("sumario", {})
        self._build_sumario_card(content, sumario)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _divider(self, parent: ctk.CTkScrollableFrame) -> None:
        ctk.CTkFrame(
            parent,
            fg_color=self._colors["border"],
            height=1,
        ).pack(fill="x", padx=16, pady=(16, 8))

    def _section_label(self, parent: ctk.CTkScrollableFrame, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self._colors["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=20, pady=(8, 12))

    def _build_stats_row(
        self, parent: ctk.CTkScrollableFrame, apoia: dict
    ) -> None:
        """Build the row of statistics cards."""
        stats_frame = ctk.CTkFrame(
            parent,
            fg_color=self._colors["bg_dark"],
        )
        stats_frame.pack(fill="x", padx=16, pady=(16, 0))

        dias = apoia.get("dias_filtro", 30)

        cards = [
            ("Apoiadores Ativos", apoia.get("total_apoiadores", 0), self._colors["accent"]),
            ("Pendentes", apoia.get("total_pendente", 0), "#FF9800"),
            ("Inadimplentes", apoia.get("total_inadimplente", 0), self._colors["error"]),
            (f"Ativos ({dias}d)", apoia.get("total_ativos_recentes", 0), "#29B6F6"),
            ("Recebido (mês atual)", f"R$ {apoia.get('total_recebido_mes_atual', 0):,.2f}", self._colors["success"]),
            ("Recebido (mês anterior)", f"R$ {apoia.get('total_recebido_mes_anterior', 0):,.2f}", self._colors["text_secondary"]),
        ]

        for i, (label, value, color) in enumerate(cards):
            stats_frame.columnconfigure(i, weight=1)
            card = ctk.CTkFrame(
                stats_frame,
                fg_color=self._colors["bg_card"],
                corner_radius=12,
                border_width=1,
                border_color=self._colors["border"],
            )
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")

            ctk.CTkLabel(
                card,
                text=str(value),
                font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                text_color=color,
            ).pack(padx=12, pady=(14, 2))

            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self._colors["text_secondary"],
            ).pack(padx=12, pady=(0, 12))

    def _build_tier_card(
        self,
        parent: ctk.CTkScrollableFrame,
        title: str,
        groups: dict,
        accent: str,
    ) -> None:
        """Build a single tier card with its status sub-rows.

        Args:
            parent: Scrollable content frame.
            title: Display title for the tier card.
            groups: Dict of group fields from the YAML tier section.
            accent: Accent colour for the tier header.
        """
        card = ctk.CTkFrame(
            parent,
            fg_color=self._colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self._colors["border"],
        )
        card.pack(fill="x", padx=20, pady=6)

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=accent,
            anchor="w",
        ).pack(side="left")

        # Sub-rows for each field
        sub_rows = [
            ("nomes_unicos", "Nomes únicos", self._colors["text_primary"]),
            ("apoiadores_com_status_ativo", "Ativos", self._colors["success"]),
            ("apoiadores_com_outros_status", "Outros status", "#FF9800"),
            ("apoiadores_ativos_ultimos_n_dias", "Ativos recentes", "#29B6F6"),
        ]

        for field_key, display_name, color in sub_rows:
            names_str = groups.get(field_key, "")
            if not names_str:
                continue
            self._build_names_row(card, display_name, names_str, color)

        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _build_sumario_card(
        self, parent: ctk.CTkScrollableFrame, sumario: dict
    ) -> None:
        """Build the sumário card with combined names from both tiers.

        Args:
            parent: Scrollable content frame.
            sumario: The sumario dict from the YAML output.
        """
        card = ctk.CTkFrame(
            parent,
            fg_color=self._colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self._colors["border"],
        )
        card.pack(fill="x", padx=20, pady=6)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header,
            text="📊  Sumário Geral",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self._colors["text_primary"],
            anchor="w",
        ).pack(side="left")

        sumario_rows = [
            ("ativos", "Ativos (todos os tiers)", self._colors["success"]),
            ("ativos_recentes", "Ativos recentes (todos)", "#29B6F6"),
            ("lista_completa", "Lista completa", self._colors["accent"]),
        ]

        for field_key, display_name, color in sumario_rows:
            names_str = sumario.get(field_key, "")
            if not names_str:
                continue
            self._build_names_row(card, display_name, names_str, color)

        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _build_names_row(
        self,
        card: ctk.CTkFrame,
        display_name: str,
        names_str: str,
        color: str,
    ) -> None:
        """Build a label + count + copy button row, then the names text below.

        Args:
            card: Parent card frame.
            display_name: Human-readable label for this group.
            names_str: Comma-separated names string.
            color: Colour for the label dot and count.
        """
        name_count = len([n for n in names_str.split(", ") if n.strip()])

        group_frame = ctk.CTkFrame(card, fg_color="transparent")
        group_frame.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(
            group_frame,
            text=f"● {display_name} ({name_count})",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=color,
            anchor="w",
        ).pack(side="left")

        copy_btn = ctk.CTkButton(
            group_frame,
            text="📋 Copiar",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self._colors["bg_input"],
            hover_color=self._colors["border"],
            text_color=self._colors["text_secondary"],
            corner_radius=6,
            width=80,
            height=26,
        )
        copy_btn.configure(
            command=lambda ns=names_str, b=copy_btn: self._copy_names(ns, b)
        )
        copy_btn.pack(side="right")

        ctk.CTkLabel(
            card,
            text=names_str,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self._colors["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=32, pady=(0, 4))

    def _copy_names(self, names: str, btn: ctk.CTkButton | None) -> None:
        """Copy names to clipboard and show feedback.

        Args:
            names: Comma-separated name string.
            btn: The button to update with feedback.
        """
        self._parent.clipboard_clear()
        self._parent.clipboard_append(names)

        if btn is not None:
            original_text = btn.cget("text")
            btn.configure(text="✅ Copiado!", text_color=self._colors["success"])
            btn.after(1500, lambda: btn.configure(
                text=original_text,
                text_color=self._colors["text_secondary"],
            ))
