"""Comprueba lectura real y CRUD de una fila PRUEBA-; no modifica datos reales."""

import json
import sys
import uuid
from pathlib import Path

from pea.cliente_http import ClienteHTTPSupabase
from pea.excepciones import ErrorPEA


def probar() -> None:
    configuracion = json.loads(Path("config/pea.config.json").read_text(encoding="utf-8"))
    cliente = ClienteHTTPSupabase(configuracion["url"], configuracion["clave_publishable"])
    cliente.autenticar_evaluacion()
    grupos = cliente.get_paginado("grupos", {"select": "id,es_ejemplo"})
    assert any(not grupo["es_ejemplo"] for grupo in grupos), "No se encontraron grupos reales."
    print(f"Lectura autenticada: {len(grupos)} grupos; hay datos reales.")
    codigo = "PRUEBA-ENTREGA-" + uuid.uuid4().hex[:12]
    filtros = {"codigo_gruplac": "eq." + codigo, "es_ejemplo": "eq.true"}
    creado = False
    try:
        cliente.post("grupos", {"codigo_gruplac": codigo, "nombre": codigo,
                                "categoria": "C", "es_ejemplo": True,
                                "fecha_creacion": "2026-10-21", "departamento_ciudad": "PRUEBA",
                                "lider": "PRUEBA", "institucion_principal": "PRUEBA",
                                "gran_area_ocde": "PRUEBA", "area_ocde": "PRUEBA"})
        creado = True
        assert len(cliente.get("grupos", filtros)) == 1
        cliente.patch("grupos", {"nombre": codigo + " editado"}, filtros)
        cliente.patch("grupos", {"activo": False}, filtros)
        assert cliente.get("grupos", filtros)[0]["activo"] is False
        cliente.patch("grupos", {"activo": True}, filtros)
        assert cliente.get("grupos", filtros)[0]["es_ejemplo"] is True
        print("CRUD: crear, editar, desactivar y reactivar correctos.")
    finally:
        if creado:
            cliente.eliminar("grupos", filtros)
            assert cliente.get("grupos", filtros) == []
            print("Limpieza: solo se elimino la fila PRUEBA- creada por esta prueba.")
        cliente.cerrar_sesion()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        probar()
    except ErrorPEA as error:
        print(f"FALLO: {error.mensaje}")
        raise SystemExit(1) from None
