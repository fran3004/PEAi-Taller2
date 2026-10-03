"""Servicio orquestador de ingesta con Cola propia FIFO y persistencia atómica por lote."""

from __future__ import annotations

import uuid
from pathlib import Path

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.estructuras.cola import Cola, EstadoTarea, TareaIngesta
from pea.ingesta.extractor_pdf import ExtractorPDF
from pea.ingesta.extractor_url import ExtractorURL
from pea.ingesta.lector_csv import LectorCSV
from pea.ingesta.modelos import InformeIngesta
from pea.servicios.servicio_dominio import CatalogoInvestigacion


class ServicioIngesta:
    """Orquesta las tareas de ingesta (URL, CSV, PDF) utilizando la Cola propia FIFO y el Catálogo."""

    def __init__(
        self,
        catalogo: CatalogoInvestigacion,
        extractor_url: ExtractorURL | None = None,
        extractor_pdf: ExtractorPDF | None = None,
    ) -> None:
        self.catalogo = catalogo
        self.extractor_url = extractor_url or ExtractorURL()
        self.extractor_pdf = extractor_pdf or ExtractorPDF()
        self.cola_tareas: Cola[TareaIngesta] = self.catalogo.cola_importacion

    def encolar_url(
        self,
        url: str,
        persistir: bool = False,
        anonimizar: bool = False,
        es_privado: bool = False,
        salida_dir: Path | None = None,
    ) -> TareaIngesta:
        """Encola una tarea de extracción web para GrupLAC o CvLAC."""
        id_tarea = f"URL-{uuid.uuid4().hex[:8]}"
        tipo_fuente, _ = self.extractor_url.validar_url(url)
        tarea = TareaIngesta(
            id_tarea=id_tarea,
            tipo_fuente=f"url_{tipo_fuente}",
            origen=url,
            estado=EstadoTarea.PENDIENTE,
            detalles={
                "persistir": persistir,
                "anonimizar": anonimizar,
                "es_privado": es_privado,
                "salida_dir": str(salida_dir) if salida_dir else None,
            },
        )
        self.cola_tareas.encolar(tarea)
        return tarea

    def encolar_csv(
        self,
        ruta_csv: Path | str,
        tipo_entidad: str | None = None,
        persistir: bool = False,
    ) -> TareaIngesta:
        """Encola una tarea de importación de archivo tabular CSV."""
        path = Path(ruta_csv)
        tipo = tipo_entidad or LectorCSV.detectar_tipo_archivo(path)
        id_tarea = f"CSV-{uuid.uuid4().hex[:8]}"
        tarea = TareaIngesta(
            id_tarea=id_tarea,
            tipo_fuente=f"csv_{tipo}",
            origen=str(path.resolve()),
            estado=EstadoTarea.PENDIENTE,
            detalles={"tipo_entidad": tipo, "persistir": persistir},
        )
        self.cola_tareas.encolar(tarea)
        return tarea

    def encolar_pdf(
        self,
        ruta_pdf: Path | str,
        salida_dir: Path | None = None,
    ) -> TareaIngesta:
        """Encola una tarea de extracción de tablas y texto desde PDF."""
        path = Path(ruta_pdf)
        id_tarea = f"PDF-{uuid.uuid4().hex[:8]}"
        tarea = TareaIngesta(
            id_tarea=id_tarea,
            tipo_fuente="archivo_pdf",
            origen=str(path.resolve()),
            estado=EstadoTarea.PENDIENTE,
            detalles={"salida_dir": str(salida_dir) if salida_dir else None},
        )
        self.cola_tareas.encolar(tarea)
        return tarea

    def procesar_siguiente(self) -> InformeIngesta | None:
        """Extrae la siguiente tarea de la Cola propia y la ejecuta según su tipo de fuente."""
        if self.cola_tareas.esta_vacia():
            return None

        tarea = self.cola_tareas.desencolar()
        tarea.estado = EstadoTarea.PROCESANDO

        try:
            if tarea.tipo_fuente.startswith("url_"):
                informe = self._procesar_tarea_url(tarea)
            elif tarea.tipo_fuente.startswith("csv_"):
                informe = self._procesar_tarea_csv(tarea)
            elif tarea.tipo_fuente == "archivo_pdf":
                informe = self._procesar_tarea_pdf(tarea)
            else:
                raise ValueError(f"Tipo de tarea no reconocido: {tarea.tipo_fuente}")

            tarea.estado = EstadoTarea.TERMINADA
            tarea.elementos_procesados = (
                informe.grupos_procesados
                + informe.investigadores_procesados
                + informe.productos_procesados
            )
            return informe

        except Exception as err:
            tarea.estado = EstadoTarea.CON_ERROR
            tarea.mensaje_error = str(err)
            informe_error = InformeIngesta(
                origen=tarea.origen,
                tipo_fuente=tarea.tipo_fuente,
                exito=False,
                mensaje=f"Error durante la ingesta: {err}",
                advertencias=[str(err)],
            )
            return informe_error

    def procesar_todas(self) -> list[InformeIngesta]:
        """Procesa secuencialmente todas las tareas pendientes en la Cola."""
        resultados: list[InformeIngesta] = []
        while not self.cola_tareas.esta_vacia():
            inf = self.procesar_siguiente()
            if inf is not None:
                resultados.append(inf)
        return resultados

    # =========================================================================
    # PROCESAMIENTO INTERNO DE TAREAS
    # =========================================================================

    def _procesar_tarea_url(self, tarea: TareaIngesta) -> InformeIngesta:
        detalles = tarea.detalles or {}
        persistir = bool(detalles.get("persistir", False))
        anonimizar = bool(detalles.get("anonimizar", False))
        es_privado = bool(detalles.get("es_privado", False))
        salida_dir = Path(detalles["salida_dir"]) if detalles.get("salida_dir") else None

        informe = self.extractor_url.procesar_url(
            url=tarea.origen,
            salida_dir=salida_dir,
            anonimizar=anonimizar,
            es_privado=es_privado,
        )

        # Cargar entidades en el dominio de la aplicación
        tipo = "gruplac" if "gruplac" in tarea.tipo_fuente else "cvlac"
        alias = f"{tipo}_{tarea.id_tarea}"
        raw_bytes, meta = self.extractor_url.descargar_o_cargar_cache(tarea.origen, alias=alias)
        enc = meta.get("encoding_utilizada", "utf-8")
        html_txt = raw_bytes.decode(enc, errors="replace")

        if tipo == "gruplac":
            grupo_ing, _, _ = self.extractor_url.parsear_gruplac(html_txt, meta)
            # Desduplicación en memoria
            g_existente = self.catalogo.buscar_grupo(grupo_ing.codigo_gruplac)
            if g_existente is None:
                institucion = (
                    grupo_ing.instituciones[0].nombre
                    if grupo_ing.instituciones
                    else "Universidad Popular del Cesar"
                )
                nuevo_grp = Grupo(
                    codigo_gruplac=grupo_ing.codigo_gruplac,
                    nombre=grupo_ing.nombre_grupo or f"Grupo {grupo_ing.codigo_gruplac}",
                    categoria=grupo_ing.clasificacion,
                    lider=grupo_ing.lider,
                    institucion_principal=institucion,
                    departamento_ciudad=grupo_ing.departamento_ciudad,
                    gran_area_ocde=grupo_ing.area_conocimiento,
                )
                self.catalogo.crear_grupo(nuevo_grp, persistir=persistir)

            # Ingesta de productos asociados
            for idx, prod_ing in enumerate(
                grupo_ing.articulos + grupo_ing.libros + grupo_ing.capitulos + grupo_ing.softwares,
                start=1,
            ):
                cod_prod = f"PROD-{grupo_ing.codigo_gruplac}-{idx:04d}"
                if self.catalogo.buscar_producto(cod_prod) is None:
                    p = Producto(
                        codigo_identificador=cod_prod,
                        titulo=prod_ing.titulo,
                        tipo_mayor=prod_ing.tipo_mayor,
                        subtipo=prod_ing.subtipo or prod_ing.tipo,
                        ano=prod_ing.ano or 2024,
                        estado_validacion="Aprobado",
                        detalles={"origen": "GrupLAC", "fuente": tarea.origen},
                    )
                    self.catalogo.crear_producto(
                        p,
                        codigo_gruplac=grupo_ing.codigo_gruplac,
                        persistir=persistir,
                    )

        elif tipo == "cvlac":
            inv_ing, _, _ = self.extractor_url.parsear_cvlac(html_txt, meta)
            inv_existente = self.catalogo.buscar_investigador(inv_ing.codigo_rh)
            if inv_existente is None:
                nivel_formacion = inv_ing.formacion[0].nivel if inv_ing.formacion else "Profesional"
                nuevo_inv = Investigador(
                    codigo_rh=inv_ing.codigo_rh,
                    nombre_completo=inv_ing.nombre_completo or f"Investigador {inv_ing.codigo_rh}",
                    categoria=inv_ing.categoria_declarada,
                    formacion_academica=nivel_formacion,
                    nacionalidad=inv_ing.nacionalidad or "Colombiana",
                    sexo=inv_ing.sexo,
                    nombre_en_citas=inv_ing.nombre_citaciones,
                )
                self.catalogo.crear_investigador(nuevo_inv, persistir=persistir)

            for idx, prod_ing in enumerate(
                inv_ing.articulos + inv_ing.capitulos + inv_ing.softwares,
                start=1,
            ):
                cod_prod = f"PROD-CVLAC-{inv_ing.codigo_rh}-{idx:04d}"
                prod_existente = self.catalogo.buscar_producto(cod_prod)
                if prod_existente is None:
                    p = Producto(
                        codigo_identificador=cod_prod,
                        titulo=prod_ing.titulo,
                        tipo_mayor=prod_ing.tipo_mayor,
                        subtipo=prod_ing.subtipo or prod_ing.tipo,
                        ano=prod_ing.ano or 2024,
                        estado_validacion="Aprobado",
                        detalles={"origen": "CvLAC", "fuente": tarea.origen},
                    )
                    self.catalogo.crear_producto(
                        p,
                        codigos_rh_autores=[inv_ing.codigo_rh],
                        persistir=persistir,
                    )
                else:
                    # Enlazar coautor si ya existe el nodo sin duplicarlo
                    inv_obj = self.catalogo.buscar_investigador(inv_ing.codigo_rh)
                    if inv_obj:
                        self.catalogo.multilista_productos.agregar_autor_a_producto(cod_prod, inv_obj)

        return informe

    def _procesar_tarea_csv(self, tarea: TareaIngesta) -> InformeIngesta:
        detalles = tarea.detalles or {}
        tipo = detalles.get("tipo_entidad") or LectorCSV.detectar_tipo_archivo(tarea.origen)
        persistir = bool(detalles.get("persistir", False))

        informe = InformeIngesta(
            origen=tarea.origen,
            tipo_fuente=f"csv_{tipo}",
            exito=True,
            mensaje=f"Importación de CSV tipo '{tipo}' procesada",
        )

        if tipo == "grupos":
            grupos, errs = LectorCSV.leer_grupos(tarea.origen)
            for g in grupos:
                if self.catalogo.buscar_grupo(g.codigo_gruplac) is None:
                    self.catalogo.crear_grupo(g, persistir=persistir)
                    informe.grupos_procesados += 1
            informe.filas_erroneas.extend(errs)

        elif tipo == "investigadores":
            invs, errs = LectorCSV.leer_investigadores(tarea.origen)
            for inv in invs:
                if self.catalogo.buscar_investigador(inv.codigo_rh) is None:
                    self.catalogo.crear_investigador(inv, persistir=persistir)
                    informe.investigadores_procesados += 1
            informe.filas_erroneas.extend(errs)

        elif tipo == "productos":
            prods, errs = LectorCSV.leer_productos(tarea.origen)
            for p, grp_cod in prods:
                if self.catalogo.buscar_producto(p.codigo_identificador) is None:
                    self.catalogo.crear_producto(p, codigo_gruplac=grp_cod, persistir=persistir)
                    informe.productos_procesados += 1
            informe.filas_erroneas.extend(errs)

        elif tipo == "autores":
            relaciones, errs = LectorCSV.leer_autores(tarea.origen)
            for rel in relaciones:
                inv = self.catalogo.buscar_investigador(rel.investigador_codigo)
                if inv and self.catalogo.buscar_producto(rel.producto_codigo):
                    self.catalogo.multilista_productos.agregar_autor_a_producto(rel.producto_codigo, inv)
                    informe.autores_procesados += 1
            informe.filas_erroneas.extend(errs)

        return informe

    def _procesar_tarea_pdf(self, tarea: TareaIngesta) -> InformeIngesta:
        detalles = tarea.detalles or {}
        salida_dir = Path(detalles["salida_dir"]) if detalles.get("salida_dir") else None

        doc_pdf = self.extractor_pdf.procesar_archivo(tarea.origen)

        informe = InformeIngesta(
            origen=tarea.origen,
            tipo_fuente="archivo_pdf",
            exito=True,
            mensaje=f"PDF procesado: {doc_pdf.total_paginas} páginas, {doc_pdf.total_caracteres} caracteres.",
            advertencias=doc_pdf.advertencias,
        )

        if salida_dir:
            salida_dir.mkdir(parents=True, exist_ok=True)
            md_path = salida_dir / f"{Path(tarea.origen).stem}.md"
            self.extractor_pdf.exportar_a_markdown(doc_pdf, md_path)
            informe.archivos_generados["markdown"] = str(md_path)

        return informe
