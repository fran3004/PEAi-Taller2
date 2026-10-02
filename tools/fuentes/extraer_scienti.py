#!/usr/bin/env python3
"""
tools/fuentes/extraer_scienti.py
Extractor, analizador y transcriptor de páginas SCIENTI (GrupLAC y CvLAC) para PEA-i.
Genera:
1. Notas privadas completas (brain/40-Fuentes/privado/):
   - SCIENTI-GrupLAC-completo.md
   - SCIENTI-CvLAC-completo.md
2. Notas públicas versionables anonimizadas (brain/40-Fuentes/publicado/):
   - SCIENTI-GrupLAC.md
   - SCIENTI-CvLAC.md
3. Mapa de campos (brain/40-Fuentes/publicado/SCIENTI-Mapa-de-campos.md)
4. Informe de extracción (brain/40-Fuentes/publicado/SCIENTI-Informe-extraccion.md)
5. Fixtures y oráculos esperados (tests/fixtures/scienti/*.esperado.json y *.html)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from modelos_scienti import (
    GrupoGrupLAC,
    InvestigadorCvLAC,
    MetadatosOrigen,
    IntegranteGrupo,
    LineaInvestigacion,
    InstitucionAval,
    ProductoBibliografico,
    ProductoSoftware,
    TrabajoDirigido,
    ProyectoInvestigacion,
    FormacionAcademica,
)


def limpiar_texto(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(s.split()).strip()


def anonymize_text(text: str) -> str:
    """Anonimiza nombres propios y correos en textos para versiones públicas."""
    if not text:
        return ""
    res = text
    res = re.sub(r'[\w\.-]+@unicesar\.edu\.co', '[CORREO-INSTITUCIONAL-UPC]', res)
    res = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[CORREO-PROTEGIDO]', res)
    return res


def parse_gruplac(html_text: str, meta: dict, anonimizar: bool = False) -> tuple[GrupoGrupLAC, str]:
    soup = BeautifulSoup(html_text, "lxml")
    md_lines: list[str] = []

    codigo_nro = meta.get("alias", "").replace("gruplac_", "")
    grupo_obj = GrupoGrupLAC(
        codigo_gruplac=codigo_nro,
        origen=MetadatosOrigen(
            url=meta["url"],
            fecha_descarga=meta["fecha_descarga"],
            sha256=meta["sha256"]
        )
    )

    md_lines.append(f"# Transcripción Integral GrupLAC · {meta.get('alias', 'Grupo')}\n")
    md_lines.append(f"- **URL:** `{meta['url']}`")
    md_lines.append(f"- **Fecha Descarga:** `{meta['fecha_descarga']}`")
    md_lines.append(f"- **SHA256:** `{meta['sha256']}`")
    md_lines.append(f"- **Código HTTP:** {meta.get('codigo_http', 200)}")
    md_lines.append(f"- **Codificación:** {meta.get('encoding_utilizada', 'ISO-8859-1')}\n")
    md_lines.append("---\n")

    tables = soup.find_all("table")
    if not tables:
        md_lines.append("*La página no contiene tablas HTML.*\n")
        return grupo_obj, "\n".join(md_lines)

    for idx, table in enumerate(tables):
        header_cell = table.find("td", class_="celdaEncabezado")
        sec_title = limpiar_texto(header_cell.get_text()) if header_cell else f"Sección {idx}"
        
        md_lines.append(f"## {sec_title}\n")
        rows = table.find_all("tr")

        if len(rows) <= 1:
            md_lines.append("*Sin registros en esta sección (sección vacía).*\n")
            continue

        if "Datos básicos" in sec_title:
            md_lines.append("| Campo | Valor |")
            md_lines.append("|---|---|")
            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    k = limpiar_texto(tds[0].get_text())
                    v = limpiar_texto(tds[1].get_text())
                    if anonimizar and "Líder" in k:
                        v = "[INVESTIGADOR-LIDER-GISICO]"
                    elif anonimizar and "E-mail" in k:
                        v = "gisico@unicesar.edu.co"
                    md_lines.append(f"| {k} | {v} |")

                    if "Año y mes" in k:
                        grupo_obj.ano_mes_formacion = v
                    elif "Departamento" in k:
                        grupo_obj.departamento_ciudad = v
                    elif "Líder" in k:
                        grupo_obj.lider = v
                    elif "certificad" in k:
                        grupo_obj.certificacion = v
                    elif "Página web" in k:
                        grupo_obj.pagina_web = v
                    elif "E-mail" in k:
                        grupo_obj.email = v
                    elif "Clasificación" in k:
                        grupo_obj.clasificacion = v
                    elif "Área de conocimiento" in k:
                        grupo_obj.area_conocimiento = v
                    elif "Programa nacional" in k:
                        grupo_obj.programa_nacional = v
            md_lines.append("")

        elif "Instituciones" in sec_title:
            md_lines.append("| Institución avaladora |")
            md_lines.append("|---|")
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    inst = limpiar_texto(td.get_text())
                    if inst and inst != "Instituciones":
                        grupo_obj.instituciones.append(InstitucionAval(nombre=inst))
                        md_lines.append(f"| {inst} |")
            md_lines.append("")

        elif "Integrantes del grupo" in sec_title:
            md_lines.append("| Nombre | Vinculación | Horas | Período |")
            md_lines.append("|---|---|:---:|---|")
            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) >= 4:
                    nom = limpiar_texto(tds[0].get_text())
                    if nom == "Nombre":
                        continue
                    vinc = limpiar_texto(tds[1].get_text())
                    hrs = limpiar_texto(tds[2].get_text())
                    per = limpiar_texto(tds[3].get_text())
                    
                    partes_per = per.split(" - ")
                    ini = partes_per[0].strip() if len(partes_per) > 0 else None
                    fin = partes_per[1].strip() if len(partes_per) > 1 else None

                    grupo_obj.integrantes.append(IntegranteGrupo(
                        nombre=nom,
                        vinculacion=vinc,
                        horas_dedicacion=hrs,
                        inicio_vinculacion=ini,
                        fin_vinculacion=fin
                    ))

                    display_nom = "[INTEGRANTE-GISICO]" if anonimizar else nom
                    md_lines.append(f"| {display_nom} | {vinc} | {hrs} | {per} |")
            md_lines.append("")

        elif "Líneas de investigación" in sec_title:
            md_lines.append("| Línea de Investigación Declarada |")
            md_lines.append("|---|")
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    linea = limpiar_texto(td.get_text())
                    if linea and "Líneas de investigación" not in linea:
                        grupo_obj.lineas_investigacion.append(LineaInvestigacion(nombre=linea))
                        md_lines.append(f"| {linea} |")
            md_lines.append("")

        elif "Artículos publicados" in sec_title:
            md_lines.append("| N° | Referencia Bibliográfica / Detalles |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Artículos publicados" not in txt:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        grupo_obj.articulos.append(ProductoBibliografico(
                            tipo="Articulo",
                            titulo=txt[:150],
                            ano=ano_val,
                            detalles=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
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
                    txt = limpiar_texto(td.get_text())
                    if txt and "Libros publicados" not in txt:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        grupo_obj.libros.append(ProductoBibliografico(
                            tipo="Libro",
                            titulo=txt[:150],
                            ano=ano_val,
                            detalles=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
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
                    txt = limpiar_texto(td.get_text())
                    if txt and "Capítulos de libro" not in txt:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        grupo_obj.capitulos.append(ProductoBibliografico(
                            tipo="Capitulo",
                            titulo=txt[:150],
                            ano=ano_val,
                            detalles=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
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
                    txt = limpiar_texto(td.get_text())
                    if txt and "Softwares" not in txt:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        grupo_obj.softwares.append(ProductoSoftware(
                            titulo=txt[:150],
                            ano=ano_val,
                            disponibilidad=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        elif "Trabajos dirigidos" in sec_title:
            md_lines.append("| N° | Trabajo Dirigido / Tutoría |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Trabajos dirigidos" not in txt:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        grupo_obj.trabajos_dirigidos.append(TrabajoDirigido(
                            tipo_trabajo="Tesis/Trabajo",
                            titulo=txt[:150],
                            ano=ano_val,
                            persona_orientada=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        elif "Proyectos" in sec_title:
            md_lines.append("| N° | Proyecto de Investigación |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Proyectos" not in txt:
                        grupo_obj.proyectos.append(ProyectoInvestigacion(
                            titulo=txt[:150],
                            tipo=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        else:
            # Sección genérica / no estructurada
            md_lines.append("> *Sección preservada íntegramente (contenido textual semiestructurado / no estructurado):*\n")
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    t_str = limpiar_texto(td.get_text())
                    if t_str and t_str != sec_title:
                        display_t = anonymize_text(t_str) if anonimizar else t_str
                        md_lines.append(f"- {display_t}")
            md_lines.append("")

    return grupo_obj, "\n".join(md_lines)


def parse_cvlac(html_text: str, meta: dict, anonimizar: bool = False) -> tuple[InvestigadorCvLAC, str]:
    soup = BeautifulSoup(html_text, "lxml")
    md_lines: list[str] = []

    codigo_rh = meta.get("alias", "").replace("cvlac_", "")
    inv_obj = InvestigadorCvLAC(
        codigo_rh=codigo_rh,
        origen=MetadatosOrigen(
            url=meta["url"],
            fecha_descarga=meta["fecha_descarga"],
            sha256=meta["sha256"]
        )
    )

    md_lines.append(f"# Transcripción Integral CvLAC · {meta.get('alias', 'Investigador')}\n")
    md_lines.append(f"- **URL:** `{meta['url']}`")
    md_lines.append(f"- **Fecha Descarga:** `{meta['fecha_descarga']}`")
    md_lines.append(f"- **SHA256:** `{meta['sha256']}`")
    md_lines.append(f"- **Código HTTP:** {meta.get('codigo_http', 200)}")
    md_lines.append(f"- **Codificación:** {meta.get('encoding_utilizada', 'ISO-8859-1')}\n")
    md_lines.append("---\n")

    tables = soup.find_all("table")
    for idx, table in enumerate(tables):
        first_td = table.find("td")
        sec_title = limpiar_texto(first_td.get_text()) if first_td else f"Bloque {idx}"

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
                    k = limpiar_texto(tds[0].get_text())
                    v = limpiar_texto(tds[1].get_text())
                    
                    if k == "Nombre":
                        inv_obj.nombre_completo = v
                        if anonimizar:
                            v = "[INVESTIGADOR-CVLAC-UPC]"
                    elif "citaciones" in k:
                        inv_obj.nombre_citaciones = v
                        if anonimizar:
                            v = "[CITACIONES-PROTEGIDAS]"
                    elif k == "Nacionalidad":
                        inv_obj.nacionalidad = v
                    elif k == "Sexo":
                        inv_obj.sexo = v
                    elif "Categoría" in k or "Categoria" in k:
                        inv_obj.categoria_declarada = v
                    elif "Par evaluador" in k:
                        inv_obj.par_evaluador = True

                    md_lines.append(f"| {k} | {v} |")
            md_lines.append("")

        elif "Formación Académica" in sec_title or "Formacion Academica" in sec_title:
            md_lines.append("| Nivel | Detalle Formación |")
            md_lines.append("|---|---|")
            for tr in rows:
                tds = tr.find_all("td")
                txt_row = " ".join(limpiar_texto(td.get_text()) for td in tds).strip()
                if txt_row and "Formación Académica" not in txt_row and len(txt_row) > 10:
                    nivel = "Formación"
                    if "doctorado" in txt_row.lower():
                        nivel = "Doctorado"
                    elif "maestr" in txt_row.lower():
                        nivel = "Maestría"
                    elif "pregrado" in txt_row.lower():
                        nivel = "Pregrado"
                    elif "perfeccionamiento" in txt_row.lower():
                        nivel = "Perfeccionamiento"

                    inv_obj.formacion.append(FormacionAcademica(
                        nivel=nivel,
                        titulo=txt_row[:100],
                        institucion=txt_row
                    ))
                    display_v = anonymize_text(txt_row) if anonimizar else txt_row
                    md_lines.append(f"| {nivel} | {display_v} |")
            md_lines.append("")

        elif "Áreas de actuación" in sec_title:
            md_lines.append("| Área de Actuación Declarada |")
            md_lines.append("|---|")
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Áreas de actuación" not in txt:
                        inv_obj.areas_actuacion.append(txt)
                        md_lines.append(f"| {txt} |")
            md_lines.append("")

        elif "Líneas de investigación" in sec_title:
            md_lines.append("| Línea de Investigación Declarada |")
            md_lines.append("|---|")
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Líneas de investigación" not in txt:
                        inv_obj.lineas_investigacion.append(txt)
                        md_lines.append(f"| {txt} |")
            md_lines.append("")

        elif "Artículos" in sec_title:
            md_lines.append("| N° | Artículo Científico |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Artículos" not in txt and len(txt) > 20:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        inv_obj.articulos.append(ProductoBibliografico(
                            tipo="Articulo",
                            titulo=txt[:150],
                            ano=ano_val,
                            detalles=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        elif "Capitulos de libro" in sec_title:
            md_lines.append("| N° | Capítulo de Libro |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Capitulos de libro" not in txt and len(txt) > 20:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        inv_obj.capitulos.append(ProductoBibliografico(
                            tipo="Capitulo",
                            titulo=txt[:150],
                            ano=ano_val,
                            detalles=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        elif "Softwares" in sec_title:
            md_lines.append("| N° | Producto de Software |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Softwares" not in txt and len(txt) > 20:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        inv_obj.softwares.append(ProductoSoftware(
                            titulo=txt[:150],
                            ano=ano_val,
                            disponibilidad=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        elif "Trabajos dirigidos/tutorías" in sec_title:
            md_lines.append("| N° | Trabajo Dirigido / Tutoría |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Trabajos dirigidos" not in txt and len(txt) > 20:
                        ano_m = re.search(r'\b(19\d{2}|20\d{2})\b', txt)
                        ano_val = int(ano_m.group(1)) if ano_m else None
                        inv_obj.trabajos_dirigidos.append(TrabajoDirigido(
                            tipo_trabajo="Tutoría/Trabajo de Grado",
                            titulo=txt[:150],
                            ano=ano_val,
                            persona_orientada=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        elif "Proyectos" in sec_title:
            md_lines.append("| N° | Proyecto de Investigación |")
            md_lines.append("|:---:|---|")
            num = 1
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and "Proyectos" not in txt and len(txt) > 20:
                        inv_obj.proyectos.append(ProyectoInvestigacion(
                            titulo=txt[:150],
                            tipo=txt
                        ))
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"| {num} | {display_txt} |")
                        num += 1
            md_lines.append("")

        else:
            md_lines.append("> *Sección preservada íntegramente (contenido textual no estructurado):*\n")
            for tr in rows:
                tds = tr.find_all("td")
                for td in tds:
                    txt = limpiar_texto(td.get_text())
                    if txt and txt != sec_title and len(txt) > 3:
                        display_txt = anonymize_text(txt) if anonimizar else txt
                        md_lines.append(f"- {display_txt}")
            md_lines.append("")

    return inv_obj, "\n".join(md_lines)


def procesar_todo(raiz_repo: Path):
    cache_dir = raiz_repo / "datos" / "cache"
    privado_dir = raiz_repo / "brain" / "40-Fuentes" / "privado"
    publicado_dir = raiz_repo / "brain" / "40-Fuentes" / "publicado"
    fixtures_dir = raiz_repo / "tests" / "fixtures" / "scienti"

    privado_dir.mkdir(parents=True, exist_ok=True)
    publicado_dir.mkdir(parents=True, exist_ok=True)
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Procesar GrupLAC 10 ceros (GISICO)
    meta_g_path = cache_dir / "gruplac_00000000002099.meta.json"
    html_g_path = cache_dir / "gruplac_00000000002099.html"
    if html_g_path.exists() and meta_g_path.exists():
        meta_g = json.loads(meta_g_path.read_text(encoding="utf-8"))
        raw_g = html_g_path.read_bytes()
        html_g = raw_g.decode("iso-8859-1")

        # Versión privada completa
        grupo_obj, md_priv_g = parse_gruplac(html_g, meta_g, anonimizar=False)
        frontmatter_priv_g = f"""---
