"""Herramienta de galería visual para componentes de la GUI de PEA-i (Sección 8).

Permite visualizar todos los componentes estilizados y generar una captura
offscreen de alta fidelidad en datos/capturas/galeria.png para auditoría de diseño.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Asegurar que src está en el PYTHONPATH
RUTA_RAIZ = Path(__file__).resolve().parent.parent
if str(RUTA_RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RUTA_RAIZ / "src"))

from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes import (  # noqa: E402
    Avatar,
    CampoBusqueda,
    ChipVentana,
    Esqueleto,
    EstadoVacio,
    FichaKPI,
    GestorAvisos,
    Pildora,
    SelectorSegmentado,
    Tarjeta,
)
from pea.gui.estilo import (  # noqa: E402
    HOJA_ESTILOS_GLOBAL,
    MARGEN_CONTENIDO,
    SEPARACION_TARJETAS,
    TAMANO_TITULO_PANTALLA,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.recursos import cargar_pixmap  # noqa: E402
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios  # noqa: E402


class VentanaGaleria(QMainWindow):
    """Ventana contenedora que exhibe todos los componentes reutilizables."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Galería de Componentes GUI · PEA-i")
        self.resize(1360, 880)

        widget_central = QWidget(self)
        widget_central.setObjectName("fondo")
        self.setCentralWidget(widget_central)

        layout_raiz = QVBoxLayout(widget_central)
        layout_raiz.setContentsMargins(MARGEN_CONTENIDO, MARGEN_CONTENIDO, MARGEN_CONTENIDO, MARGEN_CONTENIDO)
        layout_raiz.setSpacing(SEPARACION_TARJETAS)

        # -------------------------------------------------------------------
        # Cabecera de la galería
        # -------------------------------------------------------------------
        cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Galería de Componentes Institucionales (Sección 8)", self)
        lbl_titulo.setStyleSheet(
            f"font-size: {TAMANO_TITULO_PANTALLA}pt; font-weight: bold; color: {TEXTO};"
        )
        cabecera.addWidget(lbl_titulo)
        cabecera.addStretch()

        self.chip_filtro = ChipVentana(FiltroAnios(modo=ModoFiltroAnios.MODELO_2024), self)
        cabecera.addWidget(self.chip_filtro)
        layout_raiz.addLayout(cabecera)

        # -------------------------------------------------------------------
        # Rejilla 2x2 de tarjetas
        # -------------------------------------------------------------------
        rejilla = QGridLayout()
        rejilla.setSpacing(SEPARACION_TARJETAS)

        # 1. Fichas KPI y Minigráficos
        tarjeta_kpi = Tarjeta(titulo="Indicadores y Fichas KPI", parent=self)
        layout_kpi = QHBoxLayout()
        layout_kpi.setSpacing(12)

        kpi1 = FichaKPI("Grupos activos", 14, "En la institución", parent=tarjeta_kpi)
        kpi2 = FichaKPI("Investigadores", 86, "Autores vinculados", parent=tarjeta_kpi)
        kpi3 = FichaKPI("Productos (ventana)", 342, "Corte 2024", con_minigrafico=True, parent=tarjeta_kpi)
        if kpi3.minigrafico:
            kpi3.minigrafico.actualizar_datos([28, 45, 60, 52, 78, 85, 94])

        kpi4 = FichaKPI("Promedio / Autor", 3.98, "Productos por persona", parent=tarjeta_kpi)

        layout_kpi.addWidget(kpi1)
        layout_kpi.addWidget(kpi2)
        layout_kpi.addWidget(kpi3)
        layout_kpi.addWidget(kpi4)
        tarjeta_kpi.layout_contenido.addLayout(layout_kpi)
        rejilla.addWidget(tarjeta_kpi, 0, 0)

        # 2. Controles de Búsqueda, Selector Segmentado y Píldoras
        tarjeta_controles = Tarjeta(titulo="Búsqueda, Selector Segmentado y Píldoras", parent=self)
        layout_ctrl = QVBoxLayout()
        layout_ctrl.setSpacing(12)

        fila_busqueda = QHBoxLayout()
        fila_busqueda.setSpacing(12)
        busqueda = CampoBusqueda("Buscar investigador o grupo...", parent=tarjeta_controles)
        busqueda.setText("Inteligencia Artificial")
        fila_busqueda.addWidget(busqueda, stretch=1)

        selector = SelectorSegmentado(
            opciones=[("institucion", "Institución"), ("grupo", "Grupo")],
            parent=tarjeta_controles,
        )
        fila_busqueda.addWidget(selector, stretch=0)
        layout_ctrl.addLayout(fila_busqueda)

        # Muestra de píldoras
        layout_pildoras = QHBoxLayout()
        layout_pildoras.setSpacing(6)
        layout_pildoras.addWidget(Pildora("GNC"))
        layout_pildoras.addWidget(Pildora("DTI"))
        layout_pildoras.addWidget(Pildora("ASC"))
        layout_pildoras.addWidget(Pildora("FRH"))
        layout_pildoras.addWidget(Pildora("Avalado"))
        layout_pildoras.addWidget(Pildora("Con soporte"))
        layout_pildoras.addWidget(Pildora("Senior"))
        layout_pildoras.addWidget(Pildora("Junior"))
        layout_pildoras.addWidget(Pildora("Conectado", variante="exito"))
        layout_pildoras.addWidget(Pildora("Demo", variante="aviso"))
        layout_pildoras.addStretch()
        layout_ctrl.addLayout(layout_pildoras)

        tarjeta_controles.layout_contenido.addLayout(layout_ctrl)
        rejilla.addWidget(tarjeta_controles, 0, 1)

        # 3. Avatares y Esqueleto de carga
        tarjeta_avatares = Tarjeta(titulo="Avatares y Marcador de Carga (Esqueleto)", parent=self)
        layout_avatares_col = QVBoxLayout()
        layout_avatares_col.setSpacing(12)

        fila_avs = QHBoxLayout()
        fila_avs.setSpacing(16)
        try:
            logo_upc = cargar_pixmap("logo_upc.png", 64, 64)
        except Exception:
            logo_upc = None

        av1 = Avatar(diametro=40, nombre="Juan Pérez", parent=tarjeta_avatares)
        av2 = Avatar(diametro=48, nombre="María González", con_anillo=True, parent=tarjeta_avatares)
        av3 = Avatar(diametro=64, nombre="Robótica y Automatización", con_anillo=True, parent=tarjeta_avatares)
        av4 = Avatar(diametro=64, pixmap=logo_upc, con_anillo=True, parent=tarjeta_avatares)

        fila_avs.addWidget(av1)
        fila_avs.addWidget(av2)
        fila_avs.addWidget(av3)
        fila_avs.addWidget(av4)
        fila_avs.addStretch()
        layout_avatares_col.addLayout(fila_avs)

        lbl_esq = QLabel("Carga asíncrona de datos (esqueleto con pulso suave):", tarjeta_avatares)
        lbl_esq.setStyleSheet(f"font-size: 10pt; color: {TEXTO_SECUNDARIO};")
        layout_avatares_col.addWidget(lbl_esq)

        esqueleto = Esqueleto(filas=3, altura_fila=16, espaciado=6, parent=tarjeta_avatares)
        layout_avatares_col.addWidget(esqueleto)

        tarjeta_avatares.layout_contenido.addLayout(layout_avatares_col)
        rejilla.addWidget(tarjeta_avatares, 1, 0)

        # 4. Estado vacío informativo
        tarjeta_estados = Tarjeta(titulo="Estado Vacío Informativo", parent=self)
        vacio = EstadoVacio(
            titulo="Sin datos en esta ventana",
            mensaje="Intenta seleccionando “Todos los años” en el filtro o recargando los datos.",
            texto_principal="Conectar con Supabase",
            texto_secundario="Cargar demostración",
            parent=tarjeta_estados,
        )
        tarjeta_estados.layout_contenido.addWidget(vacio)
        rejilla.addWidget(tarjeta_estados, 1, 1)

        layout_raiz.addLayout(rejilla)

        # -------------------------------------------------------------------
        # Gestor de Avisos (Toasts en esquina inferior derecha)
        # -------------------------------------------------------------------
        self.gestor_avisos = GestorAvisos(self)


