"""Search tab — filterable table for JSON metadata."""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk


class SearchTab:
    """Tab for searching and browsing supporter metadata."""

    def __init__(self, parent: ctk.CTkFrame, colors: dict[str, str]) -> None:
        """Initialize the search tab.

        Args:
            parent: Parent frame from the TabView.
            colors: Color palette dict.
        """
        self._colors = colors
        self._parent = parent
        self._all_data: list[dict[str, str]] = []

        parent.configure(fg_color=colors["bg_dark"])

        # -- Persistent wrapper --
        self._wrapper = ctk.CTkFrame(parent, fg_color=colors["bg_dark"])
        self._wrapper.pack(fill="both", expand=True)

        # -- Placeholder --
        self._placeholder = ctk.CTkLabel(
            self._wrapper,
            text="Importe um CSV primeiro para buscar apoiadores",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=colors["text_muted"],
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._built = False

    def _clear_wrapper(self) -> None:
        """Destroy all children inside the wrapper frame."""
        for child in self._wrapper.winfo_children():
            child.pack_forget()
            child.place_forget()
            child.destroy()

    def populate(self, metadata: list[dict[str, str]]) -> None:
        """Populate the search tab with metadata.

        Args:
            metadata: List of dicts with id, nome, email.
        """
        self._all_data = metadata

        if not self._built:
            # First time: remove placeholder and build UI
            self._clear_wrapper()
            self._build_ui()
            self._built = True

        self._refresh_table(self._all_data)

    def _build_ui(self) -> None:
        """Build the search bar and results table."""
        # -- Search bar --
        search_frame = ctk.CTkFrame(
            self._wrapper,
            fg_color=self._colors["bg_card"],
            corner_radius=12,
        )
        search_frame.pack(fill="x", padx=16, pady=(16, 8))

        search_icon = ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=16),
        )
        search_icon.pack(side="left", padx=(14, 0), pady=10)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)

        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Buscar por ID, nome ou email...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=self._colors["bg_input"],
            border_color=self._colors["border"],
            text_color=self._colors["text_primary"],
            placeholder_text_color=self._colors["text_muted"],
            corner_radius=8,
            height=36,
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        self._count_label = ctk.CTkLabel(
            search_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self._colors["text_secondary"],
        )
        self._count_label.pack(side="right", padx=14, pady=10)

        # -- Results table (using ttk.Treeview for performance) --
        table_frame = ctk.CTkFrame(
            self._wrapper,
            fg_color=self._colors["bg_card"],
            corner_radius=12,
        )
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Style the Treeview to match dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.Treeview",
            background=self._colors["bg_card"],
            foreground=self._colors["text_primary"],
            fieldbackground=self._colors["bg_card"],
            borderwidth=0,
            font=("Segoe UI", 11),
            rowheight=32,
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=self._colors["bg_input"],
            foreground=self._colors["accent"],
            font=("Segoe UI", 12, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", self._colors["accent_dim"])],
            foreground=[("selected", self._colors["text_primary"])],
        )
        style.map(
            "Dark.Treeview.Heading",
            background=[("active", self._colors["bg_input"])],
        )

        columns = ("id", "nome", "email")
        self._tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
        )

        self._tree.heading("id", text="ID")
        self._tree.heading("nome", text="Nome")
        self._tree.heading("email", text="Email")

        self._tree.column("id", width=120, minwidth=80, anchor="w")
        self._tree.column("nome", width=300, minwidth=150, anchor="w")
        self._tree.column("email", width=350, minwidth=150, anchor="w")

        scrollbar = ctk.CTkScrollbar(
            table_frame,
            command=self._tree.yview,
            fg_color=self._colors["bg_card"],
            button_color=self._colors["border"],
            button_hover_color=self._colors["text_muted"],
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=12)

    def _on_search(self, *args: object) -> None:
        """Filter the table based on search query."""
        query = self._search_var.get().strip().lower()

        if not query:
            self._refresh_table(self._all_data)
            return

        filtered = [
            row for row in self._all_data
            if query in row.get("id", "").lower()
            or query in row.get("nome", "").lower()
            or query in row.get("email", "").lower()
        ]
        self._refresh_table(filtered)

    def _refresh_table(self, data: list[dict[str, str]]) -> None:
        """Clear and repopulate the table.

        Args:
            data: List of metadata dicts to display.
        """
        for item in self._tree.get_children():
            self._tree.delete(item)

        for row in data:
            self._tree.insert("", "end", values=(
                row.get("id", ""),
                row.get("nome", ""),
                row.get("email", ""),
            ))

        self._count_label.configure(text=f"{len(data):,} resultados")
