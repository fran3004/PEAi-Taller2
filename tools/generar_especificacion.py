"""Genera la especificación de requisitos de software (IEEE 830) de PEA-i en Word.

Parte de ``docs/plantilla/plantilla_formato_ieee830.docx`` (la plantilla del enunciado
convertida a .docx), conserva su portada, ficha, encabezados y estilos, y sustituye el
cuerpo por el contenido del proyecto, con capturas y diagramas UML de ``docs/imagenes``.

Uso (desde la raíz; requiere python-docx y Word para actualizar el índice)::

    py -3 tools/generar_especificacion.py
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "docs" / "plantilla" / "plantilla_formato_ieee830.docx"
IMAGENES = RAIZ / "docs" / "imagenes"
SALIDA = RAIZ / "entrega" / "Especificacion_Tecnica_PEAi.docx"
EVIDENCIA = RAIZ / "docs" / "evidencias" / "parcial-urls-20261025.json"
LOGO = RAIZ / "docs" / "entrada" / "identidad" / "logo_upc.png"

PROYECTO = "PEA-i · Programa Estadístico de Análisis de Investigación"
VERSION = "0.2.1"
FECHA = "25/10/2026"
AZUL = "12355B"


# ---------------------------------------------------------------------------
# Utilidades de documento
# ---------------------------------------------------------------------------
class Constructor:
    def __init__(self, doc: Document) -> None:
        self.doc = doc
        self.cuerpo = doc.element.body
        self.n_fig = 0
        self.n_tab = 0
        self._cola = self.cuerpo.find(qn("w:sectPr"))

    def _anadir(self, el) -> None:
        self._cola.addprevious(el)

    def parrafo(self, texto: str = "", estilo: str = "Normal indentado 2", negrita: bool = False, cursiva: bool = False,
                alinear=None, tam: float | None = None, color: str | None = None) -> Paragraph:
        p = self.doc.add_paragraph(style=estilo)
        self._anadir(p._p)
        self._runs(p, texto, negrita, cursiva, tam, color)
        if alinear is not None:
            p.alignment = alinear
        return p

    @staticmethod
    def _runs(p: Paragraph, texto: str, negrita=False, cursiva=False, tam=None, color=None) -> None:
        # **negrita** y `código` dentro del texto
        for trozo in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", texto):
            if not trozo:
                continue
            if trozo.startswith("**"):
                r = p.add_run(trozo[2:-2])
                r.bold = True
            elif trozo.startswith("`"):
                r = p.add_run(trozo[1:-1])
                r.font.name = "Consolas"
                r.font.size = Pt((tam or 9) - 0.5)
            else:
                r = p.add_run(trozo)
                r.bold = negrita or None
            r.italic = cursiva or None
            if tam and not trozo.startswith("`"):
                r.font.size = Pt(tam)
            if color:
                r.font.color.rgb = RGBColor.from_string(color)

    def h1(self, t):
        p = self.parrafo(t, "Heading 1")
        p.paragraph_format.page_break_before = True
        return p

    def h2(self, t):
        return self.parrafo(t, "Heading 2")

    def h3(self, t):
        return self.parrafo(t, "Heading 3")

    def p(self, t, nivel=2, **kw):
        return self.parrafo(t, f"Normal indentado {nivel}", **kw)

    def vinetas(self, items, nivel=2):
        for it in items:
            p = self.parrafo("•	" + it, f"Normal indentado {nivel}")
            p.paragraph_format.left_indent = Cm(1.04 * nivel + 0.6)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(1.04 * nivel + 0.6))
            p.paragraph_format.space_after = Pt(2)

    def numeradas(self, items, nivel=2):
        for i, it in enumerate(items, 1):
            p = self.parrafo(f"{i}. {it}", f"Normal indentado {nivel}")
            p.paragraph_format.space_after = Pt(2)

    def codigo(self, texto: str, nivel=2) -> None:
        for linea in texto.strip("\n").split("\n"):
            p = self.parrafo("", f"Normal indentado {nivel}")
            r = p.add_run(linea or " ")
            r.font.name = "Consolas"
            r.font.size = Pt(8)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear")
            sh.set(qn("w:fill"), "F2F4F7")
            p._p.get_or_add_pPr().append(sh)

    def figura(self, archivo: str, leyenda: str, ancho_cm: float = 13.5, nivel=2, alto_max_cm: float = 17.5) -> None:
        ruta = IMAGENES / archivo
        w, h = Image.open(ruta).size
        ancho = min(ancho_cm, alto_max_cm * w / h)
        p = self.parrafo("", f"Normal indentado {nivel}", alinear=WD_ALIGN_PARAGRAPH.CENTER)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(6)
        p.add_run().add_picture(str(ruta), width=Cm(ancho))
        self.n_fig += 1
        c = self.parrafo(f"Figura {self.n_fig}. {leyenda}", "Caption", alinear=WD_ALIGN_PARAGRAPH.CENTER)
        c.paragraph_format.left_indent = Cm(1.0 * nivel)

    def tabla(self, filas: list[list[str]], anchos_cm: list[float], encabezado: bool = True, leyenda: str | None = None,
              tam: float = 8, nivel=2) -> Table:
        if leyenda:
            self.n_tab += 1
            c = self.parrafo(f"Tabla {self.n_tab}. {leyenda}", "Caption", alinear=WD_ALIGN_PARAGRAPH.LEFT)
            c.paragraph_format.left_indent = Cm(1.0 * nivel)
            c.paragraph_format.keep_with_next = True
        t = self.doc.add_table(rows=len(filas), cols=len(anchos_cm))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        self._anadir(t._tbl)
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                celda = t.cell(i, j)
                celda.width = Cm(anchos_cm[j])
                celda.text = ""
                par = celda.paragraphs[0]
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.space_before = Pt(1)
                lineas = str(valor).split("\n")
                for k, linea in enumerate(lineas):
                    if k:
                        par = celda.add_paragraph()
                        par.paragraph_format.space_after = Pt(1)
                    self._runs(par, linea, negrita=(encabezado and i == 0), tam=tam)
                if encabezado and i == 0:
                    self._sombrear(celda, AZUL)
                    for r in celda.paragraphs[0].runs:
                        r.font.color.rgb = RGBColor(255, 255, 255)
                elif j == 0 and not encabezado:
                    self._sombrear(celda, "E3EDF7")
                    for r in celda.paragraphs[0].runs:
                        r.bold = True
        if encabezado:
            trpr = t.rows[0]._tr.get_or_add_trPr()
            th = OxmlElement("w:tblHeader")
            trpr.append(th)
        for fila in t.rows:
            trpr = fila._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            trpr.append(cs)
        sep = self.parrafo("", "Normal", tam=4)
        sep.paragraph_format.space_after = Pt(4)
        return t

    @staticmethod
    def _sombrear(celda, color: str) -> None:
        tcpr = celda._tc.get_or_add_tcPr()
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear")
        sh.set(qn("w:color"), "auto")
        sh.set(qn("w:fill"), color)
        tcpr.append(sh)

    def requisito(self, numero: str, nombre: str, fuente: str, prioridad: str = "Alta", tipo: str = "Requisito") -> None:
        marca = lambda cond: "☒" if cond else "☐"  # noqa: E731
        t = self.doc.add_table(rows=5, cols=4)
        t.style = "Table Grid"
        t.autofit = False
        self._anadir(t._tbl)
        anchos = [4.0, 3.6, 3.6, 3.8]
        datos = [
            ("Número de requisito", numero),
            ("Nombre de requisito", nombre),
            ("Tipo", None),
            ("Fuente del requisito", fuente),
            ("Prioridad del requisito", None),
        ]
        for i, (a, b) in enumerate(datos):
            for j in range(4):
                t.cell(i, j).width = Cm(anchos[j])
            c0 = t.cell(i, 0)
            c0.text = ""
            self._runs(c0.paragraphs[0], a, negrita=True, tam=8)
            self._sombrear(c0, "E3EDF7")
            if b is not None:
                m = t.cell(i, 1).merge(t.cell(i, 3))
                m.text = ""
                self._runs(m.paragraphs[0], b, tam=8, negrita=(i == 1))
        valores_tipo = [f"{marca(tipo == 'Requisito')} Requisito", f"{marca(tipo != 'Requisito')} Restricción"]
        for j, v in enumerate(valores_tipo, 1):
            t.cell(2, j).text = ""
            self._runs(t.cell(2, j).paragraphs[0], v, tam=8)
        t.cell(2, 3).text = ""
        prios = [("Alta", "Alta/Esencial"), ("Media", "Media/Deseado"), ("Baja", "Baja/Opcional")]
        for j, (clave, etiqueta) in enumerate(prios, 1):
            t.cell(4, j).text = ""
            self._runs(t.cell(4, j).paragraphs[0], f"{marca(prioridad == clave)} {etiqueta}", tam=8)
        for fila in t.rows:
            for c in fila.cells:
                for par in c.paragraphs:
                    par.paragraph_format.space_after = Pt(1)
                    par.paragraph_format.space_before = Pt(1)
        sep = self.parrafo("", "Normal", tam=4)
        sep.paragraph_format.space_after = Pt(2)

    def salto(self) -> None:
        p = self.doc.add_paragraph()
        self._anadir(p._p)
        p.add_run().add_break(__import__("docx").enum.text.WD_BREAK.PAGE)


# ---------------------------------------------------------------------------
# Plantilla: portada, ficha y limpieza
# ---------------------------------------------------------------------------
def reemplazar_texto(raiz, mapa: dict[str, str]) -> None:
    for nodo in raiz.iter(qn("w:t"), qn("w:instrText")):
        if nodo.text:
            for a, b in mapa.items():
                if a in nodo.text:
                    nodo.text = nodo.text.replace(a, b)


def poner_celda(celda, texto: str, tam: float = 8.5, negrita=False) -> None:
    for p in list(celda.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    p = celda.paragraphs[0]
    for hijo in list(p._p):
        if hijo.tag != qn("w:pPr"):
            p._p.remove(hijo)
    r = p.add_run(texto)
    r.font.size = Pt(tam)
    r.bold = negrita or None


def preparar_plantilla() -> Document:
    d = Document(str(PLANTILLA))
    hijos = list(d.element.body.iterchildren())
    # 1. Quitar la hoja de instrucciones (párrafos 54-108: guiazul y Body Text de la sección 2)
    for el in hijos[54:109]:
        if el.tag == qn("w:p"):
            el.getparent().remove(el)
    # 2. Quitar el cuerpo de ejemplo (desde «Introducción» hasta antes del sectPr final)
    hijos = list(d.element.body.iterchildren())
    inicio = next(i for i, el in enumerate(hijos)
                  if el.tag == qn("w:p") and Paragraph(el, d).style.name == "Heading 1")
    for el in hijos[inicio:]:
        if el.tag != qn("w:sectPr"):
            el.getparent().remove(el)
    # 3. Textos de campos (portada, encabezados)
    mapa = {
        "[Nombre del proyecto]": "PEA-i",
        "[99.99]": VERSION,
        "[Mes de año]": "Octubre de 2026",
        "[Nombre documento]": "Especificación de requisitos",
        "Modelo de ingeniería": "PEA-i",
    }
    reemplazar_texto(d.element.body, mapa)
    for parte in d.part.package.iter_parts():
        if "/word/header" in str(parte.partname) or "/word/footer" in str(parte.partname):
            reemplazar_texto(parte._element, mapa)
    # 4. Portada: nombre largo del proyecto
    for p in d.paragraphs:
        if p.text.startswith("Proyecto:"):
            reemplazar_texto(p._p, {"PEA-i": PROYECTO})
    # 5. Ficha del documento
    tablas = d.tables
    ficha = next(t for t in tablas if t.rows[0].cells[0].text.strip() == "Fecha")
    for celda, valor in zip(ficha.rows[1].cells,
                            [FECHA, VERSION, "Franier Fernandez\nSantiago Moreno\n(Grupo 8)",
                             "Autores, con `verificar.ps1` (pruebas Python y C++)"], strict=True):
        poner_celda(celda, valor.replace("`", ""))
    validacion = next(t for t in tablas if t.rows[0].cells[0].text.strip().startswith("Por el cliente"))
    poner_celda(validacion.rows[1].cells[0], "Docente de Estructura de Datos\nUniversidad Popular del Cesar", 8.5)
    poner_celda(validacion.rows[1].cells[1], "Grupo 8: Franier Fernandez y Santiago Moreno", 8.5)
    poner_celda(validacion.rows[2].cells[0], "Fdo. D./Dña: ______________________", 8.5)
    poner_celda(validacion.rows[2].cells[1], "Fdo. D./Dña: ______________________", 8.5)
    for p in d.paragraphs:
        if p.text.startswith("Documento validado por las partes"):
            for r in p.runs[1:]:
                r.text = ""
            p.runs[0].text = f"Documento validado por las partes en fecha: {FECHA}"
    return d


# ---------------------------------------------------------------------------
# Contenido
# ---------------------------------------------------------------------------
def cargar_evidencia() -> dict:
    return json.loads(EVIDENCIA.read_text(encoding="utf-8"))


def redactar(c: Constructor, ev: dict) -> None:
    r = ev["resultados"]

    def f(v: float) -> str:
        return f"{v:.6f}".replace(".", ",")

    # ------------------------------------------------------------------ 1
    c.h1("Introducción")
    c.p("Este documento es la Especificación de Requisitos de Software (SRS) del **Programa Estadístico de Análisis "
        "de Investigación (PEA-i)**, redactada con el formato de la plantilla IEEE Std 830-1998 entregada con el Parcial 2 "
        "de Estructura de Datos. Describe qué hace el sistema, cómo se estructura su información, la estrategia de solución "
        "y la forma de comprobar cada requisito, e incluye diagramas de casos de uso y de secuencia (UML), las capturas de "
        "ambas aplicaciones y la trazabilidad con el enunciado.", 1)
    c.h2("Propósito")
    c.p("El documento fija el contrato funcional y técnico de la versión **0.2.1 · Parcial 2** de PEA-i para que el "
        "docente pueda evaluarla, los autores puedan mantenerla y cualquier persona pueda reproducir la instalación y las "
        "pruebas. Está dirigido a:")
    c.vinetas(["El docente de Estructura de Datos de la Universidad Popular del Cesar (UPC), como cliente y evaluador.",
               "Los autores (Grupo 8), como equipo de desarrollo y pruebas.",
               "Futuros mantenedores que necesiten entender las estructuras de datos, la arquitectura y las decisiones."])
    c.h2("Alcance")
    c.p("El producto se denomina **PEA-i** y consta de dos aplicaciones independientes que comparten arquitectura, "
        "reglas del dominio y base de datos: una aplicación de escritorio **Python 3.12 con interfaz gráfica PySide6** y "
        "una aplicación **C++17 de terminal interactiva (FTXUI) y línea de comandos**. Ambas gestionan grupos de "
        "investigación, investigadores y productos de investigación del SCIENTI de Minciencias, calculan estadísticas "
        "descriptivas y el **Indicador de producción científica** del Parcial 2 para un grupo y para un investigador.")
    c.p("**Incluye:** CRUD con desactivación lógica y deshacer; listas dobles, multilista, pila, cola e hipercubo "
        "implementados a mano; importación desde URL de GrupLAC/CvLAC, CSV y PDF; filtro por años; dashboard con "
        "histogramas y barras (Python) y resumen de datos (C++); persistencia compartida en Supabase y en archivos locales "
        "JSON; paquete portable para Windows.")
    c.p("**No incluye:** una clasificación nacional oficial de Minciencias (el indicador se normaliza contra una "
        "población declarada), reconocimiento óptico de caracteres (OCR) para PDF escaneados, autenticación por roles ni "
        "versiones para otros sistemas operativos. La producción del video de sustentación queda fuera de este documento.")
    c.p("La definición es consistente con el enunciado «Parcial 2 EdD (2026-10-19)», con el Taller 2 que lo precede y con "
        "el Modelo de Medición de Grupos M601PR04G01 (versión 02, 2024).")
    c.h2("Personal involucrado")
    for nombre, rol, cat, resp, contacto in [
        ("Franier Fernandez", "Autor · desarrollo y pruebas (Grupo 8)", "Estudiante de Ingeniería de Sistemas, UPC",
         "Análisis, diseño, implementación Python/C++, pruebas y documentación; ambos autores responden por el conjunto "
         "del entregable.", "Repositorio GitHub fran3004/PEAi-Taller2"),
        ("Santiago Moreno", "Autor · desarrollo y pruebas (Grupo 8)", "Estudiante de Ingeniería de Sistemas, UPC",
         "Análisis, diseño, implementación Python/C++, pruebas y documentación; ambos autores responden por el conjunto "
         "del entregable.", "Repositorio GitHub fran3004/PEAi-Taller2"),
        ("Docente de Estructura de Datos", "Cliente y evaluador", "Docente, Facultad de Ingenierías y Tecnológicas, UPC",
         "Define el enunciado, revisa y califica la entrega.", "adithperez@unicesar.edu.co (correo de entrega del enunciado)"),
    ]:
        c.tabla([["Nombre", nombre], ["Rol", rol], ["Categoría profesional", cat], ["Responsabilidades", resp],
                 ["Información de contacto", contacto], ["Aprobación", "Pendiente de la revisión del docente"]],
                [4.0, 9.5], encabezado=False, tam=8.5)
    c.p("Nota: el enunciado pide grupos de tres estudiantes; el archivo de identificación del proyecto registra dos "
        "integrantes y no se inventa un tercero.", 2, cursiva=True, tam=9)
    c.h2("Definiciones, acrónimos y abreviaturas")
    c.tabla([["Término", "Definición"],
             ["PEA / PEA-i", "Programa Estadístico de Análisis de investigación solicitado por la UPC; PEA-i es su nombre."],
             ["SCIENTI", "Plataforma de Minciencias que publica GrupLAC (grupos) y CvLAC (currículos de investigadores)."],
             ["GrupLAC / CvLAC", "Perfil público de un grupo / de un investigador en SCIENTI; sus códigos son el número de "
                                 "GrupLAC (p. ej. 00000000002099) y el código RH (p. ej. 0000494917)."],
             ["Modelo M601PR04G01", "Modelo de medición de grupos e investigadores de Minciencias (versión 02, 2024)."],
             ["GNC, DTI, ASC, FRH", "Tipologías mayores de producto: generación de nuevo conocimiento, desarrollo tecnológico e "
                                    "innovación, apropiación social y formación de recurso humano."],
             ["Categoría de calidad", "Código del Modelo (p. ej. ART_A1, ART_D, SF, TD_B) que determina el peso relativo de un producto."],
             ["Ind.Grupo", "Indicador de producción científica: 3,7·Nc.Top + 2,3·Nc.A + 0,4·Nc.B + 1,5·AP + 0,5·DPC + 1·Fr.A + "
                           "0,2·Fr.B + 0,1·Cohe + 0,3·Coop."],
             ["λ (lambda)", "ln(1 + n / periodo): frecuencia anual amortiguada de los n productos únicos de un subtipo."],
             ["Lista doble", "Lista doblemente enlazada propia (nodos con anterior y siguiente)."],
             ["Multilista", "Estructura en la que cada producto es un único nodo referenciado desde su grupo y sus autores."],
             ["Pila / Cola", "Estructuras LIFO (deshacer) y FIFO (tareas de importación) implementadas a mano."],
             ["Hipercubo", "Tensor disperso de cinco dimensiones (grupo, investigador, categoría, año, validación)."],
             ["REST / RPC", "Acceso HTTP a tablas (PostgREST) y a funciones transaccionales de PostgreSQL en Supabase."],
             ["RLS", "Seguridad a nivel de fila de PostgreSQL."],
             ["GUI / TUI / CLI", "Interfaz gráfica / de terminal interactiva / de línea de comandos."],
             ["SRS, UML, CRUD", "Especificación de requisitos de software; lenguaje unificado de modelado; crear, leer, "
                                "actualizar y eliminar."],
             ["JCR / SJR", "Fuentes de cuartiles de revistas que exige el Modelo para las categorías de artículos."],
             ["ADR", "Registro de decisión de arquitectura (carpeta `brain/30-Decisiones`)."]],
            [3.4, 10.1], leyenda="Términos usados en el documento")
    c.h2("Referencias")
    c.tabla([["Referencia", "Título", "Ruta", "Fecha", "Autor"],
             ["[R1]", "Parcial 2 EdD (enunciado)", "docs/entrada/ y Parcial 2 EdD (2026-10-19).pdf", "19/10/2026", "UPC · EdD"],
             ["[R2]", "Taller 2 EdD · Grupo 8", "docs/entrada/Taller 2 EdD (2026-09-24) - G 8.pdf", "24/09/2026", "UPC · EdD"],
             ["[R3]", "Modelo de medición M601PR04G01 v02", "docs/entrada/Modelo-2024.original.pdf", "2024", "Minciencias"],
             ["[R4]", "IEEE Std 830-1998, plantilla de SRS", "plantilla_formato_ieee830.doc", "1998", "IEEE · Coloriuris"],
             ["[R5]", "Guía del Parcial 2", "docs/parcial-2.md", "25/10/2026", "Grupo 8"],
             ["[R6]", "Notas de la entrega 0.2.1", "docs/entrega-0.2.1.md", "25/10/2026", "Grupo 8"],
             ["[R7]", "Especificación formal SPEC (RF-01 a RF-13, RNF-01 a RNF-06)", "brain/10-Requisitos/SPEC.md", "02/10/2026", "Grupo 8"],
             ["[R8]", "Casos de uso CU-01 a CU-07", "brain/10-Requisitos/Casos-de-uso.md", "02/10/2026", "Grupo 8"],
             ["[R9]", "Arquitectura, estructuras e hipercubo", "brain/20-Diseno/", "oct. 2026", "Grupo 8"],
             ["[R10]", "Decisiones de arquitectura (ADR-0001 a ADR-0026)", "brain/30-Decisiones/", "oct. 2026", "Grupo 8"],
             ["[R11]", "Repositorio y Releases del proyecto", "https://github.com/fran3004/PEAi-Taller2", "oct. 2026", "Grupo 8"],
             ["[R12]", "SCIENTI GrupLAC y CvLAC (URL del enunciado)", "scienti.minciencias.gov.co", "consulta 25/10/2026", "Minciencias"],
             ["[R13]", "Evidencia de las URL del parcial", "docs/evidencias/parcial-urls-20261025.json", "25/10/2026", "Grupo 8"]],
            [1.4, 4.0, 4.2, 2.2, 1.7], tam=7.5, leyenda="Documentos relacionados")
    c.h2("Resumen")
    c.p("El capítulo 2 sitúa el producto, sus funciones principales (con diagramas de casos de uso), los usuarios, las "
        "restricciones y la evolución prevista. El capítulo 3 contiene la especificación detallada: interfaces (con capturas), "
        "los requisitos funcionales RF-01 a RF-23 con su tabla de identificación, y los requisitos no funcionales. El "
        "capítulo 4 reúne apéndices: diccionario de datos, el diseño de las estructuras de datos, la estrategia de solución del "
        "indicador con un ejemplo numérico, los diagramas UML de secuencia, de clases y de despliegue, los resultados "
        "obtenidos con las URL del enunciado, la trazabilidad con el parcial y la evidencia de verificación.")

    # ------------------------------------------------------------------ 2
    c.h1("Descripción general")
    c.h2("Perspectiva del producto")
    c.p("PEA-i es un producto independiente que se integra con dos sistemas externos: el portal público **SCIENTI** "
        "(fuente de datos) y un proyecto **Supabase/PostgreSQL** (persistencia compartida). Las dos aplicaciones cliente "
        "—Python y C++— son homólogas: misma arquitectura por capas, mismas estructuras de datos propias, mismas reglas y "
        "mismos resultados numéricos, verificados con una comparación automática de sus salidas.")
    c.figura("uml_10_arquitectura.png", "Arquitectura por capas: presentación, servicios, estructuras propias, repositorios, "
                                        "transporte HTTPS y Supabase.", 13)
    c.p("La presentación nunca accede a SQL, a la red ni a las estructuras; todo pasa por servicios. Los datos maestros "
        "viven solo en las estructuras propias y se sincronizan con Supabase mediante REST/RPC; si la persistencia falla, el "
        "servicio revierte la memoria. La entrega es un paquete portable para Windows x64 (diagrama de despliegue):")
    c.figura("uml_11_despliegue.png", "Diagrama de despliegue de la entrega portable.", 12.5)
    c.h2("Funcionalidad del producto")
    c.p("Resumen de las funciones principales (el detalle está en el capítulo 3):")
    c.vinetas(["Gestión de **grupos**, **investigadores**, **integrantes** y **productos** (crear, consultar, modificar, "
               "desactivar, activar y eliminar con cascada), con deshacer.",
               "Clasificación de cada producto por tipología, subtipo, año, validación y categoría de calidad con su peso.",
               "Importación desde URL de GrupLAC/CvLAC, CSV canónico y PDF, con cola FIFO y informes de errores.",
               "Filtro por años (todos, últimos N, rango, ventana del Modelo 2024) en todas las vistas.",
               "Estadísticas descriptivas desde el hipercubo: resumen de datos (C++) y dashboard con histogramas y "
               "barras (Python); análisis de redes de coautoría.",
               "**Indicador de producción científica** del grupo y del investigador, con desglose de nueve componentes.",
               "Persistencia en Supabase o en archivos locales JSON; inicio con datos o sin datos."])
    c.figura("uml_01_casos_uso_gestion.png", "Casos de uso de gestión del catálogo.", 14.5, alto_max_cm=17)
    c.figura("uml_02_casos_uso_analisis.png", "Casos de uso de consulta, importación e indicadores.", 14.5, alto_max_cm=17)
    c.figura("uml_03_casos_uso_indicador.png", "Casos de uso del Parcial 2 (indicador de producción científica).", 14.5,
             alto_max_cm=17)
    c.h2("Características de los usuarios")
    for tipo, form, hab, act in [
        ("Docente evaluador", "Profesional con posgrado en ingeniería o ciencias de la computación.",
         "Domina estructuras de datos; ejecuta paquetes portables y revisa código.",
         "Abre el paquete, importa o abre un catálogo, calcula los indicadores y revisa el código y este documento."),
        ("Analista de investigación", "Profesional o estudiante de pregrado/posgrado.",
         "Usa hojas de cálculo e interfaces gráficas; no necesita programar.",
         "Consulta estadísticas, gestiona registros, importa datos de SCIENTI y exporta resultados."),
        ("Desarrollador / mantenedor", "Estudiante o ingeniero de sistemas.",
         "Programa en Python y C++, usa Git, pruebas automáticas y CMake.",
         "Extiende módulos, ejecuta `verificar.ps1` y regenera el paquete."),
    ]:
        c.tabla([["Tipo de usuario", tipo], ["Formación", form], ["Habilidades", hab], ["Actividades", act]], [4.0, 9.5],
                encabezado=False, tam=8.5)
    c.h2("Restricciones")
    c.vinetas(["Las entidades maestras se almacenan **solo** en estructuras propias (lista doble, multilista, pila, cola, "
               "hipercubo); `list`, `dict`, `std::vector` o `std::map` se admiten únicamente como auxiliares temporales.",
               "Dos programas: Python 3.12 o superior (PySide6) y C++17 (CMake, MinGW-w64 UCRT64, Qt 6 Core/Network, FTXUI 5.0.0).",
               "Paridad: ambas implementaciones deben producir los mismos números para los mismos datos.",
               "Conexión únicamente por HTTPS a Supabase con la clave publicable; no se admiten `service_role` ni puertos SQL directos.",
               "Estadísticas descriptivas solo desde el hipercubo en memoria, sin SQL agregado.",
               "Interfaz, mensajes y documentación en español; entrega para Windows 10/11 de 64 bits.",
               "El Modelo 2024 define categorías, pesos, ventanas de observación y la fórmula del indicador."])
    c.h2("Suposiciones y dependencias")
    c.vinetas(["Hay Internet (HTTPS, puerto 443) para descargar de SCIENTI o conectar con Supabase; sin conexión se trabaja con archivos locales.",
               "El HTML público de GrupLAC/CvLAC conserva su estructura; si cambia, el extractor debe actualizarse.",
               "**SCIENTI no publica el cuartil ni el nivel de calidad** de cada producto. Sin esa categoría un producto no es "
               "puntuable en modo estricto; por eso existe el modo de estimación declarada (RF-19).",
               "Supabase permanece disponible (el plan gratuito puede pausarse); el control `keep-alive` solo reduce el riesgo.",
               "El corte 2023 corresponde a la convocatoria del Modelo 2024; puede cambiarse por el usuario.",
               "Si cambian el enunciado o el Modelo, deben revisarse las categorías y la fórmula (`modelo_2024.json`)."])
    c.h2("Evolución previsible del sistema")
    c.vinetas(["Vincular automáticamente los autores citados en el texto de GrupLAC con los integrantes, para completar cohesión y cooperación.",
               "Incorporar una población de referencia nacional (cargable por JSON) y los cuartiles JCR/SJR por ISSN.",
               "OCR para PDF escaneados y extracción estructurada de tablas en C++.",
               "Integrar la entidad Plan en las fichas de grupo y añadir una vista estadística por producto.",
               "Autenticación con roles y una versión web o multiplataforma."])

    # ------------------------------------------------------------------ 3
    c.h1("Requisitos específicos")
    c.p("Los requisitos se identifican como RF-nn (funcionales) y RNF-nn (no funcionales); cada RF lleva la tabla de "
        "identificación de la plantilla y su descripción con entradas, salidas, validaciones y respuesta a situaciones anormales. "
        "La columna «Fuente» remite al enunciado del parcial (puntos 1–12, PARCIAL 1–2, Notas 1–11) y a los documentos [R7] y [R8].", 1)
    c.h2("Requisitos comunes de los interfaces")
    c.p("Entradas y salidas del sistema: datos de SCIENTI (HTML), CSV, PDF y JSON local como entradas; pantallas, tablas, "
        "gráficos, archivos CSV/JSON/PNG y la salida de consola como resultados.")
    c.h3("Interfaces de usuario")
    c.p("**Aplicación Python (GUI PySide6).** Barra superior con nueve pantallas: Inicio, Investigadores, Grupos, Productos, "
        "Análisis de redes, Importar, Configuración, Acerca de e Indicadores; botón Deshacer, filtro de años, exportación y pie "
        "institucional con el origen de datos y la revisión. Tamaños admitidos desde 1100 × 700 píxeles lógicos.", 3)
    c.figura("gui_01_inicio.png", "Inicio: fichas, producción por año y tipología y filtro de años (datos de demostración).", 12.8, 3)
    c.figura("gui_02_investigadores.png", "Directorio de investigadores con tabla, búsqueda y ficha lateral.", 12.8, 3)
    c.figura("gui_03_grupos.png", "Directorio de grupos.", 12.8, 3)
    c.figura("gui_04_productos.png", "Catálogo de productos con categoría y validación.", 12.8, 3)
    c.figura("gui_05_redes.png", "Análisis de redes de coautoría.", 12.8, 3)
    c.figura("gui_06_importar.png", "Importación desde CSV, URL SCIENTI o PDF con la cola de tareas.", 12.8, 3)
    c.figura("gui_07_configuracion.png", "Configuración: origen de datos, conexión y verificación cruzada.", 12.8, 3)
    c.figura("gui_09_indicador_ejemplo.png", "Indicadores: cálculo del grupo del catálogo de ejemplo (modo estricto).", 12.8, 3,
             alto_max_cm=22)
    c.figura("gui_10_indicador_estimado.png", "Indicadores con «Estimar categorías faltantes» activado.", 12.5, 3, alto_max_cm=22)
    c.figura("gui_11_indicador_gisico.png", "Indicador del grupo GISICO (URL del enunciado) con categorías estimadas.", 12.8, 3,
             alto_max_cm=22)
    c.p("**Aplicación C++ (terminal interactiva FTXUI).** Nueve pestañas numeradas (1–9), tablas paginadas de 12 filas, formularios "
        "con Tab/Enter/Escape y atajos: `/` buscar, `n` crear, `e` editar, `t` activar o desactivar, `x` eliminar con confirmación, `v` "
        "ficha, `u` deshacer, `r` recargar, `i` importar CSV, `w` importar URL, `[` y `]` paginar; en Indicadores, `c` calcular, `s` "
        "guardar y `o` abrir archivo. Admite `--ascii`, `--sin-color` y se recomienda 100 × 28 caracteres.", 3)
    c.figura("tui_01_inicio.png", "TUI C++: resumen institucional.", 11, 3)
    c.figura("tui_02_investigadores.png", "TUI C++: directorio de investigadores.", 11, 3)
    c.figura("tui_05_indicadores.png", "TUI C++: pestaña de indicadores.", 11, 3)
    c.p("**Línea de comandos.** `pea-cli.exe` (Python) y `pea-cpp.exe` (C++) comparten comandos: `info`, `verificar`, `resumen`, "
        "`importar-url`, `importar-csv`, `importar-pdf`, `exportar-csv`, `indicador`, `guardar-local`, `cargar-ejemplo` y "
        "`aplicar-escenario`.", 3)
    c.h3("Interfaces de hardware")
    c.p("No hay interfaz con hardware especial. Requiere un PC con Windows 10/11 de 64 bits, pantalla de al menos 1100 × 700 "
        "(GUI) o terminal de 100 × 28 (TUI; se recomienda Windows Terminal) y acceso de red HTTPS opcional.", 3)
    c.h3("Interfaces de software")
    c.tabla([["Producto software", "Propósito", "Definición del interfaz"],
             ["Supabase (PostgREST, RPC, Auth, RLS)", "Persistencia compartida de grupos, investigadores, integrantes, productos y vínculos.",
              "HTTPS/JSON: GET/POST/PATCH/DELETE sobre tablas y POST `/rpc/<función>`; cabecera de clave publicable y token de sesión; "
              "control de `meta.revision`."],
             ["SCIENTI GrupLAC / CvLAC", "Fuente pública de grupos, integrantes y productos.",
              "GET HTTPS de `visualizagr.jsp?nro=` y `generarCurriculoCv.do?cod_rh=`; HTML analizado con BeautifulSoup/lxml (Python) y "
              "un analizador propio (C++); pausa de 1 s, 3 reintentos, `User-Agent` institucional."],
             ["Archivo local `pea-catalogo` v1", "Persistencia sin red y trabajo sin datos.",
              "JSON UTF-8 con grupos, investigadores, integrantes, productos y relaciones; guardado atómico; sin claves."],
             ["CSV canónico", "Carga por lotes de grupos, investigadores, productos y autorías.",
              "Valores separados por comas con alias de columnas; informe de filas rechazadas."],
             ["PDF", "Extracción de texto y tablas.", "Python: pdfplumber (páginas y celdas); C++: Poppler `pdftotext` (texto alineado y SHA-256)."],
             ["Referencia de máximos (JSON)", "Normalización externa del indicador.",
              "Objeto con `fuente`, `corte`, `desde` y los nueve máximos."],
             ["Bibliotecas", "Interfaz y utilidades.", "PySide6 (Qt 6), Pydantic, requests; Qt 6 Core/Network, OpenSSL, FTXUI 5.0.0, doctest."]],
            [3.5, 4.0, 6.0], tam=7.5, leyenda="Interfaces de software", nivel=3)
    c.h3("Interfaces de comunicación")
    c.p("Toda comunicación remota usa HTTPS/TLS (puerto 443) con JSON. Las lecturas se paginan por rangos (máximo 1000 filas por "
        "petición); las mutaciones compuestas usan RPC transaccionales que reciben la `revision_esperada`. Un conflicto devuelve "
        "error y las aplicaciones muestran «La base de datos cambió». C++ consulta la revisión cada 30 segundos. No se usa el puerto 5432.", 3)

    c.h2("Requisitos funcionales")
    c.p("Cada requisito se identifica con la tabla de la plantilla. Los criterios de aceptación se verifican con las pruebas "
        "automáticas indicadas en el apéndice F.")

    def rf(num, nombre, fuente, desc, ent=None, sal=None, val=None, prioridad="Alta", tipo="Requisito"):
        c.h3(f"RF-{num:02d} {nombre}")
        c.requisito(f"RF-{num:02d}", nombre, fuente, prioridad, tipo)
        c.p(desc, 3)
        if ent:
            c.p("**Entradas:** " + ent, 3)
        if sal:
            c.p("**Salidas:** " + sal, 3)
        if val:
            c.p("**Validaciones y situaciones anormales:** " + val, 3)

    rf(1, "Selección de la fuente de datos al iniciar", "Notas 9 y 10; SPEC RF-01/CU-01",
       "Al abrir cualquiera de las aplicaciones el usuario elige entre **Supabase**, un **archivo local** o **iniciar sin datos**; "
       "existe además un catálogo de demostración en memoria. El usuario decide si carga los datos del archivo o ejecuta sin datos.",
       "Origen elegido; ruta del archivo `.json` o URL/clave en `config/pea.config.json`.",
       "Catálogo cargado en las estructuras, con el origen indicado en el pie (Datos de Supabase, Archivo local, Demostración).",
       "Si no hay red o falla la sesión se informa el error y se permite continuar con archivo local; el archivo se valida "
       "(referencias, duplicados, fechas) antes de reemplazar el catálogo.")
    rf(2, "Gestión de grupos de investigación", "Puntos 1, 3 y 9; SPEC RF-02; CU-03/04",
       "Permite crear, consultar, filtrar, modificar, desactivar y eliminar grupos con código GrupLAC, nombre, fecha de formación, "
       "institución, gran área y área OCDE, categoría (A1, A, B, C, Reconocido) y estado. Los grupos se guardan en una lista doble.",
       "Campos del grupo (apéndice A.1).", "Grupo en la lista, ficha con integrantes y estadísticas, registro persistido.",
       "No se admiten códigos GrupLAC duplicados ni vacíos; el borrado lógico conserva el grupo y sus vínculos.")
    rf(3, "Gestión de investigadores", "Puntos 1, 4 y 9; SPEC RF-03",
       "Permite crear, consultar, modificar, desactivar y eliminar investigadores con código RH, nombre, categoría Minciencias, "
       "nivel de formación, nacionalidad y sexo. Cada ficha muestra sus grupos y productos.",
       "Campos del investigador (apéndice A.2).", "Investigador en la lista doble y su perfil de producción.",
       "El código RH es único; eliminar a quien es el único líder activo de un grupo se bloquea con un mensaje.")
    rf(4, "Gestión de productos, categoría, validación y puntaje", "Puntos 2, 4, 9 y nota del PARCIAL; SPEC RF-04",
       "Gestiona productos por tipología mayor (GNC, DTI, ASC, FRH), subtipo, año, validación (Avalado, Con soporte, No avalado) y "
       "**categoría de calidad** del Modelo 2024 (169 categorías). El puntaje de un producto es `peso_base × peso_relativo` "
       "(p. ej. ART_A2 = 100 × 5,5 = 550).",
       "Datos del producto y categoría (apéndice A.3 y B).", "Producto con su peso relativo y puntaje; ficha y catálogo.",
       "El año debe ser un entero entre 1970 y el año actual; una categoría que contradice la tipología se rechaza.")
    rf(5, "Vinculación de integrantes y autores (multilista)", "Puntos 3, 4 y 8; SPEC RF-05",
       "Cada producto es **un único nodo** de la multilista, referenciado por la lista de productos del grupo y por la de cada autor. "
       "Los integrantes de un grupo guardan rol (Líder, Investigador, Estudiante) y fechas de vinculación.",
       "Código del producto, grupo, autores, integrantes con fechas.", "Navegación grupo ↔ producto ↔ investigador sin duplicar datos.",
       "Modificar un atributo del producto se refleja en todas las vistas; al eliminar se desenlaza de todas las listas sin punteros colgantes.")
    rf(6, "Activar, desactivar y eliminar con cascada", "Punto 9; SPEC RNF-06; CU-03/04",
       "**Desactivar** asigna `activo = false` (la entidad permanece y puede reactivarse; el hipercubo la excluye). **Eliminar** "
       "la retira de las estructuras y de la base de datos aplicando reglas en cascada con confirmación previa.",
       "Entidad y acción elegidas.", "Estado actualizado y vistas refrescadas.",
       "Se describe la cascada antes de confirmar; si Supabase rechaza el cambio, la memoria se revierte.")
    rf(7, "Edición de cualquier dato", "Punto 11; SPEC RF-02/03/04",
       "Todos los atributos de las tres entidades son modificables, incluidos los campos adicionales mediante un diálogo (Python) "
       "o un objeto JSON (C++, tecla `a`). Los códigos que enlazan entidades conservan su identidad.",
       "Entidad y campos a cambiar.", "Entidad actualizada, deshacer disponible y persistencia en el origen activo.",
       "Se validan tipos y rangos; la edición en modo local exige guardar el archivo para conservarla.")
    rf(8, "Deshacer con pila", "SPEC RF-07; CU-03",
       "Cada mutación apila un comando inverso en una **pila LIFO** propia; «Deshacer» (botón en la GUI, tecla `u` en la TUI) lo "
       "aplica en memoria y lo sincroniza con el origen.",
       "Acción Deshacer.", "Estado anterior restaurado.",
       "Con la pila vacía la acción está deshabilitada; si el servidor rechaza la reversión por conflicto, la memoria no cambia.")
    rf(9, "Importación desde URL de SCIENTI", "Punto 7 y Parte 1/2 del PARCIAL; SPEC RF-13; CU-06",
       "Descarga una URL de GrupLAC o CvLAC y crea grupo, integrantes, investigadores y productos. Los CvLAC enlazados en un "
       "GrupLAC se encolan y se procesan. Se respeta una pausa de 1 s, hasta 3 reintentos y un `User-Agent` institucional; "
       "las respuestas pueden guardarse en caché.",
       "URL HTTPS del dominio `scienti.minciencias.gov.co`.", "Entidades en memoria (y en Supabase si procede) e informe de la importación.",
       "Si la fuente responde 404/500 tras los reintentos o la estructura cambió, se informa sin inventar datos y se sugiere el CSV; "
       "las redirecciones se validan.")
    rf(10, "Importación desde CSV", "Punto 7; SPEC RF-13",
       "Carga grupos, investigadores, productos y autorías desde CSV canónico con alias de columnas, tolerante a filas inválidas.",
       "Archivo CSV y tipo (auto, grupos, investigadores, productos, autores).", "Entidades creadas e informe con filas rechazadas y su motivo.",
       "Validación de esquema con Pydantic (Python) y analizadores equivalentes (C++); duplicados e invalidos se rechazan por fila.")
    rf(11, "Procesamiento de PDF", "Punto 7",
       "Extrae texto por páginas y tablas de un PDF. Python usa pdfplumber (celdas); C++ usa Poppler `pdftotext` (texto alineado, "
       "huella SHA-256 y avisos de páginas sin texto). Procesar un documento no registra entidades automáticamente.",
       "Ruta del PDF y de salida JSON.", "JSON con páginas, tablas o texto y advertencias.",
       "Un PDF escaneado requiere OCR previo; no se simula una extracción.")
    rf(12, "Cola FIFO de importación", "SPEC RF-08; CU-06",
       "Las tareas de importación (URL, CSV, PDF) se encolan en una **cola FIFO** propia con estados Pendiente, Procesando, "
       "Terminada y Con error.",
       "Tareas encoladas.", "Informe por tarea.",
       "Un error en una tarea se registra y la cola continúa con la siguiente.")
    rf(13, "Filtro por años", "Punto 10; SPEC RF-11",
       "Todas las vistas aceptan un filtro: todos los años, **últimos N años**, rango, o ventana del Modelo 2024. En los indicadores "
       "se añaden el año de corte y un límite inicial opcional.",
       "Modo y años elegidos.", "Tablas, gráficos, resumen e indicadores restringidos al periodo.",
       "Los rangos invertidos o fuera de 1970–2100 se rechazan.")
    rf(14, "Estadísticas descriptivas: resumen (C++) y dashboard (Python)", "Punto 12; SPEC RF-09/10/11; CU-05",
       "Todas las cifras salen del **hipercubo 5D** en memoria mediante rebanada, subcubo y enrollado. En C++ se presentan como "
       "resumen de datos (tablas y totales; comando `resumen`); en Python como **dashboard** con fichas, histogramas (distribución "
       "de productos por investigador y por año) y diagramas de barras apiladas por tipología y validación.",
       "Ámbito (institución o grupo) y filtro de años.", "Fichas, histogramas, barras, rankings y tablas.",
       "Con datos vacíos se muestran estados vacíos claros; los resultados coinciden con la verificación SQL de las pruebas.")
    rf(15, "Análisis de redes de coautoría", "SPEC RF-11",
       "Muestra un grafo de investigadores con coautorías y un ranking de centralidad; si no hay enlaces en el ámbito se explica que "
       "no hay colaboraciones en lugar de presentar nodos aislados.",
       "Filtros de grupo y años.", "Grafo interactivo y métricas.", "Se informa cuántos investigadores no tienen enlaces.", "Media")
    rf(16, "Puntaje por producto", "Nota de la Parte 1 del PARCIAL (peso relativo por categoría)",
       "Asigna a cada producto la categoría, el peso relativo y el puntaje a partir del catálogo `modelo_2024.json` (169 categorías "
       "extraídas del Modelo original: clases, pesos base y relativos, ventanas y página de origen).",
       "Producto con su categoría.", "Peso relativo, puntaje y clase de indicador.",
       "Sin categoría verificable el producto se enumera como excluido y se indica el motivo.")
    rf(17, "Indicador de producción científica del grupo", "PARCIAL 1; Modelo 2024 secciones 3.5–3.10",
       "Calcula `Ind.Grupo = 3,7·Nc.Top + 2,3·Nc.A + 0,4·Nc.B + 1,5·AP + 0,5·DPC + 1·Fr.A + 0,2·Fr.B + 0,1·Cohe + 0,3·Coop`. Para cada "
       "subtipo: `λ = ln(1 + n/periodo)` y `bruto de clase = Σ λ × peso_base × peso_relativo`; cada índice es `bruto / máximo` de la "
       "población de referencia. Cohe y Coop provienen de autores internos y grupos relacionados por producto GNC/DTI. Se aplican las "
       "ventanas de la Tabla 5 (5, 7 o 10 años), la edad del grupo y el año de corte.",
       "Grupo (código o URL GrupLAC), corte, límite inicial, referencia opcional.",
       "Indicador, tabla de nueve componentes (bruto, máximo, índice, coeficiente, aporte), productos incluidos, exclusiones y avisos; JSON.",
       "Máximos negativos, no finitos, incompletos o menores al observado se rechazan; si todo es cero el aporte es cero; el resultado se "
       "marca «parcial» si hay exclusiones o datos de colaboración incompletos.")
    rf(18, "Indicador de producción científica del investigador", "PARCIAL 2",
       "Aplica la misma fórmula a los productos del investigador (adaptación académica explícita: la cohesión usa todos sus coautores). "
       "Acepta el código RH o la URL del CvLAC.",
       "Investigador (código RH o URL CvLAC), corte, límite inicial, referencia opcional.", "Igual que RF-17.",
       "Igual que RF-17; la población de referencia son los investigadores del catálogo.")
    rf(19, "Estimación declarada de categorías faltantes", "PARCIAL 1–2 (calcular con datos públicos)",
       "SCIENTI no publica el cuartil ni el nivel de calidad. Con la opción «Estimar categorías faltantes» (GUI), el campo "
       "`Estimar… (si/no)` (TUI) o `--estimar-categorias` (CLI), cada producto sin categoría recibe la de **menor peso de su "
       "tipología**: artículo → ART_D, libro → LIB_C, capítulo → CAP_LIB_C, software → SF y trabajo dirigido → TD_B, TM_B o TP_B según "
       "el texto. Los productos con categoría informada no se tocan y el resultado se marca estimado e incompleto.",
       "Opción de estimar.", "Lista `estimadas` con el código y la regla; aviso en el desglose.",
       "No se estiman proyectos ni trabajos en curso; la estimación no modifica el catálogo original.", "Alta")
    rf(20, "Referencia de normalización", "PARCIAL; Modelo 2024 sección 3.6",
       "Por defecto los máximos son los de los grupos activos del catálogo de la misma gran área OCDE (o los investigadores del catálogo); "
       "puede cargarse un JSON con fuente, corte, desde y los nueve máximos para una población más amplia.",
       "Archivo JSON de referencia opcional.", "Máximos usados y su procedencia.",
       "La referencia debe coincidir con el corte y el límite inicial elegidos; el resultado no es una clasificación nacional oficial.",
       "Media")
    rf(21, "Archivos locales de persistencia", "Notas 9 y 10",
       "Guarda y abre el catálogo en un archivo JSON `pea-catalogo` v1 (grupos, investigadores, integrantes, productos y relaciones), "
       "interoperable entre Python y C++, con guardado atómico y sin claves ni variables de entorno.",
       "Ruta del archivo.", "Catálogo guardado o restaurado con listas y nodos compartidos reconstruidos.",
       "Se validan referencias, duplicados y fechas de vinculación (se aceptan AAAA, AAAA-MM, AAAA/M y «Actual»).")
    rf(22, "Exportación de resultados", "SPEC RF-11",
       "Exporta tablas a CSV, gráficos a PNG y el desglose del indicador a JSON; la CLI `exportar-csv` genera los CSV del catálogo.",
       "Destino elegido.", "Archivos CSV, PNG o JSON.", "Se validan rutas y permisos de escritura.", "Media")
    rf(23, "Control de revisión y concurrencia", "SPEC RF-01/RF-12; CU-07",
       "Antes de cada mutación se compara `meta.revision` remota con la local; las mutaciones compuestas usan RPC transaccionales con "
       "`revision_esperada`. Si cambió, se bloquea la escritura, se muestra «La base de datos cambió» y se ofrece recargar. La "
       "persistencia es atómica: si falla, la memoria se revierte.",
       "Mutación solicitada.", "Escritura confirmada con revisión + 1, o error sin cambios.",
       "Los errores 4xx/5xx o de red muestran el motivo y conservan el formulario abierto.")

    c.h2("Requisitos no funcionales")
    c.h3("Requisitos de rendimiento")
    c.vinetas(["RNF-01. El cálculo estadístico en memoria para hasta 10 000 productos debe tardar menos de 50 ms (criterio de diseño del hipercubo).",
               "RNF-02. Las tablas de Python muestran 50 filas por página y las de C++ 12, con consultas remotas paginadas por rangos.",
               "RNF-03. Importar una URL respeta 1 s entre peticiones; el cálculo del indicador se hace en memoria, sin red, una vez cargado el catálogo.",
               "RNF-04. Una instancia por usuario; la base soporta lecturas concurrentes y detecta escrituras en conflicto."], 3)
    c.h3("Seguridad")
    c.vinetas(["RNF-05. Solo HTTPS/TLS; los clientes usan la clave **publicable**; `service_role` y `sb_secret_…` están prohibidos y "
               "se buscan en cada verificación (0 hallazgos en 533 archivos).",
               "RNF-06. Los tokens de sesión solo viven en memoria; RLS permanece activo.",
               "RNF-07. Por decisión expresa del propietario (ADR-0025) el acceso académico permite leer y modificar los datos "
               "compartidos sin identificar al profesor: quien obtenga el paquete tiene los mismos permisos; no es apto para información privada.",
               "RNF-08. Los archivos locales no contienen claves; las redirecciones HTTP se validan; las operaciones destructivas piden confirmación."], 3)
    c.h3("Fiabilidad")
    c.vinetas(["RNF-09. Persistencia atómica con compensación: ante un fallo la memoria queda en su estado previo.",
               "RNF-10. Pruebas automáticas: 419 de Python y 75 casos (1 249 aserciones) de C++ sin fallos; 27 combinaciones de GUI y 36 de TUI sin hallazgos.",
               "RNF-11. Verificación cruzada Python/C++: mismos resultados con tolerancia de 1e-11 en los escenarios del parcial."], 3)
    c.h3("Disponibilidad")
    c.p("La disponibilidad depende de Supabase y de SCIENTI; un flujo programado consulta la disponibilidad cada tres días sin "
        "modificar datos. Sin red, ambas aplicaciones operan con archivos locales o sin datos (RNF-12).", 3)
    c.h3("Mantenibilidad")
    c.vinetas(["RNF-13. Arquitectura por capas con servicios, repositorios y estructuras desacoplados; 27 ADR documentan las decisiones.",
               "RNF-14. Calidad automática: Ruff, Vulture y compilación C++17 con advertencias tratadas como errores; documentación verificada por `verificar_brain.py`.",
               "RNF-15. Mantenimiento por los desarrolladores: ejecutar `scripts/verificar.ps1` antes de cada entrega y regenerar el paquete con `empaquetar.ps1`."], 3)
    c.h3("Portabilidad")
    c.vinetas(["RNF-16. Paquete portable `PEAi-Windows-x64.zip` con Python, PySide6, Qt, OpenSSL, MinGW y Poppler; sin instalar nada.",
               "RNF-17. Compilación desde código con CPython 3.12 y MSYS2 UCRT64; instaladores mediante `preparar.ps1` y CI en GitHub Actions.",
               "RNF-18. Interfaz, mensajes y documentación en español con UTF-8."], 3)
    c.h2("Otros requisitos")
    c.p("**Legales y académicos.** El Modelo y los datos de SCIENTI son públicos de Minciencias; las dependencias conservan sus "
        "licencias (se incluyen en el paquete). Los datos personales importados se tratan como públicos de SCIENTI y existe la opción "
        "de anonimizar en la importación. **Identidad institucional:** logo, nombre y colores de la UPC en el pie de la GUI.", 2)

    # ------------------------------------------------------------------ 4
    c.h1("Apéndices")
    c.h2("Apéndice A. Diccionario de datos")
    c.p("Variables de entrada y salida del modelo (Parcial punto 6), tanto de la estructura de grupos como de investigadores.", 1)
    c.tabla([["Campo", "Tipo", "E/S", "Descripción"],
             ["codigo_gruplac", "Texto, único", "E/S", "Código GrupLAC (p. ej. 00000000002099)."],
             ["nombre, lider, institucion_principal", "Texto", "E/S", "Nombre, líder e institución avaladora."],
             ["fecha_creacion", "AAAA-MM-DD", "E/S", "Fecha de formación; determina la edad del grupo."],
             ["gran_area_ocde, area_ocde", "Texto", "E/S", "Clasificación OCDE; define la población de referencia."],
             ["categoria", "A1, A, B, C, Reconocido", "E/S", "Categoría Minciencias del grupo."],
             ["activo", "Booleano", "E/S", "Borrado lógico."]], [3.9, 3.3, 1.2, 5.1], leyenda="A.1 Grupo", tam=7.5)
    c.tabla([["Campo", "Tipo", "E/S", "Descripción"],
             ["codigo_rh", "Texto, único", "E/S", "Código CvLAC (p. ej. 0000494917)."],
             ["nombre_completo, nombre_en_citas", "Texto", "E/S", "Nombre y variante bibliográfica."],
             ["categoria", "Enumeración", "E/S", "Emérito, Senior, Asociado, Junior o Sin categoría."],
             ["formacion_academica, nacionalidad, sexo", "Texto", "E/S", "Datos personales públicos de SCIENTI."],
             ["activo", "Booleano", "E/S", "Borrado lógico."],
             ["Integrante: rol, fecha_inicio, fecha_fin", "Líder / Investigador / Estudiante; fechas", "E/S",
              "Vinculación al grupo; «Actual» indica vigencia."]], [3.9, 3.3, 1.2, 5.1], leyenda="A.2 Investigador e integrante", tam=7.5)
    c.tabla([["Campo", "Tipo", "E/S", "Descripción"],
             ["codigo_identificador", "Texto, único", "E/S", "Clave del producto y del nodo único de la multilista."],
             ["titulo, subtipo, pais", "Texto", "E/S", "Datos bibliográficos."],
             ["tipo_mayor", "GNC, DTI, ASC, FRH", "E/S", "Tipología mayor (dimensión del hipercubo)."],
             ["ano, mes", "Entero 1970–año actual; 1–12", "E/S", "Fecha de obtención (dimensión del hipercubo)."],
             ["estado_validacion", "Avalado, Con soporte, No avalado", "E/S", "Validación institucional."],
             ["detalles.categoria_minciencias", "Código del Modelo", "E/S", "Categoría de calidad que define el peso relativo."],
             ["peso_relativo, puntaje", "Decimal", "S", "Calculados: peso_base × peso_relativo."],
             ["activo", "Booleano", "E/S", "Borrado lógico; excluido del hipercubo si es falso."]],
            [3.9, 3.3, 1.2, 5.1], leyenda="A.3 Producto", tam=7.5)
    c.tabla([["Salida", "Origen", "Descripción"],
             ["Totales, series por año, categoría y validación", "Hipercubo (rebanada, subcubo, enrollado)", "Estadísticas descriptivas y rankings."],
             ["Histogramas", "Servicio de estadísticas", "Productos por investigador y por año."],
             ["Indicador y nueve componentes", "Módulo de indicadores", "Bruto, máximo, índice, coeficiente y aporte."],
             ["Exclusiones, estimaciones y avisos", "Módulo de indicadores", "Trazabilidad del cálculo."]],
            [4.5, 4.5, 4.5], leyenda="A.4 Salidas del modelo", tam=7.5)
    c.h2("Apéndice B. Diseño de las estructuras de datos")
    c.p("Para la estructura de **listas** solicitada en el punto 8 se adoptó una combinación de estructuras enlazadas hechas a mano, "
        "cada una elegida por su patrón de acceso:", 1)
    c.tabla([["Estructura", "Contiene", "Operaciones y complejidad"],
             ["Lista doblemente enlazada", "Grupos, investigadores e integrantes", "Insertar al inicio/final O(1); eliminar un nodo conocido O(1); buscar O(n)."],
             ["Multilista", "Productos compartidos entre grupo y autores", "Navegar grupo ↔ producto ↔ investigador; un nodo por producto; eliminar sin punteros colgantes."],
             ["Pila (LIFO)", "Comandos inversos", "apilar, desapilar, tope en O(1)."],
             ["Cola (FIFO)", "Tareas de importación", "encolar, desencolar, frente en O(1)."],
             ["Hipercubo 5D disperso", "Productos activos por (grupo, investigador, categoría, año, validación)", "rebanada, subcubo, enrollado; base de las estadísticas."]],
            [3.4, 4.6, 5.5], leyenda="Estructuras de datos del sistema", tam=7.5)
    c.figura("estructura_01_multilista.png", "Multilista: un nodo por producto compartido entre su grupo y sus autores.", 12.5, 1)
    c.figura("estructura_02_hipercubo.png", "Hipercubo disperso de cinco dimensiones y sus operaciones.", 12.5, 1)
    c.figura("uml_08_clases_dominio.png", "Diagrama de clases del dominio y las estructuras propias.", 13, 1, alto_max_cm=19)
    c.figura("uml_09_clases_servicios.png", "Diagrama de clases de servicios, ingesta y persistencia.", 13, 1, alto_max_cm=19)
    c.figura("uml_12_entidad_relacion.png", "Modelo entidad-relación de la base de datos compartida.", 13, 1, alto_max_cm=19)
    c.h2("Apéndice C. Estrategia de solución del indicador")
    c.figura("uml_13_actividad_indicador.png", "Diagrama de actividades del cálculo del indicador.", 11, 1, alto_max_cm=19)
    c.p("**Ejemplo numérico (catálogo `datos/ejemplo-parcial.json`, grupo PRUEBA-G1, corte 2023).** Dos artículos ART_A2 "
        "(550 puntos cada uno) con ventana de 7 años: λ = ln(1 + 2/7) = 0,251314, bruto Nc.Top = 550 × 0,251314 = 138,222. Un software SF "
        "(35 × 8 = 280) con ventana de 5 años: λ = ln(1 + 1/5) = 0,182322, bruto Nc.B = 280 × 0,182322 = 51,050. Cohe = Coop = 1/3. "
        "Al ser el único grupo, cada máximo es su bruto y los índices valen 1; el indicador es 3,7 + 0,4 + 0,1 + 0,3 = **4,5**. Los "
        "dos productos restantes se excluyen: uno sin categoría y otro no avalado.", 1)
    c.p("**Resultado con las URL del enunciado** (descarga real de SCIENTI, corte 2023, ambas aplicaciones con resultado equivalente):", 1)
    filas = [["Caso", "Modo", "Indicador", "Incluidos", "Excluidos", "Estimados", "Python = C++"]]
    nombres = {"grupo": "Grupo GISICO (GrupLAC 00000000002099)", "investigador": "Investigador (CvLAC 0000494917)"}
    for clave, datos in r.items():
        ambito, modo = clave.split("_")
        py = datos["python"]
        filas.append([nombres[ambito], "Estimado" if modo == "estimado" else "Estricto", f(py["indicador"]), str(py["incluidos"]),
                      str(py["excluidos"]), str(py["estimadas"]), "Sí" if datos["equivalentes"] else "No"])
    c.tabla(filas, [4.6, 1.8, 1.9, 1.4, 1.4, 1.4, 1.6], leyenda="Indicadores obtenidos con las URL del Parcial 2", tam=7.5, nivel=1)
    g = r["grupo_estimado"]["python"]["brutos"]
    c.p("Interpretación: en **modo estricto** el resultado es 0 porque la fuente pública no informa el cuartil ni el nivel de calidad "
        "de ningún producto y el Modelo exige esa categoría. En **modo estimado** los productos se puntúan con la categoría base de su "
        f"tipología: el grupo acumula un bruto Nc.B de {f(g['Nc.B'])} y, al ser el único grupo del catálogo descargado, su índice es 1 "
        "(aporte 0,4). Los valores son una **estimación declarada**, no una clasificación oficial: con las categorías reales del "
        "Modelo (asignables producto por producto en la pantalla Indicadores) o con una referencia de máximos externa el valor cambia. "
        "Para el investigador se aplica la misma fórmula sobre sus productos.", 1)
    c.h2("Apéndice D. Diagramas de secuencia")
    for archivo, texto in [
        ("uml_03_secuencia_crear_producto.png", "Registro de un producto con persistencia atómica y compensación."),
        ("uml_04_secuencia_indicador_url.png", "Cálculo del indicador de un grupo desde su URL de GrupLAC."),
        ("uml_05_secuencia_importacion_cola.png", "Importación por lotes con la cola FIFO."),
        ("uml_06_secuencia_deshacer_conflicto.png", "Deshacer y conflicto de revisión."),
        ("uml_07_secuencia_estadisticas.png", "Consulta estadística desde el hipercubo."),
    ]:
        c.figura(archivo, texto, 14.5, 1, alto_max_cm=20)
    c.h2("Apéndice E. Trazabilidad con el enunciado del Parcial 2")
    c.tabla([["Requisito del enunciado", "Requisitos", "Implementación y comprobación"],
             ["Dos programas en C/C++ y Python", "RNF-16, RF-01", "GUI/CLI Python y TUI/CLI C++; comparación de procesos en `tools/interop/verificar_parcial.py`."],
             ["1. Gestionar grupos e investigadores", "RF-02, RF-03", "`CatalogoInvestigacion`, listas dobles; `tests/unit/test_servicios_nuevos.py`."],
             ["2, 4. Productos y puntaje por grupo e investigador", "RF-04, RF-05, RF-16", "Multilista; catálogo de 169 categorías; `test_indicadores_parcial.py`."],
             ["3. Profesores y productos de cada grupo", "RF-05", "Integrantes con rol y fechas; ficha de grupo."],
             ["5, 6. Modelo, variables de entrada y salida", "Apéndice A", "Diccionario de datos y catálogo reproducible `generar_catalogo_puntajes.py`."],
             ["7. URL, PDF o CSV", "RF-09, RF-10, RF-11", "`extractor_url`, `lector_csv`, `extractor_pdf`; pruebas de ingesta."],
             ["8. Estructura de listas", "Apéndice B", "Lista doble, multilista, pila, cola e hipercubo propios."],
             ["9, 11. CRUD, categoría, validación, edición total", "RF-02 a RF-07", "Servicios de dominio; pruebas de cascadas y deshacer."],
             ["10. Filtro por años", "RF-13", "`FiltroAnios` y ventana del Modelo; pruebas de hipercubo."],
             ["12.a Resumen de datos en C", "RF-14", "Comando `resumen` y TUI en C++."],
             ["12.b Dashboard con histogramas y barras en Python", "RF-14, RF-15", "Pantalla Inicio; `test_graficos_seccion9.py`."],
             ["PARCIAL 1. Indicador del grupo", "RF-17, RF-19, RF-20", "`calcular_indicador` en Python y C++; evidencia [R13]."],
             ["PARCIAL 2. Indicador del investigador", "RF-18, RF-19", "Ídem con el código RH."],
             ["Nota 1. Entregar los dos archivos de código", "Apéndice G", "`Parcial2_FF_SM.py` y `Parcial2_FF_SM.cpp`."],
             ["Nota 2. Word con UML de casos de uso y secuencia", "Este documento", "Casos de uso (Figuras 3 a 5) y secuencia (Figuras 25 a 29, apéndice D)."],
             ["Nota 4. Identificación de estudiantes", "—", "`entrega/integrantes.txt`."],
             ["Nota 8. Archivos con iniciales", "—", "Sufijo `FF_SM`."],
             ["Notas 9 y 10. Persistencia y elegir datos o no", "RF-01, RF-21", "Archivo JSON `datos/ejemplo-parcial.json` e inicio sin datos."]],
            [4.6, 2.5, 6.4], leyenda="Trazabilidad enunciado → requisitos → comprobación", tam=7.5, nivel=1)
    c.p("Las notas 3 (video) y 5–7 (envío por correo y plazos) son acciones de entrega externas y no forman parte de este documento.", 1,
        cursiva=True, tam=9)
    c.h2("Apéndice F. Evidencia de verificación")
    c.tabla([["Comprobación", "Resultado"],
             ["Pruebas Python (`pytest`)", "419 aprobadas; 3 de red excluidas por defecto."],
             ["Pruebas C++ (`CTest`, doctest)", "75 casos y 1 249 aserciones aprobados."],
             ["GUI Python (autoprueba)", "9 pantallas × 3 resoluciones = 27 combinaciones, 0 hallazgos."],
             ["TUI C++ (autoprueba)", "9 pantallas × 4 tamaños = 36 combinaciones, 0 hallazgos."],
             ["Paridad Python/C++ (CLI)", "Escenarios del parcial con JSON equivalente (tolerancia 1e-11)."],
             ["URL del parcial", "Resultados idénticos en ambos lenguajes (Apéndice C)."],
             ["Búsqueda de secretos", "0 hallazgos en los archivos versionables."]],
            [5.5, 8.0], leyenda="Resumen de la verificación (25/10/2026)", tam=8, nivel=1)
    c.h2("Apéndice G. Archivos de la entrega y ejecución")
    c.tabla([["Archivo o carpeta", "Contenido"],
             ["`entrega/Parcial2_FF_SM.py` / `.cpp`", "Entradas académicas de los dos programas (sobre el proyecto modular completo)."],
             ["`entrega/Taller2_FF_SM.py` / `.cpp`", "Entradas del Taller 2."],
             ["`entrega/Especificacion_Tecnica_PEAi.docx`", "Este documento."],
             ["`entrega/integrantes.txt`", "Identificación de los estudiantes."],
             ["`datos/ejemplo-parcial.json`", "Archivo de persistencia de ejemplo (catálogo sintético)."],
             ["`src/pea`, `cpp`", "Código Python y C++."],
             ["`tests`, `cpp/tests`", "Pruebas automáticas."],
             ["Release `PEAi-Windows-x64.zip`", "Paquete portable con ambos ejecutables y `SHA256SUMS.txt`."]],
            [5.5, 8.0], leyenda="Contenido de la entrega", tam=8, nivel=1)
    c.p("**Ejecución rápida.** Extraer el ZIP, abrir `Iniciar-Python.cmd` o `Iniciar-Cpp.cmd`, elegir el origen de datos y abrir la pantalla "
        "Indicadores. Desde la línea de comandos:", 1)
    c.codigo("""
