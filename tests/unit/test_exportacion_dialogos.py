"""Pruebas de la exportación (PDF, PNG y CSV): explorador de archivos, rutas y mensajes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from pea.gui import dialogos_exportacion as dlg
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.exportador_visual import guardar_csv_profesional
from pea.gui.pantallas.grupos import PantallaGrupos
from pea.gui.pantallas.inicio import PantallaInicio
from pea.gui.pantallas.investigadores import PantallaInvestigadores
from pea.gui.pantallas.productos import PantallaProductos
from pea.gui.pantallas.redes import PantallaRedes
from pea.servicios.servicio_aplicacion import ServicioAplicacion


@pytest.fixture
def servicio() -> ServicioAplicacion:
    s = ServicioAplicacion()
    s.cargar_demostracion()
    return s


@pytest.fixture
def avisos(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Captura los avisos (tipo, mensaje) que las pantallas intentan mostrar."""
    capturados: list[tuple[str, str]] = []

    def falso(_widget: Any, mensaje: str, tipo: str = "info", titulo: str | None = None) -> None:
        capturados.append((tipo, mensaje))

    monkeypatch.setattr(GestorAvisos, "mostrar_desde", falso)
    return capturados


def _simular_explorador(monkeypatch: pytest.MonkeyPatch, elegido: Path | None) -> list[str]:
    """Sustituye el explorador de archivos: devuelve la ruta elegida o simula una cancelación."""
    llamadas: list[str] = []

    def guardar(_padre: Any, titulo: str, inicial: str, _filtro: str) -> tuple[str, str]:
        llamadas.append(f"{titulo}|{inicial}")
        return (str(elegido) if elegido else "", "")

    def carpeta(_padre: Any, titulo: str, _inicial: str) -> str:
        llamadas.append(titulo)
        return str(elegido) if elegido else ""

    monkeypatch.setattr(dlg.QFileDialog, "getSaveFileName", staticmethod(guardar))
    monkeypatch.setattr(dlg.QFileDialog, "getExistingDirectory", staticmethod(carpeta))
    return llamadas


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def test_destino_explicito_ignora_booleanos_de_senales() -> None:
    assert dlg.destino_explicito(False) is None
    assert dlg.destino_explicito(True) is None
    assert dlg.destino_explicito(None) is None
    assert dlg.destino_explicito("   ") is None
    assert dlg.destino_explicito("reporte.pdf") == Path("reporte.pdf")


def test_nombre_archivo_seguro_sin_tildes_ni_espacios() -> None:
    nombre = dlg.nombre_archivo_seguro("Directorio de Investigación: Ñandú/2024", ".pdf", con_fecha=False)
    assert nombre == "directorio_de_investigacion_nandu_2024.pdf"


def test_asegurar_extension_agrega_la_faltante() -> None:
    assert dlg.asegurar_extension(Path("a/b"), ".csv") == Path("a/b.csv")
    assert dlg.asegurar_extension(Path("a/b.CSV"), ".csv") == Path("a/b.CSV")


def test_exportador_rechaza_destino_booleano(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        guardar_csv_profesional(False, ["A"], [("1",)])  # type: ignore[arg-type]
    assert not (tmp_path / "False").exists()
    assert not Path("False").exists()


def test_mensaje_error_es_comprensible() -> None:
    assert "otra aplicación" in dlg.mensaje_error(PermissionError())
    assert "ya no existe" in dlg.mensaje_error(FileNotFoundError())


# ---------------------------------------------------------------------------
# Inicio: PDF, CSV y PNG (incluye el caso que fallaba con «_lbl_subtitulo_ambito»)
# ---------------------------------------------------------------------------


def test_inicio_exporta_pdf_csv_y_png_sin_errores(
    qapp: QApplication, servicio: ServicioAplicacion, avisos: list[tuple[str, str]], tmp_path: Path
) -> None:
    pantalla = PantallaInicio(servicio=servicio)
    pantalla.resize(QSize(1400, 900))
    qapp.processEvents()

    pdf, csv, png = tmp_path / "r.pdf", tmp_path / "d.csv", tmp_path / "p.png"
    pantalla.exportar_pdf(pdf)
    pantalla.exportar_csv(csv)
    pantalla.exportar_png(png)
    pantalla.exportar_png_individuales(tmp_path / "graficos")

    assert [t for t, _ in avisos] == ["exito"] * 4, avisos
    assert pdf.stat().st_size > 5_000
    assert png.stat().st_size > 5_000
    assert csv.read_bytes().startswith(b"\xef\xbb\xbf")
    assert len(list((tmp_path / "graficos").glob("*.png"))) == 3
    assert not Path("False").exists()


def test_inicio_menu_abre_el_explorador_y_guarda_donde_elige_el_usuario(
    qapp: QApplication,
    servicio: ServicioAplicacion,
    avisos: list[tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pantalla = PantallaInicio(servicio=servicio)
    qapp.processEvents()
    elegido = tmp_path / "mi_reporte.pdf"
    llamadas = _simular_explorador(monkeypatch, elegido)

    acciones = pantalla._menu_exportar.actions()
    acciones[0].trigger()  # Reporte ejecutivo (PDF)

    assert len(llamadas) == 1, "debe abrirse el explorador de archivos"
    assert elegido.exists()
    assert not Path("False").exists()
    assert avisos[-1][0] == "exito"
    assert "mi_reporte.pdf" in avisos[-1][1]


def test_inicio_cancelar_el_explorador_no_crea_archivos(
    qapp: QApplication,
    servicio: ServicioAplicacion,
    avisos: list[tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pantalla = PantallaInicio(servicio=servicio)
    qapp.processEvents()
    llamadas = _simular_explorador(monkeypatch, None)

    for accion in pantalla._menu_exportar.actions():
        accion.trigger()

    assert len(llamadas) == 4
    assert avisos == []
    assert list(tmp_path.iterdir()) == []
    assert not Path("False").exists()


# ---------------------------------------------------------------------------
# Resto de pantallas con la misma garantía
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("clase", "metodos"),
    [
        (PantallaInvestigadores, ("_al_exportar_directorio_pdf", "_al_exportar_ficha_png", "_al_exportar_directorio_csv")),
        (PantallaGrupos, ("_exportar_directorio_pdf", "_exportar_grupo_png", "_exportar_directorio_csv")),
        (PantallaProductos, ("_exportar_catalogo_pdf", "_exportar_catalogo_csv")),
        (PantallaRedes, ("exportar_pdf", "exportar_png", "exportar_csv")),
    ],
)
def test_pantallas_exportan_a_la_ruta_elegida_y_nunca_a_false(
    qapp: QApplication,
    servicio: ServicioAplicacion,
    avisos: list[tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    clase: Any,
    metodos: tuple[str, ...],
) -> None:
    pantalla = clase(servicio=servicio)
    pantalla.resize(QSize(1400, 900))
    qapp.processEvents()

    for metodo in metodos:
        # Un booleano (lo que emite triggered/clicked) debe tratarse como «sin destino»: abre el explorador.
        llamadas = _simular_explorador(monkeypatch, None)
        getattr(pantalla, metodo)(False)
        assert len(llamadas) == 1, f"{metodo} debe abrir el explorador de archivos"

        sufijo = ".pdf" if "pdf" in metodo else ".csv" if "csv" in metodo else ".png"
        destino = tmp_path / f"{metodo}{sufijo}"
        avisos.clear()
        getattr(pantalla, metodo)(destino)
        assert [t for t, _ in avisos] == ["exito"], (metodo, avisos)
        assert destino.exists() and destino.stat().st_size > 0, metodo

    assert not Path("False").exists()

