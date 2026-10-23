"""Pruebas unitarias para tools/db/reconciliar_codigos_cvlac.py."""

from __future__ import annotations

import csv
import datetime
from pathlib import Path
from typing import Any

from tools.db.reconciliar_codigos_cvlac import (
    analizar_candidatos_reconciliacion,
    ejecutar_reconciliacion,
    exportar_informe_csv,
    verificar_respaldo_reciente,
)


def test_analizar_candidatos_reconciliacion_casos_ok_y_ocurrencias() -> None:
    prods = [
        {
            "id": 1,
            "codigo_identificador": "PROD-CVLAC-0000494917-0001",
            "titulo": "Gestión 1",
            "detalles": {"referencia_original": "Cita A"},
        },
        {
            "id": 2,
            "codigo_identificador": "PROD-CVLAC-0000494917-0002",
            "titulo": "Gestión 2",
            "detalles": {"referencia_original": "Cita A"},  # Mismo investigador, misma cita
        },
        {
            "id": 3,
            "codigo_identificador": "PROD-CVLAC-0000494917-0003",
            "titulo": "Gestión 3",
            "detalles": {"referencia_original": "Cita B"},
        },
    ]

    resultados, resumen = analizar_candidatos_reconciliacion(prods)
    assert resumen["total"] == 3
    assert resumen["OK"] == 3
    assert resumen["SIN_CITA"] == 0
    assert resumen["COLISION"] == 0

    assert resultados[0]["id"] == 1
    assert not resultados[0]["codigo_nuevo"].endswith("-2")

    assert resultados[1]["id"] == 2
    assert resultados[1]["codigo_nuevo"].endswith("-2")

    assert resultados[2]["id"] == 3
    assert not resultados[2]["codigo_nuevo"].endswith("-2")


def test_analizar_candidatos_sin_cita_y_colision() -> None:
    prods = [
        {
            "id": 10,
            "codigo_identificador": "PROD-CVLAC-0000123456-0001",
            "titulo": "",
            "detalles": {},  # Sin cita ni título
        },
        {
            "id": 11,
            "codigo_identificador": "PROD-CVLAC-0000123456-0002",
            "titulo": "Título de producto",
            "detalles": {"referencia_original": "Cita Existente"},
        },
        # Otro producto ya tiene el código resultante de 'Cita Existente'
        {
            "id": 99,
            "codigo_identificador": "PROD-CVLAC-0000123456-c3ab3e5b66d4",
            "titulo": "Otro",
            "detalles": {},
        },
    ]

    resultados, resumen = analizar_candidatos_reconciliacion(prods)
    assert resumen["total"] == 2
    assert resumen["SIN_CITA"] == 1


def test_verificar_respaldo_reciente(tmp_path: Path) -> None:
    assert verificar_respaldo_reciente(tmp_path) is None

    archivo_viejo = tmp_path / "respaldo_20200101.json"
    archivo_viejo.write_text("{}", encoding="utf-8")
    # Forzar mtime antiguo
    tiempo_antiguo = datetime.datetime.now(datetime.UTC).timestamp() - 7200
    import os
    os.utime(archivo_viejo, (tiempo_antiguo, tiempo_antiguo))

    assert verificar_respaldo_reciente(tmp_path, max_antiguedad_segundos=3600) is None

    archivo_nuevo = tmp_path / "respaldo_reciente.json"
    archivo_nuevo.write_text("{}", encoding="utf-8")

    reciente = verificar_respaldo_reciente(tmp_path, max_antiguedad_segundos=3600)
    assert reciente is not None
    assert reciente.name == "respaldo_reciente.json"


def test_exportar_informe_csv(tmp_path: Path) -> None:
    ruta_csv = tmp_path / "sub" / "informe.csv"
    items = [
        {"id": 1, "codigo_anterior": "PROD-CVLAC-001-0001", "codigo_nuevo": "PROD-CVLAC-001-abc", "estado": "OK"},
        {"id": 2, "codigo_anterior": "PROD-CVLAC-001-0002", "codigo_nuevo": "", "estado": "SIN_CITA"},
    ]
    exportar_informe_csv(items, ruta_csv)
    assert ruta_csv.exists()

    with ruta_csv.open("r", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 2
    assert filas[0]["estado"] == "OK"
    assert filas[1]["estado"] == "SIN_CITA"


def test_ejecutar_reconciliacion_simulacion_mock(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("PEA_SUPABASE_URL", "https://mock.supabase.co")
    monkeypatch.setenv("PEA_SUPABASE_ANON_KEY", "mock-anon-key")

    datos_productos = [
        {
            "id": 1,
            "codigo_identificador": "PROD-CVLAC-0000494917-0001",
            "titulo": "Gestión 1",
            "detalles": {"referencia_original": "Cita de prueba"},
            "es_ejemplo": False,
        }
    ]

    class FakeCliente:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def get_paginado(self, tabla: str, **_kwargs: Any) -> list[dict[str, Any]]:
            if tabla == "productos":
                return datos_productos
            return []

        def establecer_token_acceso(self, _t: str | None) -> None:
            pass

    monkeypatch.setattr("tools.db.reconciliar_codigos_cvlac.ClienteHTTPSupabase", FakeCliente)
    monkeypatch.setattr("tools.db.reconciliar_codigos_cvlac.obtener_token_autenticado", lambda *_: None)

    ret = ejecutar_reconciliacion(aplicar=False)
    assert ret == 0
