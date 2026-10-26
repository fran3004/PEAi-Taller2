"""Indicadores del Parcial 2. Modelo M601PR04G01 v02, secciones 3.5 a 3.10.

Los índices se normalizan contra una población declarada, nunca contra un
máximo nacional supuesto. Los productos sin categoría verificable se enumeran.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def modelo() -> dict:
    return json.loads((Path(__file__).parents[1] / "recursos/modelo_2024.json").read_text(encoding="utf-8"))


def normalizar(texto: str) -> str:
    return re.sub(
        r"[^A-Z0-9]+",
        "_",
        "".join(c for c in unicodedata.normalize("NFD", texto.upper()) if not unicodedata.combining(c)),
    ).strip("_")


def categoria_producto(producto: dict) -> dict | None:
    detalle = producto.get("detalles") or {}
    codigo = normalizar(str(detalle.get("categoria_minciencias") or producto.get("subtipo") or ""))
    # Compatibilidad únicamente con etiquetas que ya declaran una calidad concreta.
    codigo = re.sub(r"^ARTICULO(?:_DE_INVESTIGACION)?(?:_TIPO)?_", "ART_", codigo)
    return next((r for r in modelo()["categorias"] if r["codigo"] == codigo), None)


def puntaje_producto(producto: dict) -> dict:
    regla = categoria_producto(producto)
    if regla is None:
        return {
            "categoria": None,
            "peso_relativo": None,
            "puntaje": None,
            "clase": None,
            "motivo": "Falta una categoría de calidad del Modelo 2024.",
        }
    if producto.get("tipo_mayor") != regla["tipo_mayor"]:
        return {
            "categoria": regla["codigo"],
            "peso_relativo": None,
            "puntaje": None,
            "clase": None,
            "motivo": "La categoría de calidad contradice la tipología mayor.",
        }
    return {
        "categoria": regla["codigo"],
        "peso_relativo": regla["peso_relativo"],
        "puntaje": regla["peso_base"] * regla["peso_relativo"],
        "clase": regla["clase"],
        "motivo": "",
    }


def _vinculado(m: dict, anio: int) -> bool:
    inicio = str(m.get("fecha_inicio") or "")[:4]
    fin = str(m.get("fecha_fin") or "")[:4]
    # Un vínculo terminado conserva su valor histórico en el año de producción.
    return (
        (not inicio or int(inicio) <= anio)
        and (not fin or int(fin) >= anio)
        and (bool(m.get("activo", True)) or bool(fin))
    )


def _componentes(datos: dict, ambito: str, codigo: str, corte: int, desde: int | None) -> dict:
    claves = modelo()["coeficientes"]
    brutos = dict.fromkeys(claves, 0.0)
    entidad = next(
        (
            e
            for e in datos["grupos" if ambito == "grupo" else "investigadores"]
            if e["codigo_gruplac" if ambito == "grupo" else "codigo_rh"] == codigo
        ),
        None,
    )
    if entidad is None:
        raise ValueError(f"No existe {ambito}: {codigo}")
    edad = (
        corte - int(str(entidad["fecha_creacion"])[:4]) + 1
        if ambito == "grupo" and entidad.get("fecha_creacion")
        else None
    )
    if edad is not None and edad <= 0:
        raise ValueError("El año de corte precede a la creación del grupo.")
    relaciones = {p["codigo_identificador"]: p for p in datos["relaciones"]}
    conteo: Counter[str] = Counter()
    periodos = {}
    incluidos, excluidos = [], []
    autores_total = grupos_total = productos_colab = 0
    colaboracion_completa = True
    for p in sorted(datos["productos"], key=lambda x: x["codigo_identificador"]):
        rel = relaciones.get(p["codigo_identificador"], {})
        autores = set(rel.get("autores", []))
        if ambito == "grupo" and rel.get("grupo") != codigo:
            continue
        if ambito == "investigador" and codigo not in autores:
            continue
        if not p.get("activo", True) or p["ano"] > corte or (desde is not None and p["ano"] < desde):
            continue
        regla = categoria_producto(p)
        puntos = puntaje_producto(p)
        motivo = puntos["motivo"]
        if p.get("estado_validacion") != "Avalado":
            motivo = "El producto no está avalado."
        if regla:
            periodo = min(
                regla["ventana"], corte - desde + 1 if desde is not None else regla["ventana"], edad or regla["ventana"]
            )
            if p["ano"] < corte - periodo + 1:
                continue
        if motivo:
            excluidos.append({"codigo": p["codigo_identificador"], "titulo": p["titulo"], "motivo": motivo})
            continue
        conteo[regla["codigo"]] += 1
        periodos[regla["codigo"]] = periodo
        incluidos.append({"codigo": p["codigo_identificador"], "titulo": p["titulo"], **puntos, "periodo": periodo})
        if p["tipo_mayor"] in {"GNC", "DTI"}:
            productos_colab += 1
            miembros = {
                m["codigo_rh"]
                for m in datos["integrantes"]
                if m["codigo_gruplac"] == rel.get("grupo") and _vinculado(m, p["ano"])
            }
            grupos = {
                m["codigo_gruplac"]
                for m in datos["integrantes"]
                if m["codigo_rh"] in autores and _vinculado(m, p["ano"])
            }
            if rel.get("grupo"):
                grupos.add(rel["grupo"])
            internos = autores & miembros if ambito == "grupo" else autores
            if not internos or not grupos:
                colaboracion_completa = False
            autores_total += len(internos)
            grupos_total += len(grupos)
    por_subtipo = []
    for cat, cantidad in sorted(conteo.items()):
        regla = next(r for r in modelo()["categorias"] if r["codigo"] == cat)
        peso = regla["peso_base"] * regla["peso_relativo"]
        valor = math.log1p(cantidad / periodos[cat]) * peso
        brutos[regla["clase"]] += valor
        por_subtipo.append(
            {
                "categoria": cat,
                "cantidad": cantidad,
                "periodo": periodos[cat],
                "peso_relativo": regla["peso_relativo"],
                "puntaje_unitario": peso,
                "indicador": valor,
            }
        )
    if productos_colab:
        brutos["Cohe"] = max(0.0, autores_total / productos_colab - 1)
        brutos["Coop"] = max(0.0, grupos_total / productos_colab - 1)
    return {
        "codigo": codigo,
        "nombre": entidad.get("nombre") or entidad.get("nombre_completo") or codigo,
        "periodo_completo": ambito != "grupo" or edad is not None,
        "area": entidad.get("gran_area_ocde"),
        "brutos": brutos,
        "por_subtipo": por_subtipo,
        "incluidos": incluidos,
        "excluidos": excluidos,
        "colaboracion_completa": colaboracion_completa,
    }


def calcular_indicador(
    datos: dict, ambito: str, codigo: str, corte: int, desde: int | None = None, referencia: dict | None = None
) -> dict[str, Any]:
    if ambito not in {"grupo", "investigador"}:
        raise ValueError("El ámbito debe ser grupo o investigador.")
    if not 1970 <= corte <= 2100 or (desde is not None and not 1970 <= desde <= corte):
        raise ValueError("El rango temporal del indicador es inválido.")
    resultado = _componentes(datos, ambito, codigo, corte, desde)
    coeficientes = modelo()["coeficientes"]
    if referencia is None:
        poblacion = datos["grupos" if ambito == "grupo" else "investigadores"]
        clave = "codigo_gruplac" if ambito == "grupo" else "codigo_rh"
        comparables = [
            e
            for e in poblacion
            if e.get("activo", True)
            and (ambito != "grupo" or not e.get("fecha_creacion") or int(str(e["fecha_creacion"])[:4]) <= corte)
            and (ambito != "grupo" or not resultado["area"] or e.get("gran_area_ocde") == resultado["area"])
        ]
        # Incluye el sujeto seleccionado aunque esté desactivado, para que los
        # cocientes nunca se normalicen contra una población que lo omita.
        codigos = sorted({e[clave] for e in comparables} | {codigo})
        valores = [_componentes(datos, ambito, c, corte, desde)["brutos"] for c in codigos]
        maximos = {k: max((v[k] for v in valores), default=0.0) for k in coeficientes}
        procedencia = f"Catálogo local: {len(codigos)} {ambito}(s)" + (
            f"; área {resultado['area']}" if resultado["area"] else ""
        )
    else:
        if set(referencia.get("maximos", {})) != set(coeficientes) or not str(referencia.get("fuente", "")).strip():
            raise ValueError("La referencia requiere fuente y los nueve máximos del indicador.")
        if referencia.get("corte") != corte or referencia.get("desde") != desde:
            raise ValueError("La referencia no corresponde al rango temporal elegido.")
        maximos = referencia["maximos"]
        procedencia = str(referencia["fuente"])
    componentes = []
    avisos = []
    total = 0.0
    for clave, coeficiente in coeficientes.items():
        maximo = maximos[clave]
        if isinstance(maximo, bool) or not isinstance(maximo, (int, float)) or not math.isfinite(maximo) or maximo < 0:
            raise ValueError(f"Máximo inválido para {clave}.")
        bruto = resultado["brutos"][clave]
        if maximo + 1e-9 < bruto:
            raise ValueError(f"El máximo de referencia de {clave} es menor que el indicador observado.")
        indice = bruto / maximo if maximo else 0.0
        aporte = indice * coeficiente
        total += aporte
        componentes.append(
            {
                "componente": clave,
                "bruto": bruto,
                "maximo": maximo,
                "indice": indice,
                "coeficiente": coeficiente,
                "aporte": aporte,
            }
        )
    if resultado["excluidos"]:
        avisos.append(f"{len(resultado['excluidos'])} productos excluidos por categoría o validación insuficientes.")
    if not resultado["colaboracion_completa"]:
        avisos.append("Faltan autorías o vínculos históricos para completar cohesión/cooperación.")
    if not resultado["periodo_completo"]:
        avisos.append("Se desconoce la antigüedad del grupo: cálculo parcial con la ventana de cada subtipo.")
    if referencia is None:
        avisos.append("Comparación del catálogo cargado; no representa la clasificación nacional de Minciencias.")
    if ambito == "investigador":
        avisos.append("Adaptación del parcial: misma fórmula sobre sus productos; cohesión usa todos sus coautores.")
    return {
        **resultado,
        "ambito": ambito,
        "corte": corte,
        "desde": desde,
        "modelo": modelo()["version"],
        "referencia": procedencia,
        "maximos": maximos,
        "componentes": componentes,
        "indicador": total,
        "completo": not resultado["excluidos"] and resultado["colaboracion_completa"] and resultado["periodo_completo"],
        "avisos": avisos,
    }
