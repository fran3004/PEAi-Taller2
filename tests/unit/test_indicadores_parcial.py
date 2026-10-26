import copy
import json
import math
from pathlib import Path

import pytest

from pea.datos.archivo_local import cargar_archivo, guardar_archivo, restaurar_catalogo, serializar_catalogo
from pea.servicios.indicadores import (
    aplicar_estimacion,
    calcular_indicador,
    categoria_estimada,
    modelo,
    puntaje_producto,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import ModoConexion

EJEMPLO = Path(__file__).parents[2] / "datos/ejemplo-parcial.json"


@pytest.fixture
def datos():
    return json.loads(EJEMPLO.read_text(encoding="utf-8"))


def test_pesos_originales_y_categorias():
    reglas = {r["codigo"]: r for r in modelo()["categorias"]}
    assert len(reglas) == 169
    for codigo, tipo, relativo, puntos in [
        ("ART_A2", "GNC", 5.5, 550),
        ("CAP_LIB_B", "GNC", 8, 480),
        ("PA1", "GNC", 10, 5000),
        ("MA1", "GNC", 6, 3000),
        ("SF", "DTI", 8, 280),
        ("TD_B", "FRH", 5, 800),
    ]:
        p = puntaje_producto({"subtipo": codigo, "tipo_mayor": tipo})
        assert p["peso_relativo"] == relativo
        assert p["puntaje"] == puntos
    assert reglas["ART_A2"]["ventana"] == 7
    assert reglas["CAP_LIB_B"]["ventana"] == 5
    assert reglas["PA1"]["ventana"] == 10
    assert puntaje_producto({"subtipo": "Artículo", "tipo_mayor": "GNC"})["puntaje"] is None
    assert puntaje_producto({"subtipo": "ART_A1", "tipo_mayor": "DTI"})["puntaje"] is None


def test_formula_agrupa_subtipo_sin_duplicar_coautoria(datos):
    r = calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023)
    assert r["brutos"]["Nc.Top"] == pytest.approx(550 * math.log1p(2 / 7))
    assert r["brutos"]["Nc.B"] == pytest.approx(280 * math.log1p(1 / 5))
    assert r["brutos"]["Cohe"] == pytest.approx(1 / 3)
    assert r["brutos"]["Coop"] == pytest.approx(1 / 3)
    assert len(r["incluidos"]) == 3
    assert len(r["excluidos"]) == 2
    assert r["indicador"] == pytest.approx(4.5)
    assert not r["completo"]


def test_investigador_y_ventanas_y_desactivacion(datos):
    r = calcular_indicador(datos, "investigador", "PRUEBA-I1", 2023)
    assert len(r["incluidos"]) == 3
    assert r["brutos"]["Cohe"] == pytest.approx(2 / 3)
    recorte = calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, 2023)
    assert len(recorte["incluidos"]) == 2
    assert recorte["brutos"]["Nc.Top"] == pytest.approx(550 * math.log(2))
    datos["productos"][0]["activo"] = False
    assert len(calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023)["incluidos"]) == 2


def test_referencia_externa_verifica_periodo_y_maximos(datos):
    r = calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023)
    ref = {
        "fuente": "Población de prueba",
        "corte": 2023,
        "desde": None,
        "maximos": {k: 2 * v for k, v in r["maximos"].items()},
    }
    assert calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, referencia=ref)["indicador"] == pytest.approx(2.25)
    for invalido in [-1, float("nan"), True, "5"]:
        malo = copy.deepcopy(ref)
        malo["maximos"]["Nc.Top"] = invalido
        with pytest.raises(ValueError):
            calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, referencia=malo)
    ref["corte"] = 2022
    with pytest.raises(ValueError):
        calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, referencia=ref)


def test_archivo_reconstruye_nodos_compartidos_y_rechaza_huerfanos(datos, tmp_path):
    cat = restaurar_catalogo(datos)
    ruta = tmp_path / "catálogo.json"
    guardar_archivo(ruta, serializar_catalogo(cat))
    recuperado = cargar_archivo(ruta)
    assert serializar_catalogo(recuperado) == serializar_catalogo(cat)
    nodo = recuperado.multilista_productos.buscar_nodo("PRUEBA-P1")
    assert nodo.grupo is recuperado.buscar_grupo("PRUEBA-G1")
    assert next(iter(nodo.autores)) is recuperado.buscar_investigador("PRUEBA-I1")
    datos["relaciones"][0]["autores"].append("NO-EXISTE")
    with pytest.raises(ValueError):
        restaurar_catalogo(datos)


