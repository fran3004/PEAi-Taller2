"""Persistencia de autorías CSV: errores reales, idempotencia y reintentos acotados."""

from unittest.mock import Mock

import pytest

from pea.datos.repositorios import RepositorioProductos
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.estructuras.cola import EstadoTarea
from pea.excepciones import ConflictoRevision, ErrorConexion
from pea.gui.pantallas.importar import PantallaImportar
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_dominio import CatalogoInvestigacion


@pytest.fixture
def escenario(tmp_path):
    catalogo = CatalogoInvestigacion()
    producto = Producto(id=11, codigo_identificador="PRUEBA-P", titulo="Prueba", tipo_mayor="GNC", ano=2024, es_ejemplo=True)
    investigador = Investigador(id=21, codigo_rh="PRUEBA-I", nombre_completo="Prueba", es_ejemplo=True)
    catalogo.crear_producto(producto, persistir=False)
    catalogo.crear_investigador(investigador, persistir=False)
    catalogo.repo_productos = Mock()
    servicio = ServicioIngesta(catalogo)
    ruta = tmp_path / "autores.csv"
    ruta.write_text("producto_codigo,investigador_codigo,orden_autoria\nPRUEBA-P,PRUEBA-I,2\n", encoding="utf-8")
    return catalogo, servicio, ruta, producto, investigador


def test_autor_con_error_de_conexion_no_se_cuenta_ni_se_agrega(escenario):
    catalogo, servicio, ruta, _, _ = escenario
    catalogo.repo_productos.asociar_autor.side_effect = ErrorConexion("Conexión interrumpida")
    tarea = servicio.encolar_csv(ruta, "autores", persistir=True)
    informe = servicio.procesar_siguiente()
    assert informe.autores_procesados == 0
    assert not informe.exito
    assert informe.mensaje == "0 de 1 relaciones guardadas"
    assert informe.filas_erroneas[0]["fila"] == 2
    assert "Conexión interrumpida" in informe.filas_erroneas[0]["error"]
    assert informe.advertencias
    assert tarea.estado == EstadoTarea.CON_ERROR
    assert tarea.mensaje_error == informe.mensaje
    assert list(catalogo.multilista_productos.buscar_nodo("PRUEBA-P").autores) == []


@pytest.mark.parametrize("entidad", ["producto", "investigador", "repositorio"])
def test_autor_persistente_sin_identificador_o_repositorio_falla(escenario, entidad):
    catalogo, servicio, ruta, producto, investigador = escenario
    if entidad == "repositorio":
        catalogo.repo_productos = None
    else:
        (producto if entidad == "producto" else investigador).id = None
    servicio.encolar_csv(ruta, "autores", persistir=True)
    informe = servicio.procesar_siguiente()
    assert not informe.exito
    assert informe.autores_procesados == 0
    assert "sin identificador remoto" in " ".join(informe.advertencias) if entidad != "repositorio" else informe.advertencias
    assert not list(catalogo.multilista_productos.buscar_nodo("PRUEBA-P").autores)


def test_autores_parciales_conservan_numero_de_fila_y_estado(escenario):
    catalogo, servicio, ruta, _, _ = escenario
    ruta.write_text("producto_codigo,investigador_codigo,orden_autoria\nPRUEBA-P,PRUEBA-I,x\nPRUEBA-P,PRUEBA-I,1\nPRUEBA-P,PRUEBA-I,2\nPRUEBA-AUSENTE,PRUEBA-I,1\n", encoding="utf-8")
    catalogo.repo_productos.asociar_autor.side_effect = [ErrorConexion("Fallo de prueba"), None]
    tarea = servicio.encolar_csv(ruta, "autores", persistir=True)
    informe = servicio.procesar_siguiente()
    assert informe.exito
    assert informe.autores_procesados == 1
    assert informe.mensaje == "1 de 4 relaciones guardadas"
    assert sorted(error["fila"] for error in informe.filas_erroneas) == [2, 3, 5]
    assert informe.advertencias
    assert tarea.estado == EstadoTarea.TERMINADA
    assert tarea.elementos_procesados == 1
    assert len(list(catalogo.multilista_productos.buscar_nodo("PRUEBA-P").autores)) == 1


