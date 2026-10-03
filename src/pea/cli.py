"""Línea de comandos (CLI) institucional para PEA-i."""

import argparse
import csv
import os
import sys
from pathlib import Path

from pea.cliente_http import ClienteHTTPSupabase
from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.excepciones import ErrorPEA
from pea.ingesta.lector_csv import LectorCSV
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.servicio_dominio import CatalogoInvestigacion
from pea.version import APP_NAME, APP_VERSION, INSTITUCION, obtener_version


def _obtener_cliente_desde_entorno() -> ClienteHTTPSupabase | None:
    url = os.environ.get("PEA_SUPABASE_URL_PROD") or os.environ.get("PEA_SUPABASE_URL_TEST")
    key = os.environ.get("PEA_SUPABASE_ANON_PROD") or os.environ.get("PEA_SUPABASE_ANON_TEST")
    if url and key:
        return ClienteHTTPSupabase(base_url=url, anon_key=key, timeout=10.0)
    return None


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pea",
        description=f"{APP_NAME} · Programa Estadístico de Análisis de Investigación ({INSTITUCION})",
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

    # Comando verificar (antes ping)
    subparsers.add_parser("verificar", help="Verifica la conexión HTTPS, TLS y número de revisión con Supabase")
    subparsers.add_parser("ping", help="Alias de verificar")

    # Comando resumen
    parser_resumen = subparsers.add_parser("resumen", help="Muestra el resumen estadístico de entidades en memoria y remotas")
    parser_resumen.add_argument("--json", action="store_true", help="Emite el resumen en formato JSON compacto canónico")


    # Comando importar-url
    parser_url = subparsers.add_parser("importar-url", help="Extrae e ingesta datos desde portales SCIENTI (GrupLAC o CvLAC)")
    parser_url.add_argument("--url", "-u", required=True, help="URL HTTPS de GrupLAC o CvLAC")
    parser_url.add_argument("--persistir", "-p", action="store_true", help="Persiste las entidades en la base de datos remota")
    parser_url.add_argument("--anonimizar", action="store_true", help="Anonimiza correos y nombres personales en notas públicas")
    parser_url.add_argument("--privado", action="store_true", help="Guarda la transcripción en carpeta privada")
    parser_url.add_argument("--salida", "-s", default="datos/fuentes/extraccion", help="Directorio destino para Markdown, JSON y CSV")

    # Comando importar-pdf
    parser_pdf = subparsers.add_parser("importar-pdf", help="Extrae texto y tablas desde documentos oficiales PDF")
    parser_pdf.add_argument("--archivo", "-a", required=True, help="Ruta al archivo PDF a procesar")
    parser_pdf.add_argument("--salida", "-s", default="datos/fuentes/pdf", help="Directorio destino para transcripción Markdown")

    # Comando importar-csv
    parser_importar = subparsers.add_parser("importar-csv", help="Importa entidades desde archivos CSV tolerante a fallos")
    parser_importar.add_argument("--archivo", "-a", required=True, help="Ruta al archivo CSV a importar")
    parser_importar.add_argument(
        "--tipo",
        "-t",
        choices=["grupos", "investigadores", "productos", "autores"],
        default=None,
        help="Tipo de entidad contenida en el CSV (opcional, se detecta automáticamente si se omite)",
    )
    parser_importar.add_argument("--persistir", "-p", action="store_true", help="Persiste las entidades en la base de datos remota")

    # Comando exportar-csv
    parser_exportar = subparsers.add_parser("exportar-csv", help="Exporta entidades actuales a archivos CSV")
    parser_exportar.add_argument(
        "--directorio",
        "-d",
        default="datos/fuentes/csv",
        help="Directorio de destino para los archivos CSV",
    )

    # Comando cargar-ejemplo
    subparsers.add_parser("cargar-ejemplo", help="Carga datos oficiales de ejemplo con prefijo PRUEBA-")

    # Comando aplicar-escenario
    subparsers.add_parser("aplicar-escenario", help="Ejecuta un escenario secuencial de mutaciones y reversión (Undo)")

    return parser


def comando_info() -> None:
    print(f"Nombre: {APP_NAME}")
    print(f"Versión: {APP_VERSION}")
    print(f"Institución: {INSTITUCION}")
    print("Arquitectura: Python 3.12 / PySide6 / HTTPS PostgREST / Estructuras Hechas a Mano")


