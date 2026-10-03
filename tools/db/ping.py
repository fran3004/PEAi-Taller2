#!/usr/bin/env python3
"""
tools/db/ping.py
Verifica la conectividad HTTPS contra la base de datos Supabase remota
invocando la función RPC ping() o consultando la revisión global.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cargar_configuracion() -> tuple[str, str]:
    """Obtiene la URL y la anon_key de variables de entorno o de config/pea.config.json."""
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
        ruta_cfg = Path("config/pea.config.json")
        if not ruta_cfg.exists():
            ruta_cfg = Path("config/pea.config.example.json")
        if ruta_cfg.exists():
            try:
                with open(ruta_cfg, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    sb = cfg.get("supabase", {})
                    url = url or sb.get("url", "")
                    anon_key = anon_key or sb.get("anon_key", "")
            except Exception as e:
                print(f"[ADVERTENCIA] Error leyendo configuración: {e}", file=sys.stderr)

    url = url.rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-len("/rest/v1")]

    return url, anon_key


def ejecutar_ping() -> int:
    url, anon_key = cargar_configuracion()

    if not url or not anon_key:
        print("[ERROR] Falta configurar PEA_SUPABASE_URL y PEA_SUPABASE_ANON_KEY", file=sys.stderr)
        return 1

    endpoint = f"{url}/rest/v1/rpc/ping"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
        "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
    }

    req = Request(endpoint, data=b"{}", headers=headers, method="POST")

    inicio = time.perf_counter()
    try:
        with urlopen(req, timeout=10) as resp:
            duracion_ms = (time.perf_counter() - inicio) * 1000
            codigo = resp.status
            cuerpo = resp.read().decode("utf-8")
            data = json.loads(cuerpo)
            print(f"[OK] Conexión exitosa a Supabase ({duracion_ms:.1f} ms) - Código HTTP {codigo}")
            print(f"     Estado: {data.get('estado', 'desconocido')}")
            print(f"     Revisión remota: {data.get('revision')}")
            print(f"     Hora del servidor: {data.get('hora')}")
            return 0
    except HTTPError as e:
        duracion_ms = (time.perf_counter() - inicio) * 1000
        cuerpo = e.read().decode("utf-8", errors="replace")
        print(f"[FALLA] Error HTTP {e.code} desde {endpoint} ({duracion_ms:.1f} ms): {cuerpo}", file=sys.stderr)
        return 1
    except URLError as e:
        print(f"[FALLA] Error de red o conexión: {e.reason}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[FALLA] Error inesperado en ping: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(ejecutar_ping())