@pytest.mark.parametrize("agotado", [False, True])
def test_autores_reintentan_conflicto_revision_de_forma_acotada(escenario, monkeypatch, agotado):
    catalogo, servicio, ruta, _, _ = escenario
    catalogo.cliente = Mock()
    sincronizar = Mock()
    monkeypatch.setattr(catalogo.controlador_revision, "sincronizar", sincronizar)
    monkeypatch.setattr("pea.ingesta.servicio_ingesta.time.sleep", lambda _: None)
    conflicto = ConflictoRevision("La base de datos cambió", {"code": "P0001"})
    catalogo.repo_productos.asociar_autor.side_effect = conflicto if agotado else [conflicto, None]
    servicio.encolar_csv(ruta, "autores", persistir=True)
    informe = servicio.procesar_siguiente()
    assert catalogo.repo_productos.asociar_autor.call_count == (5 if agotado else 2)
    assert sincronizar.call_count == (4 if agotado else 1)
    assert informe.autores_procesados == (0 if agotado else 1)
    assert informe.exito is not agotado
    assert informe.requiere_recarga is agotado


def test_autores_guardan_antes_de_modificar_memoria_y_demo_no_escribe(escenario):
    catalogo, servicio, ruta, _, _ = escenario
    def guardar(*args, **kwargs):
        assert not list(catalogo.multilista_productos.buscar_nodo("PRUEBA-P").autores)
    catalogo.repo_productos.asociar_autor.side_effect = guardar
    tarea = servicio.encolar_csv(ruta, "autores", persistir=True)
    informe = servicio.procesar_siguiente()
    assert informe.exito
    assert informe.autores_procesados == tarea.elementos_procesados == 1
    catalogo.repo_productos.asociar_autor.assert_called_once_with(11, 21, orden=2, es_ejemplo=True)
    servicio.encolar_csv(ruta, "autores", persistir=False)
    assert servicio.procesar_siguiente().autores_procesados == 1
    assert catalogo.repo_productos.asociar_autor.call_count == 1


@pytest.mark.parametrize("codigo", ["23505", "23503", "P0001"])
def test_repositorio_autor_solo_acepta_duplicado_confirmado(codigo):
    cliente = Mock()
    cliente.post.side_effect = ConflictoRevision("Conflicto de concurrencia o violación de clave única", {"code": codigo})
    repositorio = RepositorioProductos(cliente)
    if codigo == "23505":
        repositorio.asociar_autor(11, 21, es_ejemplo=True)
    else:
        with pytest.raises(ConflictoRevision):
            repositorio.asociar_autor(11, 21, es_ejemplo=True)
    assert cliente.post.call_count == 1


@pytest.mark.parametrize("todas", [False, True])
def test_gui_muestra_resumen_y_advertencias_de_autorias(qtbot, monkeypatch, todas):
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    pantalla = PantallaImportar(servicio=servicio, ejecutor=None)
    qtbot.addWidget(pantalla)
    pendientes = [{"exito": True, "mensaje": "1 de 2 relaciones guardadas", "autores": 1,
                   "filas_erroneas": 1, "advertencias": ("Fila 3: sin identificador remoto",)}]
    monkeypatch.setattr(servicio, "tareas_pendientes", lambda: len(pendientes))
    monkeypatch.setattr(servicio, "procesar_siguiente_tarea", lambda: pendientes.pop())
    avisos = Mock()
    monkeypatch.setattr(pantalla, "_notificar_aviso", avisos)
    (pantalla._al_procesar_todas if todas else pantalla._al_procesar_siguiente)()
    mensaje = avisos.call_args.args[0]
    assert "1 de 2 relaciones guardadas" in mensaje
    assert "Fila 3: sin identificador remoto" in mensaje
