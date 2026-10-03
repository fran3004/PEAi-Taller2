"""Jerarquía de excepciones tipadas para PEA-i."""

from typing import Any


class ErrorPEA(Exception):
    """Excepción base para todos los errores de la aplicación PEA-i."""

    def __init__(self, mensaje: str, detalle: Any = None) -> None:
        super().__init__(f"{mensaje} - Detalle: {detalle}" if detalle else mensaje)
        self.mensaje = mensaje
        self.detalle = detalle


class ErrorConexion(ErrorPEA):
    """Fallo en la conectividad de red o tiempo de espera agotado."""



class ErrorAutenticacion(ErrorPEA):
    """Error al autenticar credenciales (HTTP 401)."""



class ErrorAutorizacion(ErrorPEA):
    """Acceso no autorizado por políticas RLS o permisos (HTTP 403)."""



class RecursoNoEncontrado(ErrorPEA):
    """El recurso o registro solicitado no existe (HTTP 404)."""



class ConflictoRevision(ErrorPEA):
    """Conflicto de concurrencia optimista o violación de clave única (HTTP 409)."""



class ErrorValidacion(ErrorPEA):
    """Datos inválidos o rechazo de restricción de integridad (HTTP 422)."""



class ErrorServidor(ErrorPEA):
    """Error interno en Supabase / PostgreSQL (HTTP 5xx)."""

