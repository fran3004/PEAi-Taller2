"""Controlador y verificador de concurrencia optimista mediante meta.revision."""

from typing import Any

from pea.cliente_http import ClienteHTTPSupabase
from pea.excepciones import ConflictoRevision, ErrorConexion


def _revision_valida(valor: Any) -> int | None:
    """Devuelve la revisión si es un entero mayor que cero; en otro caso None (igual que C++)."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, float):
        if not valor.is_integer():
            return None
        valor = int(valor)
    if isinstance(valor, str):
        try:
            valor = int(valor.strip())
        except ValueError:
            return None
    if isinstance(valor, int) and valor > 0:
        return valor
    return None


class ControladorRevision:
    """Gestiona la revisión local y comprueba conflictos con la base remota."""

    def __init__(self, revision_inicial: int = 1) -> None:
        self._revision_local: int = revision_inicial

    @property
    def revision_local(self) -> int:
        return self._revision_local

    def actualizar_local(self, nueva_revision: int) -> None:
        """Actualiza el número de revisión local."""
        self._revision_local = nueva_revision

    def consultar_remota(self, cliente: ClienteHTTPSupabase) -> int:
        """Consulta el número de revisión vigente en Supabase.

        Solo acepta revisiones mayores que cero. Si ni la RPC ni la tabla meta entregan una
        válida, lanza ErrorConexion: nunca se da por sincronizado lo que no se pudo comprobar.
        """
        # 1. Intentar por RPC rápida
        error_rpc = "La RPC no devolvió una revisión válida."
        try:
            resultado: Any = cliente.rpc("obtener_revision_actual")
            if isinstance(resultado, dict):
                resultado = resultado.get("revision")
            revision = _revision_valida(resultado)
            if revision is not None:
                return revision
        except Exception as err:
            error_rpc = str(err) or type(err).__name__

        # 2. Respaldo por consulta REST a tabla meta
        error_meta = "La tabla meta no devolvió una revisión válida."
        try:
            filas: Any = cliente.get("meta", params={"select": "revision", "id": "eq.1"})
            if isinstance(filas, list) and filas and isinstance(filas[0], dict):
                revision = _revision_valida(filas[0].get("revision"))
                if revision is not None:
                    return revision
        except Exception as err:
            error_meta = str(err) or type(err).__name__

        raise ErrorConexion(
            f"No fue posible verificar la revisión remota. RPC: {error_rpc} Consulta meta: {error_meta}"
        )

    def verificar_consistencia(self, cliente: ClienteHTTPSupabase) -> None:
        """Verifica que la revisión remota sea idéntica a la esperada localmente.

        Lanza ConflictoRevision si la base de datos cambió.
        """
        remota = self.consultar_remota(cliente)
        if remota != self._revision_local:
            raise ConflictoRevision(
                "La base de datos cambió",
                f"Revisión remota: {remota}, Revisión local esperada: {self._revision_local}",
            )

    def sincronizar(self, cliente: ClienteHTTPSupabase) -> int:
        """Actualiza la revisión local con el valor remoto más reciente."""
        self._revision_local = self.consultar_remota(cliente)
        return self._revision_local
