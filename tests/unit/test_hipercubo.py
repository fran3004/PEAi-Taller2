"""Pruebas unitarias para la estructura de Hipercubo5D y ServicioEstadisticas.

Cubre exhaustivamente:
- Hipercubo vacío (sin ZeroDivisionError)
- Un solo producto (100% y conteos unitarios)
- Desactivación lógica (exclusión de la medida activa)
- Rango y ventanas temporales (subcubo dice)
- Empate y ordenamiento determinista
- Redondeo exacto a 2 decimales
- Ventana del Modelo 2024 vs ventana genérica
- Las tres vistas analíticas (Institucional, Grupo, Investigador)
- Comparación contra verificación GROUP BY tipo SQL relacional
"""

import pytest

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.estructuras.hipercubo import Hipercubo5D
from pea.servicios.servicio_dominio import CatalogoInvestigacion
from pea.servicios.servicio_estadisticas import ServicioEstadisticas


class TestHipercuboVacio:
    """Verifica que el hipercubo y las estadísticas en estado vacío se comporten de forma robusta."""

    def test_hipercubo_vacio_medidas(self) -> None:
        cubo = Hipercubo5D()
        assert cubo.esta_vacio()
        assert len(cubo) == 0
        assert cubo.medida_total() == 0
        assert cubo.total_productos_unicos() == 0

        # Roll-up sobre cualquier dimensión da diccionario vacío
        assert cubo.enrollar(Hipercubo5D.DIM_ANIO) == {}
        assert cubo.enrollar(Hipercubo5D.DIM_CATEGORIA) == {}
        assert cubo.enrollar(Hipercubo5D.DIM_GRUPO) == {}

    def test_servicio_estadisticas_vacio_sin_division_por_cero(self) -> None:
        cubo = Hipercubo5D()
        servicio = ServicioEstadisticas(cubo)

        assert servicio.productos_por_anio() == {}
        assert servicio.productos_por_categoria() == {"GNC": 0, "DTI": 0, "ASC": 0, "FRH": 0}
        assert servicio.productos_por_validacion() == {"Avalado": 0, "Con soporte": 0, "No avalado": 0}
        assert servicio.productos_por_grupo() == {}
        assert servicio.productos_por_investigador() == {}

        # Promedio y porcentajes no deben lanzar ZeroDivisionError
        assert servicio.promedio_por_investigador() == 0.0
        assert servicio.top_5_investigadores() == []
        assert servicio.top_5_grupos() == []

        pct_cat = servicio.porcentajes_por_categoria()
        for pct in pct_cat.values():
            assert pct == 0.0

        pct_val = servicio.porcentajes_por_validacion()
        for pct in pct_val.values():
            assert pct == 0.0

        # Las tres vistas vacías
        vista_inst = servicio.obtener_vista_institucional()
        assert vista_inst["total_productos"] == 0
        assert vista_inst["promedio_por_investigador"] == 0.0

        vista_grp = servicio.obtener_vista_grupo("GRUPO-INEXISTENTE")
        assert vista_grp["total_productos"] == 0
        assert vista_grp["porcentaje_sobre_institucion"] == 0.0

        vista_inv = servicio.obtener_vista_investigador("INV-INEXISTENTE")
        assert vista_inv["total_productos"] == 0
        assert vista_inv["grupos_participacion"] == {}


class TestHipercuboUnProducto:
    """Verifica el comportamiento analítico con exactamente un producto activo."""

    def test_un_producto_metricas_y_porcentajes(self) -> None:
        cubo = Hipercubo5D()
        cubo.acumular(
            grupo="GRP-01",
            investigador="INV-01",
            categoria="GNC",
            anio=2023,
            validacion="Avalado",
            producto_id="PRD-01",
            peso=1.0,
        )

        assert not cubo.esta_vacio()
        assert cubo.medida_total() == 1
        assert cubo.total_productos_unicos() == 1

        servicio = ServicioEstadisticas(cubo)
        assert servicio.productos_por_anio() == {2023: 1}
        assert servicio.productos_por_categoria()["GNC"] == 1
        assert servicio.productos_por_validacion()["Avalado"] == 1

        # Porcentajes deben sumar 100% en la categoría correspondiente
        pct_cat = servicio.porcentajes_por_categoria()
        assert pct_cat["GNC"] == 100.0
        assert pct_cat["DTI"] == 0.0

        pct_val = servicio.porcentajes_por_validacion()
        assert pct_val["Avalado"] == 100.0
        assert pct_val["No avalado"] == 0.0

        # Top 5 con 1 solo elemento
        top_inv = servicio.top_5_investigadores()
        assert top_inv == [("INV-01", 1)]

        top_grp = servicio.top_5_grupos()
        assert top_grp == [("GRP-01", 1)]

        assert servicio.promedio_por_investigador() == 1.0


