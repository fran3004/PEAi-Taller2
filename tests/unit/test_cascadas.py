"""Pruebas de reglas de cascada y desactivación lógica reversible."""

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.servicios.servicio_dominio import CatalogoInvestigacion


def test_desactivacion_logica_reversible_no_destruye_enlaces() -> None:
    catalogo = CatalogoInvestigacion()

    grupo = Grupo(codigo_gruplac="GRP-01", nombre="Grupo de Redes")
    inv = Investigador(codigo_rh="RH-01", nombre_completo="Dra. Laura")
    prod = Producto(
        codigo_identificador="PRD-01",
        titulo="Estudio de Grafos",
        tipo_mayor="GNC",
        ano=2024,
    )

    catalogo.crear_grupo(grupo, persistir=False)
    catalogo.crear_investigador(inv, persistir=False)
    catalogo.vincular_integrante(grupo.codigo_gruplac, inv.codigo_rh, rol="Lider", persistir=False)
    catalogo.crear_producto(
        prod,
        codigo_gruplac=grupo.codigo_gruplac,
        codigos_rh_autores=[inv.codigo_rh],
        persistir=False,
    )

    # Desactivar producto
    catalogo.desactivar_producto(prod.codigo_identificador, persistir=False)
    assert not prod.activo

    # Los enlaces siguen intactos
    prods_grupo = catalogo.multilista_productos.obtener_productos_grupo(grupo.codigo_gruplac)
    prods_inv = catalogo.multilista_productos.obtener_productos_investigador(inv.codigo_rh)
    assert len(prods_grupo) == 1
    assert len(prods_inv) == 1
    assert not prods_grupo.cabeza.dato.activo

    # Reactivar producto
    catalogo.activar_producto(prod.codigo_identificador, persistir=False)
    assert prod.activo
    assert prods_grupo.cabeza.dato.activo


def test_cascada_eliminacion_producto() -> None:
    catalogo = CatalogoInvestigacion()

    grupo = Grupo(codigo_gruplac="GRP-01", nombre="Grupo IA")
    inv1 = Investigador(codigo_rh="RH-01", nombre_completo="Investigador 1")
    inv2 = Investigador(codigo_rh="RH-02", nombre_completo="Investigador 2")

    catalogo.crear_grupo(grupo, persistir=False)
    catalogo.crear_investigador(inv1, persistir=False)
    catalogo.crear_investigador(inv2, persistir=False)

    p1 = Producto(codigo_identificador="P-01", titulo="Artículo 1", tipo_mayor="GNC", ano=2023)
    p2 = Producto(codigo_identificador="P-02", titulo="Artículo 2", tipo_mayor="GNC", ano=2024)

    catalogo.crear_producto(p1, codigo_gruplac=grupo.codigo_gruplac, codigos_rh_autores=[inv1.codigo_rh, inv2.codigo_rh], persistir=False)
    catalogo.crear_producto(p2, codigo_gruplac=grupo.codigo_gruplac, codigos_rh_autores=[inv2.codigo_rh], persistir=False)

    assert len(catalogo.multilista_productos) == 2
    assert len(catalogo.multilista_productos.obtener_productos_investigador(inv2.codigo_rh)) == 2

    # Eliminar P-01
    catalogo.eliminar_producto(p1.codigo_identificador, persistir=False)

    assert len(catalogo.multilista_productos) == 1
    assert catalogo.buscar_producto("P-01") is None
    # Inv1 ya no tiene productos
    assert len(catalogo.multilista_productos.obtener_productos_investigador(inv1.codigo_rh)) == 0
    # Inv2 aún conserva P-02
    assert len(catalogo.multilista_productos.obtener_productos_investigador(inv2.codigo_rh)) == 1


def test_cascada_eliminacion_investigador() -> None:
    catalogo = CatalogoInvestigacion()

    grupo = Grupo(codigo_gruplac="GRP-01", nombre="Grupo Robótica")
    inv = Investigador(codigo_rh="RH-01", nombre_completo="Dr. Robótica")
    prod = Producto(codigo_identificador="P-ROB-01", titulo="Brazo Mecatrónico", tipo_mayor="DTI", ano=2024)

    catalogo.crear_grupo(grupo, persistir=False)
    catalogo.crear_investigador(inv, persistir=False)
    catalogo.vincular_integrante(grupo.codigo_gruplac, inv.codigo_rh, rol="Lider", persistir=False)
    catalogo.crear_producto(prod, codigo_gruplac=grupo.codigo_gruplac, codigos_rh_autores=[inv.codigo_rh], persistir=False)

    assert len(catalogo.integrantes) == 1
    nodo_prod = catalogo.multilista_productos.buscar_nodo(prod.codigo_identificador)
    assert len(nodo_prod.autores) == 1

    # Eliminar investigador
    catalogo.eliminar_investigador(inv.codigo_rh, persistir=False)

    # Sale de la lista de investigadores
    assert catalogo.buscar_investigador(inv.codigo_rh) is None
    # Sale de integrantes
    assert len(catalogo.integrantes) == 0
    # Sale de la autoría del producto sin romper el nodo del producto
    assert len(nodo_prod.autores) == 0
    assert catalogo.buscar_producto(prod.codigo_identificador) is not None


def test_cascada_eliminacion_grupo() -> None:
    catalogo = CatalogoInvestigacion()

    grupo = Grupo(codigo_gruplac="GRP-01", nombre="Grupo Energías")
    inv = Investigador(codigo_rh="RH-01", nombre_completo="Ing. Solar")
    prod = Producto(codigo_identificador="P-SOLAR-01", titulo="Panel Eficiente", tipo_mayor="DTI", ano=2024)

    catalogo.crear_grupo(grupo, persistir=False)
    catalogo.crear_investigador(inv, persistir=False)
    catalogo.vincular_integrante(grupo.codigo_gruplac, inv.codigo_rh, rol="Lider", persistir=False)
    catalogo.crear_producto(prod, codigo_gruplac=grupo.codigo_gruplac, codigos_rh_autores=[inv.codigo_rh], persistir=False)

    # Eliminar grupo
    catalogo.eliminar_grupo(grupo.codigo_gruplac, persistir=False)

    # Grupo eliminado
    assert catalogo.buscar_grupo(grupo.codigo_gruplac) is None
    # Integrantes del grupo eliminados
    assert len(catalogo.integrantes) == 0
    # Producto desvinculado del grupo en la multilista
    nodo_prod = catalogo.multilista_productos.buscar_nodo(prod.codigo_identificador)
    assert nodo_prod.grupo is None
