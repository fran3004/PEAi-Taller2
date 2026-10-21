"""Entrada de consola portable para comandos y comprobación cruzada."""

import sys

from pea.cli import main

if __name__ == "__main__":
    # El ejecutable congelado no aplica PYTHONIOENCODING como el interprete.
    # La verificacion cruzada y los procesos padre intercambian UTF-8.
    for flujo in (sys.stdin, sys.stdout, sys.stderr):
        if flujo is not None and hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    if "--comprobar-conexion" in sys.argv:
        from pea.servicios.servicio_aplicacion import ServicioAplicacion

        servicio = ServicioAplicacion()
        estado = servicio.conectar()
        print(f"Conexion automatica: {estado.modo.value}; revision {estado.revision_local}")
        servicio.desconectar()
        raise SystemExit(0)
    if "--autoprueba-gui" in sys.argv:
        from pea.gui import main as main_gui

        raise SystemExit(main_gui(["--autoprueba"]))
    if "--verificar-cruzada" in sys.argv:
        from pea.servicios.servicio_verificacion_cruzada import ServicioVerificacionCruzada

        resultado = ServicioVerificacionCruzada().ejecutar()
        print(resultado.mensaje)
        for paso in resultado.pasos:
            print(f"{paso.nombre}: {paso.detalle}")
        raise SystemExit(0 if resultado.exito else 1)
    raise SystemExit(main())