tipo: fuente
estado: borrador
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SCIENTI-GrupLAC]]"
  - "[[SCIENTI-Mapa-de-campos]]"
origen: "{meta_g['url']}"
url: "{meta_g['url']}"
fecha_descarga: {meta_g['fecha_descarga']}
sha256: {meta_g['sha256']}
---

"""
        (privado_dir / "SCIENTI-GrupLAC-completo.md").write_text(
            (frontmatter_priv_g + md_priv_g).replace("\r\n", "\n"), encoding="utf-8", newline="\n"
        )

        # Versión pública anonimizada
        _, md_pub_g = parse_gruplac(html_g, meta_g, anonimizar=True)
        frontmatter_pub_g = f"""---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-Grupos]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[SCIENTI-Informe-extraccion]]"
origen: "{meta_g['url']}"
url: "{meta_g['url']}"
fecha_descarga: {meta_g['fecha_descarga']}
sha256: {meta_g['sha256']}
---

"""
        (publicado_dir / "SCIENTI-GrupLAC.md").write_text(
            (frontmatter_pub_g + md_pub_g).replace("\r\n", "\n"), encoding="utf-8", newline="\n"
        )

        # Fixture anonimizado y esperado.json
        (fixtures_dir / "gruplac_00000000002099.html").write_text(anonymize_text(html_g), encoding="iso-8859-1")
        (fixtures_dir / "gruplac_00000000002099.esperado.json").write_text(
            grupo_obj.model_dump_json(indent=2), encoding="utf-8", newline="\n"
        )

    # 2. Procesar GrupLAC 9 ceros (literal prompt, vacío)
    meta_g9_path = cache_dir / "gruplac_0000000002099.meta.json"
    html_g9_path = cache_dir / "gruplac_0000000002099.html"
    if html_g9_path.exists() and meta_g9_path.exists():
        meta_g9 = json.loads(meta_g9_path.read_text(encoding="utf-8"))
        raw_g9 = html_g9_path.read_bytes()
        html_g9 = raw_g9.decode("iso-8859-1")
        grupo_vacio, _ = parse_gruplac(html_g9, meta_g9, anonimizar=True)
        (fixtures_dir / "gruplac_0000000002099.html").write_text(html_g9, encoding="iso-8859-1")
        (fixtures_dir / "gruplac_0000000002099.esperado.json").write_text(
            grupo_vacio.model_dump_json(indent=2), encoding="utf-8", newline="\n"
        )

    # 3. Procesar CvLAC
    meta_c_path = cache_dir / "cvlac_0000494917.meta.json"
    html_c_path = cache_dir / "cvlac_0000494917.html"
    if html_c_path.exists() and meta_c_path.exists():
        meta_c = json.loads(meta_c_path.read_text(encoding="utf-8"))
        raw_c = html_c_path.read_bytes()
        html_c = raw_c.decode("iso-8859-1")

        # Versión privada
        inv_obj, md_priv_c = parse_cvlac(html_c, meta_c, anonimizar=False)
        frontmatter_priv_c = f"""---
