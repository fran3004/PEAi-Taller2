"""Hipercubo multidimensional 5D para cálculo estadístico OLAP en memoria.

Dimensiones canónicas: Grupo × Investigador × Categoría × Año × Validación.
Medida: Conteo de productos activos que cumplan el criterio vigente.
Operaciones: acumular, desacumular, rebanada (slice), subcubo por ventana (dice) y enrollar (roll-up).
Conforme a AGENTS.md, Hipercubo.md, SPEC.md y ADR-0006.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NamedTuple

from pea.estructuras.lista_doble import ListaDoble


class Coordenada5D(NamedTuple):
    """Coordenada ortogonal en el espacio de 5 dimensiones."""

    grupo: str
    investigador: str
    categoria: str
    anio: int
    validacion: str


@dataclass
class CeldaHipercubo:
    """Contenido de una celda escalar en el hipercubo."""

    coordenada: Coordenada5D
    cantidad: int = 0
    peso_ponderado: float = 0.0

    def __post_init__(self) -> None:
        self.productos_ids: ListaDoble[str] = ListaDoble()

    def agregar_producto_id(self, producto_id: str) -> bool:
        if not producto_id:
            return False
        if self.productos_ids.buscar(lambda pid: pid == producto_id) is None:
            self.productos_ids.insertar_final(producto_id)
            return True
        return False

    def remover_producto_id(self, producto_id: str) -> bool:
        if not producto_id:
            return False
        eliminado = self.productos_ids.eliminar_por_criterio(lambda pid: pid == producto_id)
        return eliminado is not None


class Hipercubo5D:
    """Tensor pentadimensional disperso para agregaciones analíticas instantáneas."""

    DIM_GRUPO = "grupo"
    DIM_INVESTIGADOR = "investigador"
    DIM_CATEGORIA = "categoria"
    DIM_ANIO = "anio"
    DIM_VALIDACION = "validacion"

    DIMENSIONES_VALIDAS = {
        DIM_GRUPO,
        DIM_INVESTIGADOR,
        DIM_CATEGORIA,
        DIM_ANIO,
        DIM_VALIDACION,
    }

    def __init__(self) -> None:
        # Estructura propia hecha a mano para almacenar y recorrer celdas
        self._celdas: ListaDoble[CeldaHipercubo] = ListaDoble()
        # Índice auxiliar hash para acceso O(1) directo por coordenada (ADR-0006)
        self._indice: dict[Coordenada5D, CeldaHipercubo] = {}
        # Registro auxiliar (producto_id, Coordenada5D) para evitar duplicados en la misma celda
        self._productos_registrados: set[tuple[str, Coordenada5D]] = set()

    def __len__(self) -> int:
        return len(self._celdas)

    def esta_vacio(self) -> bool:
        return len(self._celdas) == 0

    def limpiar(self) -> None:
        """Reinicia el hipercubo a estado vacío."""
        self._celdas = ListaDoble()
        self._indice.clear()
        self._productos_registrados.clear()

    def obtener_celda(
        self,
        grupo: str,
        investigador: str,
        categoria: str,
        anio: int,
        validacion: str,
    ) -> CeldaHipercubo | None:
        """Retorna la celda en las coordenadas especificadas si existe."""
        coord = Coordenada5D(
            str(grupo or "SIN_GRUPO"),
            str(investigador or "SIN_INVESTIGADOR"),
            str(categoria or "GNC"),
            int(anio),
            str(validacion or "No avalado"),
        )
        return self._indice.get(coord)

    def acumular(
        self,
        grupo: str,
        investigador: str,
        categoria: str,
        anio: int,
        validacion: str,
        producto_id: str | None = None,
        peso: float = 1.0,
    ) -> None:
        """Incrementa la medida en la coordenada dada."""
        coord = Coordenada5D(
            str(grupo or "SIN_GRUPO"),
            str(investigador or "SIN_INVESTIGADOR"),
            str(categoria or "GNC"),
            int(anio),
            str(validacion or "No avalado"),
        )

        pid = str(producto_id or "").strip()
        if pid:
            clave_registro = (pid, coord)
            if clave_registro in self._productos_registrados:
                # Ya fue acumulado para esta coordenada exacta
                return
            self._productos_registrados.add(clave_registro)

        celda = self._indice.get(coord)
        if celda is None:
            celda = CeldaHipercubo(coordenada=coord, cantidad=1, peso_ponderado=float(peso))
            if pid:
                celda.agregar_producto_id(pid)
            self._indice[coord] = celda
            self._celdas.insertar_final(celda)
        else:
            celda.cantidad += 1
            celda.peso_ponderado += float(peso)
            if pid:
                celda.agregar_producto_id(pid)

    def desacumular(
        self,
        grupo: str,
        investigador: str,
        categoria: str,
        anio: int,
        validacion: str,
        producto_id: str | None = None,
        peso: float = 1.0,
    ) -> bool:
        """Decrementa la medida en la coordenada dada (ej. tras desactivar o eliminar)."""
        coord = Coordenada5D(
            str(grupo or "SIN_GRUPO"),
            str(investigador or "SIN_INVESTIGADOR"),
            str(categoria or "GNC"),
            int(anio),
            str(validacion or "No avalado"),
        )

        pid = str(producto_id or "").strip()
        if pid:
            clave_registro = (pid, coord)
            if clave_registro in self._productos_registrados:
                self._productos_registrados.remove(clave_registro)

        celda = self._indice.get(coord)
        if celda is None:
            return False

        celda.cantidad -= 1
        celda.peso_ponderado = max(0.0, celda.peso_ponderado - float(peso))
        if pid:
            celda.remover_producto_id(pid)

        if celda.cantidad <= 0:
            # Retirar de la estructura enlazada y del índice
            del self._indice[coord]
            self._celdas.eliminar_por_criterio(lambda c: c.coordenada == coord)

        return True

    def medida_total(self) -> int:
        """Suma total de cantidades en todas las celdas."""
        total = 0
        for celda in self._celdas:
            total += celda.cantidad
        return total

    def total_productos_unicos(self) -> int:
        """Retorna la cantidad de productos únicos distintos indexados."""
        unicos: set[str] = set()
        for pid, _ in self._productos_registrados:
            unicos.add(pid)
        if not unicos:
            # Si se acumuló sin IDs específicos, sumar la medida total
            return self.medida_total()
        return len(unicos)

    def rebanada(self, dimension: str, valor: Any) -> Hipercubo5D:
        """Operación Slice: fija una dimensión en un valor constante y retorna un nuevo hipercubo."""
        dim = dimension.lower().strip()
        if dim not in self.DIMENSIONES_VALIDAS:
            raise ValueError(f"Dimensión no válida: '{dimension}'. Válidas: {self.DIMENSIONES_VALIDAS}")

        nuevo_cubo = Hipercubo5D()

        for celda in self._celdas:
            c = celda.coordenada
            coincide = False
            if dim == self.DIM_GRUPO and c.grupo == str(valor):
                coincide = True
            elif dim == self.DIM_INVESTIGADOR and c.investigador == str(valor):
                coincide = True
            elif dim == self.DIM_CATEGORIA and c.categoria == str(valor):
                coincide = True
            elif dim == self.DIM_ANIO and c.anio == int(valor):
                coincide = True
            elif dim == self.DIM_VALIDACION and c.validacion == str(valor):
                coincide = True

            if coincide:
                # Copiar productos asociados
                if len(celda.productos_ids) > 0:
                    for pid in celda.productos_ids:
                        peso_unitario = (
                            celda.peso_ponderado / celda.cantidad if celda.cantidad > 0 else 1.0
                        )
                        nuevo_cubo.acumular(
                            c.grupo,
                            c.investigador,
                            c.categoria,
                            c.anio,
                            c.validacion,
                            producto_id=pid,
                            peso=peso_unitario,
                        )
                else:
                    for _ in range(celda.cantidad):
                        peso_unitario = (
                            celda.peso_ponderado / celda.cantidad if celda.cantidad > 0 else 1.0
                        )
                        nuevo_cubo.acumular(
                            c.grupo,
                            c.investigador,
                            c.categoria,
                            c.anio,
                            c.validacion,
                            peso=peso_unitario,
                        )

        return nuevo_cubo

    def subcubo_por_ventana(
        self,
        anio_inicio: int | None = None,
        anio_fin: int | None = None,
        categorias: set[str] | list[str] | None = None,
        grupos: set[str] | list[str] | None = None,
        investigadores: set[str] | list[str] | None = None,
        validaciones: set[str] | list[str] | None = None,
    ) -> Hipercubo5D:
        """Operación Dice: filtra un hipervolumen por rango de años y filtros opcionales."""
        set_cats = {str(c) for c in categorias} if categorias is not None else None
        set_grps = {str(g) for g in grupos} if grupos is not None else None
        set_invs = {str(i) for i in investigadores} if investigadores is not None else None
        set_vals = {str(v) for v in validaciones} if validaciones is not None else None

        nuevo_cubo = Hipercubo5D()

        for celda in self._celdas:
            c = celda.coordenada

            if anio_inicio is not None and c.anio < anio_inicio:
                continue
            if anio_fin is not None and c.anio > anio_fin:
                continue
            if set_cats is not None and c.categoria not in set_cats:
                continue
            if set_grps is not None and c.grupo not in set_grps:
                continue
            if set_invs is not None and c.investigador not in set_invs:
                continue
            if set_vals is not None and c.validacion not in set_vals:
                continue

            if len(celda.productos_ids) > 0:
                for pid in celda.productos_ids:
                    peso_unitario = (
                        celda.peso_ponderado / celda.cantidad if celda.cantidad > 0 else 1.0
                    )
                    nuevo_cubo.acumular(
                        c.grupo,
                        c.investigador,
                        c.categoria,
                        c.anio,
                        c.validacion,
                        producto_id=pid,
                        peso=peso_unitario,
                    )
            else:
                for _ in range(celda.cantidad):
                    peso_unitario = (
                        celda.peso_ponderado / celda.cantidad if celda.cantidad > 0 else 1.0
                    )
                    nuevo_cubo.acumular(
                        c.grupo,
                        c.investigador,
                        c.categoria,
                        c.anio,
                        c.validacion,
                        peso=peso_unitario,
                    )

        return nuevo_cubo

    def subcubo_modelo_2024(self, anio_corte: int = 2023) -> Hipercubo5D:
        """Aplica la ventana oficial del Modelo 2024 diferenciada por tipología.

        - Ventana estándar de 5 años (2019-2023 si anio_corte=2023): GNC ordinario, DTI, ASC, FRH.
        - Ventana ampliada de 10 años (2014-2023 si anio_corte=2023): Libros de investigación y patentes.
        """
        inicio_5 = anio_corte - 4
        inicio_10 = anio_corte - 9

        nuevo_cubo = Hipercubo5D()

        for celda in self._celdas:
            c = celda.coordenada
            if c.anio > anio_corte:
                continue

            # Determinación de ventana según tipología
            # Para celdas que representen libros o patentes, la ventana es de 10 años
            es_ventana_ampliada = False
            cat_upper = c.categoria.upper()
            if "LIBRO" in cat_upper or "PATENTE" in cat_upper or "VARIEDAD" in cat_upper:
                es_ventana_ampliada = True

            inicio_vigente = inicio_10 if es_ventana_ampliada else inicio_5
            if c.anio < inicio_vigente:
                continue

            if len(celda.productos_ids) > 0:
                for pid in celda.productos_ids:
                    peso_unitario = (
                        celda.peso_ponderado / celda.cantidad if celda.cantidad > 0 else 1.0
                    )
                    nuevo_cubo.acumular(
                        c.grupo,
                        c.investigador,
                        c.categoria,
                        c.anio,
                        c.validacion,
                        producto_id=pid,
                        peso=peso_unitario,
                    )
            else:
                for _ in range(celda.cantidad):
                    peso_unitario = (
                        celda.peso_ponderado / celda.cantidad if celda.cantidad > 0 else 1.0
                    )
                    nuevo_cubo.acumular(
                        c.grupo,
                        c.investigador,
                        c.categoria,
                        c.anio,
                        c.validacion,
                        peso=peso_unitario,
                    )

        return nuevo_cubo

    def enrollar(self, dimension: str) -> dict[Any, int]:
        """Operación Roll-up: colapsa las demás dimensiones y totaliza sobre la dimensión solicitada.

        Para evitar sobreconteo por coautorías entre investigadores cuando se agrupa
        por año, grupo, categoría o validación, se computa la cantidad de productos únicos.
        """
        dim = dimension.lower().strip()
        if dim not in self.DIMENSIONES_VALIDAS:
            raise ValueError(f"Dimensión no válida: '{dimension}'. Válidas: {self.DIMENSIONES_VALIDAS}")

        agrupacion: dict[Any, set[str]] = {}
        conteo_sin_id: dict[Any, int] = {}

        for celda in self._celdas:
            c = celda.coordenada
            if dim == self.DIM_GRUPO:
                clave = c.grupo
            elif dim == self.DIM_INVESTIGADOR:
                clave = c.investigador
            elif dim == self.DIM_CATEGORIA:
                clave = c.categoria
            elif dim == self.DIM_ANIO:
                clave = c.anio
            elif dim == self.DIM_VALIDACION:
                clave = c.validacion
            else:
                clave = "TODOS"

            if clave not in agrupacion:
                agrupacion[clave] = set()
                conteo_sin_id[clave] = 0

            if len(celda.productos_ids) > 0:
                for pid in celda.productos_ids:
                    agrupacion[clave].add(pid)
            else:
                conteo_sin_id[clave] += celda.cantidad

        resultado: dict[Any, int] = {}
        for clave, pids in agrupacion.items():
            if len(pids) > 0:
                resultado[clave] = len(pids) + conteo_sin_id[clave]
            else:
                resultado[clave] = conteo_sin_id[clave]

        return resultado

    def poblar_desde_multilista(self, multilista: Any) -> None:
        """Reconstruye el hipercubo a partir de los productos activos en la Multilista."""
        self.limpiar()

        if multilista is None:
            return

        for nodo in multilista.iterar_nodos():
            prod = nodo.producto
            # Regla de oro: solo se indexan productos activos
            if not getattr(prod, "activo", True):
                continue

            grupo = getattr(nodo.grupo, "codigo_gruplac", None) or "SIN_GRUPO"
            categoria = getattr(prod, "tipo_mayor", "GNC") or "GNC"
            subtipo = getattr(prod, "subtipo", "") or ""
            anio = int(getattr(prod, "ano", 2024))
            validacion = getattr(prod, "estado_validacion", "No avalado") or "No avalado"
            pid = getattr(prod, "codigo_identificador", "") or ""

            # Determinar si la categoría debe llevar especificación de libro/patente para la ventana
            if "LIB" in subtipo.upper():
                categoria_cubo = "GNC_LIBRO"
            elif "PA" in subtipo.upper() or "PATENTE" in subtipo.upper():
                categoria_cubo = "GNC_PATENTE"
            else:
                categoria_cubo = categoria

            # Ponderación según tipo o por defecto 1.0
            peso = 1.0

            autores_lista = nodo.autores
            if autores_lista is not None and len(autores_lista) > 0:
                for autor in autores_lista:
                    inv_codigo = (
                        getattr(autor, "codigo_rh", None)
                        or getattr(autor, "nombre", None)
                        or "SIN_INVESTIGADOR"
                    )
                    self.acumular(
                        grupo=grupo,
                        investigador=inv_codigo,
                        categoria=categoria_cubo,
                        anio=anio,
                        validacion=validacion,
                        producto_id=pid,
                        peso=peso,
                    )
            else:
                self.acumular(
                    grupo=grupo,
                    investigador="SIN_INVESTIGADOR",
                    categoria=categoria_cubo,
                    anio=anio,
                    validacion=validacion,
                    producto_id=pid,
                    peso=peso,
                )
