"""Servicio orquestador de ingesta con Cola propia FIFO y persistencia atómica por lote."""

from __future__ import annotations

import re
import uuid
from datetime import date
from pathlib import Path

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto, validar_ano_producto
from pea.estructuras.cola import Cola, EstadoTarea, TareaIngesta
from pea.excepciones import ConflictoRevision
from pea.ingesta.extractor_pdf import ExtractorPDF
from pea.ingesta.extractor_url import ExtractorURL
from pea.ingesta.lector_csv import LectorCSV
from pea.ingesta.modelos import InformeIngesta, InvestigadorIngesta
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
                requiere_recarga=isinstance(err, ConflictoRevision),
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
                if inf.requiere_recarga:
                    break
        return resultados

    # =========================================================================
    # PROCESAMIENTO INTERNO DE TAREAS
    # =========================================================================

    @staticmethod
    def _validar_ano_producto_url(
        ano: int | None,
        fuente: str,
        indice: int,
        informe: InformeIngesta,
    ) -> int | None:
        if ano is None:
            informe.advertencias.append(
                f"Se omitió el producto {fuente} #{indice}: la fuente no informa el año."
            )
            return None
        try:
            return validar_ano_producto(ano)
        except ValueError as err:
            informe.advertencias.append(
                f"Se omitió el producto {fuente} #{indice}: {err}"
            )
            return None

    @staticmethod
    def _normalizar_categoria_investigador(categoria: str | None) -> str:
        texto = (categoria or "").casefold()
        if "emerit" in texto or "emérit" in texto:
            return "Investigador Emérito"
        for nivel in ("senior", "asociado", "junior"):
            if nivel in texto:
                return f"Investigador {nivel.capitalize()}"
        return "Sin categoría / Vinculado"

    @staticmethod
    def _normalizar_formacion_investigador(nivel: str | None) -> str:
        texto = (nivel or "").casefold()
        if "doctor" in texto or "posdoctor" in texto:
            return "Doctorado"
        if "maestr" in texto or "magist" in texto:
            return "Maestría"
        if "especial" in texto:
            return "Especialización"
        return "Pregrado"

    def _ingestar_cvlac(
        self,
        investigador_ing: InvestigadorIngesta,
        url: str,
        persistir: bool,
        informe: InformeIngesta,
    ) -> None:
        investigador_existente = self.catalogo.buscar_investigador(investigador_ing.codigo_rh)
        nombre = (
            investigador_ing.nombre_completo
            or (investigador_existente.nombre_completo if investigador_existente else "")
            or f"Investigador {investigador_ing.codigo_rh}"
        )
        categoria = self._normalizar_categoria_investigador(
            investigador_ing.categoria_declarada
        )
        formacion = self._normalizar_formacion_investigador(
            investigador_ing.formacion[0].nivel if investigador_ing.formacion else None
        )
        datos_investigador = {
            "nombre_completo": nombre,
            "nombre_en_citas": investigador_ing.nombre_citaciones,
            "nacionalidad": investigador_ing.nacionalidad or "Colombiana",
            "sexo": investigador_ing.sexo or "No especificado",
            "categoria": categoria,
            "formacion_academica": formacion,
            "par_evaluador": investigador_ing.par_evaluador,
            "detalles": investigador_ing.model_dump(mode="json"),
        }
        if investigador_existente is None:
            self.catalogo.crear_investigador(
                Investigador(
                    codigo_rh=investigador_ing.codigo_rh,
                    **datos_investigador,
                ),
                persistir=persistir,
            )
        else:
            self.catalogo.actualizar_investigador(
                investigador_ing.codigo_rh,
                datos_investigador,
                persistir=persistir,
            )

        productos = (
            investigador_ing.articulos
            + investigador_ing.libros
            + investigador_ing.capitulos
            + investigador_ing.softwares
            + investigador_ing.trabajos_dirigidos
            + investigador_ing.proyectos
        )
        for indice, producto_ing in enumerate(productos, start=1):
            ano_producto = self._validar_ano_producto_url(
                producto_ing.ano, "CvLAC", indice, informe
            )
            if ano_producto is None:
                continue
            codigo = f"PROD-CVLAC-{investigador_ing.codigo_rh}-{indice:04d}"
            producto_existente = self.catalogo.buscar_producto(codigo)
            if producto_existente is None:
                producto = Producto(
                    codigo_identificador=codigo,
                    titulo=producto_ing.titulo,
                    tipo_mayor=producto_ing.tipo_mayor,
                    subtipo=(producto_ing.subtipo or producto_ing.tipo or "Producto CvLAC")[:100],
                    ano=ano_producto,
                    estado_validacion="Avalado",
                    detalles={
                        "origen": "CvLAC",
                        "fuente": url,
                        "referencia_original": producto_ing.detalles,
                        "autores": producto_ing.autores,
                        "doi_o_isbn": producto_ing.doi_o_isbn,
                    },
                )
                self.catalogo.crear_producto(
                    producto,
                    codigos_rh_autores=[investigador_ing.codigo_rh],
                    persistir=persistir,
                )
            elif investigador_existente is not None:
                self.catalogo.multilista_productos.agregar_autor_a_producto(
                    codigo,
                    investigador_existente,
                )
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
            fecha_creacion = grupo_ing.fecha_creacion or date.today().isoformat()
            categoria_origen = (grupo_ing.clasificacion or "").strip()
            coincidencia_categoria = re.search(r"\b(A1|A|B|C)\b", categoria_origen, re.IGNORECASE)
            categoria = coincidencia_categoria.group(1).upper() if coincidencia_categoria else "Reconocido"
            detalles_grupo = {
                "origen": "GrupLAC",
                "url": tarea.origen,
                "ano_mes_formacion": grupo_ing.ano_mes_formacion,
                "certificacion": grupo_ing.certificacion,
                "pagina_web": grupo_ing.pagina_web,
                "email": grupo_ing.email,
                "programa_nacional": grupo_ing.programa_nacional,
                "programa_secundario": grupo_ing.programa_secundario,
                "nombre_grupo": grupo_ing.nombre_grupo,
                "clasificacion": grupo_ing.clasificacion,
                "area_conocimiento": grupo_ing.area_conocimiento,
                "instituciones": [i.model_dump() for i in grupo_ing.instituciones],
                "lineas_investigacion": [linea.model_dump() for linea in grupo_ing.lineas_investigacion],
                "integrantes": [integrante.model_dump() for integrante in grupo_ing.integrantes],
                "productos": {
                    "articulos": [producto.model_dump() for producto in grupo_ing.articulos],
                    "libros": [producto.model_dump() for producto in grupo_ing.libros],
                    "capitulos": [producto.model_dump() for producto in grupo_ing.capitulos],
                    "softwares": [producto.model_dump() for producto in grupo_ing.softwares],
                    "trabajos_dirigidos": [
                        producto.model_dump() for producto in grupo_ing.trabajos_dirigidos
                    ],
                    "proyectos": [producto.model_dump() for producto in grupo_ing.proyectos],
                },
                "fecha_descarga": grupo_ing.origen.fecha_descarga,
                "sha256": grupo_ing.origen.sha256,
            }
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
                    fecha_creacion=fecha_creacion,
                    categoria=categoria,
                    lider=grupo_ing.lider or "Sin información",
                    institucion_principal=institucion,
                    departamento_ciudad=grupo_ing.departamento_ciudad or "Sin información",
                    gran_area_ocde=grupo_ing.area_conocimiento or "Sin información",
                    area_ocde=grupo_ing.area_conocimiento or "Sin información",
                    detalles=detalles_grupo,
                )
                self.catalogo.crear_grupo(nuevo_grp, persistir=persistir)
            else:
                self.catalogo.actualizar_grupo(
                    grupo_ing.codigo_gruplac,
                    {"detalles": detalles_grupo},
                    persistir=persistir,
                )

            # Crear perfiles mínimos solo cuando GrupLAC publica un código CvLAC
            # verificable; sus fichas detalladas se procesan en tareas propias.
            urls_cvlac_encoladas: set[str] = set()
            for integrante in grupo_ing.integrantes:
                if not integrante.codigo_rh:
                    informe.advertencias.append(
                        f"No se pudo crear el vínculo de {integrante.nombre}: GrupLAC no informa su código CvLAC."
                    )
                    continue
                url_cvlac = integrante.url_cvlac or (
                    "https://scienti.minciencias.gov.co/cvlac/visualizador/"
                    f"generarCurriculoCv.do?cod_rh={integrante.codigo_rh}"
                )
                if url_cvlac not in urls_cvlac_encoladas:
                    self.encolar_url(
                        url_cvlac,
                        persistir=persistir,
                        anonimizar=anonimizar,
                        es_privado=es_privado,
                        salida_dir=salida_dir,
                    )
                    urls_cvlac_encoladas.add(url_cvlac)
                investigador = self.catalogo.buscar_investigador(integrante.codigo_rh)
                if investigador is None:
                    investigador = Investigador(
                        codigo_rh=integrante.codigo_rh,
                        nombre_completo=integrante.nombre,
                        nacionalidad="Colombiana",
                        sexo="No especificado",
                        categoria="Sin categoría / Vinculado",
                        formacion_academica="Pregrado",
                    )
                    self.catalogo.crear_investigador(investigador, persistir=persistir)

                rol_texto = integrante.vinculacion.casefold()
                if "lider" in rol_texto or "líder" in rol_texto:
                    rol = "Lider"
                elif "estudiante" in rol_texto:
                    rol = "Estudiante"
                else:
                    rol = "Investigador"
                if not any(
                    m.codigo_gruplac == grupo_ing.codigo_gruplac
                    and m.codigo_rh == integrante.codigo_rh
                    for m in self.catalogo.integrantes
                ):
                    horas = re.search(r"\d+", integrante.horas_dedicacion or "")
                    self.catalogo.vincular_integrante(
                        grupo_ing.codigo_gruplac,
                        integrante.codigo_rh,
                        rol=rol,
                        persistir=persistir,
                        fecha_inicio=integrante.inicio_vinculacion or fecha_creacion,
                        fecha_fin=integrante.fin_vinculacion,
                        vinculacion=integrante.vinculacion,
                        horas_dedicacion=int(horas.group()) if horas else 0,
                        detalles={"url_cvlac": integrante.url_cvlac},
                    )
            if urls_cvlac_encoladas:
                informe.mensaje = (
                    f"{informe.mensaje} Se encolaron {len(urls_cvlac_encoladas)} "
                    "perfiles CvLAC enlazados."
                ).strip()

            # Ingesta de productos asociados de todas las secciones publicadas
            for idx, prod_ing in enumerate(
                grupo_ing.articulos
                + grupo_ing.libros
                + grupo_ing.capitulos
                + grupo_ing.softwares
                + grupo_ing.trabajos_dirigidos
                + grupo_ing.proyectos,
                start=1,
            ):
                ano_producto = self._validar_ano_producto_url(
                    prod_ing.ano, "GrupLAC", idx, informe
                )
                if ano_producto is None:
                    continue
                cod_prod = f"PROD-{grupo_ing.codigo_gruplac}-{idx:04d}"
                if self.catalogo.buscar_producto(cod_prod) is None:
                    p = Producto(
                        codigo_identificador=cod_prod,
                        titulo=prod_ing.titulo,
                        tipo_mayor=prod_ing.tipo_mayor,
                        subtipo=(prod_ing.subtipo or prod_ing.tipo or "Producto GrupLAC")[:100],
                        ano=ano_producto,
                        estado_validacion="Avalado",
                        detalles={
                            "origen": "GrupLAC",
                            "fuente": tarea.origen,
                            "referencia_original": prod_ing.detalles,
                            "autores": prod_ing.autores,
                            "doi_o_isbn": prod_ing.doi_o_isbn,
                            "disponibilidad": prod_ing.detalles if prod_ing.tipo == "Software" else None,
                        },
                    )
                    self.catalogo.crear_producto(
                        p,
                        codigo_gruplac=grupo_ing.codigo_gruplac,
                        persistir=persistir,
                    )

        elif tipo == "cvlac":
            inv_ing, _, _ = self.extractor_url.parsear_cvlac(html_txt, meta)
            self._ingestar_cvlac(inv_ing, tarea.origen, persistir, informe)

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
                prod = self.catalogo.buscar_producto(rel.producto_codigo)
                if inv and prod:
                    self.catalogo.multilista_productos.agregar_autor_a_producto(rel.producto_codigo, inv)
                    if persistir and self.catalogo.repo_productos and prod.id and inv.id:
                        try:
                            self.catalogo.repo_productos.asociar_autor(
                                prod.id,
                                inv.id,
                                orden=rel.orden_autoria,
                                es_ejemplo=prod.es_ejemplo,
                            )
                        except Exception:
                            pass
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