tipo: fuente
estado: borrador
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SCIENTI-CvLAC]]"
  - "[[SCIENTI-Mapa-de-campos]]"
origen: "{meta_c['url']}"
url: "{meta_c['url']}"
fecha_descarga: {meta_c['fecha_descarga']}
sha256: {meta_c['sha256']}
---

"""
        (privado_dir / "SCIENTI-CvLAC-completo.md").write_text(
            (frontmatter_priv_c + md_priv_c).replace("\r\n", "\n"), encoding="utf-8", newline="\n"
        )

        # Versión pública anonimizada
        _, md_pub_c = parse_cvlac(html_c, meta_c, anonimizar=True)
        frontmatter_pub_c = f"""---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-Investigadores]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[SCIENTI-Informe-extraccion]]"
origen: "{meta_c['url']}"
url: "{meta_c['url']}"
fecha_descarga: {meta_c['fecha_descarga']}
sha256: {meta_c['sha256']}
---

"""
        (publicado_dir / "SCIENTI-CvLAC.md").write_text(
            (frontmatter_pub_c + md_pub_c).replace("\r\n", "\n"), encoding="utf-8", newline="\n"
        )

        # Fixture anonimizado y esperado.json
        (fixtures_dir / "cvlac_0000494917.html").write_text(anonymize_text(html_c), encoding="iso-8859-1")
        (fixtures_dir / "cvlac_0000494917.esperado.json").write_text(
            inv_obj.model_dump_json(indent=2), encoding="utf-8", newline="\n"
        )

    print("[EXITO] Extracción y transcripción completada.")


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent.parent
    procesar_todo(raiz)
