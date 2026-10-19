"""Exportador visual institucional (PDF ejecutivo, PNG HiDPI con membrete y CSV UTF-8 BOM).

Cumple estrictamente ADR-0017: utiliza únicamente Qt Widgets / Qt Gui / QPainter / QPdfWriter / QImage
sin dependencias prohibidas (ni matplotlib, ni QtWebEngine, ni reportlab).
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QMarginsF, QPoint, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QLinearGradient,
    QPageLayout,
    QPageSize,
    QPainter,
    QPdfWriter,
    QPen,
    QRegion,
)
from PySide6.QtWidgets import QWidget

from pea.gui import estilo
from pea.version import APP_NAME, APP_VERSION, INSTITUCION, NOMBRE_COMPLETO

FACULTAD = "Facultad de Ingenierías y Tecnológicas"
PROGRAMA = "Programa de Ingeniería de Sistemas"


def renderizar_widget_imagen(widget: QWidget, escala: float = 2.0) -> QImage:
    """Renderiza un QWidget o GraficoBase en una QImage de alta resolución (2x por defecto)."""
    # Si es un GraficoBarrasApiladas (con _lienzo) o un GraficoBase (con _dibujar),
    # renderizar en proporción panorámica ejecutiva (740x460 lógico -> 1480x920 px)
    objetivo_dibujo = getattr(widget, "_lienzo", widget)
    if hasattr(objetivo_dibujo, "_dibujar"):
        ancho_logico = 740.0
        alto_logico = 460.0
        w_px = int(round(ancho_logico * escala))
        h_px = int(round(alto_logico * escala))
        img = QImage(w_px, h_px, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(estilo.SUPERFICIE))

        progreso_prev = getattr(objetivo_dibujo, "_progreso_animacion", 1.0)
        tooltip_prev = getattr(objetivo_dibujo, "_tooltip_visible", False)
        objetivo_dibujo._progreso_animacion = 1.0
        objetivo_dibujo._tooltip_visible = False
        try:
            with QPainter(img) as painter:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                painter.scale(escala, escala)
                rect_export = QRectF(0.0, 0.0, ancho_logico, alto_logico)
                if hasattr(objetivo_dibujo, "_calcular_posiciones"):
                    objetivo_dibujo._calcular_posiciones(rect_export)
                objetivo_dibujo._dibujar(painter, rect_export)
        finally:
            objetivo_dibujo._progreso_animacion = progreso_prev
            objetivo_dibujo._tooltip_visible = tooltip_prev
            if hasattr(objetivo_dibujo, "_calcular_posiciones"):
                objetivo_dibujo._calcular_posiciones(QRectF(objetivo_dibujo.rect()))
        return img

    ancho_base = max(widget.width(), widget.minimumWidth(), 520)
    alto_base = max(widget.height(), widget.minimumHeight(), 280)
    tam_original = widget.size()
    redimensionado = False
    if widget.width() < 320 or widget.height() < 180:
        widget.resize(ancho_base, alto_base)
        redimensionado = True

    w_px = max(1, int(widget.width() * escala))
    h_px = max(1, int(widget.height() * escala))
    img = QImage(w_px, h_px, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(estilo.SUPERFICIE))

    objetos_anim: list[tuple[Any, float]] = []
    for obj in [widget, *widget.findChildren(QWidget)]:
        if hasattr(obj, "_progreso_animacion"):
            objetos_anim.append((obj, float(obj._progreso_animacion)))
            obj._progreso_animacion = 1.0

    painter = QPainter(img)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.scale(escala, escala)
        widget.render(painter, QPoint(0, 0), QRegion(), QWidget.RenderFlag.DrawChildren)
    finally:
        painter.end()
        for obj, val_prev in objetos_anim:
            obj._progreso_animacion = val_prev

    if redimensionado:
        widget.resize(tam_original)
    return img


def _normalizar_imagenes(
    imagenes: Sequence[QImage | tuple[str, QImage]],
) -> list[tuple[str, QImage]]:
    resultado: list[tuple[str, QImage]] = []
    for item in imagenes:
        if isinstance(item, tuple) and len(item) == 2:
            etiqueta, img = item
            if isinstance(img, QImage) and not img.isNull():
                resultado.append((str(etiqueta), img))
        elif isinstance(item, QImage) and not item.isNull():
            resultado.append(("", item))
    return resultado


def guardar_csv_profesional(
    ruta: str | Path,
    columnas: Sequence[str] = (),
    filas: Sequence[Sequence[Any]] = (),
    *,
    titulo: str = "",
    metadatos: Sequence[tuple[str, str]] = (),
) -> Path:
    """Guarda una tabla en formato CSV con BOM UTF-8 (utf-8-sig) y delimitador ';' para Excel."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        if titulo or metadatos:
            escritor.writerow([f"{APP_NAME} · {NOMBRE_COMPLETO}"])
            if titulo:
                escritor.writerow(["Reporte", titulo])
            escritor.writerow(["Institución", INSTITUCION])
            for clave, valor in metadatos:
                escritor.writerow([str(clave), str(valor)])
            escritor.writerow([])

        if columnas:
            escritor.writerow([str(c).strip() for c in columnas])
        for fila in filas:
            fila_limpia = [
                " ".join(str("" if v is None else v).splitlines()).strip()
                for v in fila
            ]
            escritor.writerow(fila_limpia)
    return destino


