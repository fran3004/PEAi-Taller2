"""Ejecutor de tareas en segundo plano para mantener la GUI fluida.

Conforme a AGENTS.md y python-pyside6/SKILL.md:
- Toda llamada de red, ingesta o verificación cruzada se realiza FUERA del hilo principal.
- Los resultados y errores se envían al hilo de la GUI mediante señales Qt.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class SenalesTrabajo(QObject):
    """Señales emitidas durante el ciclo de vida de una tarea en segundo plano."""

    iniciado = Signal()
    terminado = Signal(object)  # resultado de la tarea
    error = Signal(Exception, str)  # excepción, mensaje detallado


class TareaSegundoPlano(QRunnable):
    """Ejecuta una función en el pool de hilos de Qt y emite señales seguras."""

    def __init__(self, funcion: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs
        self.senales = SenalesTrabajo()

    def run(self) -> None:
        self.senales.iniciado.emit()
        try:
            resultado = self.funcion(*self.args, **self.kwargs)
            self.senales.terminado.emit(resultado)
        except Exception as err:
            detalle = traceback.format_exc()
            self.senales.error.emit(err, detalle)


class EjecutorAsincrono(QObject):
    """Fachada para lanzar tareas al QThreadPool global de la aplicación."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.pool = QThreadPool.globalInstance()
        self._tareas_activas: set[TareaSegundoPlano] = set()

    _instancia_unica: EjecutorAsincrono | None = None

    @classmethod
    def instancia(cls) -> EjecutorAsincrono:
        if cls._instancia_unica is None:
            cls._instancia_unica = EjecutorAsincrono()
        return cls._instancia_unica

    def ejecutar(
        self,
        funcion: Callable[..., Any],
        al_terminar: Callable[[Any], None] | None = None,
        al_fallar: Callable[[Exception, str], None] | None = None,
        al_iniciar: Callable[[], None] | None = None,
        al_tener_exito: Callable[[Any], None] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> TareaSegundoPlano:
        cb_terminar = al_tener_exito if al_tener_exito is not None else al_terminar
        tarea = TareaSegundoPlano(funcion, *args, **kwargs)
        if al_iniciar is not None:
            tarea.senales.iniciado.connect(al_iniciar)
        if cb_terminar is not None:
            tarea.senales.terminado.connect(cb_terminar)
        if al_fallar is not None:
            tarea.senales.error.connect(al_fallar)

        self._tareas_activas.add(tarea)

        def _limpiar(*_: Any) -> None:
            self._tareas_activas.discard(tarea)

        tarea.senales.terminado.connect(_limpiar)
        tarea.senales.error.connect(_limpiar)

        self.pool.start(tarea)
        return tarea


EjecutorHilos = EjecutorAsincrono

