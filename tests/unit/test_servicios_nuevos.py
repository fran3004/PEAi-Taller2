"""Pruebas unitarias de los nuevos servicios analíticos y de gestión de ServicioAplicacion.

Cubre:
1. serie_anual_por_categoria: suma idéntica a productos_por_anio, filtros, vacío y grupo inexistente.
2. red_coautoria: cálculo desde Multilista, Brandes determinista, umbral min_coautorias,
   inclusión de coautores externos, vacío y un solo nodo.
3. actualizar_producto: edición de campos, cambio de grupo, validaciones, deshacer
   y compensación en memoria ante fallo de persistencia remota.
4. Datos para fichas: estudiantes del grupo, productos avalados, años con producción,
   coautores del investigador y aporte institucional del grupo.
"""

import pytest
import responses

from pea.cliente_http import ClienteHTTPSupabase
from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.excepciones import ErrorPEA, ErrorValidacion, RecursoNoEncontrado
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_dominio import CatalogoInvestigacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios

# =============================================================================
# 1. SERIE ANUAL POR CATEGORÍA
# =============================================================================


def test_serie_anual_por_categoria_vacio() -> None:
    app = ServicioAplicacion()
    serie = app.serie_anual_por_categoria(FiltroAnios())
    assert serie == {}


def test_serie_anual_por_categoria_grupo_inexistente() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()
    with pytest.raises(RecursoNoEncontrado):
        app.serie_anual_por_categoria(FiltroAnios(), codigo_grupo="GRP-NO-EXISTE")


def test_serie_anual_por_categoria_coincide_con_productos_por_anio() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()

    # Probar con distintos filtros: todos, ventana 5 años y modelo 2024
    filtros = [
        FiltroAnios(modo=ModoFiltroAnios.TODOS),
        FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=5),
        FiltroAnios(modo=ModoFiltroAnios.MODELO_2024),
    ]

    for f in filtros:
        resumen = app.resumen_general(f)
        productos_por_anio = resumen["productos_por_anio"]
        serie = app.serie_anual_por_categoria(f)

        # Mismos años reportados
        assert set(serie.keys()) == set(productos_por_anio.keys())

        # La suma de las 4 tipologías en cada año debe ser idéntica al conteo anual
        for anio, conteo_esperado in productos_por_anio.items():
            tipos = serie[anio]
            assert set(tipos.keys()) == {"GNC", "DTI", "ASC", "FRH"}
            assert sum(tipos.values()) == conteo_esperado


def test_serie_anual_por_categoria_con_filtro_grupo() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()
    filtro = FiltroAnios(modo=ModoFiltroAnios.TODOS)

    vg = app.vista_grupo("PRUEBA-GRP-001", filtro)
    prod_anio_grupo = vg["productos_por_anio"]

    serie_grupo = app.serie_anual_por_categoria(filtro, codigo_grupo="PRUEBA-GRP-001")
    assert set(serie_grupo.keys()) == set(prod_anio_grupo.keys())
    for anio, conteo_esperado in prod_anio_grupo.items():
        assert sum(serie_grupo[anio].values()) == conteo_esperado


# =============================================================================
# 2. RED DE COAUTORÍA
# =============================================================================


def test_red_coautoria_vacio() -> None:
    app = ServicioAplicacion()
    red = app.red_coautoria(FiltroAnios())
    assert red["resumen"]["investigadores"] == 0
    assert red["resumen"]["vinculos"] == 0
    assert red["resumen"]["densidad"] == 0.0
    assert len(red["nodos"]) == 0
    assert len(red["aristas"]) == 0


def test_red_coautoria_un_solo_nodo() -> None:
    app = ServicioAplicacion()
    cat = app._catalogo

    inv = Investigador(codigo_rh="INV-SOLO-1", nombre_completo="Investigador Solitario", categoria="Junior")
    cat.crear_investigador(inv, persistir=False)
    prod = Producto(
        codigo_identificador="P-SOLO-1",
        titulo="Monografía Individual",
        tipo_mayor="GNC",
        ano=2024,
    )
    cat.crear_producto(prod, codigos_rh_autores=["INV-SOLO-1"], persistir=False)

    red = app.red_coautoria(FiltroAnios(), min_coautorias=1)
    assert red["resumen"]["investigadores"] == 1
    assert red["resumen"]["vinculos"] == 0
    assert red["resumen"]["densidad"] == 0.0

    nodo = red["nodos"][0]
    assert nodo["codigo"] == "INV-SOLO-1"
    assert nodo["grado"] == 0
    assert nodo["intermediacion"] == 0.0


def test_red_coautoria_grupo_inexistente() -> None:
    app = ServicioAplicacion()
    with pytest.raises(RecursoNoEncontrado):
        app.red_coautoria(FiltroAnios(), codigo_grupo="GRP-FANTASMA")


