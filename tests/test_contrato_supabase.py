"""Contrato de conteos reales de pea-prod; se ejecuta solo con ``-m red``."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import pytest

from pea.cliente_http import ClienteHTTPSupabase

_HOST_PEA_PROD = "wdmchsncexayqbjueamb.supabase.co"
_CONTEOS_ESPERADOS = {"grupos": 1, "investigadores": 85, "productos": 855}


def _variable(*nombres: str) -> str:
    return next((os.environ[nombre] for nombre in nombres if os.environ.get(nombre)), "")


@pytest.mark.red
def test_conteos_reales_de_pea_prod() -> None:
    """Verifica los conteos mediante REST con clave publicable y sesión normal."""
    url = _variable("PEA_SUPABASE_URL_PROD", "PEA_SUPABASE_URL", "PEA_SUPABASE_URL_TEST").strip()
    clave_publicable = _variable(
        "PEA_SUPABASE_PUBLISHABLE_KEY",
        "PEA_SUPABASE_ANON_KEY",
        "PEA_SUPABASE_ANON_PROD",
        "PEA_SUPABASE_ANON_TEST",
    ).strip()
    correo = os.environ.get("PEA_USUARIO_CORREO", "").strip()
    clave_usuario = os.environ.get("PEA_USUARIO_CLAVE", "")

    if not all((url, clave_publicable, correo, clave_usuario)):
        pytest.skip("Faltan variables de entorno para la sesión normal de pea-prod.")
    if urlsplit(url).hostname != _HOST_PEA_PROD:
        pytest.fail("La prueba red solo puede consultar el proyecto pea-prod.")

    cliente = ClienteHTTPSupabase(url, clave_publicable)
    cliente.autenticar(correo, clave_usuario)
    conteos = {
        tabla: len(cliente.get_paginado(tabla, params={"select": "id", "es_ejemplo": "eq.false"}))
        for tabla in _CONTEOS_ESPERADOS
    }

    assert conteos == _CONTEOS_ESPERADOS