pea-cli.exe indicador --ambito grupo --url "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099" --corte 2023 --estimar-categorias
pea-cpp.exe indicador --ambito investigador --url "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917" --corte 2023 --estimar-categorias
pea-cpp.exe indicador --archivo datos/ejemplo-parcial.json --ambito grupo --codigo PRUEBA-G1 --corte 2023
""", 1)


def postprocesar(ruta: Path) -> None:
    """Sustituye los logotipos de la plantilla por el de la UPC y ajusta sus marcos."""
    tmp = ruta.with_suffix(".tmp")
    with zipfile.ZipFile(ruta) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            datos = zin.read(item.filename)
            if item.filename == "word/media/image2.png":
                datos = LOGO.read_bytes()
            elif item.filename.startswith("word/_rels/") and item.filename.endswith(".rels"):
                datos = datos.replace(b"media/image1.emf", b"media/image2.png")
            elif item.filename in {"word/document.xml"} or re.fullmatch(r"word/header\d\.xml", item.filename):
                texto = datos.decode("utf-8")
                texto = re.sub(r'(<v:shape [^>]*style=")width:[\d.]+pt;height:[\d.]+pt', r"\1width:34pt;height:34pt", texto)
                datos = texto.encode("utf-8")
            zout.writestr(item, datos)
    shutil.move(tmp, ruta)


def main() -> int:
    ev = cargar_evidencia()
    doc = preparar_plantilla()
    c = Constructor(doc)
    redactar(c, ev)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    doc.core_properties.title = "Especificación de requisitos de software · PEA-i"
    doc.core_properties.author = "Grupo 8 · Franier Fernandez y Santiago Moreno"
    doc.core_properties.subject = "Parcial 2 · Estructura de Datos · UPC"
    doc.save(str(SALIDA))
    postprocesar(SALIDA)
    print("Generado", SALIDA, f"({c.n_fig} figuras, {c.n_tab} tablas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