def capturar_galeria(ruta_destino: Path) -> bool:
    """Renderiza la galería y guarda una captura PNG con las fuentes nativas de Windows."""
    os.environ["PEA_SIN_ANIMACIONES"] = "1"

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyleSheet(HOJA_ESTILOS_GLOBAL)

    ventana = VentanaGaleria()
    ventana.resize(1360, 880)
    ventana.show()
    app.processEvents()

    # Mostrar toasts flotantes para la captura
    ventana.gestor_avisos.mostrar_exito(
        "Sincronización con Supabase finalizada (Revisión 142).",
        titulo="Operación completada",
        duracion_ms=60000,
    )
    ventana.gestor_avisos.mostrar_aviso(
        "Trabajando en modo de datos de demostración.",
        titulo="Aviso del sistema",
        duracion_ms=60000,
    )
    app.processEvents()

    pixmap = ventana.grab()
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    exito = pixmap.save(str(ruta_destino), "PNG")
    ventana.close()
    return exito


if __name__ == "__main__":
    destino = RUTA_RAIZ / "datos" / "capturas" / "galeria.png"
    if "--interactivo" in sys.argv:
        app = QApplication.instance() or QApplication(sys.argv)
        app.setStyleSheet(HOJA_ESTILOS_GLOBAL)
        win = VentanaGaleria()
        win.show()
        win.gestor_avisos.mostrar_exito("Sincronización con Supabase finalizada.")
        sys.exit(app.exec())
    else:
        ok = capturar_galeria(destino)
        if ok:
            print(f"Captura de galería guardada exitosamente en: {destino}")
            sys.exit(0)
        else:
            print(f"Error al guardar captura en: {destino}")
            sys.exit(1)
