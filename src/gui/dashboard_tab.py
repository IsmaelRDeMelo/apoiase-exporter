"""Dashboard tab — statistics cards and reward tier breakdown with copy buttons."""

import customtkinter as ctk


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
        # Nuke everything inside wrapper (placeholder or previous content)
        self._clear_wrapper()

        # Create scrollable content inside wrapper
        content = ctk.CTkScrollableFrame(
            self._wrapper,
            fg_color=self._colors["bg_dark"],
            corner_radius=0,
        )
        content.pack(fill="both", expand=True, padx=0, pady=0)

        apoia = yaml_data.get("apoia-se", {})

        # -- Stats cards --
        self._build_stats_row(content, apoia)

        # -- Divider --
        divider = ctk.CTkFrame(
            content,
            fg_color=self._colors["border"],
            height=1,
        )
        divider.pack(fill="x", padx=16, pady=(16, 8))

        # -- Section title --
        section = ctk.CTkLabel(
            content,
            text="Recompensas por categoria",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self._colors["text_primary"],
            anchor="w",
        )
        section.pack(fill="x", padx=20, pady=(8, 12))

        # -- Reward tier cards --
        recompensas = apoia.get("recompensas", {})
        for tier_key, groups in recompensas.items():
            self._build_tier_card(content, tier_key, groups)

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

            val_label = ctk.CTkLabel(
                card,
                text=str(value),
                font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                text_color=color,
            )
            val_label.pack(padx=12, pady=(14, 2))

            desc_label = ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self._colors["text_secondary"],
            )
            desc_label.pack(padx=12, pady=(0, 12))

    def _build_tier_card(
        self,
        parent: ctk.CTkScrollableFrame,
        tier_key: str,
        groups: dict,
    ) -> None:
        """Build a single reward tier card with status groups.

        Args:
            parent: Scrollable content frame to add the card to.
            tier_key: The tier key (e.g. '5-pesetas').
            groups: Dict of status groups with name lists.
        """
        card = ctk.CTkFrame(
            parent,
            fg_color=self._colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self._colors["border"],
        )
        card.pack(fill="x", padx=20, pady=6)

        # -- Tier header --
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        tier_label = ctk.CTkLabel(
            header,
            text=f"🏆  {tier_key.upper()}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self._colors["accent"],
            anchor="w",
        )
        tier_label.pack(side="left")

        # -- Status groups --
        status_labels = {
            "apoiadores_com_status_ativo": ("Ativos", self._colors["success"]),
            "apoiadores_com_status_pendente": ("Pendentes", "#FF9800"),
            "apoiadores_com_status_inadimplente": ("Inadimplentes", self._colors["error"]),
            "apoiadores_com_status_aguardando_confirmacao": ("Aguardando", "#FF9800"),
            "apoiadores_ativos_ultimos_n_dias": ("Ativos Recentes", "#29B6F6"),
        }

        for status_key, (display_name, color) in status_labels.items():
            names_str = groups.get(status_key, "")
            if not names_str:
                continue

            group_frame = ctk.CTkFrame(card, fg_color="transparent")
            group_frame.pack(fill="x", padx=16, pady=(4, 2))

            # Count names
            name_count = len(names_str.split(", "))

            status_tag = ctk.CTkLabel(
                group_frame,
                text=f"● {display_name} ({name_count})",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=color,
                anchor="w",
            )
            status_tag.pack(side="left")

            # Copy button
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
                command=lambda ns=names_str, btn=None: self._copy_names(ns, btn),
            )
            # Store ref for feedback
            copy_btn.configure(
                command=lambda ns=names_str, b=copy_btn: self._copy_names(ns, b)
            )
            copy_btn.pack(side="right")

            # Names text
            names_label = ctk.CTkLabel(
                card,
                text=names_str,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self._colors["text_secondary"],
                anchor="w",
                justify="left",
                wraplength=900,
            )
            names_label.pack(fill="x", padx=32, pady=(0, 4))

        # Bottom padding
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

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
