#!/usr/bin/env python3
"""
tools/db/volcar.py
Vuelca los datos actuales de la base remota a un archivo JSON canónico
estructurado para comparación e interoperabilidad con Python y C++.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from respaldar import (
    TABLAS_A_RESPALDAR,
    ErrorRespaldo,
    cargar_configuracion,
    descargar_tabla,
    obtener_token_autenticado,
)


def volcar(ruta_destino: Path) -> int:
    try:
        url, clave_publica = cargar_configuracion()
        token = obtener_token_autenticado(url, clave_publica)
    except ErrorRespaldo as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print(f"[*] Volcando datos canónicos desde {url} hacia {ruta_destino}...")
    resultado = {}

    for tabla in TABLAS_A_RESPALDAR:
        filas = descargar_tabla(url, clave_publica, tabla, token)
        # Ordenamiento canónico por id si existe
        if filas and "id" in filas[0]:
            filas = sorted(filas, key=lambda x: x["id"])
        resultado[tabla] = filas
        print(f"    - {tabla}: {len(filas)} filas")

    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"[OK] Volcado canónico guardado en: {ruta_destino}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Volcado canónico de tablas de Supabase a JSON")
    parser.add_argument("--salida", "-s", type=Path, default=Path("datos/volcado_actual.json"),
                        help="Ruta de destino del archivo JSON")
    args = parser.parse_args()
    sys.exit(volcar(args.salida))
