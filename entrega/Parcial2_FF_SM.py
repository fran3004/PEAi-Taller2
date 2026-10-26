"""UPC · Estructura de Datos · Parcial 2 · Grupo 8 · FF / SM.

Autores: franier fernandez y santiago moreno.
Entrada académica del programa Python del proyecto modular completo (ver docs/parcial-2.md).

Respuestas a los ejercicios:
  Puntos 1-12 (gestión, listas, URL/PDF/CSV, filtros, dashboard):
    python Parcial2_FF_SM.py                  abre la interfaz gráfica (Supabase, archivo local o sin datos)
  PARCIAL 1 y 2 (indicador del grupo 00000000002099 y del investigador 0000494917):
    python Parcial2_FF_SM.py --respuestas     descarga ambas URL y calcula los dos indicadores
  Módulos: pea.servicios.indicadores (fórmula), pea.estructuras (listas, multilista, pila, cola, hipercubo).
Instalación: scripts/preparar.ps1. Sin datos: --vacio. Archivo local: --archivo datos/ejemplo-parcial.json.
No es una copia monolítica ni reemplaza las dependencias de la distribución.
"""

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--respuestas"]:
        from pea.cli import main as cli

        return cli(["respuestas-parcial", *args[1:]])
    from pea.gui import main as gui

    return gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
