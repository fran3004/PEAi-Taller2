"""Gestor de sesión de usuario y credenciales en memoria volátil."""

import time
from typing import Any

from pea.excepciones import ErrorAutenticacion


class Sesion:
    """Administra el estado de autenticación exclusivamente en memoria RAM."""

    def __init__(self) -> None:
        self._token_acceso: str | None = None
        self._correo: str | None = None
        self._rol: str = "anon"
        self._expira_en: float | None = None
        self._metadatos_usuario: dict[str, Any] = {}

    @property
    def token_acceso(self) -> str | None:
        if self.esta_expirada():
            self.cerrar_sesion()
            raise ErrorAutenticacion("La sesión ha expirado. Por favor inicie sesión nuevamente.")
        return self._token_acceso

    @property
    def correo(self) -> str | None:
        return self._correo

    @property
    def rol(self) -> str:
        return self._rol

    def esta_autenticado(self) -> bool:
        """Determina si existe una sesión válida no expirada."""
        if self._token_acceso is None:
            return False
        if self.esta_expirada():
            self.cerrar_sesion()
            return False
        return True

    def esta_expirada(self) -> bool:
        """Indica si el tiempo de vida del token ha culminado."""
        if self._expira_en is None:
            return False
        return time.time() >= self._expira_en

    def iniciar_sesion(
        self,
        token: str,
        correo: str,
        tiempo_expiracion_segundos: float = 3600.0,
        metadatos: dict[str, Any] | None = None,
    ) -> None:
        """Establece la sesión autenticada."""
        self._token_acceso = token
        self._correo = correo
        self._rol = "authenticated"
        self._expira_en = time.time() + tiempo_expiracion_segundos
        self._metadatos_usuario = metadatos or {}

    def cerrar_sesion(self) -> None:
        """Elimina de la memoria todo dato de sesión."""
        self._token_acceso = None
        self._correo = None
        self._rol = "anon"
        self._expira_en = None
        self._metadatos_usuario.clear()

    def simular_expiracion(self) -> None:
        """Método de prueba para simular token expirado."""
        if self._expira_en is not None:
            self._expira_en = time.time() - 1.0