def test_red_coautoria_algoritmo_brandes_linea() -> None:
    """En un grafo línea A-B-C, B tiene centralidad de intermediación 1.0 (máxima)."""
    app = ServicioAplicacion()
    cat = app._catalogo

    for cod, nom in [("A", "Investigador A"), ("B", "Investigador B"), ("C", "Investigador C")]:
        cat.crear_investigador(Investigador(codigo_rh=cod, nombre_completo=nom), persistir=False)

    # Coautoría A con B (2 productos)
    for i in range(2):
        cat.crear_producto(
            Producto(codigo_identificador=f"P-AB-{i}", titulo=f"Prod AB {i}", tipo_mayor="GNC", ano=2024),
            codigos_rh_autores=["A", "B"],
            persistir=False,
        )

    # Coautoría B con C (2 productos)
    for i in range(2):
        cat.crear_producto(
            Producto(codigo_identificador=f"P-BC-{i}", titulo=f"Prod BC {i}", tipo_mayor="DTI", ano=2024),
            codigos_rh_autores=["B", "C"],
            persistir=False,
        )

    red = app.red_coautoria(FiltroAnios(), min_coautorias=2)
    assert red["resumen"]["investigadores"] == 3
    assert red["resumen"]["vinculos"] == 2
    # Densidad 2*2 / (3*2) = 4/6 = 0.6667
    assert red["resumen"]["densidad"] == pytest.approx(0.6667, rel=1e-3)

    nodos_por_cod = {n["codigo"]: n for n in red["nodos"]}
    assert nodos_por_cod["B"]["grado"] == 2
    assert nodos_por_cod["B"]["intermediacion"] == 1.0
    assert nodos_por_cod["A"]["grado"] == 1
    assert nodos_por_cod["A"]["intermediacion"] == 0.0
    assert nodos_por_cod["C"]["grado"] == 1
    assert nodos_por_cod["C"]["intermediacion"] == 0.0


def test_red_coautoria_filtro_grupo_e_investigadores_externos() -> None:
    app = ServicioAplicacion()
    cat = app._catalogo

    grp = Grupo(codigo_gruplac="GRP-100", nombre="Grupo Principal")
    cat.crear_grupo(grp, persistir=False)

    inv_interno = Investigador(codigo_rh="INV-INT", nombre_completo="Investigador Interno")
    inv_externo = Investigador(codigo_rh="INV-EXT", nombre_completo="Investigador Externo")
    cat.crear_investigador(inv_interno, persistir=False)
    cat.crear_investigador(inv_externo, persistir=False)

    cat.vincular_integrante("GRP-100", "INV-INT", rol="Investigador", persistir=False)

    # Producto del grupo con coautoría interno + externo (2 productos)
    for i in range(2):
        cat.crear_producto(
            Producto(codigo_identificador=f"P-GRP-{i}", titulo=f"Prod Grp {i}", tipo_mayor="GNC", ano=2024),
            codigo_gruplac="GRP-100",
            codigos_rh_autores=["INV-INT", "INV-EXT"],
            persistir=False,
        )

    red = app.red_coautoria(FiltroAnios(), codigo_grupo="GRP-100", min_coautorias=2)
    assert red["resumen"]["investigadores"] == 2
    assert red["resumen"]["vinculos"] == 1

    nodos_map = {n["codigo"]: n for n in red["nodos"]}
    assert not nodos_map["INV-INT"]["es_externo"]
    assert nodos_map["INV-EXT"]["es_externo"]


# =============================================================================
# 3. ACTUALIZAR PRODUCTO, VALIDACIONES Y DESHACER
# =============================================================================


def test_actualizar_producto_edicion_campos_y_deshacer() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()

    detalle_orig = app.detalle_producto("PRUEBA-PROD-001")
    assert detalle_orig["titulo"] != "Título Modificado"

    # Editar campos escalares
    msg = app.actualizar_producto(
        "PRUEBA-PROD-001",
        {
            "titulo": "Título Modificado",
            "tipologia": "DTI",
            "subtipo": "Software Registrado",
            "anio": 2023,
            "validacion": "Avalado",
        },
    )
    assert "PRUEBA-PROD-001 actualizado" in msg

    editado = app.detalle_producto("PRUEBA-PROD-001")
    assert editado["titulo"] == "Título Modificado"
    assert editado["tipo_mayor"] == "DTI"
    assert editado["subtipo"] == "Software Registrado"
    assert editado["ano"] == 2023
    assert editado["validacion"] == "Avalado"

    # Deshacer edición
    msg_undo = app.deshacer()
    assert "Deshecho" in msg_undo

    restaurado = app.detalle_producto("PRUEBA-PROD-001")
    assert restaurado["titulo"] == detalle_orig["titulo"]
    assert restaurado["tipo_mayor"] == detalle_orig["tipo_mayor"]
    assert restaurado["subtipo"] == detalle_orig["subtipo"]
    assert restaurado["ano"] == detalle_orig["ano"]
    assert restaurado["validacion"] == detalle_orig["validacion"]


