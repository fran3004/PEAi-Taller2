"""Algoritmo de disposición por fuerzas determinista para la red de colaboración (ADR-0015).

Implementa un modelo físico de repulsión de Coulomb y atracción de Hooke con enfriamiento
progresivo y separación de componentes desconectados para evitar que nodos aislados
compriman el núcleo conectado de coautorías.
"""

from __future__ import annotations

import math
from typing import Any


def calcular_disposicion_fuerzas(
    nodos: list[dict[str, Any]],
    aristas: list[dict[str, Any]],
    ancho: float = 960.0,
    alto: float = 640.0,
    iteraciones: int = 120,
    semilla: int = 42,
) -> dict[str, tuple[float, float]]:
    """Calcula coordenadas (x, y) deterministas centradas en (0, 0).

    Parámetros:
        nodos: Lista de diccionarios con al menos 'codigo' (o 'id') y 'grado'.
        aristas: Lista de diccionarios con 'origen', 'destino' y 'peso' (o 'productos_compartidos').
        ancho: Ancho lógico del área de dibujo.
        alto: Alto lógico del área de dibujo.
        iteraciones: Número de pasos de simulación física (90 a 150 según ADR-0015).
        semilla: Semilla determinista (42 por defecto) para desempates angulares.

    Retorna:
        Diccionario {codigo_nodo: (x, y)}.
    """
    if not nodos:
        return {}

    def _id_nodo(n: dict[str, Any]) -> str:
        return str(n.get("codigo") or n.get("id") or "")

    def _grado_nodo(n: dict[str, Any]) -> int:
        return int(n.get("grado", 0))

    nodos_ordenados = sorted(
        nodos,
        key=lambda n: (-_grado_nodo(n), _id_nodo(n)),
    )

    n_total = len(nodos_ordenados)
    if n_total == 1:
        return {_id_nodo(nodos_ordenados[0]): (0.0, 0.0)}

    ids_totales = {_id_nodo(n) for n in nodos_ordenados}

    # Filtrar aristas válidas y detectar qué nodos participan en al menos un enlace
    enlaces_validos: list[tuple[str, str, float]] = []
    ids_con_enlace: set[str] = set()
    for a in aristas:
        u = str(a.get("origen", ""))
        v = str(a.get("destino", ""))
        if u in ids_totales and v in ids_totales and u != v:
            peso = float(a.get("peso") or a.get("productos_compartidos") or 1.0)
            enlaces_validos.append((u, v, max(1.0, peso)))
            ids_con_enlace.add(u)
            ids_con_enlace.add(v)

    nodos_conectados = [n for n in nodos_ordenados if _id_nodo(n) in ids_con_enlace]
    nodos_aislados = [n for n in nodos_ordenados if _id_nodo(n) not in ids_con_enlace]

    # Si ningún nodo tiene aristas activas, distribuir en anillos concéntricos armónicos
    if not nodos_conectados:
        pos_sin_aristas: dict[str, tuple[float, float]] = {}
        desfase_base = ((semilla % 360) * math.pi) / 180.0
        for idx, n_item in enumerate(nodos_ordenados):
            nid = _id_nodo(n_item)
            if idx == 0 and n_total > 4:
                pos_sin_aristas[nid] = (0.0, 0.0)
                continue
            k = idx - 1 if n_total > 4 else idx
            total_anillo = n_total - 1 if n_total > 4 else n_total
            angulo = desfase_base + (2.0 * math.pi * k) / max(1, total_anillo)
            rx = ancho * 0.38
            ry = alto * 0.36
            pos_sin_aristas[nid] = (rx * math.cos(angulo), ry * math.sin(angulo))
        return pos_sin_aristas

    # ------------------------------------------------------------------
    # Simulación física sobre el subgrafo conectado (nodos_conectados)
    # ------------------------------------------------------------------
    n_con = len(nodos_conectados)
    pos_x: dict[str, float] = {}
    pos_y: dict[str, float] = {}
    grados: dict[str, int] = {}

    desfase_semilla = ((semilla % 360) * math.pi) / 180.0
    radio_inicial_x = ancho * 0.34
    radio_inicial_y = alto * 0.32

    for idx, nodo in enumerate(nodos_conectados):
        nid = _id_nodo(nodo)
        grados[nid] = _grado_nodo(nodo)
        if n_con == 1:
            pos_x[nid] = 0.0
            pos_y[nid] = 0.0
        elif idx == 0 and n_con >= 4:
            pos_x[nid] = 0.0
            pos_y[nid] = 0.0
        else:
            k = idx - 1 if n_con >= 4 else idx
            m = n_con - 1 if n_con >= 4 else n_con
            angulo = desfase_semilla + (2.0 * math.pi * k) / max(1, m)
            factor_anillo = 0.62 if (k % 2 == 0 and m > 6) else 1.0
            pos_x[nid] = radio_inicial_x * factor_anillo * math.cos(angulo)
            pos_y[nid] = radio_inicial_y * factor_anillo * math.sin(angulo)

    area = ancho * alto * 0.65
    k_optimo = math.sqrt(area / max(1, n_con))
    k_repulsion = k_optimo * k_optimo * 1.45
    k_atraccion = 1.0 / max(1.0, k_optimo * 1.05)

    ids_con = [_id_nodo(n) for n in nodos_conectados]
    temp_inicial = min(ancho, alto) * 0.20

    if n_con > 1:
        for paso in range(iteraciones):
            progreso = paso / max(1, iteraciones - 1)
            temperatura = temp_inicial * ((1.0 - progreso) ** 1.4)
            if temperatura < 0.4:
                temperatura = 0.4

            disp_x: dict[str, float] = {nid: 0.0 for nid in ids_con}
            disp_y: dict[str, float] = {nid: 0.0 for nid in ids_con}

            # Repulsión de Coulomb entre pares conectados
            for i in range(n_con):
                u = ids_con[i]
                ux, uy = pos_x[u], pos_y[u]
                for j in range(i + 1, n_con):
                    v = ids_con[j]
                    dx = ux - pos_x[v]
                    dy = uy - pos_y[v]
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < 1.0:
                        ang = desfase_semilla + (i * 0.7 + j * 1.3)
                        dx = math.cos(ang)
                        dy = math.sin(ang)
                        dist_sq = 1.0
                    dist = math.sqrt(dist_sq)
                    fuerza_rep = k_repulsion / dist
                    fx = (dx / dist) * fuerza_rep
                    fy = (dy / dist) * fuerza_rep
                    disp_x[u] += fx
                    disp_y[u] += fy
                    disp_x[v] -= fx
                    disp_y[v] -= fy

            # Atracción de Hooke en las aristas
            for u, v, peso in enlaces_validos:
                dx = pos_x[u] - pos_x[v]
                dy = pos_y[u] - pos_y[v]
                dist = math.hypot(dx, dy)
                if dist < 0.1:
                    continue
                factor_peso = 1.0 + 0.30 * math.log2(peso)
                fuerza_atr = (dist * dist) * k_atraccion * factor_peso
                fx = (dx / dist) * fuerza_atr
                fy = (dy / dist) * fuerza_atr
                disp_x[u] -= fx
                disp_y[u] -= fy
                disp_x[v] += fx
                disp_y[v] += fy

            # Gravedad suave hacia el centro
            for nid in ids_con:
                peso_grav = 0.04 + 0.015 * math.sqrt(max(1, grados[nid]))
                disp_x[nid] -= pos_x[nid] * peso_grav
                disp_y[nid] -= pos_y[nid] * peso_grav

            # Actualizar posiciones limitadas por temperatura
            for nid in ids_con:
                dx = disp_x[nid]
                dy = disp_y[nid]
                mag = math.hypot(dx, dy)
                if mag > 0.0:
                    despl = min(mag, temperatura)
                    pos_x[nid] += (dx / mag) * despl
                    pos_y[nid] += (dy / mag) * despl

    # Normalización del subgrafo conectado para que ocupe generosamente el lienzo central
    tiene_aislados = len(nodos_aislados) > 0
    fraccion_lienzo = 0.62 if tiene_aislados else 0.80
    mitad_w = (ancho * fraccion_lienzo) / 2.0
    mitad_h = (alto * fraccion_lienzo) / 2.0

    if n_con > 1:
        min_x = min(pos_x.values())
        max_x = max(pos_x.values())
        min_y = min(pos_y.values())
        max_y = max(pos_y.values())

        rango_x = max(1.0, max_x - min_x)
        rango_y = max(1.0, max_y - min_y)
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0

        for nid in ids_con:
            pos_x[nid] = ((pos_x[nid] - cx) / (rango_x / 2.0)) * mitad_w
            pos_y[nid] = ((pos_y[nid] - cy) / (rango_y / 2.0)) * mitad_h

        # Pase de anticolisión para garantizar legibilidad de etiquetas y nodos
        dist_min = max(72.0, min(ancho, alto) / max(4.5, math.sqrt(n_con) * 2.1))
        for _ in range(18):
            hubo_ajuste = False
            for i in range(n_con):
                u = ids_con[i]
                for j in range(i + 1, n_con):
                    v = ids_con[j]
                    dx = pos_x[u] - pos_x[v]
                    dy = pos_y[u] - pos_y[v]
                    d = math.hypot(dx, dy)
                    if d < dist_min:
                        hubo_ajuste = True
                        if d < 0.01:
                            ang = desfase_semilla + i * 1.1 + j * 0.7
                            dx, dy, d = math.cos(ang), math.sin(ang), 1.0
                        empuje = (dist_min - d) * 0.52
                        ux = (dx / d) * empuje
                        uy = (dy / d) * empuje
                        pos_x[u] = max(-mitad_w * 1.08, min(mitad_w * 1.08, pos_x[u] + ux))
                        pos_y[u] = max(-mitad_h * 1.08, min(mitad_h * 1.08, pos_y[u] + uy))
                        pos_x[v] = max(-mitad_w * 1.08, min(mitad_w * 1.08, pos_x[v] - ux))
                        pos_y[v] = max(-mitad_h * 1.08, min(mitad_h * 1.08, pos_y[v] - uy))
            if not hubo_ajuste:
                break

    # ------------------------------------------------------------------
    # Ubicación perimetral ordenada para nodos aislados (grado == 0)
    # ------------------------------------------------------------------
    n_ais = len(nodos_aislados)
    if n_ais > 0:
        rx_ais = ancho * 0.46
        ry_ais = alto * 0.44
        for idx_a, nodo_a in enumerate(nodos_aislados):
            nid_a = _id_nodo(nodo_a)
            angulo = desfase_semilla + (2.0 * math.pi * idx_a) / max(1, n_ais)
            xa = rx_ais * math.cos(angulo)
            ya = ry_ais * math.sin(angulo)
            # Evitar colisión con nodos conectados cercanos al borde del anillo interior
            for _ in range(8):
                colision = False
                for nid_c in ids_con:
                    dx_c = xa - pos_x[nid_c]
                    dy_c = ya - pos_y[nid_c]
                    d_c = math.hypot(dx_c, dy_c)
                    if d_c < 84.0:
                        colision = True
                        angulo += 0.16
                        xa = (rx_ais + 16.0) * math.cos(angulo)
                        ya = (ry_ais + 14.0) * math.sin(angulo)
                        break
                if not colision:
                    break
            pos_x[nid_a] = xa
            pos_y[nid_a] = ya

    resultado: dict[str, tuple[float, float]] = {}
    for n_item in nodos_ordenados:
        nid = _id_nodo(n_item)
        resultado[nid] = (round(pos_x[nid], 4), round(pos_y[nid], 4))
    return resultado


