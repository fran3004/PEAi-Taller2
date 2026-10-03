"""Controlador y verificador de concurrencia optimista mediante meta.revision."""

from typing import Any

from pea.cliente_http import ClienteHTTPSupabase
from pea.excepciones import ConflictoRevision


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
        """Consulta el número de revisión vigente en Supabase."""
        try:
            # 1. Intentar por RPC rápida
            resultado = cliente.rpc("obtener_revision_actual")
            if isinstance(resultado, int):
                return resultado
            if isinstance(resultado, dict) and "revision" in resultado:
                return int(resultado["revision"])
        except Exception:
            pass

        # 2. Respaldo por consulta REST a tabla meta
        filas: Any = cliente.get("meta", params={"select": "revision", "id": "eq.1"})
        if isinstance(filas, list) and len(filas) > 0:
            return int(filas[0].get("revision", 1))

        return self._revision_local

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
