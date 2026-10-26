"""Genera los diagramas UML y de estructuras de la especificación técnica.

Cada diagrama se dibuja con matplotlib (sin Java ni Graphviz) en ``docs/imagenes``.
Las unidades de los ejes son pulgadas, de modo que el tamaño de letra del PNG es el
que se verá en el documento Word (ancho útil aproximado: 6,3 pulgadas).

Uso (desde la raíz)::

    py -3 tools/diagramas_documento.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "imagenes"
AZUL = "#12355B"
VERDE = "#2E7D32"
VERDE_CLARO = "#E8F5E9"
AZUL_CLARO = "#E3EDF7"
AMARILLO = "#FFF8DC"
GRIS = "#5F6B7A"
GRIS_CLARO = "#F2F4F7"
NARANJA = "#C75B12"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.unicode_minus": False})


class Lienzo:
    """Figura cuyos ejes miden pulgadas."""

    def __init__(self, ancho: float, alto: float) -> None:
        self.ancho, self.alto = ancho, alto
        self.fig = plt.figure(figsize=(ancho, alto), dpi=220)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, ancho)
        self.ax.set_ylim(0, alto)
        self.ax.axis("off")
        self._r = self.fig.canvas.get_renderer()

    def medir(self, texto: str, tam: float = 8, peso: str = "normal") -> float:
        t = self.ax.text(0, 0, texto, fontsize=tam, fontweight=peso)
        ancho = t.get_window_extent(self._r).width / self.fig.dpi
        t.remove()
        return ancho

    def ajustar(self, texto: str, ancho_max: float, tam: float = 8, peso: str = "normal") -> str:
        lineas: list[str] = []
        for parrafo in texto.split("\n"):
            actual = ""
            for palabra in parrafo.split(" "):
                prueba = (actual + " " + palabra).strip()
                if actual and self.medir(prueba, tam, peso) > ancho_max:
                    lineas.append(actual)
                    actual = palabra
                else:
                    actual = prueba
            lineas.append(actual)
        return "\n".join(lineas)

    def guardar(self, nombre: str) -> None:
        DESTINO.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(DESTINO / f"{nombre}.png", facecolor="white", bbox_inches="tight", pad_inches=0.12)
        plt.close(self.fig)

    # --- primitivas -------------------------------------------------------
    def caja(self, x, y, w, h, texto="", fondo=AZUL_CLARO, borde=AZUL, tam=8, peso="normal", color="black",
             redondeo=0.05, estilo="-", z=2, ha="center"):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={redondeo}",
                                         fc=fondo, ec=borde, lw=1.0, ls=estilo, zorder=z))
        if texto:
            tx = x + w / 2 if ha == "center" else x + 0.07
            self.ax.text(tx, y + h / 2, texto, ha=ha, va="center", fontsize=tam, fontweight=peso,
                         color=color, zorder=z + 1, linespacing=1.15)
        return (x, y, w, h)

    def texto(self, x, y, s, tam=8, ha="center", va="center", peso="normal", color="black", z=5, **kw):
        return self.ax.text(x, y, s, ha=ha, va=va, fontsize=tam, fontweight=peso, color=color, zorder=z,
                            linespacing=1.15, **kw)

    def linea(self, p, q, color=GRIS, estilo="-", lw=1.0, z=1):
        self.ax.plot([p[0], q[0]], [p[1], q[1]], color=color, ls=estilo, lw=lw, zorder=z, solid_capstyle="butt")

    def flecha(self, p, q, color=GRIS, estilo="-", lw=1.0, cabeza="llena", z=3, tam=0.11):
        self.linea(p, q, color, estilo, lw, z)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        a = (q[0] - tam * math.cos(ang - 0.38), q[1] - tam * math.sin(ang - 0.38))
        b = (q[0] - tam * math.cos(ang + 0.38), q[1] - tam * math.sin(ang + 0.38))
        if cabeza == "llena":
            self.ax.add_patch(Polygon([q, a, b], closed=True, fc=color, ec=color, lw=0.6, zorder=z + 1))
        elif cabeza == "abierta":
            self.linea(q, a, color, "-", lw, z + 1)
            self.linea(q, b, color, "-", lw, z + 1)
        elif cabeza == "hueca":
            self.ax.add_patch(Polygon([q, a, b], closed=True, fc="white", ec=color, lw=1.0, zorder=z + 1))

    def rombo(self, p, q, color=GRIS, lleno=False, tam=0.13):
        """Rombo de agregación/composición en el extremo ``p`` de la línea p→q."""
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        c1 = (p[0] + tam * math.cos(ang), p[1] + tam * math.sin(ang))
        c2 = (p[0] + 2 * tam * math.cos(ang), p[1] + 2 * tam * math.sin(ang))
        lado = tam * 0.55
        n = (-math.sin(ang), math.cos(ang))
        pts = [p, (c1[0] + lado * n[0], c1[1] + lado * n[1]), c2, (c1[0] - lado * n[0], c1[1] - lado * n[1])]
        self.ax.add_patch(Polygon(pts, closed=True, fc=color if lleno else "white", ec=color, lw=1.0, zorder=4))
        return c2

    def titulo(self, s):
        self.texto(self.ancho / 2, self.alto - 0.17, s, tam=9.5, peso="bold", color=AZUL)

    def actor(self, x, y, nombre, escala=1.0, color=AZUL):
        r = 0.09 * escala
        self.ax.add_patch(Circle((x, y + 0.42 * escala), r, fc="white", ec=color, lw=1.2, zorder=3))
        self.linea((x, y + 0.42 * escala - r), (x, y + 0.14 * escala), color, lw=1.2, z=3)
        self.linea((x - 0.17 * escala, y + 0.30 * escala), (x + 0.17 * escala, y + 0.30 * escala), color, lw=1.2, z=3)
        self.linea((x, y + 0.14 * escala), (x - 0.14 * escala, y - 0.06 * escala), color, lw=1.2, z=3)
        self.linea((x, y + 0.14 * escala), (x + 0.14 * escala, y - 0.06 * escala), color, lw=1.2, z=3)
        self.texto(x, y - 0.2 * escala, nombre, tam=7.5, peso="bold", color=color)


# ---------------------------------------------------------------------------
# Casos de uso
# ---------------------------------------------------------------------------
def _borde_elipse(centro, ancho, alto, hacia):
    dx, dy = hacia[0] - centro[0], hacia[1] - centro[1]
    d = math.hypot(dx / (ancho / 2), dy / (alto / 2)) or 1
    return centro[0] + dx / d, centro[1] + dy / d


def _caso(lz: Lienzo, centro, etiqueta, ancho=1.75, alto=0.52, fondo="white", borde=VERDE, tam=7.2):
    lz.ax.add_patch(Ellipse(centro, ancho, alto, fc=fondo, ec=borde, lw=1.1, zorder=3))
    lz.texto(centro[0], centro[1], lz.ajustar(etiqueta, ancho * 0.84, tam), tam=tam, z=4)


def casos_uso_columna(nombre: str, titulo: str, sistema: str, casos: list[tuple[str, str]],
                      relaciones: list[tuple[str, str, str]], izquierda: list[tuple[str, list[str]]],
                      derecha: list[tuple[str, list[str], float | None]], nota: str = "") -> None:
    paso, ancho_e, alto_e = 0.84, 2.7, 0.5
    n = len(casos)
    alto = 1.2 + n * paso + (0.35 if nota else 0)
    lz = Lienzo(7.6, alto)
    lz.titulo(titulo)
    x0 = 3.8
    lz.ax.add_patch(Rectangle((x0 - 1.75, 0.2 + (0.35 if nota else 0)), 3.5, alto - 0.95 - (0.35 if nota else 0), fc="#FBFCFD",
                              ec=AZUL, lw=1.3, zorder=0))
    lz.texto(x0, alto - 0.55, sistema, tam=8, peso="bold", color=AZUL)
    centros = {}
    for k, (clave, _) in enumerate(casos):
        centros[clave] = (x0, alto - 1.05 - k * paso)
    medio = (alto - 1.05 + (alto - 1.05 - (n - 1) * paso)) / 2

    def enlazar(actor_xy, claves):
        for clave in claves:
            lz.linea((actor_xy[0] + (0.12 if actor_xy[0] < x0 else -0.12), actor_xy[1] + 0.3),
                     _borde_elipse(centros[clave], ancho_e, alto_e, actor_xy), GRIS, lw=0.85, z=1)

    for nombre_actor, claves in izquierda:
        xy = (0.6, medio)
        enlazar(xy, claves)
        lz.actor(xy[0], xy[1], nombre_actor)
    for nombre_actor, claves, y_actor in derecha:
        xy = (7.0, y_actor if y_actor is not None else medio)
        enlazar(xy, claves)
        lz.actor(xy[0], xy[1], nombre_actor)
    for clave, etiqueta in casos:
        c = centros[clave]
        lz.ax.add_patch(Ellipse(c, ancho_e, alto_e, fc="white", ec=VERDE, lw=1.1, zorder=3))
        lz.texto(c[0], c[1], lz.ajustar(etiqueta, ancho_e * 0.86, 7.4), tam=7.4, z=4)
    for a, b, tipo in relaciones:
        p1 = _borde_elipse(centros[a], ancho_e, alto_e, centros[b])
        q1 = _borde_elipse(centros[b], ancho_e, alto_e, centros[a])
        lz.flecha(p1, q1, VERDE, "--", 0.9, "abierta", z=2)
        lz.texto((p1[0] + q1[0]) / 2 + 0.42, (p1[1] + q1[1]) / 2, f"«{tipo}»", tam=6.5, color=VERDE, peso="bold", z=6)
    if nota:
        lz.texto(3.8, 0.28, nota, tam=6.8, color=GRIS)
    lz.guardar(nombre)


def diagrama_casos_uso_general() -> None:
    casos_uso_columna(
        "uml_01_casos_uso_gestion",
        "Casos de uso · Gestión de grupos, investigadores y productos",
        "Sistema PEA-i · gestión del catálogo",
        [("G", "Gestionar grupos de investigación"), ("I", "Gestionar investigadores"),
         ("P", "Gestionar productos y su categoría"), ("V", "Vincular integrantes y autores"),
         ("D", "Desactivar o eliminar con cascada"), ("U", "Deshacer la última operación"),
         ("R", "Resolver conflicto de revisión")],
        [("P", "V", "include"), ("D", "U", "extend")],
        [("Usuario /\nAnalista de\ninvestigación", ["G", "I", "P", "V", "D", "U", "R"])],
        [("Supabase\n(PostgreSQL)", ["G", "I", "P", "V", "D", "U", "R"], None)],
        "Toda mutación se confirma en Supabase antes de apilarse para deshacer.",
    )
    casos_uso_columna(
        "uml_02_casos_uso_analisis",
        "Casos de uso · Consulta, importación e indicadores",
        "Sistema PEA-i · análisis",
        [("F", "Filtrar por años (ventana de observación)"), ("E", "Consultar estadísticas y dashboard"),
         ("M", "Importar desde URL, CSV o PDF"), ("C", "Calcular indicador de grupo"),
         ("N", "Calcular indicador de investigador"), ("Q", "Estimar categorías faltantes"),
         ("A", "Guardar o abrir archivo local")],
        [("E", "F", "include"), ("C", "M", "include"), ("Q", "N", "extend")],
        [("Usuario /\nAnalista de\ninvestigación", ["F", "E", "M", "C", "N", "Q", "A"])],
        [("Portal SCIENTI\n(GrupLAC / CvLAC)", ["M"], None)],
        "Estimar categorías es opcional y también extiende el cálculo del grupo.",
    )


def diagrama_casos_uso_indicador() -> None:
    casos_uso_columna(
        "uml_03_casos_uso_indicador",
        "Casos de uso del Parcial 2 · Indicador de producción científica",
        "Módulo de indicadores",
        [("CG", "Calcular indicador del grupo (URL GrupLAC)"), ("CI", "Calcular indicador del investigador (URL CvLAC)"),
         ("DU", "Descargar y procesar URL, CSV o PDF"), ("AC", "Asignar categoría de calidad al producto"),
         ("ES", "Estimar categorías faltantes"), ("RF", "Cargar referencia de máximos"),
         ("EX", "Exportar desglose JSON")],
        [("CI", "DU", "include"), ("ES", "AC", "extend")],
        [("Usuario", ["CG", "CI", "AC", "ES", "RF", "EX"])],
        [("Portal SCIENTI", ["DU"], None)],
        "Los dos cálculos incluyen la descarga; «Calcular indicador del grupo» también la incluye.",
    )


# ---------------------------------------------------------------------------
# Secuencia
# ---------------------------------------------------------------------------
def secuencia(nombre: str, titulo: str, participantes: list[tuple[str, str]], pasos: list[tuple], ancho=7.6,
              paso_y=0.34) -> None:
    n = len(participantes)
    margen = 0.78
    xs = [margen + i * (ancho - 2 * margen) / (n - 1) for i in range(n)]
    pos = {clave: x for (clave, _), x in zip(participantes, xs, strict=True)}
    sep = xs[1] - xs[0]
    pre = Lienzo(ancho, 4)
    y = 0.0
    # primera pasada: altura necesaria
    alto = 1.55 + sum(
        (0.5 if p[0] in ("nota",) else 0.9 if p[0] in ("marco", "sino", "fin") else 1) * paso_y
        + (0.16 * (pre.ajustar(p[3], sep * 1.9, 7).count("\n")) if p[0] in ("llama", "ret") and p[1] != p[2] else 0)
        for p in pasos
    )
    plt.close(pre.fig)
    lz = Lienzo(ancho, alto)
    lz.titulo(titulo)
    top = alto - 0.55
    ancho_cab = min(1.35, sep - 0.08)
    for clave, etiqueta in participantes:
        lz.caja(pos[clave] - ancho_cab / 2, top - 0.42, ancho_cab, 0.5, lz.ajustar(etiqueta, ancho_cab - 0.1, 7.2, "bold"),
                fondo=AZUL_CLARO, borde=AZUL, tam=7.2, peso="bold")
    y = top - 0.65
    pila: list[tuple[str, float]] = []
    marcos: list[tuple[str, float]] = []
    barras: list[tuple[float, float, float]] = []
    fin_lifelines = 0.25
    for p in pasos:
        tipo = p[0]
        if tipo == "llama":
            _, a, b, texto = p
            if a == b:
                lz.texto(pos[a] + 0.22, y, lz.ajustar(texto, 1.6, 7), tam=7, ha="left", va="center")
                y -= 0.16 * texto.count("\n")
                lz.linea((pos[a], y + 0.1), (pos[a] + 0.2, y + 0.1), z=3)
                lz.linea((pos[a] + 0.2, y + 0.1), (pos[a] + 0.2, y - 0.1), z=3)
                lz.flecha((pos[a] + 0.2, y - 0.1), (pos[a] + 0.02, y - 0.1))
                y -= paso_y
            else:
                t = lz.ajustar(texto, sep * 1.9, 7)
                extra = 0.16 * t.count("\n")
                x1, x2 = pos[a], pos[b]
                d = 1 if x2 > x1 else -1
                lz.texto((x1 + x2) / 2, y + 0.07 + extra / 2 + 0.03, t, tam=7, va="bottom" if extra == 0 else "center")
                y -= extra
                lz.flecha((x1 + (0.05 if d > 0 else -0.05)*0, y), (x2 - d * 0.05, y), color="black", lw=0.9)
                pila.append((b, y))
                y -= paso_y
        elif tipo == "ret":
            _, a, b, texto = p
            t = lz.ajustar(texto, sep * 1.9, 7)
            extra = 0.16 * t.count("\n")
            x1, x2 = pos[a], pos[b]
            lz.texto((x1 + x2) / 2, y + 0.07 + extra / 2 + 0.03, t, tam=7, va="bottom" if extra == 0 else "center")
            y -= extra
            d = 1 if x2 > x1 else -1
            lz.flecha((x1, y), (x2 - d * 0.05, y), color=GRIS, estilo="--", lw=0.9, cabeza="abierta")
            for i in range(len(pila) - 1, -1, -1):
                if pila[i][0] == a:
                    barras.append((pos[a], pila[i][1] + 0.0, y))
                    pila.pop(i)
                    break
            y -= paso_y
        elif tipo == "nota":
            _, clave, texto = p
            t = lz.ajustar(texto, 2.3, 6.8)
            lineas = t.count("\n") + 1
            h = 0.17 * lineas + 0.1
            x = min(pos[clave] - 0.1, ancho - 2.45)
            lz.caja(x, y - h + 0.1, 2.4, h, t, fondo=AMARILLO, borde="#B79B00", tam=6.8, redondeo=0.02)
            y -= h + 0.08
        elif tipo == "marco":
            _, etiqueta, condicion = p
            marcos.append((etiqueta + " [" + condicion + "]", y + 0.05))
            lz.caja(0.2, y - 0.2, 0.62, 0.2, etiqueta, fondo="white", borde=GRIS, tam=6.8, peso="bold", redondeo=0.02, z=6)
            lz.texto(0.88, y - 0.1, f"[{condicion}]", tam=6.8, ha="left", color=NARANJA, peso="bold", z=6)
            y -= 0.3
        elif tipo == "sino":
            _, condicion = p
            lz.linea((0.2, y + 0.07), (ancho - 0.2, y + 0.07), GRIS, "--", 0.9, z=2)
            lz.texto(0.3, y - 0.07, f"[{condicion}]", tam=6.8, ha="left", color=NARANJA, peso="bold", z=6)
            y -= 0.28
        elif tipo == "fin":
            etiqueta, y0 = marcos.pop()
            lz.ax.add_patch(Rectangle((0.2, y + 0.05), ancho - 0.4, y0 - y - 0.05, fc="none", ec=GRIS, lw=1.0, zorder=2))
            y -= 0.3
    fondo = max(y, fin_lifelines)
    for clave, _ in participantes:
        lz.linea((pos[clave], top - 0.42), (pos[clave], fondo), GRIS, "--", 0.8, z=1)
    for x, y0, y1 in barras:
        lz.ax.add_patch(Rectangle((x - 0.045, y1), 0.09, y0 - y1, fc="white", ec=AZUL, lw=0.9, zorder=2))
    lz.guardar(nombre)


def diagramas_secuencia() -> None:
    secuencia(
        "uml_03_secuencia_crear_producto",
        "Secuencia · Registrar producto con persistencia atómica y compensación",
        [("U", "Usuario"), ("UI", "Interfaz\n(GUI / TUI)"), ("S", "Catálogo de\nInvestigación"), ("M", "Multilista +\nHipercubo"),
         ("R", "Repositorio\nREST / RPC"), ("DB", "Supabase\nPostgreSQL")],
        [
            ("llama", "U", "UI", "Completa el formulario y pulsa Guardar"),
            ("llama", "UI", "S", "crear_producto(datos, grupo, autores)"),
            ("llama", "S", "S", "validar año, tipología y vínculos"),
            ("llama", "S", "M", "agregar_producto() y acumular()"),
            ("ret", "M", "S", "nodo único creado"),
            ("llama", "S", "R", "crear_con_rpc(revision_esperada)"),
            ("llama", "R", "DB", "POST /rpc/crear_producto"),
            ("marco", "alt", "transacción confirmada"),
            ("ret", "DB", "R", "200 OK · meta.revision + 1"),
            ("ret", "R", "S", "producto persistido"),
            ("llama", "S", "S", "apilar ComandoInverso en la Pila"),
            ("ret", "S", "UI", "éxito"),
            ("sino", "error de red, 4xx/5xx o conflicto de revisión"),
            ("ret", "DB", "R", "error"),
            ("ret", "R", "S", "excepción"),
            ("llama", "S", "M", "eliminar_producto() y desacumular()"),
            ("ret", "S", "UI", "error: la memoria queda intacta"),
            ("fin",),
            ("ret", "UI", "U", "mensaje de resultado"),
        ],
    )
    secuencia(
        "uml_04_secuencia_indicador_url",
        "Secuencia · Calcular el indicador de un grupo desde su URL de GrupLAC",
        [("U", "Usuario"), ("UI", "Interfaz o CLI\n(indicador)"), ("IN", "Servicio de\nIngesta"), ("SC", "Portal\nSCIENTI"),
         ("CA", "Catálogo en\nmemoria"), ("IC", "Servicio de\nindicadores")],
        [
            ("llama", "U", "UI", "URL del grupo, año de corte, estimar sí/no"),
            ("llama", "UI", "IN", "encolar_url(url, persistir=False)"),
            ("llama", "IN", "SC", "GET visualizagr.jsp?nro=…"),
            ("ret", "SC", "IN", "HTML del GrupLAC"),
            ("llama", "IN", "IN", "analizar productos, integrantes y CvLAC enlazados"),
            ("llama", "IN", "CA", "crear grupo, investigadores y productos"),
            ("ret", "IN", "UI", "informes de ingesta"),
            ("llama", "UI", "IC", "calcular_indicador(datos, grupo, corte)"),
            ("marco", "opt", "estimar categorías"),
            ("llama", "IC", "IC", "aplicar_estimacion(): categoría base"),
            ("fin",),
            ("llama", "IC", "IC", "filtrar ventana, clasificar y agrupar por subtipo"),
            ("llama", "IC", "IC", "bruto = Σ ln(1 + n / periodo) × puntaje"),
            ("llama", "IC", "IC", "índice = bruto / máximo; aporte = índice × coef."),
            ("ret", "IC", "UI", "indicador, componentes, exclusiones, avisos"),
            ("ret", "UI", "U", "tabla de nueve componentes y total"),
        ],
    )
    secuencia(
        "uml_05_secuencia_importacion_cola",
        "Secuencia · Importación por lotes con cola FIFO",
        [("U", "Usuario"), ("UI", "Interfaz"), ("SI", "Servicio de\nIngesta"), ("Q", "Cola FIFO"),
         ("EX", "Extractor\nURL / CSV / PDF"), ("CA", "Catálogo")],
        [
            ("llama", "U", "UI", "Agrega URL, CSV o PDF y pulsa Procesar todas"),
            ("llama", "UI", "SI", "encolar_url() / encolar_csv() / encolar_pdf()"),
            ("llama", "SI", "Q", "encolar(tarea Pendiente)"),
            ("marco", "loop", "mientras la cola no esté vacía"),
            ("llama", "SI", "Q", "desencolar() → tarea Procesando"),
            ("ret", "Q", "SI", "tarea más antigua (FIFO)"),
            ("llama", "SI", "EX", "descargar o leer y analizar"),
            ("marco", "alt", "fuente válida"),
            ("ret", "EX", "SI", "entidades extraídas"),
            ("llama", "SI", "CA", "crear o actualizar entidades"),
            ("llama", "SI", "SI", "tarea Terminada"),
            ("sino", "404, red o formato inválido"),
            ("ret", "EX", "SI", "error"),
            ("llama", "SI", "SI", "tarea Con error + bitácora; continúa"),
            ("fin",),
            ("fin",),
            ("ret", "SI", "UI", "informes por tarea"),
        ],
    )
    secuencia(
        "uml_06_secuencia_deshacer_conflicto",
        "Secuencia · Deshacer y resolución de conflicto de revisión",
        [("U", "Usuario"), ("UI", "Interfaz"), ("S", "Catálogo de\nInvestigación"), ("P", "Pila de\ndeshacer"),
         ("R", "Repositorio"), ("DB", "Supabase")],
        [
            ("llama", "U", "UI", "Pulsa Deshacer (Ctrl+Z / tecla u)"),
            ("llama", "UI", "S", "deshacer()"),
            ("llama", "S", "P", "desapilar()"),
            ("ret", "P", "S", "ComandoInverso"),
            ("llama", "S", "S", "aplicar la mutación inversa en memoria"),
            ("llama", "S", "R", "persistir inversa(revision_esperada)"),
            ("llama", "R", "DB", "PATCH / RPC"),
            ("marco", "alt", "revisión vigente"),
            ("ret", "DB", "R", "200 OK · revisión + 1"),
            ("ret", "S", "UI", "estado restaurado"),
            ("sino", "meta.revision remota > local"),
            ("ret", "DB", "R", "conflicto"),
            ("llama", "S", "S", "revertir la memoria; reponer la pila"),
            ("ret", "S", "UI", "«La base de datos cambió»"),
            ("llama", "UI", "S", "recargar_todo() si el usuario acepta"),
            ("fin",),
        ],
    )
    secuencia(
        "uml_07_secuencia_estadisticas",
        "Secuencia · Consulta estadística desde el hipercubo en memoria",
        [("U", "Usuario"), ("UI", "Dashboard /\nResumen"), ("SE", "Servicio de\nEstadísticas"), ("H", "Hipercubo 5D")],
        [
            ("llama", "U", "UI", "Elige ámbito y ventana de años"),
            ("llama", "UI", "SE", "obtener_vista_institucional(filtro)"),
            ("llama", "SE", "H", "subcubo_por_ventana(desde, hasta)"),
            ("ret", "H", "SE", "subcubo disperso"),
            ("llama", "SE", "H", "rebanada(grupo) / enrollar(año, categoría)"),
            ("ret", "H", "SE", "totales y series"),
            ("llama", "SE", "SE", "porcentajes, promedios y rankings"),
            ("ret", "SE", "UI", "vista estadística (sin consultas SQL)"),
            ("ret", "UI", "U", "histogramas, barras y tablas"),
        ],
    )


# ---------------------------------------------------------------------------
# Clases
# ---------------------------------------------------------------------------
class Clase:
    def __init__(self, lz: Lienzo, x: float, y: float, w: float, nombre: str, atributos: list[str],
                 metodos: list[str], estereotipo: str | None = None, fondo=AZUL_CLARO, borde=AZUL, tam=7) -> None:
        self.lz, self.x, self.w, self.nombre = lz, x, w, nombre
        lh = 0.145
        h_cab = 0.26 + (0.13 if estereotipo else 0)
        h_att = lh * max(len(atributos), 1) + 0.08
        h_met = lh * max(len(metodos), 1) + 0.08 if metodos else 0
        self.h = h_cab + h_att + h_met
        self.y = y - self.h
        lz.ax.add_patch(Rectangle((x, self.y), w, self.h, fc=fondo, ec=borde, lw=1.1, zorder=2))
        lz.ax.add_patch(Rectangle((x, self.y + h_att + h_met), w, h_cab, fc=borde, ec=borde, lw=1.1, zorder=2))
        if estereotipo:
            lz.texto(x + w / 2, y - 0.1, f"«{estereotipo}»", tam=6.3, color="white", z=4)
        lz.texto(x + w / 2, y - h_cab + 0.13, nombre, tam=7.6, peso="bold", color="white", z=4)
        lz.linea((x, self.y + h_att + h_met), (x + w, self.y + h_att + h_met), borde, lw=1.0, z=3)
        for i, a in enumerate(atributos):
            lz.texto(x + 0.06, self.y + h_att + h_met - 0.07 - lh * (i + 0.5), a, tam=tam, ha="left", z=4)
        if metodos:
            lz.linea((x, self.y + h_met), (x + w, self.y + h_met), borde, lw=1.0, z=3)
            for i, m in enumerate(metodos):
                lz.texto(x + 0.06, self.y + h_met - 0.07 - lh * (i + 0.5), m, tam=tam, ha="left", z=4)

    def ancla(self, lado: str, f: float = 0.5):
        if lado == "N":
            return (self.x + self.w * f, self.y + self.h)
        if lado == "S":
            return (self.x + self.w * f, self.y)
        if lado == "W":
            return (self.x, self.y + self.h * f)
        return (self.x + self.w, self.y + self.h * f)


def relacion(lz: Lienzo, a: Clase, la: str, b: Clase, lb: str, tipo: str, ma: str = "", mb: str = "", rotulo: str = "",
             fa: float = 0.5, fb: float = 0.5, desplaza_rotulo=(0, 0.1)) -> None:
    p, q = a.ancla(la, fa), b.ancla(lb, fb)
    color = GRIS
    if tipo == "composicion":
        p2 = lz.rombo(p, q, color, True)
        lz.linea(p2, q, color)
    elif tipo == "agregacion":
        p2 = lz.rombo(p, q, color, False)
        lz.linea(p2, q, color)
    elif tipo == "herencia":
        lz.flecha(p, q, color, cabeza="hueca")
    elif tipo == "dependencia":
        lz.flecha(p, q, color, "--", cabeza="abierta")
    elif tipo == "asociacion":
        lz.linea(p, q, color)
    elif tipo == "navegable":
        lz.flecha(p, q, color, cabeza="abierta")
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    if ma:
        lz.texto(p[0] + 0.2 * math.cos(ang) - 0.1 * math.sin(ang), p[1] + 0.2 * math.sin(ang) + 0.1 * math.cos(ang), ma,
                 tam=6.5)
    if mb:
        lz.texto(q[0] - 0.2 * math.cos(ang) - 0.1 * math.sin(ang), q[1] - 0.2 * math.sin(ang) + 0.1 * math.cos(ang), mb,
                 tam=6.5)
    if rotulo:
        lz.texto((p[0] + q[0]) / 2 + desplaza_rotulo[0], (p[1] + q[1]) / 2 + desplaza_rotulo[1], rotulo, tam=6.5,
                 color=NARANJA, peso="bold", z=6)


def diagrama_clases_dominio() -> None:
    lz = Lienzo(7.6, 8.75)
    lz.titulo("Diagrama de clases · Dominio y estructuras de datos propias")
    grupo = Clase(lz, 0.15, 8.4, 2.2, "Grupo", ["codigo_gruplac: str", "nombre: str", "fecha_creacion: str", "gran_area_ocde: str",
                                                "categoria: A1|A|B|C|Reconocido", "activo: bool"], ["activar()", "desactivar()"],
                  fondo=VERDE_CLARO, borde=VERDE)
    integ = Clase(lz, 2.7, 8.4, 2.3, "IntegranteGrupo", ["codigo_gruplac: str", "codigo_rh: str", "rol: Líder|Investigador|Estudiante",
                                                         "fecha_inicio / fecha_fin", "activo: bool"], [], fondo=VERDE_CLARO, borde=VERDE)
    inv = Clase(lz, 5.35, 8.4, 2.1, "Investigador", ["codigo_rh: str", "nombre_completo: str", "categoria: str",
                                                     "formacion_academica: str", "activo: bool"], ["activar()", "desactivar()"],
                fondo=VERDE_CLARO, borde=VERDE)
    lista = Clase(lz, 0.15, 6.35, 2.2, "ListaDoble<T>", ["cabeza: NodoDoble", "cola: NodoDoble", "tamano: int"],
                  ["insertar_inicio()  O(1)", "insertar_final()  O(1)", "eliminar_nodo()  O(1)", "buscar()  O(n)", "obtener(i)"],
                  estereotipo="estructura propia")
    prod = Clase(lz, 2.7, 6.35, 2.3, "Producto", ["codigo_identificador: str", "titulo: str", "tipo_mayor: GNC|DTI|ASC|FRH",
                                                 "subtipo / categoria_minciencias", "ano: int  (1970..)", "estado_validacion: str",
                                                 "activo: bool"], ["activar()", "desactivar()"], fondo=VERDE_CLARO, borde=VERDE)
    multi = Clase(lz, 5.2, 6.35, 2.3, "Multilista", ["cabeza / cola", "tamano: int"],
                  ["agregar_producto()", "buscar_nodo()", "obtener_productos_grupo()", "obtener_productos_investigador()",
                   "eliminar_producto()", "cambiar_grupo_de_producto()"], estereotipo="estructura propia")
    nodo = Clase(lz, 2.7, 4.2, 2.3, "NodoProductoMultilista", ["producto: Producto", "grupo: Grupo | None", "autores: ListaDoble",
                                                              "siguiente_global"], ["agregar_autor()", "remover_autor()"])
    Clase(lz, 0.15, 2.4, 2.2, "Pila<ComandoInverso>", ["cima", "tamano: int"], ["apilar()", "desapilar()", "tope()"],
                 estereotipo="estructura propia")
    Clase(lz, 2.7, 2.4, 2.3, "Cola<TareaIngesta>", ["frente / final", "estado: Pendiente | Procesando", "          | Terminada | Con error"],
                 ["encolar()", "desencolar()", "ver_frente()"], estereotipo="estructura propia")
    cubo = Clase(lz, 5.2, 2.4, 2.3, "Hipercubo5D", ["celdas dispersas (g, i, c, a, v)"],
                 ["acumular()", "desacumular()", "rebanada()", "subcubo_por_ventana()", "enrollar()"], estereotipo="estructura propia")
    relacion(lz, grupo, "E", integ, "W", "asociacion", "1", "*", fa=0.4, fb=0.4)
    relacion(lz, inv, "W", integ, "E", "asociacion", "1", "*", fa=0.4, fb=0.4)
    relacion(lz, nodo, "N", prod, "S", "composicion", "", "1")
    relacion(lz, multi, "S", nodo, "E", "agregacion", "1", "*", fa=0.2, fb=0.55)
    relacion(lz, lista, "S", nodo, "W", "dependencia", "", "", "autores", fa=0.5, fb=0.55, desplaza_rotulo=(-0.5, 0.15))
    relacion(lz, multi, "S", cubo, "N", "dependencia", "", "", "alimenta", fa=0.8, fb=0.5, desplaza_rotulo=(0.4, 0.05))
    lz.texto(5.3, 3.65, "Producto único compartido:\nvarios autores y un grupo\napuntan al mismo nodo", tam=6.8,
             ha="left", color=NARANJA)
    lz.texto(0.2, 3.5, "Las operaciones reversibles se\napilan; la importación se\nencola y las estadísticas salen\ndel hipercubo.", tam=6.8,
             ha="left", color=NARANJA)
    lz.guardar("uml_08_clases_dominio")


def diagrama_clases_capas() -> None:
    lz = Lienzo(7.6, 7.5)
    lz.titulo("Diagrama de clases · Servicios, ingesta y persistencia")
    app = Clase(lz, 0.15, 7.15, 2.35, "ServicioAplicacion", ["catalogo: CatalogoInvestigacion", "modo: Supabase|Local|Demo"],
                ["conectar() / iniciar_local()", "crear_producto() / eliminar()", "deshacer()", "datos_indicador()",
                 "guardar_local(ruta)"], estereotipo="fachada de la GUI")
    cat = Clase(lz, 2.75, 7.15, 2.35, "CatalogoInvestigacion", ["grupos / investigadores: ListaDoble",
                                                                "multilista_productos: Multilista", "pila: Pila", "hipercubo: Hipercubo5D"],
                ["crear_ / actualizar_ / eliminar_*", "vincular_integrante()", "deshacer()", "recargar_todo()",
                 "resumen_dict()"], estereotipo="servicio de dominio")
    est = Clase(lz, 5.4, 7.15, 2.1, "ServicioEstadisticas", ["hipercubo: Hipercubo5D"],
                ["productos_por_anio()", "obtener_vista_grupo()", "obtener_vista_investigador()", "distribucion_...()"])
    ind = Clase(lz, 0.15, 4.65, 2.35, "indicadores (módulo)", ["coeficientes de la fórmula", "169 categorías del Modelo"],
                ["calcular_indicador()", "puntaje_producto()", "categoria_estimada()", "aplicar_estimacion()"], estereotipo="Parcial 2")
    ing = Clase(lz, 2.75, 4.65, 2.35, "ServicioIngesta", ["cola: Cola<TareaIngesta>"],
                ["encolar_url() / _csv() / _pdf()", "procesar_siguiente()", "procesar_todas()"])
    rev = Clase(lz, 5.4, 4.65, 2.1, "ControladorRevision", ["revision_local: int"], ["consultar_remota()", "verificar_consistencia()",
                                                                                    "sincronizar()"])
    arch = Clase(lz, 0.15, 2.7, 2.35, "archivo_local", [], ["serializar_catalogo()", "restaurar_catalogo()", "guardar_archivo()"],
                 estereotipo="persistencia local")
    ext = Clase(lz, 2.75, 2.7, 2.35, "Extractores", [], ["ExtractorURL (HTML GrupLAC/CvLAC)", "LectorCSV (canónico)",
                                                         "ExtractorPDF (pdfplumber / Poppler)"], estereotipo="ingesta")
    repo = Clase(lz, 5.4, 2.7, 2.1, "Repositorios", [], ["RepositorioGrupos / Investigadores", "RepositorioIntegrantes",
                                                        "RepositorioProductos (RPC)"], estereotipo="REST / RPC")
    http = Clase(lz, 5.4, 1.15, 2.1, "ClienteHTTPSupabase", ["url, clave publicable", "token (solo en memoria)"],
                 ["get() / post() / patch() / delete()", "rpc()"], estereotipo="HTTPS · TLS")
    relacion(lz, app, "E", cat, "W", "navegable", "", "1", fa=0.5, fb=0.5)
    relacion(lz, cat, "E", est, "W", "dependencia", fa=0.4, fb=0.4)
    relacion(lz, app, "S", ind, "N", "dependencia", fa=0.5, fb=0.5)
    relacion(lz, ing, "N", cat, "S", "dependencia", fa=0.5, fb=0.5)
    relacion(lz, cat, "E", rev, "W", "dependencia", fa=0.1, fb=0.5)
    relacion(lz, ind, "S", arch, "N", "dependencia", fa=0.5, fb=0.5)
    relacion(lz, ing, "S", ext, "N", "dependencia", fa=0.5, fb=0.5)
    relacion(lz, rev, "S", repo, "N", "dependencia", fa=0.5, fb=0.5)
    relacion(lz, repo, "S", http, "N", "dependencia", fa=0.5, fb=0.5)
    lz.guardar("uml_09_clases_servicios")


# ---------------------------------------------------------------------------
# Arquitectura, despliegue, ER y estructuras
# ---------------------------------------------------------------------------
def diagrama_arquitectura() -> None:
    lz = Lienzo(7.6, 5.6)
    lz.titulo("Arquitectura por capas · flujo unidireccional")
    capas = [
        ("1 · Presentación", "GUI PySide6 (Python)  ·  Terminal FTXUI y CLI (C++)", AZUL_CLARO, AZUL),
        ("2 · Servicios", "ServicioAplicacion · CatalogoInvestigacion · ServicioEstadisticas · ServicioIngesta · indicadores", VERDE_CLARO, VERDE),
        ("3 · Estructuras propias", "ListaDoble · Multilista · Pila · Cola · Hipercubo5D (sin list/dict/vector/map como almacén)", "#FDF1E3", NARANJA),
        ("4 · Repositorios", "REST (GET/POST/PATCH/DELETE) y RPC · control de revisión optimista", AZUL_CLARO, AZUL),
        ("5 · Transporte", "HTTPS / TLS · clave publicable · sesión Supabase Auth en memoria", GRIS_CLARO, GRIS),
        ("6 · Supabase (pea-prod)", "PostgREST · funciones RPC · RLS · PostgreSQL 17 · tabla meta(revision)", VERDE_CLARO, VERDE),
    ]
    y = 4.85
    anterior = None
    for etiqueta, texto, fondo, borde in capas:
        lz.caja(0.35, y - 0.55, 6.9, 0.62, "", fondo=fondo, borde=borde)
        lz.texto(0.5, y - 0.12, etiqueta, tam=8.3, peso="bold", ha="left", color=borde)
        lz.texto(0.5, y - 0.38, lz.ajustar(texto, 6.6, 7.2), tam=7.2, ha="left")
        if anterior is not None:
            lz.flecha((3.8, anterior - 0.55), (3.8, y + 0.07), GRIS)
        anterior = y
        y -= 0.78
    lz.caja(0.35, 0.02, 3.25, 0.34, "Archivos JSON / CSV / PDF → servicios", fondo=AMARILLO, borde="#B79B00", tam=7)
    lz.caja(4.0, 0.02, 3.25, 0.34, "SCIENTI (GrupLAC · CvLAC) → ingesta", fondo=AMARILLO, borde="#B79B00", tam=7)
    lz.guardar("uml_10_arquitectura")


def diagrama_despliegue() -> None:
    lz = Lienzo(7.6, 4.6)
    lz.titulo("Diagrama de despliegue · entrega portable para Windows x64")
    lz.caja(0.2, 0.3, 4.4, 3.75, "", fondo="#FBFCFD", borde=AZUL)
    lz.texto(2.4, 3.88, "«device» PC del profesor (Windows 10/11 x64)", tam=8, peso="bold", color=AZUL)
    lz.caja(0.4, 2.15, 1.95, 1.45, "", fondo=AZUL_CLARO, borde=AZUL)
    lz.texto(1.37, 3.42, "«artifact» PEAi-Python", tam=7.5, peso="bold", color=AZUL)
    lz.texto(1.37, 2.88, "Iniciar-Python.cmd\npea-gui.exe · pea-cli.exe\nPySide6 + Python empaquetados", tam=6.8)
    lz.caja(2.55, 2.15, 1.85, 1.45, "", fondo=VERDE_CLARO, borde=VERDE)
    lz.texto(3.47, 3.42, "«artifact» PEAi-Cpp", tam=7.5, peso="bold", color=VERDE)
    lz.texto(3.47, 2.88, "Iniciar-Cpp.cmd\npea-cpp.exe (TUI/CLI)\nQt Core/Network · OpenSSL\nPoppler (pdftotext)", tam=6.8)
    lz.caja(0.4, 0.5, 4.0, 1.35, "", fondo=AMARILLO, borde="#B79B00")
    lz.texto(2.4, 1.68, "Datos locales", tam=7.5, peso="bold", color="#7A6600")
    lz.texto(2.4, 1.05, "config/pea.config.json (URL + clave publicable)\ndatos/ejemplo-parcial.json · catálogos *.json\nCSV canónicos · PDF · exportaciones",
             tam=6.8)
    lz.caja(5.3, 2.7, 2.1, 1.2, "", fondo=VERDE_CLARO, borde=VERDE)
    lz.texto(6.35, 3.72, "«cloud» Supabase pea-prod", tam=7.5, peso="bold", color=VERDE)
    lz.texto(6.35, 3.2, "PostgREST · RPC · Auth\nRLS · PostgreSQL 17", tam=6.8)
    lz.caja(5.3, 0.6, 2.1, 1.2, "", fondo=GRIS_CLARO, borde=GRIS)
    lz.texto(6.35, 1.62, "«external» SCIENTI", tam=7.5, peso="bold", color=GRIS)
    lz.texto(6.35, 1.1, "scienti.minciencias.gov.co\nGrupLAC · CvLAC (HTML)", tam=6.8)
    lz.flecha((4.6, 3.3), (5.3, 3.3), AZUL, "-", 1.1, "abierta")
    lz.texto(4.95, 3.45, "HTTPS 443", tam=6.5, color=AZUL, peso="bold")
    lz.flecha((4.6, 1.2), (5.3, 1.2), GRIS, "--", 1.1, "abierta")
    lz.texto(4.95, 1.35, "HTTPS", tam=6.5, color=GRIS, peso="bold")
    lz.guardar("uml_11_despliegue")


def diagrama_er() -> None:
    lz = Lienzo(7.6, 6.7)
    lz.titulo("Modelo entidad-relación · base de datos compartida (Supabase)")

    def tabla(x, y, w, nombre, campos, fondo=AZUL_CLARO, borde=AZUL):
        lh = 0.15
        h = 0.27 + lh * len(campos) + 0.06
        lz.ax.add_patch(Rectangle((x, y - h), w, h, fc=fondo, ec=borde, lw=1.1, zorder=2))
        lz.ax.add_patch(Rectangle((x, y - 0.27), w, 0.27, fc=borde, ec=borde, lw=1.1, zorder=2))
        lz.texto(x + w / 2, y - 0.135, nombre, tam=7.8, peso="bold", color="white", z=4)
        for i, c in enumerate(campos):
            lz.texto(x + 0.07, y - 0.27 - lh * (i + 0.6) - 0.02, c, tam=6.6, ha="left", z=4)
        return {"x": x, "y": y - h, "w": w, "h": h, "top": y}

    g = tabla(0.15, 6.3, 2.1, "grupos", ["PK id", "codigo_gruplac  (único)", "nombre", "fecha_creacion", "institucion_principal",
                                          "gran_area_ocde / area_ocde", "categoria", "detalles (jsonb)", "activo · es_ejemplo"],
              VERDE_CLARO, VERDE)
    i = tabla(5.35, 6.3, 2.1, "investigadores", ["PK id", "codigo_rh  (único)", "nombre_completo", "categoria", "formacion_academica",
                                                 "detalles (jsonb)", "activo · es_ejemplo"], VERDE_CLARO, VERDE)
    tabla(2.75, 6.1, 2.1, "integrantes_grupo", ["PK id", "FK grupo_id", "FK investigador_id", "rol",
                                                 "fecha_inicio · fecha_fin", "activo"])
    pg = tabla(0.15, 3.85, 2.1, "producto_grupos", ["FK producto_id", "FK grupo_id"])
    tabla(2.75, 4.1, 2.1, "productos", ["PK id", "codigo_identificador  (único)", "titulo", "tipo_mayor (GNC/DTI/ASC/FRH)",
                                         "subtipo", "ano  (1970..)", "estado_validacion", "detalles (jsonb)", "activo · es_ejemplo"],
          VERDE_CLARO, VERDE)
    pa = tabla(5.35, 3.85, 2.1, "producto_autores", ["FK producto_id", "FK investigador_id", "orden"])
    tabla(0.15, 2.0, 2.1, "meta", ["clave", "valor", "revision  (contador global)", "trigger: +1 por mutación"],
          "#FDF1E3", NARANJA)
    tabla(2.75, 1.85, 2.1, "auditoria_cambios", ["PK id", "tabla · operacion", "datos_anteriores (jsonb)", "revision · fecha"],
          GRIS_CLARO, GRIS)
    tabla(5.35, 2.2, 2.1, "proyectos / semilleros", ["PK id", "FK grupo_id", "nombre · estado", "fechas"], GRIS_CLARO, GRIS)
    lz.linea((2.25, 5.35), (2.75, 5.35), GRIS, lw=1.1)
    lz.linea((4.85, 5.35), (5.35, 5.35), GRIS, lw=1.1)
    for x, t in [(2.33, "1"), (2.67, "*"), (4.93, "*"), (5.27, "1")]:
        lz.texto(x, 5.5, t, tam=6.5)
    lz.linea((1.2, g["y"]), (1.2, pg["top"]), GRIS, lw=1.1)
    lz.texto(1.28, g["y"] - 0.12, "1", tam=6.5)
    lz.texto(1.28, pg["top"] + 0.1, "*", tam=6.5)
    lz.linea((6.4, i["y"]), (6.4, pa["top"]), GRIS, lw=1.1)
    lz.texto(6.48, i["y"] - 0.12, "1", tam=6.5)
    lz.texto(6.48, pa["top"] + 0.1, "*", tam=6.5)
    lz.linea((2.25, 3.4), (2.75, 3.4), GRIS, lw=1.1)
    lz.linea((4.85, 3.4), (5.35, 3.4), GRIS, lw=1.1)
    for x, t in [(2.33, "*"), (2.67, "1"), (4.93, "1"), (5.27, "*")]:
        lz.texto(x, 3.55, t, tam=6.5)
    lz.texto(3.8, 0.55, "Un producto es una sola fila compartida por N grupos y N autores;\n"
             "las tablas puente producto_grupos y producto_autores reproducen la multilista en memoria.\n"
             "Toda escritura incrementa meta.revision (control de concurrencia optimista).",
             tam=7, color=GRIS)
    lz.guardar("uml_12_entidad_relacion")


def diagrama_multilista() -> None:
    lz = Lienzo(7.6, 4.9)
    lz.titulo("Estructura de datos · multilista de productos compartidos")
    # grupos
    for x, nombre in [(0.9, "Grupo G1"), (3.8, "Grupo G2")]:
        lz.caja(x, 4.05, 1.5, 0.45, nombre, fondo=VERDE_CLARO, borde=VERDE, tam=7.8, peso="bold")
    # productos
    prods = [(0.9, "Producto P1"), (2.4, "Producto P2"), (3.9, "Producto P3"), (5.4, "Producto P4")]
    for x, nombre in prods:
        lz.caja(x, 2.45, 1.3, 0.55, nombre, fondo=AZUL_CLARO, borde=AZUL, tam=7.6, peso="bold")
    # investigadores
    invs = [(0.9, "Inv. A"), (2.85, "Inv. B"), (4.8, "Inv. C")]
    for x, nombre in invs:
        lz.caja(x, 0.55, 1.3, 0.45, nombre, fondo=VERDE_CLARO, borde=VERDE, tam=7.8, peso="bold")
    # lista de productos del grupo G1: P1 -> P2 ; G2: P3 -> P4
    lz.flecha((1.65, 4.05), (1.55, 3.0), VERDE, lw=1.1)
    lz.flecha((2.6, 2.72), (2.4 + 0.0, 2.72), VERDE, "-", 1.0, "llena") if False else None
    lz.flecha((2.2, 2.78), (2.4, 2.78), VERDE, lw=1.1)
    lz.flecha((4.55, 4.05), (4.55, 3.0), VERDE, lw=1.1)
    lz.flecha((5.2, 2.78), (5.4, 2.78), VERDE, lw=1.1)
    lz.texto(1.85, 3.55, "lista de productos\ndel grupo", tam=6.5, color=VERDE, ha="left")
    lz.texto(4.65, 3.55, "lista de productos\ndel grupo", tam=6.5, color=VERDE, ha="left")
    # autores: P1 -> A,B ; P2 -> B ; P3 -> B,C ; P4 -> C
    enlaces = [(1.55, 2.45, 1.55, 1.0), (1.55, 2.45, 3.5, 1.0), (3.05, 2.45, 3.4, 1.0), (4.55, 2.45, 3.7, 1.0),
               (4.55, 2.45, 5.2, 1.0), (6.05, 2.45, 5.6, 1.0)]
    for x1, y1, x2, y2 in enlaces:
        lz.flecha((x1, y1), (x2, y2), NARANJA, "-", 1.0)
    lz.texto(0.15, 1.7, "listas de\nautores", tam=6.5, color=NARANJA, ha="left")
    lz.caja(5.9, 3.75, 1.55, 0.95, "Cada producto es\nUN solo nodo.\nModificarlo se ve\nen grupo y autores.", fondo=AMARILLO,
            borde="#B79B00", tam=6.6, redondeo=0.03)
    lz.texto(3.8, 0.2, "Las listas son doblemente enlazadas; eliminar un nodo conocido es O(1) y no deja punteros colgantes.",
             tam=6.8, color=GRIS)
    lz.guardar("estructura_01_multilista")


def diagrama_hipercubo() -> None:
    lz = Lienzo(7.6, 4.6)
    lz.titulo("Estructura de datos · hipercubo disperso de cinco dimensiones")
    dims = [("D1 Grupo", "código GrupLAC"), ("D2 Investigador", "código CvLAC"), ("D3 Categoría", "GNC · DTI · ASC · FRH"),
            ("D4 Año", "1970 … año actual"), ("D5 Validación", "Avalado · Con soporte · No avalado")]
    for k, (a, b) in enumerate(dims):
        lz.caja(0.2 + k * 1.5, 3.3, 1.4, 0.7, f"{a}\n" + lz.ajustar(b, 1.25, 6.3), fondo=AZUL_CLARO if k % 2 == 0 else VERDE_CLARO,
                borde=AZUL if k % 2 == 0 else VERDE, tam=6.3)
    lz.texto(3.8, 3.0, "celda (g, i, c, a, v)  →  conjunto de productos ACTIVOS  (medida = cantidad)", tam=7.6, peso="bold",
             color=AZUL)
    lz.caja(0.2, 1.7, 3.45, 1.0, "Solo existen las celdas con datos (dispersa).\nDesactivar un producto lo retira de la celda;\n"
            "reactivarlo lo repone. Todas las estadísticas\nsalen de aquí, sin SQL agregado.", fondo=AMARILLO, borde="#B79B00",
            tam=7)
    ops = [("rebanada(dim, valor)", "fija una dimensión"), ("subcubo_por_ventana()", "filtra el rango de años"),
           ("enrollar(dim)", "colapsa y suma"), ("poblar_desde_multilista()", "reconstruye el cubo")]
    for k, (a, b) in enumerate(ops):
        lz.caja(3.95, 2.45 - k * 0.5, 3.45, 0.42, f"{a}  —  {b}", fondo=GRIS_CLARO, borde=GRIS, tam=6.8, ha="left")
    lz.texto(3.8, 0.3, "Ejemplo: enrollar(Año) tras rebanada(Grupo = G1) produce la serie anual del grupo.", tam=7, color=GRIS)
    lz.guardar("estructura_02_hipercubo")


def diagrama_flujo_indicador() -> None:
    lz = Lienzo(7.6, 7.6)
    lz.titulo("Diagrama de actividades · cálculo del indicador de producción científica")
    pasos = [
        "Obtener datos: URL GrupLAC/CvLAC, CSV, PDF o archivo local",
        "Seleccionar grupo o investigador y año de corte (2023 = Modelo 2024)",
        "¿Productos sin categoría? → estimar (opcional) con la categoría base",
        "Filtrar: activos, avalados, tipología coherente y ventana por subtipo (5, 7 o 10 años)",
        "Agrupar por subtipo y contar productos únicos  n",
        "λ = ln(1 + n / periodo)  ·  bruto de clase = Σ λ × peso_base × peso_relativo",
        "Cohe y Coop desde autores internos y grupos por producto GNC/DTI",
        "Normalizar: índice = bruto / máximo de la población de referencia",
        "Ind = 3,7·Nc.Top + 2,3·Nc.A + 0,4·Nc.B + 1,5·AP + 0,5·DPC + 1·Fr.A + 0,2·Fr.B + 0,1·Cohe + 0,3·Coop",
        "Mostrar desglose, exclusiones, avisos y exportar JSON",
    ]
    y = 6.7
    lz.ax.add_patch(Circle((3.8, 7.0), 0.1, fc=AZUL, ec=AZUL, zorder=3))
    lz.flecha((3.8, 6.9), (3.8, y + 0.2), GRIS)
    for k, texto in enumerate(pasos):
        decision = k == 2
        fondo = AMARILLO if decision else (VERDE_CLARO if k == 8 else AZUL_CLARO)
        borde = "#B79B00" if decision else (VERDE if k == 8 else AZUL)
        lz.caja(0.9, y - 0.4, 5.8, 0.6, lz.ajustar(texto, 5.5, 7.4), fondo=fondo, borde=borde, tam=7.4, redondeo=0.12)
        if k < len(pasos) - 1:
            lz.flecha((3.8, y - 0.4), (3.8, y - 0.62), GRIS)
        y -= 0.62
    lz.flecha((3.8, y + 0.22), (3.8, y - 0.02), GRIS)
    lz.ax.add_patch(Circle((3.8, y - 0.12), 0.1, fc="white", ec=AZUL, lw=1.5, zorder=3))
    lz.ax.add_patch(Circle((3.8, y - 0.12), 0.055, fc=AZUL, ec=AZUL, zorder=4))
    lz.guardar("uml_13_actividad_indicador")


def main() -> int:
    for funcion in (
        diagrama_casos_uso_general,
        diagrama_casos_uso_indicador,
        diagramas_secuencia,
        diagrama_clases_dominio,
        diagrama_clases_capas,
        diagrama_arquitectura,
        diagrama_despliegue,
        diagrama_er,
        diagrama_multilista,
        diagrama_hipercubo,
        diagrama_flujo_indicador,
    ):
        funcion()
        print("OK", funcion.__name__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
