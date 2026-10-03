#!/usr/bin/env python3
"""
tools/db/respaldar.py
Genera una copia de seguridad integral fechada en JSON de todas las tablas de Supabase.
Maneja paginación automática mediante cabeceras HTTP Range (máx 1000 registros por lote).
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TABLAS_A_RESPALDAR = [
    "meta",
    "grupos",
    "investigadores",
    "integrantes_grupo",
    "productos",
    "producto_autores",
    "producto_grupos",
    "proyectos",
    "semilleros",
]


def cargar_configuracion() -> tuple[str, str]:
    ruta_env = Path(".env")
    if ruta_env.exists():
        try:
            with open(ruta_env, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ and v:
                            os.environ[k] = v
        except Exception:
            pass

    url = (
        os.getenv("PEA_SUPABASE_URL", "")
        or os.getenv("PEA_SUPABASE_URL_PROD", "")
        or os.getenv("PEA_SUPABASE_URL_TEST", "")
    )
    anon_key = (
        os.getenv("PEA_SUPABASE_ANON_KEY", "")
        or os.getenv("PEA_SUPABASE_KEY_PROD", "")
        or os.getenv("PEA_SUPABASE_KEY_TEST", "")
        or os.getenv("PEA_SUPABASE_PUBLISHABLE_KEY", "")
    )

    if not url or not anon_key:
        for ruta in [Path("config/pea.config.json"), Path("config/pea.config.example.json")]:
            if ruta.exists():
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        sb = json.load(f).get("supabase", {})
                        url = url or sb.get("url", "")
                        anon_key = anon_key or sb.get("anon_key", "")
                except Exception:
                    pass

    url = url.rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-len("/rest/v1")]

    return url, anon_key


def descargar_tabla(url: str, anon_key: str, tabla: str) -> list[dict]:
    registros: list[dict] = []
    lote_tamano = 1000
    inicio = 0

    while True:
        fin = inicio + lote_tamano - 1
        endpoint = f"{url}/rest/v1/{tabla}?select=*&order=id.asc" if tabla != "meta" else f"{url}/rest/v1/{tabla}?select=*"
        headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Range-Unit": "items",
            "Range": f"{inicio}-{fin}",
            "Prefer": "count=exact",
            "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
        }

        req = Request(endpoint, headers=headers, method="GET")
        try:
            with urlopen(req, timeout=15) as resp:
                cuerpo = resp.read().decode("utf-8")
                filas = json.loads(cuerpo)
                if not filas:
                    break
                registros.extend(filas)
                if len(filas) < lote_tamano:
                    break
                inicio += lote_tamano
        except HTTPError as e:
            if e.code in (404, 403, 401):
                # La tabla puede no existir todavía en la base inicial o estar bloqueada por RLS
                print(f"[INFO] Tabla '{tabla}' retornó HTTP {e.code} (posiblemente vacía, sin migrar o restringida)", file=sys.stderr)
                break
            else:
                cuerpo_err = e.read().decode("utf-8", errors="replace")
                print(f"[ADVERTENCIA] Error leyendo tabla '{tabla}' (HTTP {e.code}): {cuerpo_err}", file=sys.stderr)
                break
        except Exception as e:
            print(f"[ADVERTENCIA] Error de red descargando tabla '{tabla}': {e}", file=sys.stderr)
            break

    return registros


def respaldar() -> int:
    url, anon_key = cargar_configuracion()
    if not url or not anon_key:
        print("[ERROR] Falta configurar PEA_SUPABASE_URL y PEA_SUPABASE_ANON_KEY", file=sys.stderr)
        return 1

    ahora = datetime.datetime.now(datetime.timezone.utc)
    ts = ahora.strftime("%Y%m%d_%H%M%S")
    dir_respaldos = Path("datos/respaldos")
    dir_respaldos.mkdir(parents=True, exist_ok=True)
    ruta_salida = dir_respaldos / f"respaldo_{ts}.json"

    print(f"[*] Iniciando respaldo remoto desde {url}...")

    datos_respaldo = {
        "metadatos": {
            "fecha_utc": ahora.isoformat(),
            "servidor": url,
            "herramienta": "PEA-i respaldar.py",
        },
        "tablas": {},
    }

    total_filas = 0
    for tabla in TABLAS_A_RESPALDAR:
        filas = descargar_tabla(url, anon_key, tabla)
        datos_respaldo["tablas"][tabla] = filas
        total_filas += len(filas)
        print(f"    - {tabla}: {len(filas)} filas descargadas")

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(datos_respaldo, f, ensure_ascii=False, indent=2)

    print(f"[OK] Respaldo completado exitosamente: {ruta_salida} ({total_filas} registros en total)")
    return 0


if __name__ == "__main__":
    sys.exit(respaldar())
