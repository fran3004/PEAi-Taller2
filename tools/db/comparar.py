#!/usr/bin/env python3
"""
tools/db/comparar.py
Compara dos archivos de volcado JSON (o el estado de la base remota contra un oráculo)
y reporta discrepancias campo por campo y fila por fila.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def comparar_diccionarios(dict_a: dict[str, Any], dict_b: dict[str, Any], ruta_campo: str = "") -> list[str]:
    diferencias = []
    todas_claves = sorted(set(dict_a.keys()) | set(dict_b.keys()))

    for k in todas_claves:
        camino = f"{ruta_campo}.{k}" if ruta_campo else k
        if k not in dict_a:
            diferencias.append(f"[FALTA EN A] {camino}: no existe en primer conjunto (B={dict_b[k]})")
        elif k not in dict_b:
            diferencias.append(f"[FALTA EN B] {camino}: no existe en segundo conjunto (A={dict_a[k]})")
        else:
            val_a = dict_a[k]
            val_b = dict_b[k]
            if isinstance(val_a, dict) and isinstance(val_b, dict):
                diferencias.extend(comparar_diccionarios(val_a, val_b, camino))
            elif val_a != val_b:
                diferencias.append(f"[DIFERENCIA] {camino}: A={val_a!r} vs B={val_b!r}")

    return diferencias


def comparar_archivos(archivo_a: Path, archivo_b: Path) -> int:
    if not archivo_a.exists():
        print(f"[ERROR] Archivo origen no existe: {archivo_a}", file=sys.stderr)
        return 1
    if not archivo_b.exists():
        print(f"[ERROR] Archivo destino no existe: {archivo_b}", file=sys.stderr)
        return 1

    with open(archivo_a, "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(archivo_b, "r", encoding="utf-8") as f:
        data_b = json.load(f)

    # Extraer si viene envuelto en "tablas"
    tablas_a = data_a.get("tablas", data_a)
    tablas_b = data_b.get("tablas", data_b)

    discrepancias_totales: list[str] = []
    todas_tablas = sorted(set(tablas_a.keys()) | set(tablas_b.keys()))

    for tabla in todas_tablas:
        filas_a = tablas_a.get(tabla, [])
        filas_b = tablas_b.get(tabla, [])

        if len(filas_a) != len(filas_b):
            discrepancias_totales.append(
                f"[CANTIDAD] Tabla '{tabla}': A tiene {len(filas_a)} filas, B tiene {len(filas_b)} filas"
            )

        # Mapear por ID o código natural si es lista de objetos
        if isinstance(filas_a, list) and isinstance(filas_b, list):
            limite = min(len(filas_a), len(filas_b))
            for i in range(limite):
                diffs = comparar_diccionarios(filas_a[i], filas_b[i], f"{tabla}[{i}]")
                discrepancias_totales.extend(diffs)

    if discrepancias_totales:
        print(f"[FALLA] Se encontraron {len(discrepancias_totales)} discrepancias:")
        for d in discrepancias_totales[:30]:
            print(f"  {d}")
        if len(discrepancias_totales) > 30:
            print(f"  ... y {len(discrepancias_totales) - 30} discrepancias más.")
        return 2

    print("[OK] Los dos conjuntos de datos son idénticos campo por campo.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compara dos volcados JSON de la base de datos PEA-i")
    parser.add_argument("archivo_a", type=Path, help="Primer archivo JSON a comparar")
    parser.add_argument("archivo_b", type=Path, help="Segundo archivo JSON a comparar")
    args = parser.parse_args()
    sys.exit(comparar_archivos(args.archivo_a, args.archivo_b))