def test_modo_local_edicion_clasificacion_persistencia_y_undo(tmp_path):
    servicio = ServicioAplicacion()
    servicio.iniciar_local(str(EJEMPLO))
    assert servicio.estado().modo == ModoConexion.LOCAL
    assert servicio.estado().escritura_permitida
    servicio.clasificar_producto("PRUEBA-P4", "ART_A1")
    assert servicio._catalogo.buscar_producto("PRUEBA-P4").detalles["categoria_minciencias"] == "ART_A1"
    servicio.deshacer()
    assert "categoria_minciencias" not in servicio._catalogo.buscar_producto("PRUEBA-P4").detalles
    ruta = tmp_path / "salida.json"
    servicio.guardar_local(str(ruta))
    assert cargar_archivo(ruta).buscar_producto("PRUEBA-P4") is not None
    ruta.write_text('{"formato":"otro"}', encoding="utf-8")
    with pytest.raises(ValueError):
        servicio.iniciar_local(str(ruta))
    assert servicio._catalogo.buscar_producto("PRUEBA-P4") is not None


def test_estimacion_es_opcional_declarada_y_no_pisa_categorias_informadas(datos):
    estricto = calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023)
    assert not estricto["estimado"] and estricto["estimadas"] == []
    estimado = calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, estimar=True)
    # Solo PRUEBA-P4 («Artículo» sin cuartil) recibe la categoría base ART_D (5 × 9 = 45).
    assert estimado["estimado"] and not estimado["completo"]
    assert [e["codigo"] for e in estimado["estimadas"]] == ["PRUEBA-P4"]
    assert estimado["estimadas"][0]["categoria"] == "ART_D"
    assert len(estimado["incluidos"]) == 4 and len(estimado["excluidos"]) == 1
    assert estimado["brutos"]["Nc.B"] == pytest.approx((280 + 45) * math.log1p(1 / 5))
    assert estimado["brutos"]["Nc.Top"] == estricto["brutos"]["Nc.Top"]
    assert any("estimada" in a for a in estimado["avisos"])
    # El catálogo de entrada no se altera.
    assert "categoria_estimada" not in json.dumps(datos)


def test_categoria_estimada_por_tipologia():
    base = {"detalles": {}, "titulo": ""}
    esperado = {
        "Articulo": "ART_D",
        "Libro": "LIB_C",
        "Capitulo": "CAP_LIB_C",
        "Software": "SF",
    }
    for subtipo, categoria in esperado.items():
        assert categoria_estimada({**base, "subtipo": subtipo})[0] == categoria
    trabajo = {**base, "subtipo": "Trabajo dirigido"}
    assert categoria_estimada({**trabajo, "titulo": "Tesis de Doctorado concluida"})[0] == "TD_B"
    assert categoria_estimada({**trabajo, "titulo": "Trabajo de grado de maestría"})[0] == "TM_B"
    assert categoria_estimada({**trabajo, "titulo": "Tesis concluida pregrado"})[0] == "TP_B"
    assert categoria_estimada({**trabajo, "titulo": "Estado: En curso"}) is None
    assert categoria_estimada({**base, "subtipo": "Proyecto"}) is None
    assert categoria_estimada({**base, "subtipo": "ART_A1"}) is None
    declarado = {**base, "subtipo": "Articulo", "detalles": {"categoria_minciencias": "ART_B"}}
    assert categoria_estimada(declarado) is None
    nuevo, estimadas = aplicar_estimacion({"productos": [declarado]})
    assert estimadas == [] and nuevo["productos"][0]["detalles"] == {"categoria_minciencias": "ART_B"}


def test_vinculo_con_fecha_actual_no_rompe_el_calculo(datos):
    for m in datos["integrantes"]:
        m["fecha_inicio"], m["fecha_fin"] = "2013/1", "Actual"
    assert calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, estimar=True)["indicador"] > 0


def test_archivo_local_acepta_fechas_de_vinculo_de_scienti_y_rechaza_basura(datos):
    for inicio, fin in [("2013/1", "Actual"), ("2013-05", None), ("2013", "2020/12"), ("2013-05-01", "")]:
        for m in datos["integrantes"]:
            m["fecha_inicio"], m["fecha_fin"] = inicio, fin
        restaurar_catalogo(datos)
    datos["integrantes"][0]["fecha_inicio"] = "ayer"
    with pytest.raises(ValueError, match="Fecha de membresía"):
        restaurar_catalogo(datos)
