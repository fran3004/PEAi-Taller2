#!/usr/bin/env python3
"""
Genera un respaldo JSON de las tablas visibles para un usuario autenticado de Supabase.
La paginación exige el conteo exacto visible por RLS y el archivo final se publica
solo después de validar su estructura e integridad.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

TAMANO_LOTE = 1000
TABLAS_A_RESPALDAR = (
    "meta",
    "grupos",
    "grupo_instituciones",
    "grupo_plan_estrategico",
    "lineas_investigacion",
    "investigadores",
    "integrantes_grupo",
    "productos",
    "producto_autores",
    "producto_grupos",
    "proyectos",
    "semilleros",
    "investigador_formacion",
    "investigador_experiencia",
    "investigador_areas_actuacion",
    "investigador_idiomas",
    "investigador_reconocimientos",
    "investigador_redes_identificadores",
    "auditoria_cambios",
)


class ErrorRespaldo(RuntimeError):
    """Error que impide certificar que el respaldo está completo."""


def _cargar_env_local() -> None:
    ruta_env = Path(".env")
    if not ruta_env.exists():
        return

    try:
        with ruta_env.open("r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    nombre, valor = linea.split("=", 1)
                    nombre = nombre.strip()
                    valor = valor.strip().strip("'\"")
                    if nombre and nombre not in os.environ and valor:
                        os.environ[nombre] = valor
    except OSError as error:
        raise ErrorRespaldo("No fue posible cargar la configuración local del respaldo.") from error


def _obtener_variable(*nombres: str) -> str:
    for nombre in nombres:
        valor = os.getenv(nombre, "").strip()
        if valor:
            return valor
    return ""


def _validar_clave_publica(clave: str) -> None:
    if clave.startswith(("sb_secret_", "service_role")):
        raise ErrorRespaldo("El respaldo solo admite una clave publishable/anon, nunca una clave secreta.")
    if clave.startswith("sb_publishable_"):
        return

    partes = clave.split(".")
    if len(partes) != 3:
        raise ErrorRespaldo("La clave de API no tiene un formato publishable/anon reconocido.")

    try:
        carga = partes[1] + "=" * (-len(partes[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(carga))
    except (ValueError, json.JSONDecodeError) as error:
        raise ErrorRespaldo("No se pudo validar que la clave de API sea publishable/anon.") from error
    if not isinstance(claims, dict) or claims.get("role") != "anon":
        raise ErrorRespaldo("El respaldo rechaza claves que no sean del rol anon/publishable.")


def cargar_configuracion() -> tuple[str, str]:
    _cargar_env_local()

    url = _obtener_variable(
        "PEA_SUPABASE_URL",
        "PEA_SUPABASE_URL_PROD",
        "PEA_SUPABASE_URL_TEST",
    ).rstrip("/")
    clave = _obtener_variable(
        "PEA_SUPABASE_PUBLISHABLE_KEY",
        "PEA_SUPABASE_ANON_KEY",
        "PEA_SUPABASE_ANON_PROD",
        "PEA_SUPABASE_ANON_TEST",
        "PEA_SUPABASE_KEY_PROD",
        "PEA_SUPABASE_KEY_TEST",
    )

    if not url or not clave:
        raise ErrorRespaldo("Falta configurar la URL, la clave publishable/anon o el usuario autenticado.")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]

    partes_url = urlsplit(url)
    if (
        partes_url.scheme != "https"
        or not partes_url.hostname
        or not partes_url.hostname.endswith(".supabase.co")
        or partes_url.username
        or partes_url.password
        or partes_url.path not in ("", "/")
        or partes_url.query
        or partes_url.fragment
    ):
        raise ErrorRespaldo("La URL debe ser el origen HTTPS del proyecto Supabase, sin credenciales ni rutas.")
    _validar_clave_publica(clave)
    return url, clave


def obtener_token_autenticado(url: str, clave_publica: str) -> str:
    correo = _obtener_variable("PEA_USUARIO_CORREO")
    contrasena = _obtener_variable("PEA_USUARIO_CLAVE")
    if not correo or not contrasena:
        raise ErrorRespaldo("Faltan las credenciales de un usuario Supabase normal; no se usará acceso anónimo.")

    endpoint = f"{url}/auth/v1/token?grant_type=password"
    solicitud = Request(
        endpoint,
        data=json.dumps({"email": correo, "password": contrasena}).encode("utf-8"),
        headers={
            "apikey": clave_publica,
            "Content-Type": "application/json",
            "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
        },
        method="POST",
    )
    try:
        with urlopen(solicitud, timeout=15) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except HTTPError as error:
        raise ErrorRespaldo(f"Falló la autenticación del usuario normal (HTTP {error.code}).") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ErrorRespaldo("No fue posible contactar el servicio de autenticación Supabase.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ErrorRespaldo("El servicio de autenticación devolvió una respuesta inválida.") from error

    token = datos.get("access_token") if isinstance(datos, dict) else None
    if not isinstance(token, str) or not token:
        raise ErrorRespaldo("La autenticación no devolvió una sesión de usuario válida.")
    return token


def _leer_rango_conteo(valor: str | None) -> tuple[int | None, int | None, int]:
    if not valor:
        raise ErrorRespaldo("PostgREST no devolvió Content-Range; no se puede certificar el conteo.")
    coincidencia = re.fullmatch(r"(\d+)-(\d+)/(\d+)", valor.strip())
    if coincidencia:
        inicio, fin, total = map(int, coincidencia.groups())
        return inicio, fin, total

    vacio = re.fullmatch(r"\*/(\d+)", valor.strip())
    if vacio:
        return None, None, int(vacio.group(1))
    raise ErrorRespaldo("PostgREST devolvió un Content-Range inválido.")


def descargar_tabla(url: str, clave_publica: str, tabla: str, token: str) -> list[dict]:
    registros: list[dict] = []
    total_esperado: int | None = None
    inicio = 0

    while total_esperado is None or inicio < total_esperado:
        fin = inicio + TAMANO_LOTE - 1
        endpoint = f"{url}/rest/v1/{tabla}?select=*&order=id.asc"
        solicitud = Request(
            endpoint,
            headers={
                "apikey": clave_publica,
                "Authorization": f"Bearer {token}",
                "Range-Unit": "items",
                "Range": f"{inicio}-{fin}",
                "Prefer": "count=exact",
                "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
            },
            method="GET",
        )
        try:
            with urlopen(solicitud, timeout=30) as respuesta:
                filas = json.loads(respuesta.read().decode("utf-8"))
                rango_inicio, rango_fin, total = _leer_rango_conteo(respuesta.headers.get("Content-Range"))
        except HTTPError as error:
            raise ErrorRespaldo(f"No se pudo leer la tabla '{tabla}' (HTTP {error.code}); respaldo incompleto.") from error
        except (URLError, TimeoutError, OSError) as error:
            raise ErrorRespaldo(f"Error de red al leer la tabla '{tabla}'; respaldo incompleto.") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ErrorRespaldo(f"La tabla '{tabla}' devolvió JSON inválido; respaldo incompleto.") from error

        if not isinstance(filas, list) or any(not isinstance(fila, dict) for fila in filas):
            raise ErrorRespaldo(f"La tabla '{tabla}' no devolvió una lista de registros.")
        if total_esperado is None:
            total_esperado = total
        elif total != total_esperado:
            raise ErrorRespaldo(f"El conteo de '{tabla}' cambió durante la paginación.")

        if not filas:
            if total_esperado == 0 and rango_inicio is None and rango_fin is None:
                break
            raise ErrorRespaldo(f"La tabla '{tabla}' devolvió una página vacía antes del conteo esperado.")
        if (
            rango_inicio != inicio
            or rango_fin != inicio + len(filas) - 1
            or len(filas) > TAMANO_LOTE
            or rango_fin >= total_esperado
        ):
            raise ErrorRespaldo(f"La página recibida para '{tabla}' no coincide con el rango solicitado.")

        registros.extend(filas)
        inicio += len(filas)

    if total_esperado is None or len(registros) != total_esperado:
        raise ErrorRespaldo(f"La tabla '{tabla}' quedó incompleta: conteo remoto no coincide con filas recibidas.")
    return registros


def consultar_revision_remota(url: str, clave_publica: str, token: str) -> int:
    solicitud = Request(
        f"{url}/rest/v1/meta?id=eq.1&select=revision",
        headers={
            "apikey": clave_publica,
            "Authorization": f"Bearer {token}",
            "Range-Unit": "items",
            "Range": "0-0",
            "Prefer": "count=exact",
            "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar)",
        },
        method="GET",
    )
    try:
        with urlopen(solicitud, timeout=15) as respuesta:
            filas = json.loads(respuesta.read().decode("utf-8"))
            _, _, total = _leer_rango_conteo(respuesta.headers.get("Content-Range"))
    except HTTPError as error:
        raise ErrorRespaldo(f"No se pudo verificar meta.revision (HTTP {error.code}).") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ErrorRespaldo("No fue posible verificar meta.revision durante el respaldo.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ErrorRespaldo("meta.revision devolvió una respuesta inválida.") from error

    if total != 1 or not isinstance(filas, list) or len(filas) != 1:
        raise ErrorRespaldo("meta.revision no contiene una única fila visible; no se certifica el respaldo.")
    revision = filas[0].get("revision")
    if not isinstance(revision, int):
        raise ErrorRespaldo("meta.revision no es un entero válido.")
    return revision


def _guardar_y_verificar(ruta_salida: Path, datos: dict) -> tuple[int, str]:
    ruta_temporal: Path | None = None
    contenido = json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
    checksum_esperado = hashlib.sha256(contenido).hexdigest()

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=ruta_salida.parent,
            prefix=f".{ruta_salida.name}.",
            suffix=".tmp",
            delete=False,
        ) as archivo:
            ruta_temporal = Path(archivo.name)
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())

        contenido_guardado = ruta_temporal.read_bytes()
        if hashlib.sha256(contenido_guardado).hexdigest() != checksum_esperado:
            raise ErrorRespaldo("La verificación de integridad del archivo de respaldo falló.")

        datos_verificados = json.loads(contenido_guardado.decode("utf-8"))
        tablas = datos_verificados.get("tablas")
        if not isinstance(tablas, dict) or set(tablas) != set(TABLAS_A_RESPALDAR):
            raise ErrorRespaldo("El archivo no contiene exactamente todas las tablas requeridas.")
        for tabla in TABLAS_A_RESPALDAR:
            filas = tablas[tabla]
            if not isinstance(filas, list) or len(filas) != datos["metadatos"]["filas_por_tabla"][tabla]:
                raise ErrorRespaldo(f"La verificación de registros para '{tabla}' falló.")

        ruta_temporal.replace(ruta_salida)
        total = sum(len(tablas[tabla]) for tabla in TABLAS_A_RESPALDAR)
        return total, checksum_esperado
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ErrorRespaldo("No fue posible escribir o verificar el archivo de respaldo.") from error
    finally:
        if ruta_temporal is not None and ruta_temporal.exists():
            ruta_temporal.unlink()


def respaldar() -> int:
    try:
        url, clave_publica = cargar_configuracion()
        token = obtener_token_autenticado(url, clave_publica)
        revision_inicio = consultar_revision_remota(url, clave_publica, token)
        ahora = datetime.datetime.now(datetime.UTC)
        dir_respaldos = Path("datos/respaldos")
        dir_respaldos.mkdir(parents=True, exist_ok=True)
        ts = ahora.strftime("%Y%m%d_%H%M%S_%f")
        ruta_salida = dir_respaldos / f"respaldo_{ts}.json"

        tablas: dict[str, list[dict]] = {}
        filas_por_tabla: dict[str, int] = {}
        for tabla in TABLAS_A_RESPALDAR:
            filas = descargar_tabla(url, clave_publica, tabla, token)
            tablas[tabla] = filas
            filas_por_tabla[tabla] = len(filas)
            print(f"    - {tabla}: {len(filas)} filas verificadas")

        revision_fin = consultar_revision_remota(url, clave_publica, token)
        if revision_inicio != revision_fin:
            raise ErrorRespaldo("meta.revision cambió durante el respaldo; no se publica una copia inconsistente.")

        datos_respaldo = {
            "metadatos": {
                "fecha_utc": ahora.isoformat(),
                "herramienta": "PEA-i respaldar.py",
                "filas_por_tabla": filas_por_tabla,
                "revision": revision_fin,
            },
            "tablas": tablas,
        }
        total_filas, checksum = _guardar_y_verificar(ruta_salida, datos_respaldo)
        print(
            f"[OK] Respaldo completo e íntegro: {ruta_salida} "
            f"({total_filas} filas visibles bajo RLS; SHA-256 {checksum})"
        )
        return 0
    except ErrorRespaldo as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    except OSError:
        print("[ERROR] No fue posible crear el directorio local de respaldos.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(respaldar())
