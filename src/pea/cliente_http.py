"""Cliente HTTPS para Supabase (PostgREST / Auth / RPC).

Maneja comunicación exclusivamente por HTTPS mediante REST y RPC,
mapeo de errores tipados, paginación automática y almacenamiento
de tokens exclusivamente en memoria volátil.
"""

from typing import Any

import requests

from pea.excepciones import (
    ConflictoRevision,
    ErrorAutenticacion,
    ErrorAutorizacion,
    ErrorConexion,
    ErrorPEA,
    ErrorServidor,
    ErrorValidacion,
    RecursoNoEncontrado,
)


class ClienteHTTPSupabase:
    """Cliente REST/RPC para interactuar con la API HTTPS de Supabase."""

    def __init__(self, base_url: str, anon_key: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.anon_key = anon_key
        self.timeout = timeout
        self._token_acceso: str | None = None
        self._sesion = requests.Session()

    def establecer_token_acceso(self, token: str | None) -> None:
        """Almacena el JWT en memoria volátil para peticiones autenticadas."""
        self._token_acceso = token

    def cerrar_sesion(self) -> None:
        """Elimina el token de sesión de la memoria volátil."""
        self._token_acceso = None

    @property
    def token_acceso(self) -> str | None:
        """Retorna el token actual de sesión."""
        return self._token_acceso

    def _construir_cabeceras(self, prefer: str | None = None) -> dict[str, str]:
        cabeceras = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        if self._token_acceso:
            cabeceras["Authorization"] = f"Bearer {self._token_acceso}"
        else:
            cabeceras["Authorization"] = f"Bearer {self.anon_key}"

        if prefer:
            cabeceras["Prefer"] = prefer

        return cabeceras

    def _mapear_error(self, resp: requests.Response) -> None:
        codigo = resp.status_code
        try:
            detalle = resp.json()
        except ValueError:
            detalle = resp.text

        if codigo == 401:
            raise ErrorAutenticacion("Credenciales no válidas o sesión expirada", detalle)
        elif codigo == 403:
            raise ErrorAutorizacion("Acceso denegado por políticas de seguridad RLS", detalle)
        elif codigo == 404:
            raise RecursoNoEncontrado("Recurso o registro no encontrado", detalle)
        elif codigo == 409:
            raise ConflictoRevision("Conflicto de concurrencia o violación de clave única", detalle)
        elif codigo == 422:
            raise ErrorValidacion("Error de validación en los datos enviados", detalle)
        elif 500 <= codigo < 600:
            raise ErrorServidor("Error interno en Supabase / PostgreSQL", detalle)
        elif not resp.ok:
            raise ErrorPEA(f"Error HTTP {codigo}", detalle)

    def _ejecutar(
        self,
        metodo: str,
        ruta: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        prefer: str | None = None,
        headers_extra: dict[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}/{ruta.lstrip('/')}"
        cabeceras = self._construir_cabeceras(prefer=prefer)
        if headers_extra:
            cabeceras.update(headers_extra)

        try:
            resp = self._sesion.request(
                metodo,
                url,
                params=params,
                json=json_data,
                headers=cabeceras,
                timeout=self.timeout,
            )
        except requests.Timeout as err:
            raise ErrorConexion("Tiempo de espera agotado al conectar con Supabase", str(err)) from err
        except requests.RequestException as err:
            raise ErrorConexion("Fallo en la conexión de red HTTPS con Supabase", str(err)) from err

        self._mapear_error(resp)
        return resp

    def get(self, tabla: str, params: dict[str, Any] | None = None) -> Any:
        """Consulta registros de una tabla o vista mediante REST."""
        resp = self._ejecutar("GET", f"rest/v1/{tabla}", params=params)
        return resp.json() if resp.text else None

    def get_paginado(
        self,
        tabla: str,
        params: dict[str, Any] | None = None,
        lote_tamano: int = 1000,
    ) -> list[dict[str, Any]]:
        """Recupera todos los registros de una tabla paginando por rangos PostgREST."""
        resultado_total: list[dict[str, Any]] = []
        desde = 0
        parametros = dict(params or {})

        while True:
            hasta = desde + lote_tamano - 1
            headers = {
                "Range-Unit": "items",
                "Range": f"{desde}-{hasta}",
            }
            resp = self._ejecutar(
                "GET",
                f"rest/v1/{tabla}",
                params=parametros,
                headers_extra=headers,
            )
            lote = resp.json()
            if not isinstance(lote, list) or len(lote) == 0:
                break

            resultado_total.extend(lote)

            if len(lote) < lote_tamano:
                break

            desde += lote_tamano

        return resultado_total

    def post(self, tabla: str, datos: dict[str, Any] | list[dict[str, Any]]) -> Any:
        """Inserta registros retornando la representación creada."""
        resp = self._ejecutar(
            "POST",
            f"rest/v1/{tabla}",
            json_data=datos,
            prefer="return=representation",
        )
        return resp.json() if resp.text else None

    def patch(self, tabla: str, datos: dict[str, Any], params: dict[str, Any]) -> Any:
        """Actualiza registros existentes bajo los filtros dados."""
        resp = self._ejecutar(
            "PATCH",
            f"rest/v1/{tabla}",
            params=params,
            json_data=datos,
            prefer="return=representation",
        )
        return resp.json() if resp.text else None

    def eliminar(self, tabla: str, params: dict[str, Any]) -> None:
        """Elimina registros según los filtros dados."""
        self._ejecutar(
            "DELETE",
            f"rest/v1/{tabla}",
            params=params,
            prefer="return=representation",
        )

    def rpc(self, funcion: str, params: dict[str, Any] | None = None) -> Any:
        """Ejecuta una función RPC atómica en Supabase."""
        resp = self._ejecutar(
            "POST",
            f"rest/v1/rpc/{funcion}",
            json_data=params or {},
        )
        return resp.json() if resp.text else None
