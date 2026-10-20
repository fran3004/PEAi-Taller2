"""Universidad Popular del Cesar (UPC)
Facultad de Ingenierías y Tecnologías
Programa: Ingeniería de Sistemas
Asignatura: Estructura de Datos
Taller: 2
Grupo: 8

Integrantes:
- franier fernandez (FF)
- santiago moreno (SM)

Índice de implementación:
Los puntos 1–13 enlazan, en orden, los requisitos R0–R12 documentados en
brain/10-Requisitos/SPEC.md. El enunciado original numerado 1–14 no está en
docs/entrada; por ello el punto 14 queda pendiente de cotejo. La sección C++
se marca pendiente, conforme a la instrucción de entrega.

1. R0, concurrencia y revisión:
   pea.datos.revision.ControladorRevision.verificar_consistencia
2. R1, grupos:
   pea.servicios.servicio_dominio.CatalogoInvestigacion.crear_grupo
3. R2, investigadores:
   pea.servicios.servicio_dominio.CatalogoInvestigacion.crear_investigador
4. R3, productos:
   pea.servicios.servicio_dominio.CatalogoInvestigacion.crear_producto
5. R4, multilista y coautoría:
   pea.estructuras.multilista.Multilista.agregar_producto
6. R5, lista doble:
   pea.estructuras.lista_doble.ListaDoble.insertar_final
7. R6, deshacer:
   pea.servicios.servicio_dominio.CatalogoInvestigacion.deshacer
8. R7, cola e importación por lotes:
   pea.ingesta.servicio_ingesta.ServicioIngesta.procesar_todas
   pea.cli.comando_importar_url_lote
9. R8, hipercubo:
   pea.estructuras.hipercubo.Hipercubo5D.acumular
10. R9, análisis estadístico:
    pea.servicios.servicio_estadisticas.ServicioEstadisticas.obtener_vista_institucional
11. R10, GUI Python:
    pea.gui.main
12. R11, persistencia atómica:
    pea.datos.repositorios.RepositorioProductos.crear_con_rpc
13. R12, extracción e importación:
    pea.ingesta.extractor_url.ExtractorURL.procesar_url
14. Punto por cotejar con el enunciado original; C++ pendiente:
    cpp/ (se rehace en terminal; no se declara cumplido).
"""

from pea.gui import main


if __name__ == "__main__":
    raise SystemExit(main())