def comando_verificar() -> int:
    cliente = _obtener_cliente_desde_entorno()
    if cliente is None:
        print("Aviso: Variables PEA_SUPABASE_URL y PEA_SUPABASE_ANON no configuradas en el entorno.")
        print(f"Estado local: {obtener_version()} operando en modo desconectado.")
        return 0

    try:
        catalogo = CatalogoInvestigacion(cliente=cliente)
        rev = catalogo.controlador_revision.consultar_remota(cliente)
        print("============================================================")
        print("ESTADO DE CONEXIÓN REMOTA SUPABASE")
        print("============================================================")
        print(f"Base URL: {cliente.base_url}")
        print("Protocolo: HTTPS / TLS activo")
        print(f"Revisión remota actual (meta.revision): {rev}")
        print("Conectividad: OK")
        print("============================================================")
        return 0
    except (ErrorPEA, OSError) as err:
        print(f"Error conectando a Supabase: {err}", file=sys.stderr)
        return 1


def comando_resumen(salida_json: bool = False) -> int:
    cliente = _obtener_cliente_desde_entorno()
    catalogo = CatalogoInvestigacion(cliente=cliente)
    if cliente is not None:
        try:
            catalogo.recargar_todo()
        except Exception as err:
            if not salida_json:
                print(f"Aviso: no se pudo recargar de la base remota ({err}). Mostrando estado local.")

    if salida_json:
        print(catalogo.resumen_json())
        return 0

    total_grupos = len(catalogo.grupos)
    grupos_activos = sum(1 for g in catalogo.grupos if g.activo)

    total_invs = len(catalogo.investigadores)
    invs_activos = sum(1 for i in catalogo.investigadores if i.activo)

    total_prods = len(catalogo.multilista_productos)
    prods_activos = sum(1 for p in catalogo.multilista_productos if p.activo)

    print("============================================================")
    print("RESUMEN GENERAL DEL CATÁLOGO DE INVESTIGACIÓN")
    print("============================================================")
    print(f"Grupos de Investigación: {total_grupos} totales ({grupos_activos} activos)")
    print(f"Investigadores:          {total_invs} totales ({invs_activos} activos)")
    print(f"Productos Científicos:   {total_prods} totales ({prods_activos} activos)")
    print(f"Pila de Deshacer:        {len(catalogo.pila_deshacer)} operaciones apiladas")
    print("============================================================")
    return 0



def comando_importar_url(
    url: str,
    persistir: bool = False,
    anonimizar: bool = False,
    es_privado: bool = False,
    salida_str: str = "datos/fuentes/extraccion",
) -> int:
    cliente = _obtener_cliente_desde_entorno() if persistir else None
    catalogo = CatalogoInvestigacion(cliente=cliente)
    servicio = ServicioIngesta(catalogo)

    print(f"Encolando extracción web: {url}")
    tarea = servicio.encolar_url(
        url=url,
        persistir=persistir,
        anonimizar=anonimizar,
        es_privado=es_privado,
        salida_dir=Path(salida_str),
    )
    print(f"Tarea encolada: ID={tarea.id_tarea}, Estado={tarea.estado}")

    informe = servicio.procesar_siguiente()
    if informe and informe.exito:
        print("============================================================")
        print("EXTRACCIÓN WEB Y PROCESAMIENTO COMPLETADOS")
        print("============================================================")
        print(f"Grupos:        {informe.grupos_procesados}")
        print(f"Investigadores:{informe.investigadores_procesados}")
        print(f"Productos:     {informe.productos_procesados}")
        print("Archivos generados:")
        for k, v in informe.archivos_generados.items():
            print(f" - {k}: {v}")
        print("============================================================")
        return 0
    else:
        err_msg = informe.mensaje if informe else "Fallo desconocido"
        print(f"Error en la extracción web: {err_msg}", file=sys.stderr)
        return 1


def comando_importar_pdf(archivo_str: str, salida_str: str = "datos/fuentes/pdf") -> int:
    archivo = Path(archivo_str)
    if not archivo.exists():
        print(f"Error: El archivo PDF {archivo} no existe.", file=sys.stderr)
        return 1

    catalogo = CatalogoInvestigacion()
    servicio = ServicioIngesta(catalogo)

    print(f"Encolando procesamiento de PDF: {archivo.name}")
    tarea = servicio.encolar_pdf(ruta_pdf=archivo, salida_dir=Path(salida_str))
    print(f"Tarea encolada: ID={tarea.id_tarea}, Estado={tarea.estado}")
    informe = servicio.procesar_siguiente()

    if informe and informe.exito:
        print("============================================================")
        print("PROCESAMIENTO DE PDF COMPLETADO")
        print("============================================================")
        print(f"Mensaje: {informe.mensaje}")
        if informe.advertencias:
            print("Avisos:")
            for adv in informe.advertencias:
                print(f" - ⚠️ {adv}")
        for k, v in informe.archivos_generados.items():
            print(f" - {k}: {v}")
        print("============================================================")
        return 0
    else:
        err_msg = informe.mensaje if informe else "Error al procesar PDF"
        print(f"Error al procesar PDF: {err_msg}", file=sys.stderr)
        return 1


