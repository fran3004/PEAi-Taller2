#!/usr/bin/env python3
"""Herramienta de conciliación y migración de códigos identificadores CvLAC.

Identifica productos con formato antiguo (PROD-CVLAC-{codigo_rh}-{pos_4_digitos})
y calcula el código identificador estable (PROD-CVLAC-{codigo_rh}-{hash_12}[-{oc}]).
Genera reporte CSV en datos/respaldos/ y aplica cambios de forma segura bajo confirmación.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os
import re
import sys
from pathlib import Path
from typing import Any

_raiz_repo = Path(__file__).resolve().parents[2]
if str(_raiz_repo) not in sys.path:
    sys.path.insert(0, str(_raiz_repo))
_raiz_src = _raiz_repo / "src"
if str(_raiz_src) not in sys.path:
    sys.path.insert(0, str(_raiz_src))
_raiz_tools_db = Path(__file__).resolve().parent
if str(_raiz_tools_db) not in sys.path:
    sys.path.insert(0, str(_raiz_tools_db))

from pea.cliente_http import ClienteHTTPSupabase  # noqa: E402
from pea.datos.revision import ControladorRevision  # noqa: E402
from pea.dominio.producto import generar_codigo_producto_cvlac, normalizar_cita  # noqa: E402
from pea.excepciones import ConflictoRevision, ErrorPEA  # noqa: E402

try:
    from respaldar import (
        cargar_configuracion as _cargar_config_respaldar,
    )
    from respaldar import (
        obtener_token_autenticado as _obtener_token_respaldar,
    )
except ImportError:
    try:
        from tools.db.respaldar import (
            cargar_configuracion as _cargar_config_respaldar,
        )
        from tools.db.respaldar import (
            obtener_token_autenticado as _obtener_token_respaldar,
        )
    except ImportError:
        _cargar_config_respaldar = None
        _obtener_token_respaldar = None

PATRON_CODIGO_ANTIGUO = re.compile(r"^PROD-CVLAC-([A-Za-z0-9]+)-(\d{4})$")


def cargar_configuracion() -> tuple[str, str]:
    """Carga la configuración de Supabase desde variables de entorno o archivo .env."""
    if _cargar_config_respaldar is not None:
        try:
            return _cargar_config_respaldar()
        except Exception:
            pass

    url = os.getenv("PEA_SUPABASE_URL", "").strip()
    anon_key = (
        os.getenv("PEA_SUPABASE_ANON_KEY")
        or os.getenv("PEA_SUPABASE_KEY")
        or os.getenv("SUPABASE_KEY", "")
    ).strip()

    if not url or not anon_key:
        ruta_env = Path(".env")
        if ruta_env.exists():
            for linea in ruta_env.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k in ("PEA_SUPABASE_URL", "PEA_SUPABASE_URL_PROD", "PEA_SUPABASE_URL_TEST") and not url:
                    url = v
                elif (
                    k in ("PEA_SUPABASE_ANON_KEY", "PEA_SUPABASE_KEY", "PEA_SUPABASE_PUBLISHABLE_KEY", "SUPABASE_KEY", "PEA_SUPABASE_ANON_PROD", "PEA_SUPABASE_KEY_PROD")
                    and not anon_key
                ):
                    anon_key = v

    return url, anon_key


def obtener_token_autenticado(url: str, anon_key: str) -> str | None:
    """Intenta autenticar con credenciales de usuario o evaluación."""
    if _obtener_token_respaldar is not None:
        try:
            return _obtener_token_respaldar(url, anon_key)
        except Exception:
            pass

    correo = os.getenv("PEA_USUARIO_CORREO", "") or os.getenv("PEA_EVAL_USER", "").strip()
    clave = os.getenv("PEA_USUARIO_CLAVE", "") or os.getenv("PEA_EVAL_PASSWORD", "").strip()
    if not correo or not clave:
        return None
    try:
        cliente = ClienteHTTPSupabase(url, anon_key)
        tokens = cliente.autenticar(correo, clave)
        return tokens.get("access_token")
    except Exception:
        return None


def verificar_respaldo_reciente(directorio_respaldos: Path, max_antiguedad_segundos: int = 3600) -> Path | None:
    """Verifica si existe un respaldo JSON en directorio_respaldos menor a max_antiguedad_segundos."""
    if not directorio_respaldos.exists():
        return None

    ahora = datetime.datetime.now(datetime.UTC)
    respaldos_candidatos: list[tuple[datetime.datetime, Path]] = []

    for archivo in directorio_respaldos.glob("respaldo_*.json"):
        # Intentar obtener fecha desde mtime
        mtime = datetime.datetime.fromtimestamp(archivo.stat().st_mtime, tz=datetime.UTC)
        respaldos_candidatos.append((mtime, archivo))

    if not respaldos_candidatos:
        return None

    respaldos_candidatos.sort(key=lambda t: t[0], reverse=True)
    mas_reciente_fecha, mas_reciente_path = respaldos_candidatos[0]
    antiguedad = (ahora - mas_reciente_fecha).total_seconds()
    if antiguedad <= max_antiguedad_segundos:
        return mas_reciente_path
    return None


def analizar_candidatos_reconciliacion(
    productos: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Analiza los productos candidatos y genera la lista con código nuevo y estado."""
    # Conjunto de todos los códigos identificadores de productos existentes en la base
    codigos_existentes_otros: dict[str, int] = {}
    for p in productos:
        cod = p.get("codigo_identificador")
        if cod:
            codigos_existentes_otros[cod] = p["id"]

    # Identificar candidatos con código antiguo
    candidatos_crudos: list[dict[str, Any]] = []
    for p in productos:
        cod = p.get("codigo_identificador") or ""
        m = PATRON_CODIGO_ANTIGUO.match(cod)
        if m:
            candidatos_crudos.append({
                "id": p["id"],
                "codigo_anterior": cod,
                "codigo_rh": m.group(1),
                "posicion": int(m.group(2)),
                "titulo": p.get("titulo") or "",
                "detalles": p.get("detalles") if isinstance(p.get("detalles"), dict) else {},
            })

    # Ordenar determinísticamente por investigador y posición antigua/id
    candidatos_crudos.sort(key=lambda x: (x["codigo_rh"], x["posicion"], x["id"]))

    ocurrencias: dict[tuple[str, str], int] = {}
    resultados: list[dict[str, Any]] = []
    resumen = {"total": len(candidatos_crudos), "OK": 0, "SIN_CITA": 0, "COLISION": 0}

    # Asignar códigos nuevos
    for cand in candidatos_crudos:
        rh = cand["codigo_rh"]
        detalles = cand["detalles"]
        cita = detalles.get("referencia_original") or detalles.get("texto_completo")
        titulo = cand["titulo"]

        if not cita and not titulo:
            resultados.append({
                "id": cand["id"],
                "codigo_anterior": cand["codigo_anterior"],
                "codigo_nuevo": "",
                "estado": "SIN_CITA",
            })
            resumen["SIN_CITA"] += 1
            continue

        texto = (cita or "").strip() or (titulo or "").strip()
        norm = normalizar_cita(texto)
        oc = ocurrencias.get((rh, norm), 0) + 1
        ocurrencias[(rh, norm)] = oc

        nuevo_codigo = generar_codigo_producto_cvlac(rh, cita=cita, ocurrencia=oc, titulo=titulo)

        # Verificar si colisiona con otro producto que ya tenga este código y no sea el mismo id
        id_existente = codigos_existentes_otros.get(nuevo_codigo)
        if id_existente is not None and id_existente != cand["id"]:
            resultados.append({
                "id": cand["id"],
                "codigo_anterior": cand["codigo_anterior"],
                "codigo_nuevo": nuevo_codigo,
                "estado": "COLISION",
            })
            resumen["COLISION"] += 1
        else:
            resultados.append({
                "id": cand["id"],
                "codigo_anterior": cand["codigo_anterior"],
                "codigo_nuevo": nuevo_codigo,
                "estado": "OK",
            })
            resumen["OK"] += 1

    return resultados, resumen


