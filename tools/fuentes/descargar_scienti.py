#!/usr/bin/env python3
"""
tools/fuentes/descargar_scienti.py
Descargador responsable de fuentes SCIENTI (GrupLAC y CvLAC) para PEA-i.
Reglas:
- HTTPS exclusivo.
- Solo host 'scienti.minciencias.gov.co'.
- Timeout estricto de conexión y lectura.
- Máximo 3 reintentos con espera exponencial.
- Pausa mínima de 1.5 s entre peticiones.
- User-Agent de proyecto universitario UPC.
- Caché en datos/cache/ (<sha256>.html y .meta.json).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

ALLOWED_HOST = "scienti.minciencias.gov.co"
USER_AGENT = "PEAi-Taller2-UPC/1.0 (Proyecto Academico Estructura de Datos; Universidad Popular del Cesar; contact: fandresfernandez@unicesar.edu.co)"


def descargar_url(url: str, cache_dir: Path, alias: str | None = None) -> tuple[bytes, dict]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Protocolo no permitido ({parsed.scheme}). Solo se permite HTTPS.")
    if parsed.netloc != ALLOWED_HOST:
        raise ValueError(f"Host no permitido ({parsed.netloc}). Solo se permite {ALLOWED_HOST}.")

    cache_dir.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    html_cache = cache_dir / f"{url_hash}.html"
    meta_cache = cache_dir / f"{url_hash}.meta.json"

    # Si ya está en caché, cargar desde caché
    if html_cache.exists() and meta_cache.exists():
        print(f"[CACHE] Cargando desde caché existente: {url}")
        content = html_cache.read_bytes()
        meta = json.loads(meta_cache.read_text(encoding="utf-8"))
        return content, meta

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }

    max_reintentos = 3
    ultimo_error = None

    for intento in range(max_reintentos):
        try:
            print(f"[HTTP] Descargando ({intento+1}/{max_reintentos}): {url}")
            resp = requests.get(url, headers=headers, timeout=(10, 30))
            if resp.status_code == 200:
                raw_bytes = resp.content
                # Determinar codificación
                encoding = resp.encoding or resp.apparent_encoding or "latin1"
                if "iso-8859" in encoding.lower():
                    encoding = "iso-8859-1"

                sha256_content = hashlib.sha256(raw_bytes).hexdigest()
                meta = {
                    "url": url,
                    "alias": alias,
                    "fecha_descarga": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "codigo_http": resp.status_code,
                    "encoding_cabeceras": resp.encoding,
                    "encoding_aparente": resp.apparent_encoding,
                    "encoding_utilizada": encoding,
                    "longitud_bytes": len(raw_bytes),
                    "sha256": sha256_content,
                    "url_hash": url_hash
                }

                # Guardar en caché
                html_cache.write_bytes(raw_bytes)
                meta_cache.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

                if alias:
                    alias_html = cache_dir / f"{alias}.html"
                    alias_meta = cache_dir / f"{alias}.meta.json"
                    alias_html.write_bytes(raw_bytes)
                    alias_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

                print(f"[OK] Descargados {len(raw_bytes)} bytes. SHA256: {sha256_content}")
                return raw_bytes, meta
            else:
                ultimo_error = f"HTTP {resp.status_code}"
                print(f"[REINTENTO] Estado HTTP inesperado: {resp.status_code}")
        except Exception as e:
            ultimo_error = str(e)
            print(f"[ERROR] Intento {intento+1} falló: {e}")

        espera = 1.5 * (2 ** intento)
        time.sleep(espera)

    raise RuntimeError(f"Fallo al descargar {url} tras {max_reintentos} intentos. Último error: {ultimo_error}")


def main():
    raiz = Path(__file__).resolve().parent.parent.parent
    cache_dir = raiz / "datos" / "cache"

    fuentes = [
        (
            "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=0000000002099",
            "gruplac_0000000002099"
        ),
        (
            "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917",
            "cvlac_0000494917"
        )
    ]

    for url, alias in fuentes:
        descargar_url(url, cache_dir, alias)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
