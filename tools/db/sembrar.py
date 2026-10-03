#!/usr/bin/env python3
"""
tools/db/sembrar.py
Inserta o verifica el sembrado (seed) oficial de datos de prueba en Supabase.
Garantiza que todas las entidades de prueba lleven:
- es_ejemplo = true
- prefijo obligatorio PRUEBA- en códigos y nombres.
Nunca utiliza la clave secreta service_role.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from respaldar import cargar_configuracion


def obtener_token_autenticado(url: str, anon_key: str) -> str | None:
    correo = os.getenv("PEA_USUARIO_CORREO")
    clave = os.getenv("PEA_USUARIO_CLAVE")

    if not correo or not clave:
        return None

    endpoint = f"{url}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": anon_key,
        "Content-Type": "application/json",
        "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
    }
    payload = json.dumps({"email": correo, "password": clave}).encode("utf-8")

    req = Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("access_token")
    except Exception as e:
        print(f"[ADVERTENCIA] No fue posible autenticar con correo/clave: {e}", file=sys.stderr)
        return None


def sembrar() -> int:
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
        "Prefer": "resolution=merge-duplicates",
        "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
    }

    print(f"[*] Verificando / sembrando entidades de prueba en {url}...")

    # 1. Grupo de prueba
    grupo_payload = [
        {
            "codigo_gruplac": "PRUEBA-COL0001",
            "nombre": "PRUEBA-Grupo de Tecnologias Avanzadas",
            "fecha_creacion": "2015-06",
            "pais": "Colombia",
            "departamento_ciudad": "Cesar - Valledupar",
            "lider": "PRUEBA-Investigador Lider",
            "institucion_principal": "Universidad Popular del Cesar",
            "gran_area_ocde": "Ingenieria y Tecnologia",
            "area_ocde": "Ingenieria de Sistemas y Comunicaciones",
            "categoria": "A1",
            "activo": True,
            "es_ejemplo": True,
        }
    ]

    req = Request(f"{url}/rest/v1/grupos", data=json.dumps(grupo_payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            print("    [OK] Grupo de prueba sembrado/verificado.")
    except HTTPError as e:
        print(f"    [INFO] Inserción de grupo retornó HTTP {e.code} (posiblemente ya existe o RLS activo)", file=sys.stderr)

    # 2. Investigadores de prueba
    inv_payload = [
        {
            "codigo_rh": "PRUEBA-INV-001",
            "nombre_completo": "PRUEBA-Investigador Senior Uno",
            "nombre_en_citas": "P. Senior-Uno",
            "nacionalidad": "Colombia",
            "sexo": "Masculino",
            "categoria": "Investigador Senior",
            "formacion_academica": "Doctorado",
            "activo": True,
            "es_ejemplo": True,
        },
        {
            "codigo_rh": "PRUEBA-INV-002",
            "nombre_completo": "PRUEBA-Investigador Asociado Dos",
            "nombre_en_citas": "P. Asociado-Dos",
            "nacionalidad": "Colombia",
            "sexo": "Femenino",
            "categoria": "Investigador Asociado",
            "formacion_academica": "Maestria",
            "activo": True,
            "es_ejemplo": True,
        }
    ]

    req = Request(f"{url}/rest/v1/investigadores", data=json.dumps(inv_payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            print("    [OK] Investigadores de prueba sembrados/verificados.")
    except HTTPError as e:
        print(f"    [INFO] Inserción de investigadores retornó HTTP {e.code}", file=sys.stderr)

    print("[OK] Proceso de siembra finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(sembrar())
