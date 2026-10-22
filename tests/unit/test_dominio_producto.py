"""Pruebas unitarias para la entidad de dominio Producto y paridad de validación."""

from __future__ import annotations

import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from pea.dominio.producto import (
    ANO_MAXIMO_BASE,
    ANO_MAXIMO_PRODUCTO,
    ANO_MINIMO_BASE,
    ANO_MINIMO_PRODUCTO,
    Producto,
    validar_ano_producto,
)
from pea.excepciones import ErrorValidacion
from pea.servicios.servicio_aplicacion import ServicioAplicacion


def test_constantes_limite_base() -> None:
    assert ANO_MINIMO_BASE == 1970
    assert ANO_MAXIMO_BASE == 2100
    assert ANO_MINIMO_PRODUCTO == ANO_MINIMO_BASE
    assert ANO_MAXIMO_PRODUCTO == ANO_MAXIMO_BASE


def test_producto_rechaza_anos_fuera_de_rango() -> None:
    for ano_invalido in (1800, 1969, 2101):
        with pytest.raises(ValidationError) as exc_info:
            Producto(
                codigo_identificador=f"PROD-{ano_invalido}",
                titulo="Producto de prueba",
                tipo_mayor="GNC",
                ano=ano_invalido,
            )
        assert f"El año debe estar entre {ANO_MINIMO_BASE} y {ANO_MAXIMO_BASE}." in str(exc_info.value)


def test_producto_acepta_anos_limite() -> None:
    for ano_valido in (1970, 2100):
        prod = Producto(
            codigo_identificador=f"PROD-{ano_valido}",
            titulo="Producto de prueba",
            tipo_mayor="GNC",
            ano=ano_valido,
        )
        assert prod.ano == ano_valido


def test_producto_rechaza_ano_no_numerico_o_booleano() -> None:
    for valor_invalido in (True, False, "no-es-ano", "2024.5", None):
        with pytest.raises(ValidationError) as exc_info:
            Producto(
                codigo_identificador="PROD-INV",
                titulo="Producto de prueba",
                tipo_mayor="GNC",
                ano=valor_invalido,  # type: ignore[arg-type]
            )
        assert "El año debe ser un número entero." in str(exc_info.value)


def test_validar_ano_producto_conserva_limite_anio_actual() -> None:
    anio_actual = datetime.date.today().year

    # Valores válidos dentro de la ventana histórica
    assert validar_ano_producto(1970) == 1970
    assert validar_ano_producto(anio_actual) == anio_actual

    # Valores fuera de la ventana para ingesta
    for ano_invalido in (1800, 1969, anio_actual + 1):
        with pytest.raises(ValueError) as exc_info:
            validar_ano_producto(ano_invalido)
        assert f"El año debe estar entre {ANO_MINIMO_BASE} y {anio_actual}." in str(exc_info.value)

    # Límite personalizado
    assert validar_ano_producto(2028, anio_actual=2030) == 2028
    with pytest.raises(ValueError):
        validar_ano_producto(2031, anio_actual=2030)

    # Tipo no entero
    for tipo_invalido in (True, False, "2024", 2024.5, None):  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="El año debe ser un número entero."):
            validar_ano_producto(tipo_invalido)  # type: ignore[arg-type]


def test_paridad_validaciones_python_cpp() -> None:
    """Verifica la coherencia entre las reglas de validación en Python y C++.

    Valores de prueba compartidos con cpp/tests/test_deshacer.cpp y cpp/src/servicios/catalogo_investigacion.cpp:
    - 1800, 1969: rechazados por violar el límite inferior (1970).
    - 1970: aceptado como año mínimo.
    - año actual: aceptado como año vigente.
    - no entero / float / bool: rechazado con 'El año debe ser un número entero.'.
    """
    anio_actual = datetime.date.today().year
    mensaje_entero_esperado = "El año debe ser un número entero."
    mensaje_rango_catalogo = f"El año debe estar entre 1970 y {anio_actual}."
    mensaje_rango_modelo = f"El año debe estar entre {ANO_MINIMO_BASE} y {ANO_MAXIMO_BASE}."

    casos = [
        # (valor, valido_modelo_base, valido_ingesta_catalogo)
        (1800, False, False),
        (1969, False, False),
        (1970, True, True),
        (2024, True, True),
        (anio_actual, True, True),
        (2100, True, False),
        (2101, False, False),
    ]

    for val, ok_modelo, ok_catalogo in casos:
        if ok_modelo:
            p = Producto(
                codigo_identificador=f"P-{val}",
                titulo="Test",
                tipo_mayor="GNC",
                ano=val,
            )
            assert p.ano == val
        else:
            with pytest.raises(ValidationError) as err_modelo:
                Producto(
                    codigo_identificador=f"P-{val}",
                    titulo="Test",
                    tipo_mayor="GNC",
                    ano=val,
                )
            assert mensaje_rango_modelo in str(err_modelo.value)

        if ok_catalogo:
            assert validar_ano_producto(val) == val
        else:
            with pytest.raises(ValueError) as err_cat:
                validar_ano_producto(val)
            assert mensaje_rango_catalogo in str(err_cat.value)

    # Tipos no enteros
    for no_entero in (True, False, 2024.5):
        with pytest.raises(ValidationError) as err_mod:
            Producto(
                codigo_identificador="P-NO-INT",
                titulo="Test",
                tipo_mayor="GNC",
                ano=no_entero,  # type: ignore[arg-type]
            )
        assert mensaje_entero_esperado in str(err_mod.value)


def test_servicio_aplicacion_convierte_validation_error_en_error_validacion() -> None:
    app = ServicioAplicacion()
    app.cargar_demostracion()

    datos_incompletos: dict[str, Any] = {
        "codigo_identificador": "PRUEBA-VAL-ERR",
        "tipo_mayor": "GNC",
        "estado_validacion": "Avalado",
        "ano": 2024,
        # Falta "titulo" que es requerido por Producto
    }
    with pytest.raises(ErrorValidacion) as exc_info:
        app.crear_producto(datos_incompletos)

    assert "Datos inválidos:" in str(exc_info.value)