def exportar_png_institucional(
    ruta: str | Path,
    titulo: str,
    subtitulo: str,
    imagenes: Sequence[QImage | tuple[str, QImage]],
    pie_extra: str = "",
) -> Path:
    """Compone una imagen PNG de alta resolución con encabezado y pie institucional UPC / PEA-i."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)

    imgs_validas = _normalizar_imagenes(imagenes)
    alto_cab = 120
    alto_pie = 56
    espaciado = 32
    usar_rejilla_2col = len(imgs_validas) >= 2

    if usar_rejilla_2col:
        max_w_celda = max((img.width() for _, img in imgs_validas), default=1200)
        ancho_out = max(2200, max_w_celda * 2 + 160)
        filas_rejilla = [imgs_validas[i : i + 2] for i in range(0, len(imgs_validas), 2)]
        alto_imgs = 0
        for fila_im in filas_rejilla:
            h_fila = max(img.height() + (38 if etq else 0) for etq, img in fila_im) + 20
            alto_imgs += h_fila
        alto_imgs += max(0, len(filas_rejilla) - 1) * espaciado
    else:
        ancho_contenido = max((img.width() for _, img in imgs_validas), default=1600)
        ancho_out = max(1840, ancho_contenido + 96)
        alto_imgs = sum(img.height() + (38 if etq else 0) for etq, img in imgs_validas) + max(
            0, len(imgs_validas) - 1
        ) * espaciado

    alto_out = alto_cab + alto_pie + max(420, alto_imgs) + 76

    lienzo = QImage(ancho_out, alto_out, QImage.Format.Format_ARGB32_Premultiplied)
    lienzo.fill(QColor(estilo.FONDO_APP))

    painter = QPainter(lienzo)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # 1. Encabezado institucional con degradado
        grad = QLinearGradient(0, 0, ancho_out, 0)
        grad.setColorAt(0.0, QColor(estilo.ENCABEZADO_INICIO))
        grad.setColorAt(0.55, QColor(estilo.ENCABEZADO_MEDIO))
        grad.setColorAt(1.0, QColor(estilo.ENCABEZADO_FIN))
        painter.fillRect(QRectF(0, 0, ancho_out, alto_cab), grad)
        painter.fillRect(QRectF(0, alto_cab - 5, ancho_out, 5), QColor(estilo.UPC_VERDE))

        f_marca = QFont(estilo.FAMILIA_FUENTE, 18)
        f_marca.setBold(True)
        painter.setFont(f_marca)
        painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO))
        painter.drawText(
            QRectF(36, 18, ancho_out - 460, 38),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{APP_NAME} · {titulo}",
        )

        f_sub = QFont(estilo.FAMILIA_FUENTE, 11)
        painter.setFont(f_sub)
        painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO_SUAVE))
        painter.drawText(
            QRectF(36, 60, ancho_out - 460, 34),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            subtitulo,
        )

        fecha_txt = datetime.now().strftime("%Y-%m-%d %H:%M")
        f_inst = QFont(estilo.FAMILIA_FUENTE, 10)
        f_inst.setBold(True)
        painter.setFont(f_inst)
        painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO))
        painter.drawText(
            QRectF(ancho_out - 440, 18, 404, 76),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"{INSTITUCION}\n{PROGRAMA}\nGenerado: {fecha_txt}",
        )

        # 2. Contenido gráfico en tarjetas limpias (rejilla 2 columnas o columna única)
        y_cursor = float(alto_cab + 32)
        if usar_rejilla_2col:
            filas_rejilla = [imgs_validas[i : i + 2] for i in range(0, len(imgs_validas), 2)]
            for fila_im in filas_rejilla:
                h_max_fila = 0.0
                if len(fila_im) == 2:
                    w_total_fila = fila_im[0][1].width() + fila_im[1][1].width() + 48.0
                    x_inicio = (ancho_out - w_total_fila) / 2.0
                    x_actual = x_inicio
                    for etiqueta_sec, img in fila_im:
                        alto_etq = 34.0 if etiqueta_sec else 0.0
                        rect_marco = QRectF(x_actual - 12, y_cursor - 10, img.width() + 24, img.height() + alto_etq + 20)
                        painter.setPen(QPen(QColor(estilo.LINEA), 1.5))
                        painter.setBrush(QBrush(QColor(estilo.SUPERFICIE)))
                        painter.drawRoundedRect(rect_marco, 12.0, 12.0)
                        y_im = y_cursor
                        if etiqueta_sec:
                            f_sec = QFont(estilo.FAMILIA_FUENTE, 12)
                            f_sec.setBold(True)
                            painter.setFont(f_sec)
                            painter.setPen(QColor(estilo.PRIMARIO))
                            painter.drawText(
                                QRectF(x_actual + 4, y_im, img.width() - 8, 28.0),
                                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                etiqueta_sec,
                            )
                            y_im += alto_etq
                        painter.drawImage(QRectF(x_actual, y_im, img.width(), img.height()), img)
                        x_actual += img.width() + 48.0
                        h_max_fila = max(h_max_fila, img.height() + alto_etq + 20.0)
                else:
                    etiqueta_sec, img = fila_im[0]
                    x_img = (ancho_out - img.width()) / 2.0
                    alto_etq = 34.0 if etiqueta_sec else 0.0
                    rect_marco = QRectF(x_img - 12, y_cursor - 10, img.width() + 24, img.height() + alto_etq + 20)
                    painter.setPen(QPen(QColor(estilo.LINEA), 1.5))
                    painter.setBrush(QBrush(QColor(estilo.SUPERFICIE)))
                    painter.drawRoundedRect(rect_marco, 12.0, 12.0)
                    y_im = y_cursor
                    if etiqueta_sec:
                        f_sec = QFont(estilo.FAMILIA_FUENTE, 12)
                        f_sec.setBold(True)
                        painter.setFont(f_sec)
                        painter.setPen(QColor(estilo.PRIMARIO))
                        painter.drawText(
                            QRectF(x_img + 4, y_im, img.width() - 8, 28.0),
                            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                            etiqueta_sec,
                        )
                        y_im += alto_etq
                    painter.drawImage(QRectF(x_img, y_im, img.width(), img.height()), img)
                    h_max_fila = img.height() + alto_etq + 20.0
                y_cursor += h_max_fila + espaciado
        else:
            for etiqueta_sec, img in imgs_validas:
                x_img = (ancho_out - img.width()) / 2.0
                alto_etq = 34.0 if etiqueta_sec else 0.0
                rect_marco = QRectF(x_img - 10, y_cursor - 8, img.width() + 20, img.height() + alto_etq + 16)
                painter.setPen(QPen(QColor(estilo.LINEA), 1.5))
                painter.setBrush(QBrush(QColor(estilo.SUPERFICIE)))
                painter.drawRoundedRect(rect_marco, 12.0, 12.0)

                if etiqueta_sec:
                    f_sec = QFont(estilo.FAMILIA_FUENTE, 11)
                    f_sec.setBold(True)
                    painter.setFont(f_sec)
                    painter.setPen(QColor(estilo.PRIMARIO))
                    painter.drawText(
                        QRectF(x_img + 4, y_cursor, img.width() - 8, 28.0),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        etiqueta_sec,
                    )
                    y_cursor += alto_etq

                painter.drawImage(QRectF(x_img, y_cursor, img.width(), img.height()), img)
                y_cursor += img.height() + espaciado

        # 3. Pie institucional
        y_pie = float(alto_out - alto_pie)
        painter.fillRect(QRectF(0, y_pie, ancho_out, alto_pie), QColor(estilo.PIE))
        painter.setPen(QPen(QColor(estilo.LINEA), 1.0))
        painter.drawLine(0, int(y_pie), ancho_out, int(y_pie))

        f_pie = QFont(estilo.FAMILIA_FUENTE, 9)
        painter.setFont(f_pie)
        painter.setPen(QColor(estilo.TEXTO_SECUNDARIO))
        texto_izq = f"{INSTITUCION} — {FACULTAD} · {APP_NAME} v{APP_VERSION}"
        painter.drawText(
            QRectF(36, y_pie, ancho_out / 2.0, alto_pie),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            texto_izq,
        )
        if pie_extra:
            painter.drawText(
                QRectF(ancho_out / 2.0, y_pie, ancho_out / 2.0 - 36, alto_pie),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                pie_extra,
            )
    finally:
        painter.end()

    lienzo.save(str(destino), "PNG")
    return destino


def exportar_reporte_pdf(
    ruta: str | Path,
    titulo: str,
    subtitulo: str = "",
    kpis: Sequence[tuple[str, str] | tuple[str, str, str]] = (),
    imagenes: Sequence[QImage | tuple[str, QImage]] = (),
    columnas: Sequence[str] = (),
    filas: Sequence[Sequence[Any]] = (),
    *,
    metadatos: Sequence[tuple[str, str]] = (),
    columnas_tabla: Sequence[str] = (),
    filas_tabla: Sequence[Sequence[Any]] = (),
    nota_pie: str = "",
    orientacion_horizontal: bool = True,
) -> Path:
    """Genera un reporte PDF ejecutivo multipágina con membrete institucional, KPIs, gráficos y tabla."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)

    cols_finales = tuple(columnas_tabla) if columnas_tabla else tuple(columnas)
    filas_finales = tuple(filas_tabla) if filas_tabla else tuple(filas)

    writer = QPdfWriter(str(destino))
    writer.setResolution(300)
    writer.setTitle(f"{APP_NAME} - {titulo}")
    writer.setCreator(f"{APP_NAME} v{APP_VERSION} - {INSTITUCION}")

    orientacion = (
        QPageLayout.Orientation.Landscape
        if orientacion_horizontal
        else QPageLayout.Orientation.Portrait
    )
    layout_pag = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        orientacion,
        QMarginsF(12, 12, 12, 12),
        QPageLayout.Unit.Millimeter,
    )
    writer.setPageLayout(layout_pag)

    painter = QPainter(writer)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        ancho_p = float(writer.width())
        alto_p = float(writer.height())
        margen_x = ancho_p * 0.035
        ancho_util = ancho_p - 2.0 * margen_x
        alto_cab = alto_p * 0.105
        alto_pie = alto_p * 0.045
        y_max_contenido = alto_p - alto_pie - 24.0

        fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        num_pagina = 1
        sub_completo = subtitulo
        if metadatos:
            meta_str = " · ".join(f"{k}: {v}" for k, v in metadatos)
            sub_completo = f"{subtitulo} ({meta_str})" if subtitulo else meta_str

        def _dibujar_marco_pagina(pag: int) -> float:
            painter.fillRect(QRectF(0, 0, ancho_p, alto_p), QColor(estilo.SUPERFICIE))

            grad = QLinearGradient(0, 0, ancho_p, 0)
            grad.setColorAt(0.0, QColor(estilo.ENCABEZADO_INICIO))
            grad.setColorAt(0.55, QColor(estilo.ENCABEZADO_MEDIO))
            grad.setColorAt(1.0, QColor(estilo.ENCABEZADO_FIN))
            painter.fillRect(QRectF(0, 0, ancho_p, alto_cab), grad)
            painter.fillRect(QRectF(0, alto_cab - 8.0, ancho_p, 8.0), QColor(estilo.UPC_VERDE))

            f_tit = QFont(estilo.FAMILIA_FUENTE, 13)
            f_tit.setBold(True)
            painter.setFont(f_tit)
            painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO))
            painter.drawText(
                QRectF(margen_x, alto_cab * 0.14, ancho_util * 0.65, alto_cab * 0.42),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{APP_NAME} · {titulo}",
            )

            f_sub = QFont(estilo.FAMILIA_FUENTE, 9)
            painter.setFont(f_sub)
            painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO_SUAVE))
            painter.drawText(
                QRectF(margen_x, alto_cab * 0.54, ancho_util * 0.65, alto_cab * 0.34),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                sub_completo,
            )

            f_der = QFont(estilo.FAMILIA_FUENTE, 8)
            f_der.setBold(True)
            painter.setFont(f_der)
            painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO))
            painter.drawText(
                QRectF(margen_x + ancho_util * 0.65, alto_cab * 0.14, ancho_util * 0.35, alto_cab * 0.72),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{INSTITUCION}\n{PROGRAMA}\nFecha: {fecha_str}",
            )

            y_pie = alto_p - alto_pie
            painter.fillRect(QRectF(0, y_pie, ancho_p, alto_pie), QColor(estilo.PIE))
            painter.setPen(QPen(QColor(estilo.LINEA), 2.0))
            painter.drawLine(0, int(y_pie), int(ancho_p), int(y_pie))

            f_pie = QFont(estilo.FAMILIA_FUENTE, 8)
            painter.setFont(f_pie)
            painter.setPen(QColor(estilo.TEXTO_SECUNDARIO))
            pie_izq = f"{INSTITUCION} — {FACULTAD} · Reporte oficial {APP_NAME} v{APP_VERSION}"
            if nota_pie:
                pie_izq = f"{pie_izq} · {nota_pie}"
            painter.drawText(
                QRectF(margen_x, y_pie, ancho_util * 0.78, alto_pie),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                pie_izq,
            )
            painter.drawText(
                QRectF(margen_x + ancho_util * 0.78, y_pie, ancho_util * 0.22, alto_pie),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"Página {pag}",
            )
            return alto_cab + 36.0

        y_cursor = _dibujar_marco_pagina(num_pagina)

        # 1. Tarjetas KPI de resumen si fueron provistas
        if kpis:
            n_kpis = len(kpis)
            esp_kpi = 24.0
            ancho_kpi = (ancho_util - esp_kpi * (n_kpis - 1)) / max(1, n_kpis)
            alto_kpi = alto_p * 0.095

            for idx, item_kpi in enumerate(kpis):
                etiqueta_k = str(item_kpi[0])
                valor_k = str(item_kpi[1])
                sub_k = str(item_kpi[2]) if len(item_kpi) > 2 else ""

                xk = margen_x + idx * (ancho_kpi + esp_kpi)
                rect_k = QRectF(xk, y_cursor, ancho_kpi, alto_kpi)
                painter.setPen(QPen(QColor(estilo.LINEA_FUERTE), 2.0))
                painter.setBrush(QBrush(QColor(estilo.FICHA)))
                painter.drawRoundedRect(rect_k, 16.0, 16.0)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(estilo.PRIMARIO)))
                painter.drawRoundedRect(QRectF(xk, y_cursor + 12.0, 8.0, alto_kpi - 24.0), 4.0, 4.0)

                f_klbl = QFont(estilo.FAMILIA_FUENTE, 8)
                f_klbl.setBold(True)
                painter.setFont(f_klbl)
                painter.setPen(QColor(estilo.TEXTO_SECUNDARIO))
                painter.drawText(
                    QRectF(xk + 22.0, y_cursor + alto_kpi * 0.10, ancho_kpi - 32.0, alto_kpi * 0.26),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    etiqueta_k.upper(),
                )

                f_kval = QFont(estilo.FAMILIA_FUENTE, 14)
                f_kval.setBold(True)
                painter.setFont(f_kval)
                painter.setPen(QColor(estilo.PRIMARIO))
                painter.drawText(
                    QRectF(xk + 22.0, y_cursor + alto_kpi * 0.36, ancho_kpi - 32.0, alto_kpi * 0.38),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    valor_k,
                )

                if sub_k:
                    f_ksub = QFont(estilo.FAMILIA_FUENTE, 8)
                    painter.setFont(f_ksub)
                    painter.setPen(QColor(estilo.TEXTO_SECUNDARIO))
                    painter.drawText(
                        QRectF(xk + 22.0, y_cursor + alto_kpi * 0.72, ancho_kpi - 32.0, alto_kpi * 0.22),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        sub_k,
                    )

            y_cursor += alto_kpi + 36.0

        # 2. Imágenes / gráficos incrustados
        imgs_validas = _normalizar_imagenes(imagenes)
        if imgs_validas:
            alto_disp_img = y_max_contenido - y_cursor - (alto_p * 0.22 if cols_finales and filas_finales else 16.0)
            if alto_disp_img < alto_p * 0.25:
                alto_disp_img = y_max_contenido - y_cursor - 16.0

            if len(imgs_validas) >= 2 and orientacion_horizontal:
                n_par = min(len(imgs_validas), 3)
                ancho_celda = (ancho_util - 28.0 * (n_par - 1)) / n_par
                alto_max_par = 0.0
                for idx_im, (_etq, im) in enumerate(imgs_validas[:n_par]):
                    escala = min(ancho_celda / max(1, im.width()), alto_disp_img / max(1, im.height()))
                    w_d = im.width() * escala
                    h_d = im.height() * escala
                    x_d = margen_x + idx_im * (ancho_celda + 28.0) + (ancho_celda - w_d) / 2.0
                    rect_im = QRectF(x_d, y_cursor, w_d, h_d)
                    painter.setPen(QPen(QColor(estilo.LINEA), 2.0))
                    painter.setBrush(QBrush(QColor(estilo.SUPERFICIE)))
                    painter.drawRoundedRect(rect_im.adjusted(-6, -6, 6, 6), 12.0, 12.0)
                    painter.drawImage(rect_im, im)
                    alto_max_par = max(alto_max_par, h_d)
                y_cursor += alto_max_par + 36.0
            else:
                for _etq, im in imgs_validas:
                    if y_cursor + alto_p * 0.25 > y_max_contenido:
                        writer.newPage()
                        num_pagina += 1
                        y_cursor = _dibujar_marco_pagina(num_pagina)
                    alto_disp = y_max_contenido - y_cursor - (alto_p * 0.20 if cols_finales and filas_finales else 16.0)
                    escala = min(ancho_util / max(1, im.width()), max(200.0, alto_disp) / max(1, im.height()))
                    w_d = im.width() * escala
                    h_d = im.height() * escala
                    x_d = margen_x + (ancho_util - w_d) / 2.0
                    rect_im = QRectF(x_d, y_cursor, w_d, h_d)
                    painter.setPen(QPen(QColor(estilo.LINEA), 2.0))
                    painter.setBrush(QBrush(QColor(estilo.SUPERFICIE)))
                    painter.drawRoundedRect(rect_im.adjusted(-6, -6, 6, 6), 12.0, 12.0)
                    painter.drawImage(rect_im, im)
                    y_cursor += h_d + 36.0

        # 3. Tabla de datos paginada
        if cols_finales and filas_finales:
            n_cols = len(cols_finales)
            pesos_col: list[float] = []
            for _c_idx, nom_col in enumerate(cols_finales):
                nom_bajo = nom_col.lower()
                if "título" in nom_bajo or "titulo" in nom_bajo or "nombre" in nom_bajo:
                    pesos_col.append(2.6)
                elif "grupo" in nom_bajo or "autor" in nom_bajo or "líder" in nom_bajo or "formación" in nom_bajo:
                    pesos_col.append(1.7)
                else:
                    pesos_col.append(1.0)
            suma_pesos = sum(pesos_col) or 1.0
            anchos_col = [(p / suma_pesos) * ancho_util for p in pesos_col]

            alto_enc_tabla = alto_p * 0.038
            alto_fila = alto_p * 0.034

            if y_cursor + alto_enc_tabla + alto_fila * 2 > y_max_contenido:
                writer.newPage()
                num_pagina += 1
                y_cursor = _dibujar_marco_pagina(num_pagina)

            def _dibujar_encabezado_tabla(y_top: float) -> float:
                rect_h = QRectF(margen_x, y_top, ancho_util, alto_enc_tabla)
                painter.setPen(QPen(QColor(estilo.PRIMARIO), 2.0))
                painter.setBrush(QBrush(QColor(estilo.ENCABEZADO_INICIO)))
                painter.drawRoundedRect(rect_h, 8.0, 8.0)

                f_th = QFont(estilo.FAMILIA_FUENTE, 8)
                f_th.setBold(True)
                painter.setFont(f_th)
                painter.setPen(QColor(estilo.TEXTO_SOBRE_OSCURO))

                x_c = margen_x
                for c_i, col_txt in enumerate(cols_finales):
                    w_c = anchos_col[c_i]
                    painter.drawText(
                        QRectF(x_c + 12.0, y_top, w_c - 24.0, alto_enc_tabla),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        str(col_txt),
                    )
                    x_c += w_c
                return y_top + alto_enc_tabla

            y_cursor = _dibujar_encabezado_tabla(y_cursor)

            f_td = QFont(estilo.FAMILIA_FUENTE, 8)
            painter.setFont(f_td)
            fm_td = QFontMetricsF(f_td)

            for r_idx, fila in enumerate(filas_finales):
                if y_cursor + alto_fila > y_max_contenido:
                    writer.newPage()
                    num_pagina += 1
                    y_cursor = _dibujar_marco_pagina(num_pagina)
                    y_cursor = _dibujar_encabezado_tabla(y_cursor)
                    painter.setFont(f_td)

                fondo_fila = QColor(estilo.SUPERFICIE if r_idx % 2 == 0 else estilo.SUPERFICIE_ALTERNADA)
                rect_r = QRectF(margen_x, y_cursor, ancho_util, alto_fila)
                painter.fillRect(rect_r, fondo_fila)
                painter.setPen(QPen(QColor(estilo.LINEA), 1.0))
                painter.drawLine(
                    int(margen_x),
                    int(y_cursor + alto_fila),
                    int(margen_x + ancho_util),
                    int(y_cursor + alto_fila),
                )

                x_c = margen_x
                painter.setPen(QColor(estilo.TEXTO))
                for c_i in range(n_cols):
                    w_c = anchos_col[c_i]
                    val_celda = fila[c_i] if c_i < len(fila) else ""
                    txt_celda = " ".join(str("" if val_celda is None else val_celda).splitlines()).strip()
                    txt_elidido = fm_td.elidedText(txt_celda, Qt.TextElideMode.ElideRight, w_c - 24.0)
                    painter.drawText(
                        QRectF(x_c + 12.0, y_cursor, w_c - 24.0, alto_fila),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        txt_elidido,
                    )
                    x_c += w_c

                y_cursor += alto_fila
    finally:
        painter.end()

    return destino

