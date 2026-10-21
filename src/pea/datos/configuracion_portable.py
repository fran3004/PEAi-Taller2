"""Configuracion publica del paquete; nunca contiene credenciales de usuario."""

import json
import os
import sys
from pathlib import Path

from pea.excepciones import ErrorValidacion


def leer_configuracion_portable() -> dict:
    if not getattr(sys, "frozen", False) or os.getenv("PEA_OMITIR_CONFIG_PUBLICA") == "1":
        return {}
    ruta = Path(sys.executable).resolve().parent.parent / "config/pea.config.json"
    if not ruta.is_file():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ErrorValidacion("No se pudo leer la configuracion publica del paquete.") from error
    if (
        not isinstance(datos, dict)
        or datos.get("url") != "https://wdmchsncexayqbjueamb.supabase.co"
        or not str(datos.get("clave_publishable", "")).startswith("sb_publishable_")
        or datos.get("acceso_evaluacion") is not True
        or set(datos) != {"url", "clave_publishable", "acceso_evaluacion"}
    ):
        raise ErrorValidacion("La configuracion publica del paquete no es valida para pea-prod.")
    return datos
