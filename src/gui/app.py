"""Main application window for the Apoia-se Exporter GUI."""

import customtkinter as ctk

from src.gui.import_tab import ImportTab
from src.gui.dashboard_tab import DashboardTab
from src.gui.search_tab import SearchTab

# -- Theme / Color Palette --
# Dark mode + dark yellow / amber futuristic
COLORS = {
    "bg_dark": "#0D0D0D",
    "bg_card": "#1A1A1A",
    "bg_input": "#252525",
    "accent": "#D4A017",          # Dark gold/amber
    "accent_hover": "#E6B422",
    "accent_dim": "#8B6914",
    "text_primary": "#F0E6D3",
    "text_secondary": "#9E9E9E",
    "text_muted": "#666666",
    "success": "#4CAF50",
    "error": "#E53935",
    "border": "#333333",
}


class SplashScreen(ctk.CTkToplevel):
    """Loading splash screen shown while the main app initializes."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)

        # -- Borderless, always on top --
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORS["bg_dark"])

        # -- Size and centering --
        width, height = 420, 260
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # -- Outer border frame --
        border = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        border.pack(fill="both", expand=True, padx=2, pady=2)

        # -- App icon --
        icon_label = ctk.CTkLabel(
            border,
            text="⚡",
            font=ctk.CTkFont(size=48),
        )
        icon_label.pack(pady=(32, 8))

        # -- Title --
        title = ctk.CTkLabel(
            border,
            text="APOIA-SE EXPORTER",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLORS["accent"],
        )
        title.pack(pady=(0, 4))

        # -- Version --
        version = ctk.CTkLabel(
            border,
            text="v0.2.0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_muted"],
        )
        version.pack(pady=(0, 16))

        # -- Loading text --
        self._status = ctk.CTkLabel(
            border,
            text="Carregando...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
        )
        self._status.pack(pady=(0, 8))

        # -- Progress bar (indeterminate) --
        self._progress = ctk.CTkProgressBar(
            border,
            width=300,
            height=6,
            fg_color=COLORS["bg_input"],
            progress_color=COLORS["accent"],
            corner_radius=3,
            mode="indeterminate",
        )
        self._progress.pack(pady=(0, 24))
        self._progress.start()

        # Force rendering
        self.update_idletasks()
        self.update()


class ApoiaseApp(ctk.CTk):
    """Main GUI application for the Apoia-se Exporter."""

    def __init__(self) -> None:
        super().__init__()

        # -- Hide main window while loading --
        self.withdraw()

        # -- Show splash screen --
        self._splash = SplashScreen(self)

        # -- Window config --
        self.title("Apoia-se Exporter")
        self.geometry("1080x720")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        # -- CustomTkinter appearance --
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # -- Header --
        self._build_header()

        # -- Tab View --
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_card"],
            segmented_button_unselected_hover_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            corner_radius=12,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        tab_import = self.tabview.add("📂  Importar CSV")
        tab_dashboard = self.tabview.add("📊  Dashboard")
        tab_search = self.tabview.add("🔍  Buscar")

        # -- Build tabs --
        self.import_tab = ImportTab(tab_import, COLORS, self._on_process_done)
        self.dashboard_tab = DashboardTab(tab_dashboard, COLORS)
        self.search_tab = SearchTab(tab_search, COLORS)

        # -- Dismiss splash and show main window --
        self.after(200, self._dismiss_splash)

    def _dismiss_splash(self) -> None:
        """Destroy splash screen and show the main window."""
        if hasattr(self, "_splash") and self._splash is not None:
            self._splash.destroy()
            self._splash = None
        self.deiconify()

    def _build_header(self) -> None:
        """Build the top header bar."""
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=56, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="⚡ APOIA-SE EXPORTER",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["accent"],
        )
        title.pack(side="left", padx=20, pady=12)

        subtitle = ctk.CTkLabel(
            header,
            text="Ferramenta de análise de apoiadores",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
        )
        subtitle.pack(side="left", padx=0, pady=12)

    def _on_process_done(self, yaml_data: dict, metadata: list[dict]) -> None:
        """Callback when CSV processing completes.

        Args:
            yaml_data: The computed YAML summary dict.
            metadata: List of supporter metadata dicts.
        """
        self.dashboard_tab.populate(yaml_data)
        self.search_tab.populate(metadata)
        self.tabview.set("📊  Dashboard")


def run_app() -> None:
    """Entry point to launch the GUI."""
    app = ApoiaseApp()
    app.mainloop()