def test_actualizar_producto_cambio_de_grupo_y_deshacer() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()

    detalle_orig = app.detalle_producto("PRUEBA-PROD-001")
    grupo_orig_nombre = detalle_orig["grupo"]

    # Reasignar a PRUEBA-GRP-002
    app.actualizar_producto("PRUEBA-PROD-001", {"codigo_grupo": "PRUEBA-GRP-002"})
    assert app.detalle_producto("PRUEBA-PROD-001")["grupo"] == "Grupo Ficticio de Ciencias Agropecuarias"

    # Deshacer cambio de grupo
    app.deshacer()
    assert app.detalle_producto("PRUEBA-PROD-001")["grupo"] == grupo_orig_nombre


def test_actualizar_producto_validaciones() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()

    # Producto inexistente
    with pytest.raises(RecursoNoEncontrado):
        app.actualizar_producto("P-INEXISTENTE", {"titulo": "Nuevo"})

    # Título vacío
    with pytest.raises(ErrorValidacion):
        app.actualizar_producto("PRUEBA-PROD-001", {"titulo": "   "})

    # Tipología inválida
    with pytest.raises(ErrorValidacion):
        app.actualizar_producto("PRUEBA-PROD-001", {"tipo_mayor": "INVALIDA"})

    # Validación inválida
    with pytest.raises(ErrorValidacion):
        app.actualizar_producto("PRUEBA-PROD-001", {"estado_validacion": "Rechazado"})

    # Año fuera de rango
    with pytest.raises(ErrorValidacion):
        app.actualizar_producto("PRUEBA-PROD-001", {"ano": 1850})

    # Grupo inexistente
    with pytest.raises(RecursoNoEncontrado):
        app.actualizar_producto("PRUEBA-PROD-001", {"codigo_grupo": "GRP-INVENTADO"})


@responses.activate
def test_actualizar_producto_compensacion_fallo_persistencia() -> None:
    cliente = ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key")
    catalogo = CatalogoInvestigacion(cliente=cliente)

    prod = Producto(
        id=10,
        codigo_identificador="P-TX-01",
        titulo="Título Original",
        tipo_mayor="GNC",
        ano=2024,
    )
    catalogo.crear_producto(prod, persistir=False)
    catalogo.pila_deshacer.limpiar()

    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/rpc/obtener_revision_actual",
        json=1,
        status=200,
    )
    # Simular fallo en el PATCH remoto de Supabase
    responses.add(
        responses.PATCH,
        "https://ejemplo.supabase.co/rest/v1/productos",
        status=500,
        json={"error": "Fallo en base de datos"},
    )

    with pytest.raises(ErrorPEA):
        catalogo.actualizar_producto("P-TX-01", {"titulo": "Título Fallido"}, persistir=True)

    # Compensación: el título debe haberse revertido al original
    prod_mem = catalogo.buscar_producto("P-TX-01")
    assert prod_mem is not None
    assert prod_mem.titulo == "Título Original"
    assert catalogo.pila_deshacer.esta_vacia()


# =============================================================================
# 4. DATOS PARA FICHAS Y MÉTRICAS
# =============================================================================


def test_datos_fichas_metricas_completas() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()
    filtro = FiltroAnios()

    # Vincular un estudiante para verificar conteo
    inv_est = Investigador(codigo_rh="PRUEBA-INV-EST", nombre_completo="Estudiante Prueba")
    app._catalogo.crear_investigador(inv_est, persistir=False)
    app.vincular_integrante("PRUEBA-GRP-001", "PRUEBA-INV-EST", rol="Estudiante")

    # Ficha de grupo
    fg = app.datos_ficha_grupo("PRUEBA-GRP-001", filtro)
    assert fg["codigo"] == "PRUEBA-GRP-001"
    assert fg["total_productos"] > 0
    assert fg["productos_avalados"] >= 0
    assert fg["estudiantes"] == 1
    assert fg["porcentaje_sobre_institucion"] > 0

    # Ficha de investigador
    fi = app.datos_ficha_investigador("PRUEBA-INV-001", filtro)
    assert fi["codigo"] == "PRUEBA-INV-001"
    assert fi["total_productos"] > 0
    assert fi["productos_avalados"] >= 0
    assert fi["anios_con_produccion"] > 0
    assert fi["coautores"] >= 0
