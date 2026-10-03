"""Extractor web institucional para fuentes SCIENTI (GrupLAC y CvLAC).

Cumple estrictamente con las políticas de scraping responsable de AGENTS.md y ADR-0010:
- Host exclusivo: scienti.minciencias.gov.co.
- Protocolo forzado: HTTPS.
- User-Agent institucional de la Universidad Popular del Cesar.
- Timeout estricto de conexión y lectura.
- Máximo 3 reintentos con espera exponencial.
- Pausa mínima de 1.0 s entre peticiones de red.
- Caché local en datos/cache/ (<sha256>.html y .meta.json).
- Normalización Unicode NFC y limpieza de texto.
- Generación de transcripción integral en Markdown (pública anonimizada o privada completa).
- Exportación a JSON y archivos CSV canónicos.
- Generación de informe de extracción.
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from pea.ingesta.modelos import (
    FormacionIngesta,
    GrupoIngesta,
    InformeIngesta,
    InstitucionIngesta,
    IntegranteIngesta,
    InvestigadorIngesta,
    LineaIngesta,
    MetadatosOrigen,
    ProductoIngesta,
)

HOST_PERMITIDO = "scienti.minciencias.gov.co"
USER_AGENT_UPC = (
    "PEAi-Taller2-UPC/1.0 (Proyecto Academico Estructura de Datos; "
    "Universidad Popular del Cesar; contact: fandresfernandez@unicesar.edu.co)"
)


def normalizar_texto(texto: str | None) -> str:
    """Limpia espacios duplicados, elimina caracteres de control y normaliza a Unicode NFC."""
    if not texto:
        return ""
    limpio = " ".join(texto.split()).strip()
    return unicodedata.normalize("NFC", limpio)


def anonimizar_datos_personales(texto: str) -> str:
    """Anonimiza correos e identificadores personales en textos para versiones públicas."""
    if not texto:
        return ""
    res = texto
    res = re.sub(r"[\w\.-]+@unicesar\.edu\.co", "[CORREO-INSTITUCIONAL-UPC]", res)
    res = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[CORREO-PROTEGIDO]", res)
    return res


class ExtractorURL:
    """Manejador de extracción web responsable para Minciencias SCIENTI."""

    def __init__(self, cache_dir: Path | None = None, pausa_segundos: float = 1.0) -> None:
        self.cache_dir = cache_dir or Path("datos/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pausa_segundos = pausa_segundos
        self._ultima_peticion_tiempo: float = 0.0

    def validar_url(self, url: str) -> tuple[str, str]:
        """Valida que la URL cumpla el host y protocolo permitidos y extrae su tipo ('gruplac' o 'cvlac')."""
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            raise ValueError(f"Protocolo no permitido ('{parsed.scheme}'). Solo se permite HTTPS.")
        if parsed.netloc.lower() != HOST_PERMITIDO:
            raise ValueError(
                f"Host no permitido ('{parsed.netloc}'). Solo se permite '{HOST_PERMITIDO}'."
            )

        path_lower = parsed.path.lower()
        if "gruplac" in path_lower:
            return "gruplac", parsed.query
        elif "cvlac" in path_lower:
            return "cvlac", parsed.query
        else:
            raise ValueError(f"URL de SCIENTI no reconocida como GrupLAC ni CvLAC: {url}")

    def descargar_o_cargar_cache(
        self,
        url: str,
        alias: str | None = None,
        forzar_descarga: bool = False,
    ) -> tuple[bytes, dict]:
        """Obtiene el contenido HTML de la URL usando la caché local o descargando responsablemente."""
        self.validar_url(url)
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        html_cache = self.cache_dir / f"{url_hash}.html"
        meta_cache = self.cache_dir / f"{url_hash}.meta.json"

        # Verificar si existe en caché
        if not forzar_descarga and html_cache.exists() and meta_cache.exists():
            content = html_cache.read_bytes()
            meta = json.loads(meta_cache.read_text(encoding="utf-8"))
            return content, meta

        # Control de tasa (Rate Limiting institucional)
        tiempo_desde_ultima = time.time() - self._ultima_peticion_tiempo
        if tiempo_desde_ultima < self.pausa_segundos:
            time.sleep(self.pausa_segundos - tiempo_desde_ultima)

        headers = {
            "User-Agent": USER_AGENT_UPC,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es-ES;q=0.9,es;q=0.8,en;q=0.7",
        }

        max_reintentos = 3
        ultimo_error: str | None = None

        for intento in range(max_reintentos):
            try:
                self._ultima_peticion_tiempo = time.time()
                resp = requests.get(url, headers=headers, timeout=(10, 30))
                if resp.status_code == 200:
                    raw_bytes = resp.content
                    encoding = resp.encoding or resp.apparent_encoding or "latin1"
                    if "iso-8859" in encoding.lower():
                        encoding = "iso-8859-1"

                    sha256_content = hashlib.sha256(raw_bytes).hexdigest()
                    meta = {
                        "url": url,
                        "alias": alias,
                        "fecha_descarga": datetime.datetime.now(datetime.UTC).isoformat(),
                        "codigo_http": resp.status_code,
                        "encoding_cabeceras": resp.encoding,
                        "encoding_aparente": resp.apparent_encoding,
                        "encoding_utilizada": encoding,
                        "longitud_bytes": len(raw_bytes),
                        "sha256": sha256_content,
                        "url_hash": url_hash,
                    }

                    # Guardar en caché
                    html_cache.write_bytes(raw_bytes)
                    meta_cache.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

                    if alias:
                        alias_html = self.cache_dir / f"{alias}.html"
                        alias_meta = self.cache_dir / f"{alias}.meta.json"
                        alias_html.write_bytes(raw_bytes)
                        alias_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

                    return raw_bytes, meta
                else:
                    ultimo_error = f"Código HTTP {resp.status_code}"
            except Exception as err:
                ultimo_error = str(err)

            espera = self.pausa_segundos * (2**intento)
            time.sleep(espera)

        raise RuntimeError(
            f"Fallo al descargar '{url}' tras {max_reintentos} intentos. Último error: {ultimo_error}"
        )

    def parsear_gruplac(
        self,
        html_text: str,
        meta: dict,
        anonimizar: bool = False,
    ) -> tuple[GrupoIngesta, str, dict]:
        """Analiza el HTML de GrupLAC usando BeautifulSoup y lxml, genera modelo Pydantic y Markdown."""
        soup = BeautifulSoup(html_text, "lxml")
        md_lines: list[str] = []

        # Extraer código gruplac de la query si está disponible
        codigo_gruplac = ""
        query_dict = parse_qs(urlparse(meta.get("url", "")).query)
        if "nro" in query_dict and query_dict["nro"]:
            codigo_gruplac = query_dict["nro"][0]
        elif meta.get("alias"):
            codigo_gruplac = meta["alias"].replace("gruplac_", "")

        grupo = GrupoIngesta(
            codigo_gruplac=codigo_gruplac,
            origen=MetadatosOrigen(
                url=meta.get("url", ""),
                fecha_descarga=meta.get("fecha_descarga", datetime.datetime.now(datetime.UTC).isoformat()),
                sha256=meta.get("sha256", ""),
                metodo="requests + bs4 + lxml",
                encoding_utilizada=meta.get("encoding_utilizada", "ISO-8859-1"),
                codigo_http=meta.get("codigo_http", 200),
            ),
        )

        md_lines.append(f"# Transcripción Integral GrupLAC · {codigo_gruplac or 'Grupo'}\n")
        md_lines.append(f"- **URL:** `{meta.get('url', '')}`")
        md_lines.append(f"- **Fecha Descarga:** `{meta.get('fecha_descarga', '')}`")
        md_lines.append(f"- **SHA256:** `{meta.get('sha256', '')}`")
        md_lines.append(f"- **Código HTTP:** {meta.get('codigo_http', 200)}")
        md_lines.append(f"- **Codificación:** {meta.get('encoding_utilizada', 'ISO-8859-1')}\n")
        md_lines.append("---\n")

        tables = soup.find_all("table")
        if not tables:
            md_lines.append("*La página no contiene tablas HTML identificables.*\n")
            return grupo, "\n".join(md_lines), {"tablas": 0, "articulos": 0}

        articulos_extraidos = 0
        libros_extraidos = 0
        capitulos_extraidos = 0
        softwares_extraidos = 0
        integrantes_extraidos = 0

        for idx, table in enumerate(tables):
            header_cell = table.find("td", class_="celdaEncabezado")
            sec_title = normalizar_texto(header_cell.get_text()) if header_cell else f"Sección {idx}"

            md_lines.append(f"## {sec_title}\n")
            rows = table.find_all("tr")

            if len(rows) <= 1:
                md_lines.append("*Sin registros en esta sección.*\n")
                continue

            if "Datos básicos" in sec_title:
                md_lines.append("| Campo | Valor |")
                md_lines.append("|---|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    if len(tds) >= 2:
                        k = normalizar_texto(tds[0].get_text())
                        v = normalizar_texto(tds[1].get_text())
                        if anonimizar and "Líder" in k:
                            v = "[INVESTIGADOR-LIDER-PROTEGIDO]"
                        elif anonimizar and "E-mail" in k:
                            v = "[CORREO-PROTEGIDO]"
                        md_lines.append(f"| {k} | {v} |")

                        if "Año y mes" in k:
                            grupo.ano_mes_formacion = v
                        elif "Departamento" in k:
                            grupo.departamento_ciudad = v
                        elif "Líder" in k:
                            grupo.lider = v
                        elif "certificad" in k:
                            grupo.certificacion = v
                        elif "Página web" in k:
                            grupo.pagina_web = v
                        elif "E-mail" in k:
                            grupo.email = v
                        elif "Clasificación" in k:
                            grupo.clasificacion = v
                        elif "Área de conocimiento" in k:
                            grupo.area_conocimiento = v
                        elif "Programa nacional" in k:
                            grupo.programa_nacional = v
                md_lines.append("")

            elif "Instituciones" in sec_title:
                md_lines.append("| Institución avaladora |")
                md_lines.append("|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        inst = normalizar_texto(td.get_text())
                        if inst and inst != "Instituciones":
                            grupo.instituciones.append(InstitucionIngesta(nombre=inst))
                            md_lines.append(f"| {inst} |")
                md_lines.append("")

            elif "Integrantes del grupo" in sec_title:
                md_lines.append("| Nombre | Vinculación | Horas | Período |")
                md_lines.append("|---|---|:---:|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    if len(tds) >= 4:
                        nom = normalizar_texto(tds[0].get_text())
                        if nom == "Nombre":
                            continue
                        vinc = normalizar_texto(tds[1].get_text())
                        hrs = normalizar_texto(tds[2].get_text())
                        per = normalizar_texto(tds[3].get_text())

                        partes_per = per.split(" - ")
                        ini = partes_per[0].strip() if len(partes_per) > 0 else None
                        fin = partes_per[1].strip() if len(partes_per) > 1 else None

                        grupo.integrantes.append(
                            IntegranteIngesta(
                                nombre=nom,
                                vinculacion=vinc,
                                horas_dedicacion=hrs,
                                inicio_vinculacion=ini,
                                fin_vinculacion=fin,
                            )
                        )
                        integrantes_extraidos += 1
                        display_nom = "[INTEGRANTE-PROTEGIDO]" if anonimizar else nom
                        md_lines.append(f"| {display_nom} | {vinc} | {hrs} | {per} |")
                md_lines.append("")

            elif "Líneas de investigación" in sec_title:
                md_lines.append("| Línea de Investigación Declarada |")
                md_lines.append("|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        linea = normalizar_texto(td.get_text())
                        if linea and "Líneas de investigación" not in linea:
                            grupo.lineas_investigacion.append(LineaIngesta(nombre=linea))
                            md_lines.append(f"| {linea} |")
                md_lines.append("")

            elif "Artículos publicados" in sec_title:
                md_lines.append("| N° | Referencia Bibliográfica / Detalles |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Artículos publicados" not in txt and len(txt) > 10:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            grupo.articulos.append(
                                ProductoIngesta(
                                    tipo="Articulo",
                                    tipo_mayor="GNC",
                                    subtipo="Articulo",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            articulos_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            elif "Libros publicados" in sec_title:
                md_lines.append("| N° | Referencia Libro |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Libros publicados" not in txt and len(txt) > 10:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            grupo.libros.append(
                                ProductoIngesta(
                                    tipo="Libro",
                                    tipo_mayor="GNC",
                                    subtipo="Libro",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            libros_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            elif "Capítulos de libro" in sec_title:
                md_lines.append("| N° | Referencia Capítulo |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Capítulos de libro" not in txt and len(txt) > 10:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            grupo.capitulos.append(
                                ProductoIngesta(
                                    tipo="Capitulo",
                                    tipo_mayor="GNC",
                                    subtipo="Capitulo",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            capitulos_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            elif "Softwares" in sec_title:
                md_lines.append("| N° | Descripción de Software |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Softwares" not in txt and len(txt) > 10:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            grupo.softwares.append(
                                ProductoIngesta(
                                    tipo="Software",
                                    tipo_mayor="DTI",
                                    subtipo="Software",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            softwares_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            else:
                # Secciones complementarias
                md_lines.append("> *Contenido complementario preservado:*\n")
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        t_str = normalizar_texto(td.get_text())
                        if t_str and t_str != sec_title:
                            display_t = anonimizar_datos_personales(t_str) if anonimizar else t_str
                            md_lines.append(f"- {display_t}")
                md_lines.append("")

        resumen = {
            "tablas": len(tables),
            "integrantes": integrantes_extraidos,
            "articulos": articulos_extraidos,
            "libros": libros_extraidos,
            "capitulos": capitulos_extraidos,
            "softwares": softwares_extraidos,
        }
        return grupo, "\n".join(md_lines), resumen

    def parsear_cvlac(
        self,
        html_text: str,
        meta: dict,
        anonimizar: bool = False,
    ) -> tuple[InvestigadorIngesta, str, dict]:
        """Analiza el HTML de CvLAC usando BeautifulSoup y lxml, genera modelo Pydantic y Markdown."""
        soup = BeautifulSoup(html_text, "lxml")
        md_lines: list[str] = []

        codigo_rh = ""
        query_dict = parse_qs(urlparse(meta.get("url", "")).query)
        if "cod_rh" in query_dict and query_dict["cod_rh"]:
            codigo_rh = query_dict["cod_rh"][0]
        elif meta.get("alias"):
            codigo_rh = meta["alias"].replace("cvlac_", "")

        inv = InvestigadorIngesta(
            codigo_rh=codigo_rh,
            origen=MetadatosOrigen(
                url=meta.get("url", ""),
                fecha_descarga=meta.get("fecha_descarga", datetime.datetime.now(datetime.UTC).isoformat()),
                sha256=meta.get("sha256", ""),
                metodo="requests + bs4 + lxml",
                encoding_utilizada=meta.get("encoding_utilizada", "ISO-8859-1"),
                codigo_http=meta.get("codigo_http", 200),
            ),
        )

        md_lines.append(f"# Transcripción Integral CvLAC · {codigo_rh or 'Investigador'}\n")
        md_lines.append(f"- **URL:** `{meta.get('url', '')}`")
        md_lines.append(f"- **Fecha Descarga:** `{meta.get('fecha_descarga', '')}`")
        md_lines.append(f"- **SHA256:** `{meta.get('sha256', '')}`")
        md_lines.append(f"- **Código HTTP:** {meta.get('codigo_http', 200)}")
        md_lines.append(f"- **Codificación:** {meta.get('encoding_utilizada', 'ISO-8859-1')}\n")
        md_lines.append("---\n")

        tables = soup.find_all("table")
        articulos_extraidos = 0
        capitulos_extraidos = 0
        softwares_extraidos = 0
        formacion_extraida = 0

        for idx, table in enumerate(tables):
            first_td = table.find("td")
            sec_title = normalizar_texto(first_td.get_text()) if first_td else f"Bloque {idx}"
            if len(sec_title) > 60:
                sec_title = sec_title[:60] + "..."

            md_lines.append(f"## {sec_title}\n")
            rows = table.find_all("tr")

            if len(rows) <= 1:
                md_lines.append("*Sin registros en esta sección.*\n")
                continue

            if "Hoja de vida" in sec_title or idx == 0:
                md_lines.append("| Atributo | Detalle |")
                md_lines.append("|---|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    if len(tds) >= 2:
                        k = normalizar_texto(tds[0].get_text())
                        v = normalizar_texto(tds[1].get_text())

                        if k == "Nombre":
                            inv.nombre_completo = v
                            if anonimizar:
                                v = "[INVESTIGADOR-CVLAC-PROTEGIDO]"
                        elif "citaciones" in k:
                            inv.nombre_citaciones = v
                            if anonimizar:
                                v = "[CITACIONES-PROTEGIDAS]"
                        elif k == "Nacionalidad":
                            inv.nacionalidad = v
                        elif k == "Sexo":
                            inv.sexo = v
                        elif "Categoría" in k or "Categoria" in k:
                            inv.categoria_declarada = v
                        elif "Par evaluador" in k:
                            inv.par_evaluador = True

                        md_lines.append(f"| {k} | {v} |")
                md_lines.append("")

            elif "Formación Académica" in sec_title or "Formacion Academica" in sec_title:
                md_lines.append("| Nivel | Detalle Formación |")
                md_lines.append("|---|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    txt_row = " ".join(normalizar_texto(td.get_text()) for td in tds).strip()
                    if txt_row and "Formación Académica" not in txt_row and len(txt_row) > 10:
                        nivel = "Formación"
                        lower_txt = txt_row.lower()
                        if "doctorado" in lower_txt:
                            nivel = "Doctorado"
                        elif "maestr" in lower_txt:
                            nivel = "Maestría"
                        elif "especializ" in lower_txt:
                            nivel = "Especialización"
                        elif "pregrado" in lower_txt:
                            nivel = "Pregrado"

                        inv.formacion.append(
                            FormacionIngesta(
                                nivel=nivel,
                                titulo=txt_row[:120],
                                institucion=txt_row,
                            )
                        )
                        formacion_extraida += 1
                        display_v = anonimizar_datos_personales(txt_row) if anonimizar else txt_row
                        md_lines.append(f"| {nivel} | {display_v} |")
                md_lines.append("")

            elif "Áreas de actuación" in sec_title:
                md_lines.append("| Área de Actuación Declarada |")
                md_lines.append("|---|")
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Áreas de actuación" not in txt:
                            inv.areas_actuacion.append(txt)
                            md_lines.append(f"| {txt} |")
                md_lines.append("")

            elif "Artículos" in sec_title:
                md_lines.append("| N° | Artículo Científico |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Artículos" not in txt and len(txt) > 20:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            inv.articulos.append(
                                ProductoIngesta(
                                    tipo="Articulo",
                                    tipo_mayor="GNC",
                                    subtipo="Articulo",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            articulos_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            elif "Capítulos de libro" in sec_title:
                md_lines.append("| N° | Capítulo de Libro |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Capítulos de libro" not in txt and len(txt) > 20:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            inv.capitulos.append(
                                ProductoIngesta(
                                    tipo="Capitulo",
                                    tipo_mayor="GNC",
                                    subtipo="Capitulo",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            capitulos_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            elif "Softwares" in sec_title:
                md_lines.append("| N° | Software Desarrollado |")
                md_lines.append("|:---:|---|")
                num = 1
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        txt = normalizar_texto(td.get_text())
                        if txt and "Softwares" not in txt and len(txt) > 20:
                            ano_m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
                            ano_val = int(ano_m.group(1)) if ano_m else None
                            inv.softwares.append(
                                ProductoIngesta(
                                    tipo="Software",
                                    tipo_mayor="DTI",
                                    subtipo="Software",
                                    titulo=txt[:200],
                                    ano=ano_val,
                                    detalles=txt,
                                )
                            )
                            softwares_extraidos += 1
                            display_txt = anonimizar_datos_personales(txt) if anonimizar else txt
                            md_lines.append(f"| {num} | {display_txt} |")
                            num += 1
                md_lines.append("")

            else:
                md_lines.append("> *Contenido complementario preservado:*\n")
                for tr in rows:
                    tds = tr.find_all("td")
                    for td in tds:
                        t_str = normalizar_texto(td.get_text())
                        if t_str and t_str != sec_title:
                            display_t = anonimizar_datos_personales(t_str) if anonimizar else t_str
                            md_lines.append(f"- {display_t}")
                md_lines.append("")

        resumen = {
            "tablas": len(tables),
            "formacion": formacion_extraida,
            "articulos": articulos_extraidos,
            "capitulos": capitulos_extraidos,
            "softwares": softwares_extraidos,
        }
        return inv, "\n".join(md_lines), resumen

    def exportar_a_csv_canonico(
        self,
        destino_dir: Path,
        grupo: GrupoIngesta | None = None,
        investigador: InvestigadorIngesta | None = None,
    ) -> dict[str, str]:
        """Escribe o anexa los datos extraídos a los cuatro archivos CSV canónicos oficiales."""
        destino_dir.mkdir(parents=True, exist_ok=True)
        archivos_creados: dict[str, str] = {}

        # 1. grupos.csv
        if grupo:
            ruta_grupos = destino_dir / "grupos.csv"
            existe = ruta_grupos.exists()
            with ruta_grupos.open("a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if not existe:
                    writer.writerow(["codigo_minciencias", "nombre", "clasificacion", "institucion"])
                institucion = grupo.instituciones[0].nombre if grupo.instituciones else "Universidad Popular del Cesar"
                writer.writerow([
                    grupo.codigo_gruplac,
                    grupo.nombre_grupo or f"Grupo {grupo.codigo_gruplac}",
                    grupo.clasificacion or "Reconocido",
                    institucion,
                ])
            archivos_creados["grupos_csv"] = str(ruta_grupos)

        # 2. investigadores.csv
        if investigador:
            ruta_inv = destino_dir / "investigadores.csv"
            existe = ruta_inv.exists()
            with ruta_inv.open("a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if not existe:
                    writer.writerow(["codigo_cvlac", "nombre_completo", "categoria", "nacionalidad"])
                writer.writerow([
                    investigador.codigo_rh,
                    investigador.nombre_completo or f"Investigador {investigador.codigo_rh}",
                    investigador.categoria_declarada or "Investigador",
                    investigador.nacionalidad or "Colombiana",
                ])
            archivos_creados["investigadores_csv"] = str(ruta_inv)

        # 3. productos.csv y autores.csv
        productos_a_escribir: list[tuple[ProductoIngesta, str | None, str | None]] = []
        if grupo:
            for p in grupo.articulos + grupo.libros + grupo.capitulos + grupo.softwares:
                productos_a_escribir.append((p, grupo.codigo_gruplac, None))
        if investigador:
            for p in investigador.articulos + investigador.capitulos + investigador.softwares:
                productos_a_escribir.append((p, None, investigador.codigo_rh))

        if productos_a_escribir:
            ruta_prod = destino_dir / "productos.csv"
            existe_prod = ruta_prod.exists()
            with ruta_prod.open("a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if not existe_prod:
                    writer.writerow([
                        "codigo_identificador",
                        "titulo",
                        "tipo_categoria",
                        "anio",
                        "estado_validacion",
                        "grupo_codigo",
                    ])

                for idx, (prod, grp_cod, _) in enumerate(productos_a_escribir, start=1):
                    # Generar identificador determinista
                    codigo_prod = f"PROD-{prod.tipo_mayor}-{prod.ano or 2024}-{idx:04d}"
                    writer.writerow([
                        codigo_prod,
                        prod.titulo,
                        prod.tipo,
                        prod.ano or 2024,
                        "Aprobado",
                        grp_cod or "",
                    ])
            archivos_creados["productos_csv"] = str(ruta_prod)

            # autores.csv si hay autor identificado
            autores_validos = [(p, inv_c) for (p, _, inv_c) in productos_a_escribir if inv_c]
            if autores_validos:
                ruta_aut = destino_dir / "autores.csv"
                existe_aut = ruta_aut.exists()
                with ruta_aut.open("a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if not existe_aut:
                        writer.writerow(["producto_codigo", "investigador_codigo", "orden_autoria"])
                    for idx, (_, inv_c) in enumerate(autores_validos, start=1):
                        cod_p = f"PROD-GNC-2024-{idx:04d}"
                        writer.writerow([cod_p, inv_c, 1])
                archivos_creados["autores_csv"] = str(ruta_aut)

        return archivos_creados

    def procesar_url(
        self,
        url: str,
        salida_dir: Path | None = None,
        anonimizar: bool = False,
        forzar_descarga: bool = False,
        es_privado: bool = False,
    ) -> InformeIngesta:
        """Flujo completo de extracción web: descarga, parseo, Markdown, JSON, CSV e informe."""
        tipo_fuente, _ = self.validar_url(url)
        salida = salida_dir or Path("datos/fuentes/extraccion")
        salida.mkdir(parents=True, exist_ok=True)

        alias = f"{tipo_fuente}_{hashlib.sha256(url.encode()).hexdigest()[:12]}"
        raw_bytes, meta = self.descargar_o_cargar_cache(url, alias=alias, forzar_descarga=forzar_descarga)

        encoding = meta.get("encoding_utilizada", "utf-8")
        html_text = raw_bytes.decode(encoding, errors="replace")

        informe = InformeIngesta(
            origen=url,
            tipo_fuente=f"url_{tipo_fuente}",
            exito=True,
            mensaje="Extracción web completada con éxito",
        )

        archivos: dict[str, str] = {}

        if tipo_fuente == "gruplac":
            grupo, md_text, metricas = self.parsear_gruplac(html_text, meta, anonimizar=anonimizar)
            informe.grupos_procesados = 1
            informe.productos_procesados = (
                len(grupo.articulos) + len(grupo.libros) + len(grupo.capitulos) + len(grupo.softwares)
            )

            # 1. Guardar Markdown (distinguiendo privado si contiene datos reales)
            subcarpeta = "privado" if es_privado else "publicado"
            ruta_md = salida / subcarpeta / f"GrupLAC-{grupo.codigo_gruplac or alias}.md"
            ruta_md.parent.mkdir(parents=True, exist_ok=True)
            ruta_md.write_text(md_text, encoding="utf-8")
            archivos["markdown"] = str(ruta_md)

            # 2. Guardar JSON
            ruta_json = salida / f"GrupLAC-{grupo.codigo_gruplac or alias}.json"
            ruta_json.write_text(grupo.model_dump_json(indent=2), encoding="utf-8")
            archivos["json"] = str(ruta_json)

            # 3. Exportar CSV canónico
            csv_archivos = self.exportar_a_csv_canonico(salida / "csv", grupo=grupo)
            archivos.update(csv_archivos)

        elif tipo_fuente == "cvlac":
            inv, md_text, metricas = self.parsear_cvlac(html_text, meta, anonimizar=anonimizar)
            informe.investigadores_procesados = 1
            informe.productos_procesados = len(inv.articulos) + len(inv.capitulos) + len(inv.softwares)

            subcarpeta = "privado" if es_privado else "publicado"
            ruta_md = salida / subcarpeta / f"CvLAC-{inv.codigo_rh or alias}.md"
            ruta_md.parent.mkdir(parents=True, exist_ok=True)
            ruta_md.write_text(md_text, encoding="utf-8")
            archivos["markdown"] = str(ruta_md)

            ruta_json = salida / f"CvLAC-{inv.codigo_rh or alias}.json"
            ruta_json.write_text(inv.model_dump_json(indent=2), encoding="utf-8")
            archivos["json"] = str(ruta_json)

            csv_archivos = self.exportar_a_csv_canonico(salida / "csv", investigador=inv)
            archivos.update(csv_archivos)

        # Generar informe en Markdown
        ruta_informe = salida / f"Informe-{alias}.md"
        lineas_inf = [
            f"# Informe de Extracción Web · {alias}\n",
            f"- **URL Origen:** `{url}`",
            f"- **Tipo de Fuente:** {tipo_fuente.upper()}",
            f"- **Fecha:** {informe.fecha}",
            f"- **Grupos procesados:** {informe.grupos_procesados}",
            f"- **Investigadores procesados:** {informe.investigadores_procesados}",
            f"- **Productos procesados:** {informe.productos_procesados}",
            f"- **Modo Anonimizado:** {'Sí' if anonimizar else 'No'}",
            f"- **Destino Privado:** {'Sí' if es_privado else 'No'}\n",
            "## Archivos Generados\n",
        ]
        for k, path_str in archivos.items():
            lineas_inf.append(f"- **{k}:** `{path_str}`")
        ruta_informe.write_text("\n".join(lineas_inf), encoding="utf-8")
        archivos["informe"] = str(ruta_informe)

        informe.archivos_generados = archivos
        return informe
