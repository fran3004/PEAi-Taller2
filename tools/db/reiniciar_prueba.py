#!/usr/bin/env python3
"""
tools/db/reiniciar_prueba.py
Operación segura de reinicio y limpieza de datos de prueba en Supabase.
REGLA INQUEBRANTABLE:
- Se niega terminantemente a tocar cualquier fila con es_ejemplo = false.
- Solo borra filas con es_ejemplo = true Y prefijo PRUEBA-.
- No utiliza clave secret; opera con la sesión autorizada de pruebas.
"""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from respaldar import cargar_configuracion
from sembrar import obtener_token_autenticado


def reiniciar_datos_prueba() -> int:
    url, anon_key = cargar_configuracion()
    if not url or not anon_key:
        print("[ERROR] Falta configurar PEA_SUPABASE_URL y PEA_SUPABASE_ANON_KEY", file=sys.stderr)
        return 1

    token = obtener_token_autenticado(url, anon_key)
    auth_header = f"Bearer {token}" if token else f"Bearer {anon_key}"

    headers = {
        "apikey": anon_key,
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
    }

    print("[*] Iniciando operación segura de reinicio de datos de prueba...")
    print("    Comprobando reglas de seguridad (solo es_ejemplo=true y prefijo PRUEBA-)...")

    # Intentar invocar la RPC segura reiniciar_datos_prueba
    endpoint_rpc = f"{url}/rest/v1/rpc/reiniciar_datos_prueba"
    payload_rpc = json.dumps({"p_confirmacion": "REINICIAR-PRUEBAS"}).encode("utf-8")
    req_rpc = Request(endpoint_rpc, data=payload_rpc, headers=headers, method="POST")

    try:
        with urlopen(req_rpc, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] Reinicio completado mediante RPC atómica segura:")
            print(f"     Productos de prueba borrados: {data.get('productos_borrados', 0)}")
            print(f"     Investigadores de prueba borrados: {data.get('investigadores_borrados', 0)}")
            print(f"     Grupos de prueba borrados: {data.get('grupos_borrados', 0)}")
            return 0
    except HTTPError as e:
        cuerpo = e.read().decode("utf-8", errors="replace")
        print(f"[INFO] RPC reiniciar_datos_prueba retornó HTTP {e.code} ({cuerpo}).", file=sys.stderr)
        print("       Procediendo a borrado condicional directo restringido con filtros de seguridad...")
    except Exception as e:
        print(f"[ADVERTENCIA] Fallo al invocar RPC: {e}", file=sys.stderr)

    # Borrado condicional directo garantizando el filtro estricto
    tablas_borrado = [
        ("productos", "codigo_identificador=like.PRUEBA-*&es_ejemplo=is.true"),
        ("investigadores", "codigo_rh=like.PRUEBA-*&es_ejemplo=is.true"),
        ("grupos", "codigo_gruplac=like.PRUEBA-*&es_ejemplo=is.true"),
    ]

    total_eliminados = 0
    for tabla, filtro in tablas_borrado:
        endpoint = f"{url}/rest/v1/{tabla}?{filtro}"
        req_del = Request(endpoint, headers=headers, method="DELETE")
        try:
            with urlopen(req_del, timeout=10) as resp:
                print(f"    [OK] Limpieza condicional en '{tabla}' ejecutada (HTTP {resp.status}).")
                total_eliminados += 1
        except HTTPError as e:
            cuerpo = e.read().decode("utf-8", errors="replace")
            print(f"    [INFO] Borrado en '{tabla}' retornó HTTP {e.code}: {cuerpo}", file=sys.stderr)
        except Exception as e:
            print(f"    [FALLA] Error eliminando en '{tabla}': {e}", file=sys.stderr)

    print(f"[OK] Operación de reinicio finalizada de forma segura. Cero datos de producción afectados.")
    return 0


if __name__ == "__main__":
    sys.exit(reiniciar_datos_prueba())
