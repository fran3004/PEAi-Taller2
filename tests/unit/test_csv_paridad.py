from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path
from typing import Any

from pea.ingesta.lector_csv import LectorCSV


def _casos_csv_compartidos() -> list[dict[str, Any]]:
    archivo = Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_paridad.json"
    return json.loads(archivo.read_text(encoding="utf-8"))["casos"]


def test_fixtures_csv_compartidos_conservan_utf8_escapes_y_crlf() -> None:
    for caso in _casos_csv_compartidos():
        salida = io.StringIO(newline="")
        escritor = csv.writer(salida, lineterminator="\r\n")
        escritor.writerow(caso["entrada"])

        assert salida.getvalue() == caso["salida"], caso["nombre"]
        assert salida.getvalue().encode("utf-8").endswith(b"\r\n")


def test_importacion_grupos_compartida_acepta_registro_multilinea_utf8(
    tmp_path: Path,
) -> None:
    archivo_fixture = (
        Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_importacion.json"
    )
    fixture = json.loads(archivo_fixture.read_text(encoding="utf-8"))
    ruta_csv = tmp_path / "grupos.csv"
    ruta_csv.write_bytes(fixture["contenido"].encode("utf-8"))

    grupos, errores = LectorCSV.leer_grupos(ruta_csv)

    assert errores == []
    assert len(grupos) == 1
    grupo = grupos[0]
    esperado = fixture["esperado"]
    assert grupo.codigo_gruplac == esperado["codigo_gruplac"]
    assert grupo.nombre == esperado["nombre"]
    assert grupo.categoria == esperado["categoria"]
    assert grupo.institucion_principal == esperado["institucion_principal"]
    assert grupo.lider == esperado["lider"]
    assert grupo.activo is esperado["activo"]
    assert grupo.es_ejemplo is esperado["es_ejemplo"]


def test_importacion_de_los_tipos_restantes_comparte_campos_python_cpp(
    tmp_path: Path,
) -> None:
    archivo_fixture = (
        Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_importacion.json"
    )
    fixture = json.loads(archivo_fixture.read_text(encoding="utf-8"))

    ruta_investigadores = tmp_path / "investigadores.csv"
    ruta_investigadores.write_bytes(fixture["investigadores"]["contenido"].encode("utf-8"))
    investigadores, errores_investigadores = LectorCSV.leer_investigadores(ruta_investigadores)
    esperado_investigador = fixture["investigadores"]["esperado"]
    assert errores_investigadores == []
    assert len(investigadores) == 1
    investigador = investigadores[0]
    for campo in esperado_investigador:
        assert getattr(investigador, campo) == esperado_investigador[campo]

    ruta_productos = tmp_path / "productos.csv"
    ruta_productos.write_bytes(fixture["productos"]["contenido"].encode("utf-8"))
    productos, errores_productos = LectorCSV.leer_productos(ruta_productos)
    esperado_producto = fixture["productos"]["esperado"]
    assert errores_productos == []
    assert len(productos) == 1
    producto, codigo_grupo = productos[0]
    assert codigo_grupo == esperado_producto["grupo_codigo"]
    assert producto.activo is esperado_producto["activo"]
    assert producto.es_ejemplo is esperado_producto["es_ejemplo"]
    assert producto.detalles == esperado_producto["detalles"]
    for campo in (
        "codigo_identificador",
        "titulo",
        "tipo_mayor",
        "subtipo",
        "ano",
        "mes",
        "pais",
        "estado_validacion",
    ):
        assert getattr(producto, campo) == esperado_producto[campo]

    ruta_autores = tmp_path / "autores.csv"
    ruta_autores.write_bytes(fixture["autores"]["contenido"].encode("utf-8"))
    autores, errores_autores = LectorCSV.leer_autores(ruta_autores)
    assert errores_autores == []
    assert len(autores) == 1
    for campo, valor in fixture["autores"]["esperado"].items():
        assert getattr(autores[0], campo) == valor

    ruta_autores_invalidos = tmp_path / "autores_invalidos.csv"
    ruta_autores_invalidos.write_text(
        fixture["autores_invalidos"]["contenido"], encoding="utf-8"
    )
    autores_invalidos, errores_autores_invalidos = LectorCSV.leer_autores(
        ruta_autores_invalidos
    )
    assert autores_invalidos == []
    assert [
        {"fila": error["fila"], "mensaje": error["error"]}
        for error in errores_autores_invalidos
    ] == fixture["autores_invalidos"]["errores"]

    detalles_invalidos = fixture["productos_detalles_invalidos"]
    ruta_detalles_invalidos = tmp_path / "productos_detalles_invalidos.csv"
    ruta_detalles_invalidos.write_text(
        detalles_invalidos["contenido"], encoding="utf-8"
    )
    productos_con_detalles_invalidos, errores_detalles = LectorCSV.leer_productos(
        ruta_detalles_invalidos
    )
    assert productos_con_detalles_invalidos == []
    assert [
        {"fila": error["fila"], "mensaje": error["error"]}
        for error in errores_detalles
    ] == [
        {
            "fila": detalles_invalidos["fila_error"],
            "mensaje": detalles_invalidos["mensaje"],
        }
    ]

    ruta_con_errores = tmp_path / "productos_con_errores.csv"
    contenido_con_ano_actual = fixture["filas_invalidas"]["contenido"].replace(
        "ANIO_ACTUAL", str(date.today().year)
    )
    ruta_con_errores.write_bytes(contenido_con_ano_actual.encode("utf-8"))
    productos_validos, errores = LectorCSV.leer_productos(ruta_con_errores)
    assert [error["fila"] for error in errores] == fixture["filas_invalidas"]["filas_error"]
    assert [
        {"fila": error["fila"], "mensaje": error["error"]} for error in errores
    ] == fixture["filas_invalidas"]["errores"]
    assert [producto.codigo_identificador for producto, _ in productos_validos] == fixture[
        "filas_invalidas"
    ]["codigos_validos"]

    sin_columna_ano = fixture["filas_invalidas"]["sin_columna_ano"]
    ruta_sin_ano = tmp_path / "productos_sin_ano.csv"
    ruta_sin_ano.write_text(sin_columna_ano["contenido"], encoding="utf-8")
    productos_sin_ano, errores_sin_ano = LectorCSV.leer_productos(ruta_sin_ano)
    assert productos_sin_ano == []
    assert errores_sin_ano == [
        {
            "fila": sin_columna_ano["fila_error"],
            "datos": {
                "codigo_identificador": "PRUEBA-PROD-ERR-05",
                "titulo": "Producto sin año",
                "tipo_mayor": "GNC",
            },
            "error": sin_columna_ano["mensaje"],
        }
    ]


