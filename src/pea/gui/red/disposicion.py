"""Algoritmo determinista de disposición por fuerzas (Hooke + Coulomb) para grafos de coautoría.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Modelo físico: repulsión electrostática de Coulomb entre todos los nodos
  y atracción elástica de Hooke a lo largo de las aristas compartidas.
- Enfriamiento simulado (simulated annealing) para convergencia estable.
- Semilla pseudoaleatoria fija para garantizar repetibilidad 100% determinista.
"""

from __future__ import annotations

import math
import random
from typing import Any


def calcular_disposicion_fuerzas(
    nodos: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    aristas: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    ancho: float = 1000.0,
    alto: float = 700.0,
    margen: float = 60.0,
    iteraciones: int = 120,
    semilla: int = 42,
) -> dict[str, tuple[float, float]]:
    """Calcula las coordenadas (x, y) de los nodos mediante un modelo de fuerzas determinista.

    Args:
        nodos: Lista o tupla de diccionarios de nodos con al menos la clave 'codigo'.
        aristas: Lista o tupla de aristas con claves 'origen', 'destino' y opcionalmente 'productos_compartidos'.
        ancho: Ancho total del área de disposición en píxeles de escena.
        alto: Alto total del área de disposición en píxeles de escena.
        margen: Margen de resguardo respecto a los bordes.
        iteraciones: Número de pasos de simulación.
        semilla: Semilla fija para reproducibilidad matemática.

    Returns:
        Diccionario asociando el código de cada nodo con su tupla de coordenadas (x, y).
    """
    codigos = [str(n.get("codigo") or n.get("id")) for n in nodos if "codigo" in n or "id" in n]
    n = len(codigos)
    if n == 0:
        return {}

    cx = ancho / 2.0
    cy = alto / 2.0

    if n == 1:
        return {codigos[0]: (cx, cy)}

    if n == 2:
        dist_mitad = min(ancho, alto) * 0.25
        return {
            codigos[0]: (cx - dist_mitad, cy),
            codigos[1]: (cx + dist_mitad, cy),
        }

    rng = random.Random(semilla)
    indice_por_codigo = {cod: i for i, cod in enumerate(codigos)}

    # Distribución inicial circular determinista con leve perturbación fija
    pos_x = [0.0] * n
    pos_y = [0.0] * n
    radio_base = min(ancho, alto) * 0.38

    for i in range(n):
        angulo = (2.0 * math.pi * i) / n
        radio_var = radio_base + rng.uniform(-15.0, 15.0)
        pos_x[i] = cx + radio_var * math.cos(angulo)
        pos_y[i] = cy + radio_var * math.sin(angulo)

    # Parámetros del modelo Fruchterman-Reingold
    area_efectiva = (ancho - 2.0 * margen) * (alto - 2.0 * margen)
    k = math.sqrt(max(100.0, area_efectiva) / n)
    k_cuadrado = k * k

    # Lista de aristas indexadas con sus pesos
    aristas_indexadas: list[tuple[int, int, float]] = []
    for a in aristas:
        u_cod = str(a.get("origen") or a.get("source") or "")
        v_cod = str(a.get("destino") or a.get("target") or "")
        if u_cod in indice_por_codigo and v_cod in indice_por_codigo:
            u_idx = indice_por_codigo[u_cod]
            v_idx = indice_por_codigo[v_cod]
            if u_idx != v_idx:
                peso = float(a.get("productos_compartidos") or a.get("peso") or 1.0)
                aristas_indexadas.append((u_idx, v_idx, peso))

    # Temperatura inicial y amortiguamiento
    temp = min(ancho, alto) * 0.20
    enfriamiento = temp / max(1, iteraciones)

    for _paso in range(iteraciones):
        disp_x = [0.0] * n
        disp_y = [0.0] * n

        # 1. Repulsión de Coulomb entre todos los pares de nodos
        for i in range(n):
            xi = pos_x[i]
            yi = pos_y[i]
            for j in range(i + 1, n):
                dx = xi - pos_x[j]
                dy = yi - pos_y[j]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 0.01:
                    dist = 0.01

                fuerza_rep = k_cuadrado / dist
                fx = (dx / dist) * fuerza_rep
                fy = (dy / dist) * fuerza_rep

                disp_x[i] += fx
                disp_y[i] += fy
                disp_x[j] -= fx
                disp_y[j] -= fy

        # 2. Atracción de Hooke a lo largo de las aristas
        for u_idx, v_idx, peso in aristas_indexadas:
            dx = pos_x[u_idx] - pos_x[v_idx]
            dy = pos_y[u_idx] - pos_y[v_idx]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.01:
                dist = 0.01

            # Factor logarítmico del peso de coautoría
            factor_peso = min(2.5, 1.0 + 0.20 * math.log2(max(1.0, peso)))
            fuerza_atr = ((dist * dist) / k) * factor_peso

            fx = (dx / dist) * fuerza_atr
            fy = (dy / dist) * fuerza_atr

            disp_x[u_idx] -= fx
            disp_y[u_idx] -= fy
            disp_x[v_idx] += fx
            disp_y[v_idx] += fy

        # 3. Gravedad hacia el centro para evitar dispersión de componentes aislados
        for i in range(n):
            dx_c = cx - pos_x[i]
            dy_c = cy - pos_y[i]
            disp_x[i] += dx_c * 0.06
            disp_y[i] += dy_c * 0.06

        # 4. Actualización de posiciones acotada por la temperatura actual
        for i in range(n):
            dx = disp_x[i]
            dy = disp_y[i]
            dist_disp = math.sqrt(dx * dx + dy * dy)
            if dist_disp > 0.001:
                limite = min(dist_disp, temp)
                pos_x[i] += (dx / dist_disp) * limite
                pos_y[i] += (dy / dist_disp) * limite

        temp = max(0.0, temp - enfriamiento)

    # 5. Normalización y escalado para ajustar al área delimitada con margen
    min_x = min(pos_x)
    max_x = max(pos_x)
    min_y = min(pos_y)
    max_y = max(pos_y)

    rango_x = max(1.0, max_x - min_x)
    rango_y = max(1.0, max_y - min_y)

    ancho_util = ancho - 2.0 * margen
    alto_util = alto - 2.0 * margen

    escala_x = ancho_util / rango_x
    escala_y = alto_util / rango_y
    escala = min(escala_x, escala_y)

    # Centrar la red en el lienzo disponible
    centro_red_x = (min_x + max_x) / 2.0
    centro_red_y = (min_y + max_y) / 2.0

    resultado: dict[str, tuple[float, float]] = {}
    for i, cod in enumerate(codigos):
        x_final = cx + (pos_x[i] - centro_red_x) * escala
        y_final = cy + (pos_y[i] - centro_red_y) * escala
        resultado[cod] = (round(x_final, 2), round(y_final, 2))

    return resultado
