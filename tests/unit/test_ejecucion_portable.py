"""El comparador debe usar los ejecutables distribuidos al evaluar el paquete."""

import sys
from pathlib import Path

from pea.servicios.servicio_verificacion_cruzada import ServicioVerificacionCruzada


def test_comparador_portable_encuentra_cli_y_cpp_sin_interprete(tmp_path, monkeypatch):
    python = tmp_path / "PEAi-Python" / "pea-gui.exe"
    cpp = tmp_path / "PEAi-Cpp" / "pea-cpp.exe"
    cpp.parent.mkdir()
    cpp.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(python))
    monkeypatch.delenv("PEA_CPP_EXE", raising=False)
    servicio = ServicioVerificacionCruzada()
    assert servicio.raiz == tmp_path
    assert servicio.comando_python() == [str(python.with_name("pea-cli.exe"))]
    assert servicio.ruta_cpp() == cpp


def test_comparador_portable_no_agrega_msys_y_excluye_credenciales(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("PEA_USUARIO_CLAVE", "valor-ficticio")
    monkeypatch.setenv("PEA_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_ficticia")
    servicio = ServicioVerificacionCruzada(raiz_proyecto=Path(tmp_path))
    entorno = servicio._entorno_hijo(usar_base=False)
    assert entorno["PATH"] == str(tmp_path)
    assert "PEA_USUARIO_CLAVE" not in entorno
    assert "PEA_SUPABASE_PUBLISHABLE_KEY" not in entorno
