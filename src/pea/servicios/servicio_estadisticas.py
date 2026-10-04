"""Servicio de cálculo estadístico multidimensional en memoria (OLAP Local).

Calcula todas las métricas requeridas a partir exclusivamente del Hipercubo5D.
Prohibido el uso de consultas SQL de agregación durante el cálculo analítico.
Conforme a AGENTS.md, Hipercubo.md, SPEC.md y ADR-0006.
"""

from __future__ import annotations

from typing import Any

from pea.estructuras.hipercubo import Hipercubo5D


class ServicioEstadisticas:
    """Capa analítica que consume el Hipercubo5D para servir las métricas de la GUI y CLI."""

    def __init__(self, hipercubo: Hipercubo5D) -> None:
        self.hipercubo = hipercubo

    def _resolver_cubo(
        self,
        cubo: Hipercubo5D | None = None,
        ventana_anios: int | None = None,
        modelo_2024: bool = False,
        anio_referencia: int = 2024,
        anio_inicio: int | None = None,
        anio_fin: int | None = None,
    ) -> Hipercubo5D:
        """Aplica la ventana solicitada sobre el hipercubo base o suministrado.

        Diferenciación conceptual:
        1. Filtro de interfaz (ventana_anios o rango anio_inicio..anio_fin): años consecutivos.
        2. Ventana del Modelo 2024: 5 años para ordinarios, 10 años para libros/patentes.
        """
        c = cubo if cubo is not None else self.hipercubo
        if modelo_2024:
            return c.subcubo_modelo_2024(anio_corte=2023)
        if anio_inicio is not None or anio_fin is not None:
            return c.subcubo_por_ventana(anio_inicio=anio_inicio, anio_fin=anio_fin)
        if ventana_anios is not None and ventana_anios > 0:
            inicio = anio_referencia - ventana_anios + 1
            return c.subcubo_por_ventana(anio_inicio=inicio, anio_fin=anio_referencia)
        return c

    # =========================================================================
    # AGREGACIONES ELEMENTALES (ROLL-UP)
    # =========================================================================

    def productos_por_anio(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[int, int]:
        """Calcula la serie temporal de productos activos por año ordenada cronológicamente."""
        c = cubo if cubo is not None else self.hipercubo
        bruto = c.enrollar(Hipercubo5D.DIM_ANIO)
        # Ordenar por año ascendente
        return {int(a): int(cnt) for a, cnt in sorted(bruto.items(), key=lambda t: int(t[0]))}

    def productos_por_categoria(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[str, int]:
        """Calcula la cantidad de productos por tipología mayor (GNC, DTI, ASC, FRH)."""
        c = cubo if cubo is not None else self.hipercubo
        bruto = c.enrollar(Hipercubo5D.DIM_CATEGORIA)
        # Consolidar subtipos especiales de libro o patente bajo GNC si corresponde
        resultado: dict[str, int] = {"GNC": 0, "DTI": 0, "ASC": 0, "FRH": 0}
        for cat, cnt in bruto.items():
            cat_upper = str(cat).upper()
            if cat_upper in resultado:
                resultado[cat_upper] += cnt
            elif "GNC" in cat_upper or "LIBRO" in cat_upper or "PATENTE" in cat_upper:
                resultado["GNC"] += cnt
            else:
                resultado[str(cat)] = cnt
        return resultado

    def serie_anual_por_categoria(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[int, dict[str, int]]:
        """Calcula la matriz año × tipología (GNC, DTI, ASC, FRH) desde el hipercubo con rebanada y enrollar."""
        c = cubo if cubo is not None else self.hipercubo
        anios = sorted(c.enrollar(Hipercubo5D.DIM_ANIO).keys(), key=lambda x: int(x))
        resultado: dict[int, dict[str, int]] = {}
        for a in anios:
            anio_int = int(a)
            cubo_anio = c.rebanada(Hipercubo5D.DIM_ANIO, anio_int)
            tipos = self.productos_por_categoria(cubo_anio)
            resultado[anio_int] = {
                "GNC": int(tipos.get("GNC", 0)),
                "DTI": int(tipos.get("DTI", 0)),
                "ASC": int(tipos.get("ASC", 0)),
                "FRH": int(tipos.get("FRH", 0)),
            }
        return resultado

    def productos_por_validacion(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[str, int]:
        """Calcula los productos por estado de validación (Avalado, Con soporte, No avalado)."""
        c = cubo if cubo is not None else self.hipercubo
        bruto = c.enrollar(Hipercubo5D.DIM_VALIDACION)
        categorias_base = {"Avalado": 0, "Con soporte": 0, "No avalado": 0}
        for val, cnt in bruto.items():
            categorias_base[str(val)] = cnt
        return categorias_base

    def productos_por_grupo(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[str, int]:
        """Calcula la cantidad de productos asociados a cada grupo de investigación."""
        c = cubo if cubo is not None else self.hipercubo
        return c.enrollar(Hipercubo5D.DIM_GRUPO)

    def productos_por_investigador(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[str, int]:
        """Calcula la cantidad de productos vinculados a cada investigador."""
        c = cubo if cubo is not None else self.hipercubo
        return c.enrollar(Hipercubo5D.DIM_INVESTIGADOR)

    # =========================================================================
    # MÉTRICAS ESTADÍSTICAS DERIVADAS
    # =========================================================================

    def promedio_por_investigador(
        self,
        id_grupo: str | None = None,
        cubo: Hipercubo5D | None = None,
    ) -> float:
        """Calcula el promedio de productos activos por investigador (con redondeo a 2 decimales)."""
        c = cubo if cubo is not None else self.hipercubo
        if id_grupo is not None:
            c = c.rebanada(Hipercubo5D.DIM_GRUPO, id_grupo)

        conteo_inv = c.enrollar(Hipercubo5D.DIM_INVESTIGADOR)
        # Excluir la marca SIN_INVESTIGADOR si existe para el divisor
        invs_reales = [k for k in conteo_inv.keys() if k != "SIN_INVESTIGADOR"]
        total_invs = len(invs_reales)

        if total_invs == 0:
            return 0.0

        total_prods = c.total_productos_unicos()
        return round(total_prods / total_invs, 2)

    def top_5_investigadores(
        self,
        id_grupo: str | None = None,
        cubo: Hipercubo5D | None = None,
    ) -> list[tuple[str, int]]:
        """Retorna hasta 5 investigadores más productivos con desempate determinista alfabético."""
        c = cubo if cubo is not None else self.hipercubo
        if id_grupo is not None:
            c = c.rebanada(Hipercubo5D.DIM_GRUPO, id_grupo)

        conteo_inv = c.enrollar(Hipercubo5D.DIM_INVESTIGADOR)
        items = [(str(inv), int(cnt)) for inv, cnt in conteo_inv.items() if inv != "SIN_INVESTIGADOR"]

        # Desempate determinista: mayor conteo (-cnt), ante empate orden alfabético (+inv)
        items.sort(key=lambda t: (-t[1], t[0]))
        return items[:5]

    def top_5_grupos(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> list[tuple[str, int]]:
        """Retorna hasta 5 grupos con mayor producción con desempate determinista alfabético."""
        c = cubo if cubo is not None else self.hipercubo
        conteo_grp = c.enrollar(Hipercubo5D.DIM_GRUPO)
        items = [(str(grp), int(cnt)) for grp, cnt in conteo_grp.items() if grp != "SIN_GRUPO"]

        # Desempate determinista: mayor conteo (-cnt), ante empate orden alfabético (+grp)
        items.sort(key=lambda t: (-t[1], t[0]))
        return items[:5]

    def porcentajes_por_categoria(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[str, float]:
        """Calcula la distribución porcentual exacta de productos por categoría (redondeo 2 decimales)."""
        conteo = self.productos_por_categoria(cubo)
        total = sum(conteo.values())
        if total == 0:
            return {cat: 0.0 for cat in conteo}
        return {cat: round((cnt / total) * 100.0, 2) for cat, cnt in conteo.items()}

    def porcentajes_por_validacion(
        self,
        cubo: Hipercubo5D | None = None,
    ) -> dict[str, float]:
        """Calcula la distribución porcentual exacta por estado de validación (redondeo 2 decimales)."""
        conteo = self.productos_por_validacion(cubo)
        total = sum(conteo.values())
        if total == 0:
            return {val: 0.0 for val in conteo}
        return {val: round((cnt / total) * 100.0, 2) for val, cnt in conteo.items()}

    # =========================================================================
    # LAS TRES VISTAS ANALÍTICAS OFICIALES DE PEA-i
    # =========================================================================

    def obtener_vista_institucional(
        self,
        ventana_anios: int | None = None,
        modelo_2024: bool = False,
        anio_inicio: int | None = None,
        anio_fin: int | None = None,
    ) -> dict[str, Any]:
        """Vista 1: Vista Institucional General (Consolidado panorámico universitario)."""
        c = self._resolver_cubo(
            ventana_anios=ventana_anios, modelo_2024=modelo_2024, anio_inicio=anio_inicio, anio_fin=anio_fin
        )
        total_prods = c.total_productos_unicos()

        return {
            "tipo_vista": "institucional",
            "total_productos": total_prods,
            "productos_por_anio": self.productos_por_anio(c),
            "productos_por_categoria": self.productos_por_categoria(c),
            "porcentajes_categoria": self.porcentajes_por_categoria(c),
            "productos_por_validacion": self.productos_por_validacion(c),
            "porcentajes_validacion": self.porcentajes_por_validacion(c),
            "top_5_investigadores": self.top_5_investigadores(cubo=c),
            "top_5_grupos": self.top_5_grupos(cubo=c),
            "promedio_por_investigador": self.promedio_por_investigador(cubo=c),
        }

    def obtener_vista_grupo(
        self,
        id_grupo: str,
        ventana_anios: int | None = None,
        modelo_2024: bool = False,
        anio_inicio: int | None = None,
        anio_fin: int | None = None,
    ) -> dict[str, Any]:
        """Vista 2: Vista por Grupo de Investigación (Ficha analítica grupal)."""
        c_inst = self._resolver_cubo(
            ventana_anios=ventana_anios, modelo_2024=modelo_2024, anio_inicio=anio_inicio, anio_fin=anio_fin
        )
        c_grp = c_inst.rebanada(Hipercubo5D.DIM_GRUPO, id_grupo)

        total_grupo = c_grp.total_productos_unicos()
        total_inst = c_inst.total_productos_unicos()
        porcentaje_institucional = (
            round((total_grupo / total_inst) * 100.0, 2) if total_inst > 0 else 0.0
        )

        return {
            "tipo_vista": "grupo",
            "id_grupo": id_grupo,
            "total_productos": total_grupo,
            "porcentaje_sobre_institucion": porcentaje_institucional,
            "productos_por_anio": self.productos_por_anio(c_grp),
            "productos_por_categoria": self.productos_por_categoria(c_grp),
            "porcentajes_categoria": self.porcentajes_por_categoria(c_grp),
            "productos_por_validacion": self.productos_por_validacion(c_grp),
            "porcentajes_validacion": self.porcentajes_por_validacion(c_grp),
            "top_5_investigadores": self.top_5_investigadores(id_grupo=id_grupo, cubo=c_grp),
            "promedio_por_investigador": self.promedio_por_investigador(id_grupo=id_grupo, cubo=c_grp),
            "investigadores": self.productos_por_investigador(c_grp),
        }

    def obtener_vista_investigador(
        self,
        id_investigador: str,
        ventana_anios: int | None = None,
        modelo_2024: bool = False,
        anio_inicio: int | None = None,
        anio_fin: int | None = None,
    ) -> dict[str, Any]:
        """Vista 3: Vista por Investigador (Ficha analítica individual de autoría)."""
        c_inst = self._resolver_cubo(
            ventana_anios=ventana_anios, modelo_2024=modelo_2024, anio_inicio=anio_inicio, anio_fin=anio_fin
        )
        c_inv = c_inst.rebanada(Hipercubo5D.DIM_INVESTIGADOR, id_investigador)

        total_inv = c_inv.total_productos_unicos()
        grupos_conteo = c_inv.enrollar(Hipercubo5D.DIM_GRUPO)

        # Calcular porcentaje de contribución a cada grupo
        contribuciones_grupos: dict[str, dict[str, Any]] = {}
        for grp, cnt in grupos_conteo.items():
            if grp == "SIN_GRUPO":
                continue
            c_grupo = c_inst.rebanada(Hipercubo5D.DIM_GRUPO, grp)
            tot_grp = c_grupo.total_productos_unicos()
            pct = round((cnt / tot_grp) * 100.0, 2) if tot_grp > 0 else 0.0
            contribuciones_grupos[grp] = {
                "productos_propios_en_grupo": cnt,
                "total_productos_grupo": tot_grp,
                "porcentaje_aporte": pct,
            }

        return {
            "tipo_vista": "investigador",
            "id_investigador": id_investigador,
            "total_productos": total_inv,
            "productos_por_anio": self.productos_por_anio(c_inv),
            "productos_por_categoria": self.productos_por_categoria(c_inv),
            "porcentajes_categoria": self.porcentajes_por_categoria(c_inv),
            "productos_por_validacion": self.productos_por_validacion(c_inv),
            "porcentajes_validacion": self.porcentajes_por_validacion(c_inv),
            "grupos_participacion": grupos_conteo,
            "contribuciones_grupos": contribuciones_grupos,
        }
