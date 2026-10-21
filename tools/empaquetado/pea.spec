# PyInstaller: dos entradas que comparten las bibliotecas de una sola carpeta.
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

raiz = Path(SPECPATH).resolve().parents[1]
datos = collect_data_files("pea")
analisis = Analysis(
    [str(raiz / "tools/empaquetado/entrada_gui.py"), str(raiz / "tools/empaquetado/entrada_cli.py")],
    pathex=[str(raiz / "src")], datas=datos, excludes=["pytest", "ruff"],
)
entradas = {entrada[0]: entrada for entrada in analisis.scripts if entrada[0] in {"entrada_gui", "entrada_cli"}}
if set(entradas) != {"entrada_gui", "entrada_cli"}:
    raise RuntimeError("PyInstaller no encontro las dos entradas esperadas.")
hooks = [entrada for entrada in analisis.scripts if entrada[0] not in entradas]
biblioteca = PYZ(analisis.pure)
exe_gui = EXE(biblioteca, hooks + [entradas["entrada_gui"]], [], exclude_binaries=True, name="pea-gui", console=False)
exe_cli = EXE(biblioteca, hooks + [entradas["entrada_cli"]], [], exclude_binaries=True, name="pea-cli", console=True)
COLLECT(exe_gui, exe_cli, analisis.binaries, analisis.datas, name="PEAi-Python")