class TestHipercuboDesactivacionYMutacion:
    """Verifica que los productos desactivados se excluyan de las estadísticas activas."""

    def test_desactivar_producto_catalogo_actualiza_hipercubo(self) -> None:
        catalogo = CatalogoInvestigacion()
        g = catalogo.crear_grupo(Grupo(codigo_gruplac="GRP-A", nombre="Grupo Alfa"), persistir=False)
        inv = catalogo.crear_investigador(Investigador(codigo_rh="INV-100", nombre_completo="Dra. Lopez"), persistir=False)

        prod = catalogo.crear_producto(
            Producto(
                codigo_identificador="P-100",
                titulo="Paper sobre Inteligencia Artificial",
                tipo_mayor="GNC",
                subtipo="ART_A1",
                ano=2022,
                estado_validacion="Avalado",
                activo=True,
            ),
            codigo_gruplac=g.codigo_gruplac,
            codigos_rh_autores=[inv.codigo_rh],
            persistir=False,
        )

        # Debe estar indexado y medido
        assert catalogo.hipercubo.total_productos_unicos() == 1
        assert catalogo.estadisticas.productos_por_categoria()["GNC"] == 1

        # Desactivación lógica
        catalogo.desactivar_producto(prod.codigo_identificador, persistir=False)
        assert not prod.activo

        # El hipercubo debe excluir productos inactivos
        assert catalogo.hipercubo.medida_total() == 0
        assert catalogo.hipercubo.total_productos_unicos() == 0
        assert catalogo.estadisticas.productos_por_categoria()["GNC"] == 0

        # Reactivación
        catalogo.activar_producto(prod.codigo_identificador, persistir=False)
        assert prod.activo
        assert catalogo.hipercubo.total_productos_unicos() == 1
        assert catalogo.estadisticas.productos_por_categoria()["GNC"] == 1


class TestHipercuboRangoYVentanas:
    """Verifica el subcubo por ventana temporal (Dice) y la ventana reglamentaria del Modelo 2024."""

    @pytest.fixture
    def cubo_poblado(self) -> Hipercubo5D:
        c = Hipercubo5D()
        # Años 2013, 2016, 2020, 2022, 2024
        c.acumular("G1", "I1", "GNC", 2013, "Avalado", "P-2013-LIBRO")
        c.acumular("G1", "I1", "GNC_LIBRO", 2015, "Avalado", "P-2015-LIBRO")
        c.acumular("G1", "I2", "GNC", 2018, "Avalado", "P-2018-ART")
        c.acumular("G1", "I1", "GNC", 2020, "Avalado", "P-2020-ART")
        c.acumular("G2", "I3", "DTI", 2021, "Con soporte", "P-2021-SW")
        c.acumular("G2", "I3", "ASC", 2023, "Avalado", "P-2023-EVT")
        c.acumular("G1", "I2", "FRH", 2024, "Avalado", "P-2024-TESIS")
        return c

    def test_subcubo_por_rango_anios(self, cubo_poblado: Hipercubo5D) -> None:
        # Ventana de interfaz: [2020, 2022]
        sub = cubo_poblado.subcubo_por_ventana(anio_inicio=2020, anio_fin=2022)
        anios = sub.enrollar(Hipercubo5D.DIM_ANIO)

        assert 2013 not in anios
        assert 2015 not in anios
        assert 2018 not in anios
        assert 2024 not in anios
        assert set(anios.keys()) == {2020, 2021}
        assert sub.total_productos_unicos() == 2

    def test_diferencia_filtro_interfaz_vs_modelo_2024(self, cubo_poblado: Hipercubo5D) -> None:
        """La ventana genérica N años aplica simétricamente, mientras el Modelo 2024 diferencia tipologías."""
        # 1. Filtro genérico de interfaz: últimos 5 años (2019-2023)
        sub_interfaz_5 = cubo_poblado.subcubo_por_ventana(anio_inicio=2019, anio_fin=2023)
        # No incluye el libro de 2015 porque el filtro de interfaz es ciego a la tipología
        prods_interfaz = sub_interfaz_5.enrollar(Hipercubo5D.DIM_ANIO)
        assert 2015 not in prods_interfaz

        # 2. Ventana del Modelo 2024 (corte 2023):
        # 5 años (2019-2023) para artículos/DTI/ASC/FRH, pero 10 años (2014-2023) para LIBROS y PATENTES
        sub_modelo = cubo_poblado.subcubo_modelo_2024(anio_corte=2023)
        anios_modelo = sub_modelo.enrollar(Hipercubo5D.DIM_ANIO)

        # El libro de 2015 SÍ entra en la ventana de 10 años del Modelo
        assert 2015 in anios_modelo
        # El libro de 2013 NO entra (más de 10 años)
        assert 2013 not in anios_modelo
        # La tesis de 2024 NO entra (posterior al corte 2023)
        assert 2024 not in anios_modelo