def comando_importar_csv(archivo_str: str, tipo: str | None = None, persistir: bool = False) -> int:
    archivo = Path(archivo_str)
    if not archivo.exists():
        print(f"Error: El archivo {archivo} no existe.", file=sys.stderr)
        return 1

    cliente = _obtener_cliente_desde_entorno() if persistir else None
    catalogo = CatalogoInvestigacion(cliente=cliente)
    servicio = ServicioIngesta(catalogo)

    tipo_resuelto = tipo or LectorCSV.detectar_tipo_archivo(archivo)
    print(f"Encolando importación CSV: {archivo.name} (tipo resuelto: '{tipo_resuelto}')")
    servicio.encolar_csv(ruta_csv=archivo, tipo_entidad=tipo_resuelto, persistir=persistir)

    informe = servicio.procesar_siguiente()
    if informe and informe.exito:
        print("============================================================")
        print(f"IMPORTACIÓN CSV ({tipo_resuelto}) COMPLETADA")
        print("============================================================")
        print(f"Grupos:        {informe.grupos_procesados}")
        print(f"Investigadores:{informe.investigadores_procesados}")
        print(f"Productos:     {informe.productos_procesados}")
        print(f"Autores:       {informe.autores_procesados}")
        if informe.filas_erroneas:
            print(f"Avisos: {len(informe.filas_erroneas)} filas con errores ignoradas:")
            for err in informe.filas_erroneas:
                print(f" - Fila {err.get('fila')}: {err.get('error')}")
        print("============================================================")
        return 0
    else:
        err_msg = informe.mensaje if informe else "Fallo durante la importación CSV"
        print(f"Error al importar CSV: {err_msg}", file=sys.stderr)
        return 1


