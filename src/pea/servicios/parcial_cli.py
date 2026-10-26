"""Comandos del parcial aislados del despacho histórico de la CLI."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pea.datos.archivo_local import cargar_archivo, guardar_archivo, serializar_catalogo
from pea.excepciones import ErrorPEA
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.indicadores import calcular_indicador
from pea.servicios.servicio_dominio import CatalogoInvestigacion

URLS_PARCIAL = (
    ("grupo", "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099", "00000000002099"),
    ("investigador", "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917", "0000494917"),
)


def _imprimir_resultado(resultado: dict, etiqueta: str) -> None:
    marca = "Indicador" if resultado["completo"] else "Indicador parcial"
    print(f"{etiqueta} · {resultado['nombre']} · {marca}: {resultado['indicador']:.6f}")
    print("  Componente | Bruto | Máximo | Índice | Coef. | Aporte")
    for c in resultado["componentes"]:
        print(f"  {c['componente']} | {c['bruto']:.6f} | {c['maximo']:.6f} | {c['indice']:.6f} | {c['coeficiente']} | {c['aporte']:.6f}")
    print(f"  Incluidos: {len(resultado['incluidos'])} · excluidos: {len(resultado['excluidos'])} · estimados: {len(resultado.get('estimadas', []))}")


def ejecutar_respuestas(args) -> int:
    """Respuestas del PARCIAL 1 y 2: descarga las URL del enunciado y calcula ambos indicadores."""
    for ambito, url, codigo in URLS_PARCIAL:
        print(f"Descargando {url}")
        cat = CatalogoInvestigacion()
        ingesta = ServicioIngesta(cat)
        ingesta.encolar_url(url, persistir=False)
        informes = ingesta.procesar_todas()
        if not informes or any(not i.exito for i in informes):
            raise ValueError("La descarga no pudo completarse: " + "; ".join(i.mensaje for i in informes if not i.exito))
        datos = serializar_catalogo(cat)
        for estimar in (False, True):
            modo = "estimado (categoría base)" if estimar else "estricto (solo categorías publicadas)"
            _imprimir_resultado(calcular_indicador(datos, ambito, codigo, args.corte, None, None, estimar), f"{ambito.capitalize()} {modo}")
    return 0


def agregar_comandos(subparsers) -> None:
    r = subparsers.add_parser("respuestas-parcial", help="Calcula el indicador del grupo y del investigador del enunciado")
    r.add_argument("--corte", type=int, default=2023, help="Año final de observación")
    p = subparsers.add_parser("indicador", help="Indicador científico del grupo o investigador (Parcial 2)")
    p.add_argument("--ambito", choices=["grupo", "investigador"], required=True)
    p.add_argument("--codigo", help="Código GrupLAC o CvLAC")
    fuente = p.add_mutually_exclusive_group()
    fuente.add_argument("--archivo", help="Catálogo local JSON de PEA-i")
    fuente.add_argument("--url", help="URL SCIENTI que se descarga y procesa sin escribir en Supabase")
    p.add_argument("--corte", type=int, default=2023, help="Año final de observación (convocatoria 2024: 2023)")
    p.add_argument("--desde", type=int, help="Límite adicional para la ventana de observación")
    p.add_argument("--referencia", help="JSON con fuente, corte, desde y máximos de normalización")
    p.add_argument("--salida", help="Guardar desglose completo en JSON")
    p.add_argument("--guardar-catalogo", help="Conservar los datos descargados en un archivo local")
    p.add_argument(
        "--estimar-categorias",
        action="store_true",
        help="Puntuar con la categoría base de su tipología los productos sin calidad publicada (supuesto declarado)",
    )
    p.add_argument("--json", action="store_true", help="Mostrar el resultado JSON completo")
    p = subparsers.add_parser("guardar-local", help="Guardar catálogo remoto en JSON interoperable")
    p.add_argument("--salida", required=True)


def ejecutar_comando(args, obtener_cliente) -> int:
    cliente = None
    try:
        if args.comando == "respuestas-parcial":
            return ejecutar_respuestas(args)
        codigo = getattr(args, "codigo", None)
        if getattr(args, "archivo", None):
            cat = cargar_archivo(args.archivo)
        elif getattr(args, "url", None):
            cat = CatalogoInvestigacion()
            ingesta = ServicioIngesta(cat)
            ingesta.encolar_url(args.url, persistir=False)
            informes = ingesta.procesar_todas()
            if not informes or any(not i.exito for i in informes):
                raise ValueError(
                    "La descarga no pudo completarse: " + "; ".join(i.mensaje for i in informes if not i.exito)
                )
            consulta = parse_qs(urlparse(args.url).query)
            clave = "nro" if args.ambito == "grupo" else "cod_rh"
            codigo = codigo or consulta.get(clave, [None])[0]
        else:
            cliente = obtener_cliente()
            if cliente is None:
                raise ValueError("Indique un archivo local, una URL SCIENTI o configure Supabase.")
            cat = CatalogoInvestigacion(cliente=cliente)
            cat.recargar_todo()
        datos = serializar_catalogo(cat)
        if args.comando == "guardar-local":
            guardar_archivo(args.salida, datos)
            print("Catálogo local guardado.")
            return 0
        if not codigo:
            raise ValueError("Indique --codigo o una URL correspondiente al ámbito.")
        referencia = json.loads(Path(args.referencia).read_text(encoding="utf-8-sig")) if args.referencia else None
        resultado = calcular_indicador(
            datos, args.ambito, codigo, args.corte, args.desde, referencia, getattr(args, "estimar_categorias", False)
        )
        if args.guardar_catalogo:
            guardar_archivo(args.guardar_catalogo, datos)
        if args.salida:
            guardar_archivo(args.salida, resultado)
        if args.json:
            print(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False))
        else:
            etiqueta = "Indicador" if resultado["completo"] else "Indicador parcial"
            print(f"{resultado['nombre']} ({codigo}) · {etiqueta}: {resultado['indicador']:.6f}")
            print(resultado["referencia"])
            print("Componente | Indicador bruto | Máximo | Índice | Coeficiente | Aporte")
            for c in resultado["componentes"]:
                print(
                    f"{c['componente']} | {c['bruto']:.6f} | {c['maximo']:.6f} | {c['indice']:.6f} | {c['coeficiente']} | {c['aporte']:.6f}"
                )
            for aviso in resultado["avisos"]:
                print("Aviso: " + aviso)
            for e in resultado.get("estimadas", []):
                print(f"Estimado {e['codigo']}: {e['categoria']} · {e['regla']}")
            for p in resultado["excluidos"]:
                print(f"Excluido {p['codigo']}: {p['motivo']}")
        return 0
    except (OSError, ValueError, KeyError, ErrorPEA) as error:
        print(f"Error: {error}")
        return 1
    finally:
        if cliente is not None:
            cliente.cerrar_sesion()
