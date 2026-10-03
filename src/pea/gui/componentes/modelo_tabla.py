"""Modelo de tabla Qt basado en TablaDatos con ordenamiento y alineación."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from pea.servicios.vistas import TablaDatos


class ModeloTabla(QAbstractTableModel):
    """Presenta un objeto inmutable TablaDatos en un QTableView."""

    def __init__(self, tabla: TablaDatos | None = None, parent: Any = None) -> None:
        super().__init__(parent)
        self._tabla = tabla or TablaDatos(columnas=(), filas=())

    def establecer_tabla(self, tabla: TablaDatos) -> None:
        self.beginResetModel()
        self._tabla = tabla
        self.endResetModel()

    @property
    def tabla_actual(self) -> TablaDatos:
        return self._tabla

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._tabla.filas)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._tabla.columnas)


    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        fila = index.row()
        col = index.column()
        if fila < 0 or fila >= len(self._tabla.filas):
            return None
        if col < 0 or col >= len(self._tabla.columnas):
            return None

        valor = self._tabla.filas[fila][col]

        if role == Qt.ItemDataRole.DisplayRole:
            if valor is None:
                return "—"
            if isinstance(valor, bool):
                return "Sí" if valor else "No"
            return str(valor)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(valor, (int, float)):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._tabla.columnas):
                    return self._tabla.columnas[section]
            else:
                return str(section + 1)
        return None

    def obtener_clave_fila(self, fila: int) -> str | None:
        if 0 <= fila < len(self._tabla.claves):
            return self._tabla.claves[fila]
        return None
