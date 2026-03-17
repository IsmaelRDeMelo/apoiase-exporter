"""Build script to create a standalone .exe using PyInstaller."""

import subprocess
import sys
from pathlib import Path


def build() -> None:
    """Run PyInstaller to build ApoiaseExporter.exe."""
    # Find customtkinter package path for asset bundling
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent
    project_dir = Path(__file__).parent

    version_file = project_dir / "version_info.txt"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ApoiaseExporter",
        "--add-data", f"{ctk_path};customtkinter/",
        "--hidden-import", "polars",
        "--hidden-import", "yaml",
        "--hidden-import", "customtkinter",
    ]

    # Add version info if the file exists
    if version_file.exists():
        cmd.extend(["--version-file", str(version_file)])

    cmd.append("main.py")

    print("Building ApoiaseExporter.exe ...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("\nBuild complete! -> dist/ApoiaseExporter.exe")


if __name__ == "__main__":
    build()
