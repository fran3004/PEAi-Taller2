"""Respaldo administrativo por HTTPS con la sesion ya gestionada por Supabase CLI.

No accede a .env ni a tokens: la CLI conserva la autenticacion. Las consultas
son exclusivamente SELECT sobre el inventario cerrado del respaldo.
"""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

PROYECTO = "wdmchsncexayqbjueamb"


def _ejecutar_cli(argumentos: list[str]) -> Any:
    ejecutable = shutil.which("supabase.cmd") or shutil.which("supabase")
    if not ejecutable:
        raise RuntimeError("No esta instalada Supabase CLI.")
    salida = subprocess.run(
        [ejecutable, *argumentos, "--output", "json"],
        capture_output=True, encoding="utf-8", timeout=120, check=False,
    )
    if salida.returncode:
        # No incorporar stderr: puede contener informacion de autenticacion.
        raise RuntimeError("La consulta administrativa fallo; no se certifica el respaldo.")
    return json.loads(salida.stdout)


def _consultar(sql: str) -> list[dict[str, Any]]:
    if not sql.startswith("SELECT ") or ";" in sql:
        raise ValueError("Solo se admiten consultas SELECT individuales.")
    resultado = _ejecutar_cli([
        "db", "query", "--linked", "--project-ref", PROYECTO, sql,
    ])
    filas = resultado.get("rows") if isinstance(resultado, dict) else None
    if not isinstance(filas, list):
        raise RuntimeError("Respuesta administrativa invalida.")
    return filas


def respaldar_cli() -> int:
    # Importacion compatible con ejecucion directa de respaldar.py.
    from respaldar import TABLAS_A_RESPALDAR, _guardar_y_verificar

    try:
        proyectos = _ejecutar_cli(["projects", "list"])
        if not isinstance(proyectos, list) or not any(
            p.get("id") == PROYECTO and p.get("name") == "pea-prod" and p.get("linked")
            for p in proyectos
        ):
            raise RuntimeError("El proyecto vinculado no es pea-prod.")
        inventario = _consultar("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        if {fila["tablename"] for fila in inventario} != set(TABLAS_A_RESPALDAR):
            raise RuntimeError("El inventario remoto difiere del respaldo; revisar antes de continuar.")
        meta = _consultar("SELECT revision, entorno FROM public.meta")
        if len(meta) != 1 or meta[0].get("entorno") != "produccion":
            raise RuntimeError("meta no identifica el entorno esperado.")
        revision = meta[0]["revision"]
        tablas: dict[str, list[dict[str, Any]]] = {}
        conteos = {}
        for tabla in TABLAS_A_RESPALDAR:
            # tabla solo proviene de la lista cerrada anterior, nunca de entradas externas.
            cantidad = _consultar(f"SELECT count(*)::integer AS total FROM public.{tabla}")[0]["total"]
            filas: list[dict[str, Any]] = []
            for desde in range(0, cantidad, 500):
                filas.extend(_consultar(
                    f"SELECT * FROM public.{tabla} ORDER BY id LIMIT 500 OFFSET {desde}"
                ))
            if len(filas) != cantidad or len({fila["id"] for fila in filas}) != cantidad:
                raise RuntimeError(f"El conteo de {tabla} no coincide; respaldo incompleto.")
            tablas[tabla] = filas
            conteos[tabla] = cantidad
            print(f"  {tabla}: {cantidad} filas verificadas", flush=True)
        if _consultar("SELECT revision, entorno FROM public.meta") != meta:
            raise RuntimeError("La revision cambio durante el respaldo; no se publica.")
        ahora = datetime.datetime.now(datetime.UTC)
        destino = Path("datos/respaldos")
        destino.mkdir(parents=True, exist_ok=True)
        ruta = destino / f"respaldo_cli_{ahora:%Y%m%d_%H%M%S_%f}.json"
        total, checksum = _guardar_y_verificar(ruta, {
            "metadatos": {
                "fecha_utc": ahora.isoformat(), "proyecto": PROYECTO,
                "herramienta": "Supabase CLI Management API HTTPS (solo lectura)",
                "filas_por_tabla": conteos, "revision": revision,
            },
            "tablas": tablas,
        })
        print(f"[OK] Respaldo completo: {ruta}; {total} filas; SHA-256 {checksum}")
        return 0
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.SubprocessError):
        print("[ERROR] No se pudo certificar un respaldo completo por CLI. No aplicar migraciones.")
        return 1