def normalizar_nombre_investigador(nombre_completo: str) -> str:
    """Normaliza la capitalización de un nombre manteniendo partículas en minúscula."""
    limpio = " ".join(nombre_completo.strip().split())
    if not limpio:
        return "Investigador"
    particulas = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos"}
    palabras = limpio.split(" ")
    resultado: list[str] = []
    for idx, p in enumerate(palabras):
        p_low = p.lower()
        if idx > 0 and p_low in particulas:
            resultado.append(p_low)
        elif p.islower() or p.isupper():
            resultado.append(p[:1].upper() + p[1:].lower())
        else:
            resultado.append(p)
    return " ".join(resultado)


def abreviar_nombre_investigador(nombre_completo: str) -> str:
    """Abrevia un nombre completo al formato 'N. Apellido' para etiquetas de nodo."""
    limpio = normalizar_nombre_investigador(nombre_completo)
    if not limpio:
        return "Inv."
    partes = limpio.split(" ")
    if len(partes) == 1:
        return partes[0][:12]
    inicial = partes[0][0].upper()
    # Si tiene 4 partes (2 nombres + 2 apellidos), usar el primer apellido (penúltima palabra)
    # pero mantener compatibilidad con 2-3 partes usando la última o primer apellido significativo
    apellido = partes[-1]
    return f"{inicial}. {apellido}"