def test_categoria_legada_se_normaliza_y_rechaza_valores_ambiguos(
    tmp_path: Path,
) -> None:
    archivo_fixture = (
        Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_importacion.json"
    )
    fixture = json.loads(archivo_fixture.read_text(encoding="utf-8"))

    legado = fixture["productos_categoria_legada"]
    ruta_legada = tmp_path / "productos_categoria_legada.csv"
    ruta_legada.write_text(legado["contenido"], encoding="utf-8")
    productos, errores = LectorCSV.leer_productos(ruta_legada)

    assert errores == []
    assert len(productos) == len(legado["esperados"])
    for (producto, _), esperado in zip(productos, legado["esperados"], strict=True):
        assert producto.codigo_identificador == esperado["codigo_identificador"]
        assert producto.tipo_mayor == esperado["tipo_mayor"]
        assert producto.subtipo == esperado["subtipo"]
        assert producto.estado_validacion == esperado["estado_validacion"]

    invalido = fixture["productos_categoria_invalida"]
    ruta_invalida = tmp_path / "productos_categoria_invalida.csv"
    ruta_invalida.write_text(invalido["contenido"], encoding="utf-8")
    productos_invalidos, errores_invalidos = LectorCSV.leer_productos(ruta_invalida)

    assert productos_invalidos == []
    assert [
        {"fila": error["fila"], "mensaje": error["error"]}
        for error in errores_invalidos
    ] == invalido["errores"]


def test_lectores_csv_aceptan_cabeceras_sin_distinguir_mayusculas(
    tmp_path: Path,
) -> None:
    archivo_fixture = (
        Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_importacion.json"
    )
    fixture = json.loads(archivo_fixture.read_text(encoding="utf-8"))

    def escribir_cabecera_mayuscula(nombre: str, contenido: str) -> Path:
        cabecera, separador, filas = contenido.partition("\r\n")
        assert separador
        ruta = tmp_path / nombre
        ruta.write_text(f"{cabecera.upper()}{separador}{filas}", encoding="utf-8")
        return ruta

    grupos, errores_grupos = LectorCSV.leer_grupos(
        escribir_cabecera_mayuscula("grupos.csv", fixture["contenido"])
    )
    assert errores_grupos == []
    assert [grupo.codigo_gruplac for grupo in grupos] == ["PRUEBA-CSV-01"]

    investigadores, errores_investigadores = LectorCSV.leer_investigadores(
        escribir_cabecera_mayuscula(
            "investigadores.csv", fixture["investigadores"]["contenido"]
        )
    )
    assert errores_investigadores == []
    assert [investigador.codigo_rh for investigador in investigadores] == [
        "PRUEBA-RH-CSV-01"
    ]

    productos, errores_productos = LectorCSV.leer_productos(
        escribir_cabecera_mayuscula("productos.csv", fixture["productos"]["contenido"])
    )
    assert errores_productos == []
    assert [producto.codigo_identificador for producto, _ in productos] == [
        "PRUEBA-PROD-CSV-01"
    ]

    autores, errores_autores = LectorCSV.leer_autores(
        escribir_cabecera_mayuscula("autores.csv", fixture["autores"]["contenido"])
    )
    assert errores_autores == []
    assert [autor.producto_codigo for autor in autores] == ["PRUEBA-PROD-CSV-01"]
