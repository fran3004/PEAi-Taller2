"""Entrada del ejecutable portable, con diagnóstico de arranque legible."""

import ctypes
import sys

from pea.gui import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # No volcar variables de entorno, credenciales ni excepciones de red a disco.
        ctypes.windll.user32.MessageBoxW(
            None,
            "No se pudo iniciar PEA-i. Extraiga de nuevo el ZIP completo y conserve "
            "la carpeta _internal junto al ejecutable. Consulte README.md.",
            "PEA-i: error de inicio",
            0x10,
        )
        sys.exit(1)
