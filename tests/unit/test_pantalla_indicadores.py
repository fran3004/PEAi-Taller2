from pathlib import Path

from pea.gui.ejecutor import EjecutorHilos
from pea.gui.pantallas.indicadores import PantallaIndicadores
from pea.servicios.servicio_aplicacion import ServicioAplicacion


def test_pantalla_calcula_y_descarta_resultados_obsoletos(qtbot):
    servicio = ServicioAplicacion()
    servicio.iniciar_local(str(Path(__file__).parents[2] / "datos/ejemplo-parcial.json"))
    pantalla = PantallaIndicadores(servicio, EjecutorHilos())
    qtbot.addWidget(pantalla)
    pantalla.show()
    pantalla.calcular.click()
    qtbot.waitUntil(lambda: pantalla._resultado is not None, timeout=15000)
    assert pantalla._resultado["indicador"] == 4.5
    assert "Indicador parcial" in pantalla.resultado.text()
    assert pantalla.tabla.rowCount() == 9
    pantalla.corte.setValue(2024)
    assert pantalla._resultado is None
    assert pantalla.tabla.rowCount() == 0


def test_edicion_complementaria_conserva_datos_y_se_deshace():
    servicio = ServicioAplicacion()
    servicio.iniciar_local(str(Path(__file__).parents[2] / "datos/ejemplo-parcial.json"))
    servicio.editar_campos_entidad(
        "investigador", "PRUEBA-I1", {"documento_identidad": "PRUEBA-DOC", "par_evaluador": True}
    )
    assert servicio.campos_entidad("investigador", "PRUEBA-I1")["documento_identidad"] == "PRUEBA-DOC"
    servicio.deshacer()
    assert servicio.campos_entidad("investigador", "PRUEBA-I1")["documento_identidad"] is None