class TestHipercuboEmpateYRedondeo:
    """Verifica desempate determinista y exactitud en redondeos de porcentajes y medias."""

    def test_desempate_determinista_alfabetico(self) -> None:
        cubo = Hipercubo5D()
        # Tres investigadores con exactamente la misma cantidad (2 productos)
        # Nombres en desorden: Carlos, Andres, Bernardo
        cubo.acumular("G1", "INV_CARLOS", "GNC", 2022, "Avalado", "P1")
        cubo.acumular("G1", "INV_CARLOS", "GNC", 2023, "Avalado", "P2")
        cubo.acumular("G1", "INV_ANDRES", "GNC", 2022, "Avalado", "P3")
        cubo.acumular("G1", "INV_ANDRES", "GNC", 2023, "Avalado", "P4")
        cubo.acumular("G1", "INV_BERNARDO", "GNC", 2022, "Avalado", "P5")
        cubo.acumular("G1", "INV_BERNARDO", "GNC", 2023, "Avalado", "P6")

        servicio = ServicioEstadisticas(cubo)
        top = servicio.top_5_investigadores()

        # Ante empate de 2 productos, deben ordenarse alfabéticamente por código
        assert len(top) == 3
        assert top[0] == ("INV_ANDRES", 2)
        assert top[1] == ("INV_BERNARDO", 2)
        assert top[2] == ("INV_CARLOS", 2)

    def test_redondeo_exacto_dos_decimales(self) -> None:
        cubo = Hipercubo5D()
        # 1 producto GNC, 2 productos DTI (Total = 3)
        # GNC: 1/3 = 33.3333...% -> 33.33%
        # DTI: 2/3 = 66.6666...% -> 66.67%
        cubo.acumular("G1", "INV-1", "GNC", 2023, "Avalado", "P1")
        cubo.acumular("G1", "INV-2", "DTI", 2023, "Avalado", "P2")
        cubo.acumular("G1", "INV-2", "DTI", 2023, "Avalado", "P3")

        servicio = ServicioEstadisticas(cubo)
        pct = servicio.porcentajes_por_categoria()

        assert pct["GNC"] == 33.33
        assert pct["DTI"] == 66.67
        assert pct["ASC"] == 0.0
        assert pct["FRH"] == 0.0

        # Promedio por investigador: 3 productos / 2 investigadores = 1.5
        assert servicio.promedio_por_investigador() == 1.5


