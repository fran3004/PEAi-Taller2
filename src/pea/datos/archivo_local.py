"""Instantánea JSON interoperable. Solo datos de dominio, sin sesiones ni claves."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from pea.dominio.grupo import Grupo
from pea.dominio.integrante import IntegranteGrupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.servicios.servicio_dominio import CatalogoInvestigacion

# SCIENTI publica AAAA/M o AAAA-MM además de fechas ISO; «Actual» marca un vínculo vigente.
_FECHA_VINCULO = re.compile(r"\d{4}(?:[-/]\d{1,2}(?:[-/]\d{1,2})?)?|actual", re.IGNORECASE)


def serializar_catalogo(cat: CatalogoInvestigacion) -> dict:
    nodos = list(cat.multilista_productos.iterar_nodos())
    return {
        "formato": "pea-catalogo",
        "version": 1,
        "grupos": [g.model_dump(mode="json") for g in cat.grupos],
        "investigadores": [i.model_dump(mode="json") for i in cat.investigadores],
        "integrantes": [m.model_dump(mode="json") for m in cat.integrantes],
        "productos": [n.producto.model_dump(mode="json") for n in nodos],
        "relaciones": [
            {
                "codigo_identificador": n.producto.codigo_identificador,
                "grupo": n.grupo.codigo_gruplac if n.grupo else None,
                "autores": [a.codigo_rh for a in n.autores],
            }
            for n in nodos
        ],
    }


def restaurar_catalogo(datos: dict) -> CatalogoInvestigacion:
    if not isinstance(datos, dict) or datos.get("formato") != "pea-catalogo" or datos.get("version") != 1:
        raise ValueError("Formato o versión de archivo local no admitidos.")
    if any(
        not isinstance(datos.get(k), list)
        for k in ("grupos", "investigadores", "integrantes", "productos", "relaciones")
    ):
        raise ValueError("El archivo debe incluir todas las colecciones y relaciones.")
    cat = CatalogoInvestigacion()
    for coleccion, clase, clave, destino in [
        ("grupos", Grupo, "codigo_gruplac", cat.grupos),
        ("investigadores", Investigador, "codigo_rh", cat.investigadores),
    ]:
        vistos = set()
        for fila in datos[coleccion]:
            entidad = clase.model_validate(fila)
            codigo = getattr(entidad, clave)
            if not codigo or codigo in vistos:
                raise ValueError(f"Código duplicado o vacío en {coleccion}.")
            vistos.add(codigo)
            destino.insertar_final(entidad)
    vistos_miembros = set()
    for fila in datos["integrantes"]:
        m = IntegranteGrupo.model_validate(fila)
        par = (m.codigo_gruplac, m.codigo_rh)
        if not cat.buscar_grupo(m.codigo_gruplac) or not cat.buscar_investigador(m.codigo_rh) or par in vistos_miembros:
            raise ValueError("La membresía contiene una referencia inexistente o duplicada.")
        for fecha in (m.fecha_inicio, m.fecha_fin):
            if fecha and not _FECHA_VINCULO.fullmatch(str(fecha).strip()):
                raise ValueError(f"Fecha de membresía inválida: {fecha}")
        vistos_miembros.add(par)
        cat.integrantes.insertar_final(m)
    relaciones = {r["codigo_identificador"]: r for r in datos["relaciones"]}
    if len(relaciones) != len(datos["relaciones"]) or len(relaciones) != len(datos["productos"]):
        raise ValueError("Relaciones de producto duplicadas o incompletas.")
    vistos = set()
    for fila in datos["productos"]:
        p = Producto.model_validate(fila)
        if p.codigo_identificador in vistos or p.codigo_identificador not in relaciones:
            raise ValueError("Producto duplicado o sin relaciones.")
        vistos.add(p.codigo_identificador)
        rel = relaciones[p.codigo_identificador]
        g = cat.buscar_grupo(rel["grupo"]) if rel.get("grupo") else None
        autores = [cat.buscar_investigador(c) for c in rel.get("autores", [])]
        if (
            (rel.get("grupo") and g is None)
            or any(a is None for a in autores)
            or len(set(rel.get("autores", []))) != len(autores)
        ):
            raise ValueError("El producto contiene un grupo o autor inexistente o duplicado.")
        cat.multilista_productos.agregar_producto(p, g, autores)
    cat.hipercubo.poblar_desde_multilista(cat.multilista_productos)
    return cat


def cargar_archivo(ruta: str | Path) -> CatalogoInvestigacion:
    return restaurar_catalogo(json.loads(Path(ruta).read_text(encoding="utf-8-sig")))


def guardar_archivo(ruta: str | Path, datos: dict) -> None:
    destino = Path(ruta).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destino.parent, delete=False) as f:
            temporal = Path(f.name)
            json.dump(datos, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, destino)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
