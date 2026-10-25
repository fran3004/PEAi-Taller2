"""Comprueba autorías CSV reales en Python/C++; solo escribe fixtures PRUEBA-.

Ejecutar como módulo desde la raíz. Las credenciales normales se leen de .env,
igual que en tools.db.respaldar; nunca se imprimen ni se guardan en la evidencia.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from pea.cliente_http import ClienteHTTPSupabase
from pea.datos.revision import ControladorRevision
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.servicio_dominio import CatalogoInvestigacion
from tools.db.respaldar import TABLAS_A_RESPALDAR, cargar_configuracion, obtener_token_autenticado


def exigir(condicion, mensaje):
    # No usar assert: esta comprobación debe funcionar también con python -O.
    if not condicion:
        raise RuntimeError(mensaje)


def error_seguro(error, etapa):
    detalle = getattr(error, "detalle", None)
    codigo = detalle.get("code") if isinstance(detalle, dict) else None
    return {"etapa": etapa, "tipo": type(error).__name__, "codigo_postgres": codigo}


class ClienteSintetico(ClienteHTTPSupabase):
    """Bloquea escrituras ajenas a los códigos y pares de esta ejecución."""

    def __init__(self, url, clave, escenarios):
        super().__init__(url, clave)
        self.escenarios = escenarios
        self.duplicados = 0

    def _mapear_error(self, resp):
        if resp.status_code == 409:
            try:
                self.duplicados += resp.json().get("code") == "23505"
            except ValueError:
                pass
        super()._mapear_error(resp)

    def _ejecutar(self, metodo, ruta, params=None, json_data=None, **opciones):
        consulta_revision = metodo == "POST" and ruta == "rest/v1/rpc/obtener_revision_actual"
        if metodo not in ("GET", "HEAD") and not consulta_revision:
            tabla = ruta.removeprefix("rest/v1/")
            permitido = False
            for escenario in self.escenarios:
                campo = {"productos": "codigo_identificador", "investigadores": "codigo_rh"}.get(tabla)
                codigo = escenario["codigo_p" if tabla == "productos" else "codigo_i"]
                if campo and metodo == "POST" and isinstance(json_data, dict):
                    permitido |= json_data.get(campo) == codigo and json_data.get("es_ejemplo") is True
                if campo and metodo == "DELETE" and params:
                    permitido |= params.get(campo) == f"eq.{codigo}" and params.get("es_ejemplo") == "eq.true"
                if tabla == "producto_autores" and escenario.get("producto") and escenario.get("investigador"):
                    par = {"producto_id": escenario["producto"]["id"],
                           "investigador_id": escenario["investigador"]["id"]}
                    if metodo == "POST" and isinstance(json_data, dict):
                        permitido |= all(json_data.get(k) == v for k, v in par.items()) and json_data.get("es_ejemplo") is True
                    if metodo == "DELETE" and params:
                        permitido |= params == {**{k: f"eq.{v}" for k, v in par.items()}, "es_ejemplo": "eq.true"}
            exigir(permitido, "Escritura bloqueada fuera de los fixtures sintéticos")
        return super()._ejecutar(metodo, ruta, params=params, json_data=json_data, **opciones)


def conteos(cliente):
    resultado = {}
    for tabla in TABLAS_A_RESPALDAR:
        resp = cliente._ejecutar("HEAD", f"rest/v1/{tabla}", prefer="count=exact")
        total = resp.headers.get("Content-Range", "").rsplit("/", 1)[-1]
        exigir(total.isdecimal(), f"Sin conteo exacto: {tabla}")
        resultado[tabla] = int(total)
    return resultado


def huellas_reales(cliente):
    resultado = {}
    for tabla in ("grupos", "investigadores", "productos", "producto_autores"):
        filas = cliente.get_paginado(tabla, {"select": "*", "es_ejemplo": "eq.false", "order": "id.asc"})
        serializado = json.dumps(filas, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        resultado[tabla] = {"filas": len(filas), "sha256": hashlib.sha256(serializado.encode()).hexdigest()}
    return resultado


def padres(cliente, escenario):
    for tabla, clave, campo, codigo in (
        ("productos", "producto", "codigo_identificador", escenario["codigo_p"]),
        ("investigadores", "investigador", "codigo_rh", escenario["codigo_i"]),
    ):
        filas = cliente.get(tabla, {campo: f"eq.{codigo}", "es_ejemplo": "eq.true"})
        exigir(len(filas) <= 1, "Código sintético inesperadamente repetido")
        escenario[clave] = filas[0] if filas else None


def filtro_autoria(escenario):
    return {"producto_id": f'eq.{escenario["producto"]["id"]}',
            "investigador_id": f'eq.{escenario["investigador"]["id"]}', "es_ejemplo": "eq.true"}


def comprobar_fila(cliente, escenario):
    filtro = {k: v for k, v in filtro_autoria(escenario).items() if k != "es_ejemplo"}
    filas = cliente.get("producto_autores", filtro)
    exigir(len(filas) == 1, "No hay exactamente una autoría remota")
    fila = filas[0]
    exigir(fila["es_ejemplo"] is True and fila["activo"] is True and fila["orden_autoria"] == 2,
           "Los campos de la autoría no coinciden")
    return fila


def probar_python(cliente, escenario, csv):
    catalogo = CatalogoInvestigacion(cliente)
    catalogo.crear_producto(Producto.model_validate(escenario["producto"]), persistir=False)
    catalogo.crear_investigador(Investigador.model_validate(escenario["investigador"]), persistir=False)
    servicio = ServicioIngesta(catalogo)
    duplicados_antes = cliente.duplicados
    guardada = None
    for intento in range(2):
        servicio.encolar_csv(csv, "autores", persistir=True)
        informe = servicio.procesar_siguiente()
        exigir(informe is not None and informe.exito and informe.autores_procesados == 1
               and not informe.advertencias and not informe.filas_erroneas, "Falló la ingesta Python")
        fila = comprobar_fila(cliente, escenario)
        if intento == 0:
            guardada = fila
        else:
            exigir(fila == guardada and cliente.duplicados == duplicados_antes + 1,
                   "No se confirmó el duplicado idempotente Python con 23505")
    return {"guardado": True, "duplicado_idempotente": True, "codigo_duplicado": "23505", "importaciones_csv": 2}


def limpiar(cliente, escenarios, errores):
    for escenario in escenarios:
        if not escenario.get("escritura_iniciada"):
            continue
        try:
            # Buscar por código también cubre un POST exitoso cuya respuesta se perdió.
            padres(cliente, escenario)
            if escenario.get("producto") and escenario.get("investigador"):
                filtro = filtro_autoria(escenario)
                cliente.eliminar("producto_autores", filtro)
                exigir(not cliente.get("producto_autores", filtro), "Quedó una autoría sintética")
            for tabla, campo, codigo in (("productos", "codigo_identificador", escenario["codigo_p"]),
                                         ("investigadores", "codigo_rh", escenario["codigo_i"])):
                # El doble filtro nunca incluye registros reales ni fixtures de otra ejecución.
                filtro = {campo: f"eq.{codigo}", "es_ejemplo": "eq.true"}
                if cliente.get(tabla, filtro):
                    cliente.eliminar(tabla, filtro)
                exigir(not cliente.get(tabla, {campo: f"eq.{codigo}"}), "Quedó un padre sintético")
            escenario["limpieza"] = True
        except Exception as error:
            errores.append(error_seguro(error, f'limpieza_{escenario["lenguaje"]}'))


def ejecutar(args):
    # investigadores.codigo_rh es varchar(30) en el esquema remoto.
    prefijo = "PRUEBA-ACSV-" + uuid4().hex[:12]
    escenarios = [{"lenguaje": lenguaje, "codigo_p": f"{prefijo}-{sufijo}-P",
                   "codigo_i": f"{prefijo}-{sufijo}-I"} for lenguaje, sufijo in (("python", "PY"), ("cpp", "CPP"))]
    exigir(all(len(e["codigo_i"]) <= 30 for e in escenarios), "Código de investigador demasiado largo")
    evidencia = {"inicio_utc": datetime.now(UTC).isoformat(), "prefijo": prefijo,
                 "escenarios": escenarios, "errores": [], "completa": False}
    args.salida.parent.mkdir(parents=True, exist_ok=True)

    def guardar():
        args.salida.write_text(json.dumps(evidencia, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    guardar()  # Deja los códigos para diagnóstico incluso si el proceso se interrumpe.
    cliente = None
    etapa = "preparacion"
    try:
        exigir(args.cpp.is_file(), "Falta compilar el ejecutable C++")
        url, clave = cargar_configuracion()
        cliente = ClienteSintetico(url, clave, escenarios)
        cliente.establecer_token_acceso(obtener_token_autenticado(url, clave))
        evidencia["proyecto"] = url.split("//", 1)[1].split(".", 1)[0]
        etapa = "lectura_inicial"
        evidencia["antes"] = conteos(cliente)
        evidencia["reales_antes"] = huellas_reales(cliente)
        evidencia["revision_antes"] = ControladorRevision().consultar_remota(cliente)
        guardar()
        print("Conteos iniciales y huellas de datos reales registrados.", flush=True)
        for escenario in escenarios:
            etapa = f'fixture_{escenario["lenguaje"]}'
            padres(cliente, escenario)
            exigir(not escenario["producto"] and not escenario["investigador"], "Colisión de códigos sintéticos")
            escenario["escritura_iniciada"] = True
            cliente.post("productos", {"codigo_identificador": escenario["codigo_p"],
                         "titulo": escenario["codigo_p"], "tipo_mayor": "GNC", "subtipo": "Artículo de investigación",
                         "ano": 2024, "estado_validacion": "No avalado", "es_ejemplo": True})
            cliente.post("investigadores", {"codigo_rh": escenario["codigo_i"],
                         "nombre_completo": escenario["codigo_i"], "sexo": "No especificado",
                         "categoria": "Sin categoría / Vinculado", "formacion_academica": "Pregrado",
                         "es_ejemplo": True})
            padres(cliente, escenario)
            exigir(escenario["producto"] and escenario["investigador"], "No se pudieron leer los fixtures")
            with TemporaryDirectory(prefix="PRUEBA-autores-") as temporal:
                csv = Path(temporal) / "autores.csv"
                csv.write_text("producto_codigo,investigador_codigo,orden_autoria\n"
                               f'{escenario["codigo_p"]},{escenario["codigo_i"]},2\n', encoding="utf-8")
                etapa = f'ingesta_{escenario["lenguaje"]}'
                if escenario["lenguaje"] == "python":
                    resultado = probar_python(cliente, escenario, csv)
                else:
                    fixture = Path(temporal) / "fixture.json"
                    fixture.write_text(json.dumps({k: escenario[k] for k in ("producto", "investigador")}), encoding="utf-8")
                    entorno = {**os.environ, "PRUEBA_URL": url, "PRUEBA_KEY": clave, "PRUEBA_TOKEN": cliente.token_acceso}
                    proceso = subprocess.run([str(args.cpp.resolve()), str(fixture), str(csv)], env=entorno,
                                             capture_output=True, text=True, encoding="utf-8", timeout=90, check=False)
                    exigir(proceso.returncode == 0, "No terminó correctamente la comprobación C++")
                    resultado = json.loads(proceso.stdout)
                    exigir(resultado.get("guardado") is True and resultado.get("duplicado_idempotente") is True
                           and resultado.get("codigo_duplicado") == "23505" and resultado.get("importaciones_csv") == 2,
                           "Salida C++ incompleta")
                    comprobar_fila(cliente, escenario)  # Lectura independiente desde Python.
                escenario["resultado"] = resultado
                print(f'{escenario["lenguaje"]}: guardado y duplicado idempotente confirmados.', flush=True)
                guardar()
    except Exception as error:
        evidencia["errores"].append(error_seguro(error, etapa))
    finally:
        if cliente and cliente.token_acceso and "antes" in evidencia:
            limpiar(cliente, escenarios, evidencia["errores"])
            try:
                evidencia["despues"] = conteos(cliente)
                evidencia["reales_despues"] = huellas_reales(cliente)
                evidencia["revision_despues"] = ControladorRevision().consultar_remota(cliente)
                evidencia["conteos_iguales"] = evidencia["antes"] == evidencia["despues"]
                evidencia["reales_sin_cambios"] = evidencia["reales_antes"] == evidencia["reales_despues"]
                exigir(evidencia["conteos_iguales"], "Los conteos remotos no coinciden")
                exigir(evidencia["reales_sin_cambios"], "Las huellas de datos reales no coinciden")
            except Exception as error:
                evidencia["errores"].append(error_seguro(error, "comparacion_final"))
        if cliente:
            cliente.cerrar_sesion()
        evidencia["fin_utc"] = datetime.now(UTC).isoformat()
        evidencia["completa"] = (not evidencia["errores"] and evidencia.get("conteos_iguales") is True
                                 and evidencia.get("reales_sin_cambios") is True
                                 and all(e.get("limpieza") and e.get("resultado") for e in escenarios))
        guardar()
    print(json.dumps({k: evidencia.get(k) for k in ("completa", "conteos_iguales", "reales_sin_cambios", "errores")}), flush=True)
    return 0 if evidencia["completa"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpp", type=Path, default=Path("build/entrega/verificar_autores_remoto.exe"))
    parser.add_argument("--salida", type=Path, default=Path("build/evidencia-autores-remoto.json"))
    raise SystemExit(ejecutar(parser.parse_args()))