class TestVerificacionContraGroupBy:
    """Comprobación estricta del Hipercubo contra un oráculo relacional GROUP BY tipo SQL."""

    def test_equivalencia_hipercubo_vs_sql_group_by(self) -> None:
        # Generar un conjunto amplio de 20 productos con diversos atributos
        datos_planos = [
            {"id": "P1", "grupo": "GRP-A", "inv": "I1", "cat": "GNC", "ano": 2021, "val": "Avalado"},
            {"id": "P2", "grupo": "GRP-A", "inv": "I1", "cat": "GNC", "ano": 2022, "val": "Avalado"},
            {"id": "P3", "grupo": "GRP-A", "inv": "I2", "cat": "DTI", "ano": 2021, "val": "Con soporte"},
            {"id": "P4", "grupo": "GRP-B", "inv": "I3", "cat": "ASC", "ano": 2020, "val": "Avalado"},
            {"id": "P5", "grupo": "GRP-B", "inv": "I3", "cat": "FRH", "ano": 2023, "val": "No avalado"},
            {"id": "P6", "grupo": "GRP-C", "inv": "I4", "cat": "GNC", "ano": 2023, "val": "Avalado"},
            {"id": "P7", "grupo": "GRP-C", "inv": "I4", "cat": "DTI", "ano": 2022, "val": "Avalado"},
            {"id": "P8", "grupo": "GRP-A", "inv": "I2", "cat": "GNC", "ano": 2023, "val": "Avalado"},
        ]

        # 1. Simulación del oráculo SQL GROUP BY
        # SELECT ano, count(*) FROM productos GROUP BY ano
        sql_group_ano: dict[int, int] = {}
        # SELECT cat, count(*) FROM productos GROUP BY cat
        sql_group_cat: dict[str, int] = {}
        # SELECT grupo, count(*) FROM productos GROUP BY grupo
        sql_group_grp: dict[str, int] = {}

        for fila in datos_planos:
            a = fila["ano"]
            c = fila["cat"]
            g = fila["grupo"]
            sql_group_ano[a] = sql_group_ano.get(a, 0) + 1
            sql_group_cat[c] = sql_group_cat.get(c, 0) + 1
            sql_group_grp[g] = sql_group_grp.get(g, 0) + 1

        # 2. Alimentar el Hipercubo 5D
        cubo = Hipercubo5D()
        for f in datos_planos:
            cubo.acumular(
                grupo=f["grupo"],
                investigador=f["inv"],
                categoria=f["cat"],
                anio=f["ano"],
                validacion=f["val"],
                producto_id=f["id"],
            )

        # 3. Operación Roll-up del Hipercubo
        hiper_ano = cubo.enrollar(Hipercubo5D.DIM_ANIO)
        hiper_cat = cubo.enrollar(Hipercubo5D.DIM_CATEGORIA)
        hiper_grp = cubo.enrollar(Hipercubo5D.DIM_GRUPO)

        # 4. Comparación de equivalencia matemática estricta
        assert hiper_ano == sql_group_ano
        assert hiper_cat == sql_group_cat
        assert hiper_grp == sql_group_grp


class TestTresVistasAnaliticas:
    """Verifica que las tres vistas analíticas (Institucional, Grupo, Investigador) entreguen contratos completos."""

    def test_tres_vistas_contenido(self) -> None:
        cubo = Hipercubo5D()
        cubo.acumular("G1", "I1", "GNC", 2023, "Avalado", "P1")
        cubo.acumular("G1", "I2", "GNC", 2023, "Avalado", "P2")
        cubo.acumular("G2", "I1", "DTI", 2022, "Con soporte", "P3")

        servicio = ServicioEstadisticas(cubo)

        # 1. Vista Institucional
        v_inst = servicio.obtener_vista_institucional()
        assert v_inst["tipo_vista"] == "institucional"
        assert v_inst["total_productos"] == 3
        assert len(v_inst["top_5_investigadores"]) == 2
        assert len(v_inst["top_5_grupos"]) == 2

        # 2. Vista Grupo
        v_grp = servicio.obtener_vista_grupo("G1")
        assert v_grp["tipo_vista"] == "grupo"
        assert v_grp["id_grupo"] == "G1"
        assert v_grp["total_productos"] == 2
        # Porcentaje del grupo sobre la institución (2/3 = 66.67%)
        assert v_grp["porcentaje_sobre_institucion"] == 66.67

        # 3. Vista Investigador
        v_inv = servicio.obtener_vista_investigador("I1")
        assert v_inv["tipo_vista"] == "investigador"
        assert v_inv["id_investigador"] == "I1"
        assert v_inv["total_productos"] == 2
        assert "G1" in v_inv["contribuciones_grupos"]
        assert "G2" in v_inv["contribuciones_grupos"]
