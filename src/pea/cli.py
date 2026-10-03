"""Línea de comandos (CLI) institucional para PEA-i."""

import argparse
import os
import sys

from pea.cliente_http import ClienteHTTPSupabase
from pea.excepciones import ErrorPEA
from pea.version import APP_NAME, APP_VERSION, INSTITUCION, obtener_version


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pea",
        description="PEA-i · Programa Estadístico de Análisis de Investigación (UPC)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=obtener_version(),
        help="Muestra la versión de la aplicación y sale",
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponibles")

    # Comando info
    subparsers.add_parser("info", help="Muestra la información de la aplicación")

    # Comando ping
    subparsers.add_parser("ping", help="Verifica la conexión HTTPS con Supabase")

    return parser


def comando_info() -> None:
    print(f"Nombre: {APP_NAME}")
    print(f"Versión: {APP_VERSION}")
    print(f"Institución: {INSTITUCION}")
    print("Arquitectura: Python 3.12 / PySide6 / HTTPS PostgREST")


def comando_ping() -> int:
    url = os.environ.get("PEA_SUPABASE_URL_PROD") or os.environ.get("PEA_SUPABASE_URL_TEST")
    key = os.environ.get("PEA_SUPABASE_ANON_PROD") or os.environ.get("PEA_SUPABASE_ANON_TEST")

    if not url or not key:
        print("Aviso: Variables PEA_SUPABASE_URL y PEA_SUPABASE_ANON no configuradas en el entorno.")
        print("Conectividad verificable en modo de prueba.")
        return 0

    try:
        cliente = ClienteHTTPSupabase(base_url=url, anon_key=key, timeout=5.0)
        datos = cliente.get("revision", params={"select": "valor", "limit": "1"})
        print(f"Conexión exitosa con Supabase ({url}). Revisión actual: {datos}")
        return 0
    except (ErrorPEA, OSError) as err:
        print(f"Error conectando a Supabase: {err}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = crear_parser()
    args = parser.parse_args(argv)

    if args.comando == "info":
        comando_info()
        return 0
    elif args.comando == "ping":
        return comando_ping()
    elif not args.comando:
        # Si no se pasó subcomando y no fue --version (manejado por argparse), mostrar ayuda
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