def comando_exportar_csv(directorio_str: str) -> int:
    directorio = Path(directorio_str)
    directorio.mkdir(parents=True, exist_ok=True)

    cliente = _obtener_cliente_desde_entorno()
    catalogo = CatalogoInvestigacion(cliente=cliente)
    if cliente is not None:
        try:
            catalogo.recargar_todo()
        except Exception as err:
            print(f"Aviso al recargar datos remotos: {err}")

    # 1. Exportar Grupos
    ruta_grupos = directorio / "grupos.csv"
    with ruta_grupos.open("w", encoding="utf-8", newline="") as f:
        campos = ["codigo_gruplac", "nombre", "categoria", "lider", "institucion_principal", "activo"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for g in catalogo.grupos:
            escritor.writerow({c: getattr(g, c, "") for c in campos})

    # 2. Exportar Investigadores
    ruta_invs = directorio / "investigadores.csv"
    with ruta_invs.open("w", encoding="utf-8", newline="") as f:
        campos = ["codigo_rh", "nombre_completo", "categoria", "formacion_academica", "nacionalidad", "activo"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for inv in catalogo.investigadores:
            escritor.writerow({c: getattr(inv, c, "") for c in campos})

    # 3. Exportar Productos
    ruta_prods = directorio / "productos.csv"
    with ruta_prods.open("w", encoding="utf-8", newline="") as f:
        campos = ["codigo_identificador", "titulo", "tipo_mayor", "subtipo", "ano", "estado_validacion", "activo"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for p in catalogo.multilista_productos:
            escritor.writerow({c: getattr(p, c, "") for c in campos})

    print(f"Exportación completada en directorio: {directorio.resolve()}")
    return 0


def comando_cargar_ejemplo() -> int:
    cliente = _obtener_cliente_desde_entorno()
    catalogo = CatalogoInvestigacion(cliente=cliente)
    persistir = cliente is not None

    g = Grupo(
        codigo_gruplac="PRUEBA-GRP-CLI-01",
        nombre="Grupo de Prueba Automatizada CLI",
        categoria="A1",
        lider="Investigador Líder CLI",
        es_ejemplo=True,
    )
    inv1 = Investigador(
        codigo_rh="PRUEBA-INV-CLI-01",
        nombre_completo="Investigador Líder CLI",
        categoria="Senior",
        formacion_academica="Doctorado",
        es_ejemplo=True,
    )
    inv2 = Investigador(
        codigo_rh="PRUEBA-INV-CLI-02",
        nombre_completo="Investigador Asistente CLI",
        categoria="Junior",
        formacion_academica="Maestria",
        es_ejemplo=True,
    )

    try:
        catalogo.crear_grupo(g, persistir=persistir)
        catalogo.crear_investigador(inv1, persistir=persistir)
        catalogo.crear_investigador(inv2, persistir=persistir)
        catalogo.vincular_integrante(g.codigo_gruplac, inv1.codigo_rh, rol="Lider", persistir=persistir)
        catalogo.vincular_integrante(g.codigo_gruplac, inv2.codigo_rh, rol="Investigador", persistir=persistir)

        p = Producto(
            codigo_identificador="PRUEBA-PROD-CLI-01",
            titulo="Artículo Científico de Prueba CLI",
            tipo_mayor="GNC",
            subtipo="Artículo",
            ano=2024,
            estado_validacion="Avalado",
            es_ejemplo=True,
        )
        catalogo.crear_producto(
            p,
            codigo_gruplac=g.codigo_gruplac,
            codigos_rh_autores=[inv1.codigo_rh, inv2.codigo_rh],
            persistir=persistir,
        )
        print("Datos de ejemplo cargados exitosamente (1 grupo, 2 investigadores, 1 producto enlazado).")
        return 0
    except Exception as err:
        print(f"Aviso al cargar datos de ejemplo: {err}")
        return 0


def comando_aplicar_escenario() -> int:
    print("Iniciando escenario funcional de mutaciones y reversión...")
    catalogo = CatalogoInvestigacion()

    # 1. Crear entidades
    g = Grupo(codigo_gruplac="SCN-GRP-01", nombre="Grupo Escenario 1", categoria="A")
    inv = Investigador(codigo_rh="SCN-INV-01", nombre_completo="Dra. Investigadora Escenario")
    catalogo.crear_grupo(g, persistir=False)
    catalogo.crear_investigador(inv, persistir=False)
    print(f" [OK] Grupo {g.codigo_gruplac} e Investigador {inv.codigo_rh} creados en estructuras.")

    # 2. Crear producto en Multilista
    prod = Producto(
        codigo_identificador="SCN-PRD-01",
        titulo="Software de Simulación Multidimensional",
        tipo_mayor="DTI",
        subtipo="Software",
        ano=2025,
        estado_validacion="Avalado",
    )
    catalogo.crear_producto(
        prod,
        codigo_gruplac=g.codigo_gruplac,
        codigos_rh_autores=[inv.codigo_rh],
        persistir=False,
    )
    print(" [OK] Producto creado y enlazado en Multilista (Grupo e Investigador).")

    # 3. Desactivar producto
    catalogo.desactivar_producto(prod.codigo_identificador, persistir=False)
    assert not prod.activo, "El producto debería estar inactivo"
    print(" [OK] Desactivación lógica aplicada: prod.activo = False.")

    # 4. Deshacer desactivación (Undo)
    cmd = catalogo.deshacer(persistir=False)
    assert prod.activo, "El producto debería haber vuelto a activo=True tras deshacer"
    print(f" [OK] Deshacer completado ({cmd.descripcion if cmd else ''}): prod.activo = True.")

    # 5. Eliminar producto
    catalogo.eliminar_producto(prod.codigo_identificador, persistir=False)
    assert catalogo.buscar_producto(prod.codigo_identificador) is None
    print(" [OK] Eliminación física completada: producto retirado de todas las listas.")

    print("Escenario completado exitosamente sin discrepancias.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = crear_parser()
    args = parser.parse_args(argv)

    if args.comando == "info":
        comando_info()
        return 0
    elif args.comando in ("verificar", "ping"):
        return comando_verificar()
    elif args.comando == "resumen":
        return comando_resumen(salida_json=args.json)

    elif args.comando == "importar-url":
        return comando_importar_url(
            url=args.url,
            persistir=args.persistir,
            anonimizar=args.anonimizar,
            es_privado=args.privado,
            salida_str=args.salida,
        )
    elif args.comando == "importar-pdf":
        return comando_importar_pdf(archivo_str=args.archivo, salida_str=args.salida)
    elif args.comando == "importar-csv":
        return comando_importar_csv(args.archivo, tipo=args.tipo, persistir=args.persistir)
    elif args.comando == "exportar-csv":
        return comando_exportar_csv(args.directorio)
    elif args.comando == "cargar-ejemplo":
        return comando_cargar_ejemplo()
    elif args.comando == "aplicar-escenario":
        return comando_aplicar_escenario()
    elif not args.comando:
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
