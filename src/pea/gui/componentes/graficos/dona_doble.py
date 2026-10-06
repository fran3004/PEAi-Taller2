"""Gráfico de dona concéntrica doble (tipología y validación) con QPainter.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 9.2).
- Anillo exterior: Tipología (grosor 22 % del radio).
- Anillo interior: Validación (grosor 18 % del radio).
- Separación entre anillos: 4 % del radio.
- Inicio a las 12 en punto, sentido horario, orden canónico fijo.
- Hueco angular de 1° entre segmentos contiguos y borde blanco de 1,5 px.
- Centro de la dona: Total de productos; al pasar el ratón muestra nombre, cantidad y %.
- El segmento sobrevolado sobresale 4 px hacia afuera.
- Leyenda inferior en dos columnas con indicadores interactivos de atenuación.
"""

from __future__ import annotations

import math
from typing import Final

from PySide6.QtCore import (
    QEvent,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from pea.gui import estilo
from pea.gui.componentes.graficos.base import GraficoBase
from pea.gui.estilo import (
    COLOR_ASC,
    COLOR_DTI,
    COLOR_FRH,
    COLOR_GNC,
    COLOR_VALIDACION_AVALADO,
    COLOR_VALIDACION_CON_SOPORTE,
    COLOR_VALIDACION_NO_AVALADO,
    LINEA_FUERTE,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.formato import (
    NOMBRES_TIPOLOGIAS,
    NOMBRES_VALIDACIONES,
    formatear_entero,
    formatear_porcentaje,
)

TIPOLOGIAS_ORDEN: Final[tuple[str, ...]] = ("GNC", "DTI", "ASC", "FRH")
VALIDACIONES_ORDEN: Final[tuple[str, ...]] = ("Avalado", "Con soporte", "No avalado")

COLORES_TIPOLOGIAS: Final[dict[str, str]] = {
    "GNC": COLOR_GNC,
    "DTI": COLOR_DTI,
    "ASC": COLOR_ASC,
    "FRH": COLOR_FRH,
}

COLORES_VALIDACIONES: Final[dict[str, str]] = {
    "Avalado": COLOR_VALIDACION_AVALADO,
    "Con soporte": COLOR_VALIDACION_CON_SOPORTE,
    "No avalado": COLOR_VALIDACION_NO_AVALADO,
}


class _SegmentoDona:
    """Información geométrica de un segmento de la dona para dibujo y hover."""

    def __init__(
        self,
        anillo: str,  # 'externo' o 'interno'
        clave: str,
        nombre: str,
        valor: int,
        porcentaje: float,
        color_hex: str,
        angulo_inicio: float,  # Grados (90 = 12h)
        barrido: float,        # Negativo para sentido horario
        r_in: float,
        r_out: float,
    ) -> None:
        self.anillo = anillo
        self.clave = clave
        self.nombre = nombre
        self.valor = valor
        self.porcentaje = porcentaje
        self.color_hex = color_hex
        self.angulo_inicio = angulo_inicio
        self.barrido = barrido
        self.r_in = r_in
        self.r_out = r_out


class GraficoDonaDoble(GraficoBase):
    """Componente gráfico de dona concéntrica doble."""

    def __init__(
        self,
        titulo: str = "Distribución y validación de productos",
        subtitulo: str = "Tipologías (anillo exterior) y estados (anillo interior)",
        tipologias: dict[str, int] | None = None,
        validaciones: dict[str, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo=titulo, subtitulo=subtitulo, parent=parent)
        self.setObjectName("grafico_dona_doble")
        self._tipologias: dict[str, int] = dict(tipologias or {})
        self._validaciones: dict[str, int] = dict(validaciones or {})
        self._segmentos: list[_SegmentoDona] = []
        self._segmento_hover: _SegmentoDona | None = None
        self._series_atenuadas: set[str] = set()
        self._rect_leyenda_items: list[tuple[str, QRectF]] = []

    def esta_vacio(self) -> bool:
        tot_tip = sum(self._tipologias.values()) if self._tipologias else 0
        tot_val = sum(self._validaciones.values()) if self._validaciones else 0
        return (tot_tip + tot_val) == 0

    def establecer_datos(
        self,
        tipologias: dict[str, int],
        validaciones: dict[str, int] | None = None,
    ) -> None:
        """Actualiza los datos de tipologías y validaciones con animación."""
        self._tipologias = dict(tipologias)
        if validaciones is not None:
            self._validaciones = dict(validaciones)
        self._segmento_hover = None
        r = QRectF(self.rect())
        self._calcular_geometria(r if r.width() > 10 else QRectF(0, 0, 500, 450))
        self._iniciar_animacion(duracion_ms=450)

    def _calcular_geometria(self, rect: QRectF) -> None:
        margen = 16.0
        alto_encabezado = 38.0 if (self.titulo or self.subtitulo) else 0.0
        alto_leyenda = 96.0
        area_dona = QRectF(
            rect.left() + margen,
            rect.top() + alto_encabezado + 8.0,
            rect.width() - 2 * margen,
            rect.height() - (alto_encabezado + alto_leyenda + margen + 10.0),
        )

        diametro_max = min(area_dona.width(), area_dona.height())
        if diametro_max < 60.0:
            diametro_max = 240.0

        r_ext = diametro_max / 2.0
        cx = area_dona.center().x()
        cy = area_dona.center().y()
        self._centro_x = cx
        self._centro_y = cy

        r_out_ext = r_ext
        r_in_ext = r_ext * 0.78
        r_out_int = r_ext * 0.74
        r_in_int = r_ext * 0.56
        self._r_in_int = r_in_int

        self._segmentos = []
        prog = min(1.0, max(0.0, self._progreso_animacion))

        # Tipologías
        total_tip = sum(self._tipologias.get(t, 0) for t in TIPOLOGIAS_ORDEN)
        ang_actual = 90.0
        for t in TIPOLOGIAS_ORDEN:
            cant = self._tipologias.get(t, 0)
            if total_tip <= 0 or cant <= 0:
                continue
            pct = (cant / total_tip) * 100.0
            barrido = -(cant / total_tip) * 360.0 * prog
            seg = _SegmentoDona(
                anillo="externo",
                clave=t,
                nombre=NOMBRES_TIPOLOGIAS.get(t, t),
                valor=cant,
                porcentaje=pct,
                color_hex=COLORES_TIPOLOGIAS[t],
                angulo_inicio=ang_actual,
                barrido=barrido,
                r_in=r_in_ext,
                r_out=r_out_ext,
            )
            self._segmentos.append(seg)
            ang_actual += barrido

        # Validaciones
        total_val = sum(self._validaciones.get(v, 0) for v in VALIDACIONES_ORDEN)
        ang_actual = 90.0
        for v in VALIDACIONES_ORDEN:
            cant = self._validaciones.get(v, 0)
            if total_val <= 0 or cant <= 0:
                continue
            pct = (cant / total_val) * 100.0
            barrido = -(cant / total_val) * 360.0 * prog
            seg = _SegmentoDona(
                anillo="interno",
                clave=v,
                nombre=NOMBRES_VALIDACIONES.get(v, v),
                valor=cant,
                porcentaje=pct,
                color_hex=COLORES_VALIDACIONES[v],
                angulo_inicio=ang_actual,
                barrido=barrido,
                r_in=r_in_int,
                r_out=r_out_int,
            )
            self._segmentos.append(seg)
            ang_actual += barrido

        # Rectángulos de leyenda
        self._rect_leyenda_items = []
        y_ley = area_dona.bottom() + 10.0
        self._y_ley = y_ley
        ancho_util = rect.width() - 32.0
        ancho_col = ancho_util / 2.0

        x_col1 = rect.left() + 16.0
        for i, t in enumerate(TIPOLOGIAS_ORDEN):
            y_item = y_ley + 18.0 + i * 16.0
            self._rect_leyenda_items.append((t, QRectF(x_col1, y_item, ancho_col - 10.0, 15.0)))

        x_col2 = x_col1 + ancho_col
        for i, v in enumerate(VALIDACIONES_ORDEN):
            y_item = y_ley + 18.0 + i * 16.0
            self._rect_leyenda_items.append((v, QRectF(x_col2, y_item, ancho_col - 10.0, 15.0)))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        self._pos_cursor = pos
        seg_previo = self._segmento_hover
        self._segmento_hover = self._detectar_segmento(pos.x(), pos.y())

        if self._segmento_hover != seg_previo:
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._segmento_hover = None
        self._pos_cursor = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            for clave, rect_item in self._rect_leyenda_items:
                if rect_item.contains(pos):
                    if clave in self._series_atenuadas:
                        self._series_atenuadas.remove(clave)
                    else:
                        self._series_atenuadas.add(clave)
                    self.update()
                    return
        super().mousePressEvent(event)

    def _detectar_segmento(self, px: float, py: float) -> _SegmentoDona | None:
        if not self._segmentos:
            return None

        # Asumimos que todos los segmentos comparten el mismo centro
        cx = self._centro_x
        cy = self._centro_y

        dx = px - cx
        dy = py - cy
        dist = math.sqrt(dx * dx + dy * dy)

        # En coordenadas matemáticas (Y arriba):
        ang_deg = math.degrees(math.atan2(-dy, dx))
        if ang_deg < 0:
            ang_deg += 360.0

        for seg in self._segmentos:
            if not (seg.r_in - 2.0 <= dist <= seg.r_out + 6.0):
                continue

            # El arco va de angulo_inicio a (angulo_inicio + barrido), barrido es negativo
            a_ini = seg.angulo_inicio % 360.0
            a_fin = (seg.angulo_inicio + seg.barrido) % 360.0

            # Verificación de contención angular en sentido horario
            if seg.barrido < 0:
                # Caso horario
                if a_ini >= a_fin:
                    if a_fin <= ang_deg <= a_ini:
                        return seg
                else:
                    # Cruce por 0°
                    if ang_deg <= a_ini or ang_deg >= a_fin:
                        return seg

        return None

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))
        alto_encabezado = self.dibujar_encabezado(painter, rect)
        margen = 16.0

        if self.esta_vacio():
            rect_vacio = rect.adjusted(margen, alto_encabezado + 10, -margen, -margen)
            self.dibujar_estado_vacio(painter, rect_vacio)
            return

        self._calcular_geometria(rect)

        # Dibujar segmentos
        for seg in self._segmentos:
            self._dibujar_segmento(painter, seg, self._centro_x, self._centro_y)

        # 3. Centro de la dona
        total_tip = sum(self._tipologias.get(t, 0) for t in TIPOLOGIAS_ORDEN)
        total_val = sum(self._validaciones.get(v, 0) for v in VALIDACIONES_ORDEN)
        total_general = max(total_tip, total_val)
        self._dibujar_centro(painter, self._centro_x, self._centro_y, self._r_in_int, total_general)

        # 4. Leyenda inferior en dos columnas
        self._dibujar_leyenda_doble(painter, rect, self._y_ley, total_tip, total_val)

    def _dibujar_segmento(self, painter: QPainter, seg: _SegmentoDona, cx: float, cy: float) -> None:
        """Dibuja un sector anular con hueco angular de 1°, borde blanco y desplazamiento si hover."""
        if abs(seg.barrido) < 0.2:
            return

        es_hover = (self._segmento_hover is not None and
                    self._segmento_hover.anillo == seg.anillo and
                    self._segmento_hover.clave == seg.clave)

        # Desplazamiento radial de 4 px si hover
        offset_r = 4.0 if es_hover else 0.0
        ang_medio = math.radians(seg.angulo_inicio + seg.barrido / 2.0)
        desp_x = offset_r * math.cos(ang_medio)
        desp_y = -offset_r * math.sin(ang_medio)

        c_x = cx + desp_x
        c_y = cy + desp_y

        r_in = seg.r_in
        r_out = seg.r_out + (2.0 if es_hover else 0.0)

        # Hueco angular de 1° si hay espacio suficiente
        hueco = 1.0 if abs(seg.barrido) > 3.0 else 0.0
        a_ini = seg.angulo_inicio - (hueco / 2.0)
        span = seg.barrido + hueco

        rect_out = QRectF(c_x - r_out, c_y - r_out, 2 * r_out, 2 * r_out)
        rect_in = QRectF(c_x - r_in, c_y - r_in, 2 * r_in, 2 * r_in)

        path = QPainterPath()
        path.arcMoveTo(rect_out, a_ini)
        path.arcTo(rect_out, a_ini, span)
        path.arcTo(rect_in, a_ini + span, -span)
        path.closeSubpath()

        color = QColor(seg.color_hex)
        if seg.clave in self._series_atenuadas:
            color.setAlpha(45)

        painter.save()
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(estilo.SUPERFICIE), 1.5))
        painter.drawPath(path)
        painter.restore()

    def _dibujar_centro(self, painter: QPainter, cx: float, cy: float, r_centro: float, total: int) -> None:
        """Dibuja el contenido dinámico del centro de la dona."""
        rect_centro = QRectF(cx - r_centro + 4, cy - r_centro + 4, 2 * (r_centro - 4), 2 * (r_centro - 4))

        painter.save()
        # Fondo blanco interior
        painter.setBrush(QBrush(QColor(estilo.SUPERFICIE)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect_centro)

        if self._segmento_hover is not None:
            # Mostrar datos del segmento sobrevolado
            seg = self._segmento_hover

            fuente_nom = QFont()
            fuente_nom.setPointSize(estilo.TAMANO_AUXILIAR)
            fuente_nom.setBold(True)
            painter.setFont(fuente_nom)
            painter.setPen(QPen(QColor(seg.color_hex)))
            rect_nom = QRectF(rect_centro.left(), cy - 22.0, rect_centro.width(), 18.0)
            painter.drawText(rect_nom, Qt.AlignmentFlag.AlignCenter, seg.clave)

            fuente_val = QFont()
            fuente_val.setPointSize(estilo.TAMANO_TITULO_TARJETA)
            fuente_val.setBold(True)
            painter.setFont(fuente_val)
            painter.setPen(QPen(QColor(TEXTO)))
            rect_val = QRectF(rect_centro.left(), cy - 4.0, rect_centro.width(), 24.0)
            texto_cifra = f"{formatear_entero(seg.valor)}"
            painter.drawText(rect_val, Qt.AlignmentFlag.AlignCenter, texto_cifra)

            fuente_pct = QFont()
            fuente_pct.setPointSize(estilo.TAMANO_AUXILIAR)
            painter.setFont(fuente_pct)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_pct = QRectF(rect_centro.left(), cy + 18.0, rect_centro.width(), 16.0)
            painter.drawText(rect_pct, Qt.AlignmentFlag.AlignCenter, f"({formatear_porcentaje(seg.porcentaje)})")
        else:
            # Estado normal: total de productos
            fuente_tot = QFont()
            fuente_tot.setPointSize(estilo.TAMANO_KPI)
            fuente_tot.setBold(True)
            painter.setFont(fuente_tot)
            painter.setPen(QPen(QColor(TEXTO)))
            rect_tot = QRectF(rect_centro.left(), cy - 20.0, rect_centro.width(), 28.0)
            painter.drawText(rect_tot, Qt.AlignmentFlag.AlignCenter, formatear_entero(total))

            fuente_sub = QFont()
            fuente_sub.setPointSize(estilo.TAMANO_AUXILIAR)
            painter.setFont(fuente_sub)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_sub = QRectF(rect_centro.left(), cy + 10.0, rect_centro.width(), 16.0)
            painter.drawText(rect_sub, Qt.AlignmentFlag.AlignCenter, "productos")

        painter.restore()

    def _dibujar_leyenda_doble(
        self,
        painter: QPainter,
        rect: QRectF,
        y_ley: float,
        total_tip: int,
        total_val: int,
    ) -> None:
        """Dibuja la leyenda inferior en dos columnas ('Tipología' y 'Validación')."""
        self._rect_leyenda_items = []
        ancho_util = rect.width() - 32.0
        ancho_col = ancho_util / 2.0

        fuente_tit_ley = QFont()
        fuente_tit_ley.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente_tit_ley.setBold(True)

        fuente_item_ley = QFont()
        fuente_item_ley.setPointSize(estilo.TAMANO_AUXILIAR)

        # Columna 1: Tipologías
        x_col1 = rect.left() + 16.0
        painter.setFont(fuente_tit_ley)
        painter.setPen(QPen(QColor(TEXTO)))
        painter.drawText(QRectF(x_col1, y_ley, ancho_col, 16.0), Qt.AlignmentFlag.AlignLeft, "Tipología (exterior)")

        for i, t in enumerate(TIPOLOGIAS_ORDEN):
            cant = self._tipologias.get(t, 0)
            pct = (cant / total_tip * 100.0) if total_tip > 0 else 0.0
            y_item = y_ley + 18.0 + i * 16.0

            rect_click = QRectF(x_col1, y_item, ancho_col - 10.0, 15.0)
            self._rect_leyenda_items.append((t, rect_click))

            esta_atenuada = t in self._series_atenuadas
            color = QColor(COLORES_TIPOLOGIAS[t])
            if esta_atenuada:
                color.setAlpha(60)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(LINEA_FUERTE if esta_atenuada else estilo.SUPERFICIE), 1))
            painter.drawRoundedRect(QRectF(x_col1, y_item + 2.0, 10.0, 10.0), 2.0, 2.0)

            painter.setFont(fuente_item_ley)
            painter.setPen(QPen(QColor(LINEA_FUERTE if esta_atenuada else TEXTO)))
            txt = f"{t} · {formatear_entero(cant)} ({formatear_porcentaje(pct)})"
            painter.drawText(QRectF(x_col1 + 16.0, y_item, ancho_col - 26.0, 15.0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, txt)

        # Columna 2: Validaciones
        x_col2 = x_col1 + ancho_col
        painter.setFont(fuente_tit_ley)
        painter.setPen(QPen(QColor(TEXTO)))
        painter.drawText(QRectF(x_col2, y_ley, ancho_col, 16.0), Qt.AlignmentFlag.AlignLeft, "Validación (interior)")

        for i, v in enumerate(VALIDACIONES_ORDEN):
            cant = self._validaciones.get(v, 0)
            pct = (cant / total_val * 100.0) if total_val > 0 else 0.0
            y_item = y_ley + 18.0 + i * 16.0

            rect_click = QRectF(x_col2, y_item, ancho_col - 10.0, 15.0)
            self._rect_leyenda_items.append((v, rect_click))

            esta_atenuada = v in self._series_atenuadas
            color = QColor(COLORES_VALIDACIONES[v])
            if esta_atenuada:
                color.setAlpha(60)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(LINEA_FUERTE if esta_atenuada else estilo.SUPERFICIE), 1))
            painter.drawRoundedRect(QRectF(x_col2, y_item + 2.0, 10.0, 10.0), 2.0, 2.0)

            painter.setFont(fuente_item_ley)
            painter.setPen(QPen(QColor(LINEA_FUERTE if esta_atenuada else TEXTO)))
            txt = f"{v} · {formatear_entero(cant)} ({formatear_porcentaje(pct)})"
            painter.drawText(QRectF(x_col2 + 16.0, y_item, ancho_col - 26.0, 15.0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, txt)
