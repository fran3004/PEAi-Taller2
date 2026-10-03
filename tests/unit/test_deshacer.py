"""Pruebas unitarias para el mecanismo de Deshacer (Undo Stack)."""

from pea.dominio.grupo import Grupo
from pea.dominio.producto import Producto
from pea.servicios.servicio_dominio import CatalogoInvestigacion


def test_deshacer_pila_vacia() -> None:
    catalogo = CatalogoInvestigacion()
    assert catalogo.deshacer(persistir=False) is None


def test_deshacer_creacion_grupo() -> None:
    catalogo = CatalogoInvestigacion()
    grupo = Grupo(codigo_gruplac="GRP-UNDO-01", nombre="Grupo Deshacer")

    catalogo.crear_grupo(grupo, persistir=False)
    assert len(catalogo.grupos) == 1
    assert len(catalogo.pila_deshacer) == 1

    # Deshacer creación
    cmd = catalogo.deshacer(persistir=False)
    assert cmd is not None
    assert cmd.tipo_operacion == "crear"
    assert len(catalogo.grupos) == 0
    assert catalogo.buscar_grupo("GRP-UNDO-01") is None


def test_deshacer_desactivacion_y_activacion_producto() -> None:
    catalogo = CatalogoInvestigacion()
    prod = Producto(
        codigo_identificador="P-UNDO-01",
        titulo="Software de Prueba Undo",
        tipo_mayor="DTI",
        ano=2024,
    )
    catalogo.crear_producto(prod, persistir=False)
    # Vaciar pila para aislar la prueba
    catalogo.pila_deshacer.limpiar()

    # 1. Desactivar
    catalogo.desactivar_producto(prod.codigo_identificador, persistir=False)
    assert not prod.activo
    assert len(catalogo.pila_deshacer) == 1

    # Deshacer desactivación -> debe reactivarse
    catalogo.deshacer(persistir=False)
    assert prod.activo

    # 2. Desactivar y luego activar manualmente
    catalogo.desactivar_producto(prod.codigo_identificador, persistir=False)
    catalogo.activar_producto(prod.codigo_identificador, persistir=False)
    assert prod.activo

    # Deshacer activación -> debe volver a desactivado
    catalogo.deshacer(persistir=False)
    assert not prod.activo


def test_deshacer_edicion_grupo() -> None:
    catalogo = CatalogoInvestigacion()
    grupo = Grupo(codigo_gruplac="GRP-EDIT-01", nombre="Nombre Original", categoria="B")
    catalogo.crear_grupo(grupo, persistir=False)
    catalogo.pila_deshacer.limpiar()

    # Editar grupo
    catalogo.actualizar_grupo(grupo.codigo_gruplac, {"nombre": "Nombre Modificado", "categoria": "A1"}, persistir=False)
    assert grupo.nombre == "Nombre Modificado"
    assert grupo.categoria == "A1"

    # Deshacer edición
    catalogo.deshacer(persistir=False)
    assert grupo.nombre == "Nombre Original"
    assert grupo.categoria == "B"