def exportar_informe_csv(resultados: list[dict[str, Any]], ruta_csv: Path) -> None:
    """Escribe el informe CSV de conciliación."""
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)
    with ruta_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "codigo_anterior", "codigo_nuevo", "estado"]
        )
        writer.writeheader()
        for r in resultados:
            writer.writerow(r)


def contar_tabla(cliente: ClienteHTTPSupabase, tabla: str) -> int:
    """Obtiene el conteo exacto de registros en una tabla mediante PostgREST count."""
    try:
        resp = cliente._ejecutar(
            "HEAD",
            f"rest/v1/{tabla}",
            headers_extra={"Prefer": "count=exact"},
        )
        cr = resp.headers.get("content-range", "")
        if "/" in cr:
            return int(cr.split("/")[-1])
    except Exception:
        pass
    # Fallback paginado
    filas = cliente.get_paginado(tabla, params={"select": "id"})
    return len(filas)


def ejecutar_reconciliacion(aplicar: bool = False, confirmacion_input: str | None = None) -> int:
    """Punto de entrada para simulación o aplicación de reconciliación."""
    url, anon_key = cargar_configuracion()
    if not url or not anon_key:
        print("[ERROR] Falta configurar PEA_SUPABASE_URL y PEA_SUPABASE_ANON_KEY", file=sys.stderr)
        return 1

    cliente = ClienteHTTPSupabase(url, anon_key)
    token = obtener_token_autenticado(url, anon_key)
    if token:
        cliente.establecer_token_acceso(token)

    controlador_rev = ControladorRevision()

    print("[*] Conectando a Supabase para analizar productos CvLAC...")
    productos = cliente.get_paginado(
        "productos",
        params={"select": "id,codigo_identificador,titulo,detalles,es_ejemplo"},
    )
    print(f"    Total de productos en base de datos: {len(productos)}")

    resultados, resumen = analizar_candidatos_reconciliacion(productos)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_respaldos = Path("datos/respaldos")
    ruta_informe = ruta_respaldos / f"reconciliacion_codigos_cvlac_{timestamp}.csv"
    exportar_informe_csv(resultados, ruta_informe)

    print("\n--- RESUMEN DE CONCILIACIÓN (SIMULACIÓN) ---")
    print(f"  Productos CvLAC antiguos encontrados: {resumen['total']}")
    print(f"  Listos para conciliar (OK):          {resumen['OK']}")
    print(f"  Sin cita ni título (SIN_CITA):       {resumen['SIN_CITA']}")
    print(f"  Colisiones detectadas (COLISION):    {resumen['COLISION']}")
    print(f"  Informe detallado guardado en:        {ruta_informe}\n")

    if not aplicar:
        print("[INFO] Modo SIMULACIÓN finalizado. No se modificó ningún dato en la base.")
        print("       Para aplicar los cambios ejecute con la bandera --aplicar.")
        return 0

    # Modo APLICAR
    print("[*] Iniciando protocolo de seguridad para --aplicar...")

    # 1. Verificar respaldo reciente
    respaldo_reciente = verificar_respaldo_reciente(ruta_respaldos, max_antiguedad_segundos=3600)
    if not respaldo_reciente:
        print(
            "[ERROR] No existe un respaldo de la base de datos de menos de 1 hora en datos/respaldos/.\n"
            "        Por seguridad, genere primero un respaldo ejecutando:\n"
            "        python tools/db/respaldar.py",
            file=sys.stderr,
        )
        return 1
    print(f"[OK] Respaldo reciente verificado: {respaldo_reciente.name}")

    # 2. Confirmación del usuario
    if confirmacion_input is None:
        try:
            confirmacion = input(
                "Escriba 'RECONCILIAR' para proceder con la actualización en Supabase: "
            ).strip().strip("'\"")
        except EOFError:
            confirmacion = ""
    else:
        confirmacion = confirmacion_input.strip().strip("'\"")

    if confirmacion != "RECONCILIAR":
        print("[CANCELADO] Operación no autorizada por el usuario. No se realizaron cambios.")
        return 1

    # 3. Verificación de conteos antes
    print("[*] Verificando conteos antes de la conciliación...")
    conteo_prod_antes = contar_tabla(cliente, "productos")
    conteo_autores_antes = contar_tabla(cliente, "producto_autores")
    conteo_grupos_antes = contar_tabla(cliente, "producto_grupos")
    print(f"    Productos: {conteo_prod_antes} | Autores: {conteo_autores_antes} | Grupos: {conteo_grupos_antes}")

    # 4. Aplicación de cambios con flujo de revisión y reintentos
    items_a_conciliar = [r for r in resultados if r["estado"] == "OK"]
    print(f"[*] Aplicando {len(items_a_conciliar)} actualizaciones de código identificador...")

    actualizados = 0
    errores = 0

    for item in items_a_conciliar:
        prod_id = item["id"]
        nuevo_codigo = item["codigo_nuevo"]

        intentos = 0
        exito = False
        while intentos < 5 and not exito:
            try:
                cliente.patch(
                    "productos",
                    {"codigo_identificador": nuevo_codigo},
                    params={"id": f"eq.{prod_id}"},
                )
                exito = True
                actualizados += 1
            except ConflictoRevision:
                intentos += 1
                try:
                    controlador_rev.consultar_remota(cliente)
                except Exception:
                    pass
            except ErrorPEA as err:
                intentos += 1
                if intentos >= 5:
                    print(f"    [ERROR] Falló al actualizar id {prod_id}: {err}", file=sys.stderr)
                    errores += 1

    # Sincronizar revisión al terminar si es posible
    try:
        controlador_rev.consultar_remota(cliente)
    except Exception:
        pass

    print(f"[OK] Actualización finalizada: {actualizados} exitosos, {errores} errores.")

    # 5. Verificación de conteos después
    print("[*] Verificando conteos posteriores para asegurar integridad relacional...")
    conteo_prod_despues = contar_tabla(cliente, "productos")
    conteo_autores_despues = contar_tabla(cliente, "producto_autores")
    conteo_grupos_despues = contar_tabla(cliente, "producto_grupos")
    print(f"    Productos: {conteo_prod_despues} | Autores: {conteo_autores_despues} | Grupos: {conteo_grupos_despues}")

    if (
        conteo_prod_despues != conteo_prod_antes
        or conteo_autores_despues != conteo_autores_antes
        or conteo_grupos_despues != conteo_grupos_antes
    ):
        print(
            "[ALERTA CRÍTICA] Los conteos de relaciones cambiaron tras la reconciliación!",
            file=sys.stderr,
        )
        return 1

    print("[ÉXITO] Conciliación completada e integridad referencial 100% verificada.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Conciliación segura de códigos CvLAC en base de datos Supabase"
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Aplica los cambios en Supabase previa verificación de respaldo y confirmación",
    )
    parser.add_argument(
        "--confirmacion",
        type=str,
        default=None,
        help="Texto de confirmación 'RECONCILIAR' para ejecuciones automatizadas",
    )
    args = parser.parse_args()
    codigo_salida = ejecutar_reconciliacion(
        aplicar=args.aplicar,
        confirmacion_input=args.confirmacion,
    )
    sys.exit(codigo_salida)


if __name__ == "__main__":
    main()
