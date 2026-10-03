"""Exportación de tablas y del catálogo a CSV (UTF-8 con BOM para que Excel muestre tildes)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pea.servicios.vistas import TablaDatos


def _celda_csv(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    return str(valor)


class ServicioExportacion:
    """Escribe archivos CSV a partir de modelos de vista (nunca de estructuras internas)."""

    CODIFICACION = "utf-8-sig"

    @classmethod
    def exportar_tabla_csv(cls, tabla: TablaDatos, ruta: Path | str) -> Path:
        """Exporta una TablaDatos a CSV separado por comas. Devuelve la ruta escrita."""
        destino = Path(ruta)
        if destino.suffix.lower() != ".csv":
            destino = destino.with_suffix(".csv")
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding=cls.CODIFICACION, newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(tabla.columnas)
            for fila in tabla.filas:
                escritor.writerow([_celda_csv(v) for v in fila])
        return destino
