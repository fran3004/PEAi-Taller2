"""Lector robusto y tolerante a fallos para archivos CSV de PEA-i.

Características clave:
- Soporte para delimitadores coma (',') y punto y coma (';') con detección automática.
- Detección y eliminación automática de marcas BOM UTF-8 (soporte para 'utf-8-sig' y 'utf-8').
- Manejo canónico de comillas dobles y comillas escapadas.
- Tolerancia a filas corruptas o inválidas: registra advertencias y errores por fila sin abortar el procesamiento global.
- Mapeo directo y validado a entidades de dominio (Grupo, Investigador, Producto, FilaAutorCSV).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.ingesta.modelos import (
    FilaAutorCSV,
    FilaGrupoCSV,
    FilaInvestigadorCSV,
    FilaProductoCSV,
)


class LectorCSV:
    """Lector de archivos CSV con tolerancia a variaciones de formato y fallos de validación."""

    @staticmethod
    def detectar_delimitador(contenido: str) -> str:
        """Determina si el delimitador principal es coma (',') o punto y coma (';')."""
        primera_linea = contenido.splitlines()[0] if contenido.splitlines() else ""
        if ";" in primera_linea and "," not in primera_linea:
            return ";"
        if "," in primera_linea and ";" not in primera_linea:
            return ","

        # Si ambos están presentes, contar ocurrencias fuera de comillas
        cuenta_comas = primera_linea.count(",")
        cuenta_puntos_coma = primera_linea.count(";")
        return ";" if cuenta_puntos_coma > cuenta_comas else ","

    @staticmethod
    def leer_texto(ruta_csv: Path | str) -> tuple[str, str]:
        """Lee el contenido de un archivo CSV detectando UTF-8 con o sin BOM."""
        path = Path(ruta_csv)
        if not path.exists():
            raise FileNotFoundError(f"El archivo CSV no existe en la ruta: {path}")

        raw_bytes = path.read_bytes()
        # Si tiene BOM UTF-8 (\xef\xbb\xbf)
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            texto = raw_bytes.decode("utf-8-sig")
            return texto, "utf-8-sig"

        try:
            texto = raw_bytes.decode("utf-8")
            return texto, "utf-8"
        except UnicodeDecodeError:
            # Fallback a latin1
            texto = raw_bytes.decode("latin1")
            return texto, "latin1"

    @classmethod
    def obtener_lector_dict(
        cls,
        ruta_csv: Path | str,
        delimitador_fijo: str | None = None,
    ) -> tuple[csv.DictReader, list[str]]:
        """Devuelve un DictReader configurado y la lista de encabezados limpios."""
        texto, _ = cls.leer_texto(ruta_csv)
        delim = delimitador_fijo or cls.detectar_delimitador(texto)
        buffer = io.StringIO(texto)
        reader = csv.DictReader(buffer, delimiter=delim)
        # Limpiar encabezados de espacios o caracteres invisibles
        if reader.fieldnames:
            reader.fieldnames = [c.strip().lstrip("\ufeff") for c in reader.fieldnames if c]
        return reader, reader.fieldnames or []

    @classmethod
    def detectar_tipo_archivo(cls, ruta_csv: Path | str) -> str:
        """Identifica el tipo de entidad analizando los encabezados del archivo."""
        _, encabezados = cls.obtener_lector_dict(ruta_csv)
        enc_set = {h.lower() for h in encabezados}

        if "codigo_gruplac" in enc_set or "codigo_minciencias" in enc_set:
            return "grupos"
        if "codigo_cvlac" in enc_set or "codigo_rh" in enc_set:
            return "investigadores"
        if "producto_codigo" in enc_set and "investigador_codigo" in enc_set:
            return "autores"
        if "codigo_identificador" in enc_set or "tipo_mayor" in enc_set or "tipo_categoria" in enc_set:
            return "productos"

        return "desconocido"

    @classmethod
    def leer_grupos(
        cls,
        ruta_csv: Path | str,
        delimitador: str | None = None,
    ) -> tuple[list[Grupo], list[dict[str, Any]]]:
        """Lee grupos desde CSV. Reporta filas con error sin detener el proceso."""
        reader, _ = cls.obtener_lector_dict(ruta_csv, delimitador)
        grupos_validos: list[Grupo] = []
        errores: list[dict[str, Any]] = []

        for num_fila, fila in enumerate(reader, start=2):
            try:
                # Normalizar alias de columnas
                datos_fila: dict[str, Any] = {}
                for k, v in fila.items():
                    if k is None:
                        continue
                    k_limpio = k.strip()
                    val = v.strip() if isinstance(v, str) else v
                    if k_limpio in ("codigo_minciencias", "codigo_gruplac"):
                        datos_fila["codigo_gruplac"] = val
                    elif k_limpio in ("nombre", "nombre_grupo"):
                        datos_fila["nombre"] = val
                    elif k_limpio in ("clasificacion", "categoria"):
                        datos_fila["categoria"] = val
                    elif k_limpio in ("institucion", "institucion_principal"):
                        datos_fila["institucion_principal"] = val
                    else:
                        datos_fila[k_limpio] = val

                fila_validada = FilaGrupoCSV.model_validate(datos_fila)
                grupo = Grupo(
                    codigo_gruplac=fila_validada.codigo_gruplac,
                    nombre=fila_validada.nombre,
                    categoria=fila_validada.categoria,
                    lider=fila_validada.lider,
                    institucion_principal=fila_validada.institucion_principal,
                    pais=fila_validada.pais,
                    departamento_ciudad=fila_validada.departamento_ciudad,
                    gran_area_ocde=fila_validada.gran_area_ocde,
                    area_ocde=fila_validada.area_ocde,
                    activo=fila_validada.activo,
                    es_ejemplo=fila_validada.es_ejemplo,
                )
                grupos_validos.append(grupo)
            except Exception as err:
                errores.append({
                    "fila": num_fila,
                    "datos": fila,
                    "error": str(err),
                })

        return grupos_validos, errores

    @classmethod
    def leer_investigadores(
        cls,
        ruta_csv: Path | str,
        delimitador: str | None = None,
    ) -> tuple[list[Investigador], list[dict[str, Any]]]:
        """Lee investigadores desde CSV. Reporta filas con error sin detener el proceso."""
        reader, _ = cls.obtener_lector_dict(ruta_csv, delimitador)
        invs_validos: list[Investigador] = []
        errores: list[dict[str, Any]] = []

        for num_fila, fila in enumerate(reader, start=2):
            try:
                datos_fila: dict[str, Any] = {}
                for k, v in fila.items():
                    if k is None:
                        continue
                    k_limpio = k.strip()
                    val = v.strip() if isinstance(v, str) else v
                    if k_limpio in ("codigo_cvlac", "codigo_rh"):
                        datos_fila["codigo_rh"] = val
                    elif k_limpio in ("nombre_completo", "nombre"):
                        datos_fila["nombre_completo"] = val
                    elif k_limpio in ("categoria", "categoria_declarada"):
                        datos_fila["categoria"] = val
                    elif k_limpio in ("formacion_academica", "formacion"):
                        datos_fila["formacion_academica"] = val
                    else:
                        datos_fila[k_limpio] = val

                fila_validada = FilaInvestigadorCSV.model_validate(datos_fila)
                inv = Investigador(
                    codigo_rh=fila_validada.codigo_rh,
                    nombre_completo=fila_validada.nombre_completo,
                    categoria=fila_validada.categoria,
                    formacion_academica=fila_validada.formacion_academica,
                    nacionalidad=fila_validada.nacionalidad,
                    nombre_en_citas=fila_validada.nombre_en_citas,
                    documento_identidad=fila_validada.documento_identidad,
                    sexo=fila_validada.sexo,
                    activo=fila_validada.activo,
                    es_ejemplo=fila_validada.es_ejemplo,
                )
                invs_validos.append(inv)
            except Exception as err:
                errores.append({
                    "fila": num_fila,
                    "datos": fila,
                    "error": str(err),
                })

        return invs_validos, errores

    @classmethod
    def leer_productos(
        cls,
        ruta_csv: Path | str,
        delimitador: str | None = None,
    ) -> tuple[list[tuple[Producto, str | None]], list[dict[str, Any]]]:
        """Lee productos desde CSV retornando lista de pares (Producto, grupo_codigo opcional)."""
        reader, _ = cls.obtener_lector_dict(ruta_csv, delimitador)
        prods_validos: list[tuple[Producto, str | None]] = []
        errores: list[dict[str, Any]] = []

        for num_fila, fila in enumerate(reader, start=2):
            try:
                datos_fila: dict[str, Any] = {}
                for k, v in fila.items():
                    if k is None:
                        continue
                    k_limpio = k.strip()
                    val = v.strip() if isinstance(v, str) else v
                    if k_limpio in ("anio", "ano"):
                        datos_fila["ano"] = int(val) if val else 2024
                    elif k_limpio in ("tipo_categoria", "tipo_mayor"):
                        datos_fila["tipo_mayor"] = val
                    elif k_limpio in ("grupo_codigo", "codigo_gruplac"):
                        datos_fila["grupo_codigo"] = val
                    else:
                        datos_fila[k_limpio] = val

                fila_validada = FilaProductoCSV.model_validate(datos_fila)
                prod = Producto(
                    codigo_identificador=fila_validada.codigo_identificador,
                    titulo=fila_validada.titulo,
                    tipo_mayor=fila_validada.tipo_mayor,
                    subtipo=fila_validada.subtipo,
                    ano=fila_validada.ano,
                    mes=fila_validada.mes,
                    pais=fila_validada.pais,
                    estado_validacion=fila_validada.estado_validacion,
                    activo=fila_validada.activo,
                    es_ejemplo=fila_validada.es_ejemplo,
                )
                prods_validos.append((prod, fila_validada.grupo_codigo))
            except Exception as err:
                errores.append({
                    "fila": num_fila,
                    "datos": fila,
                    "error": str(err),
                })

        return prods_validos, errores

    @classmethod
    def leer_autores(
        cls,
        ruta_csv: Path | str,
        delimitador: str | None = None,
    ) -> tuple[list[FilaAutorCSV], list[dict[str, Any]]]:
        """Lee relaciones producto-autor desde autores.csv."""
        reader, _ = cls.obtener_lector_dict(ruta_csv, delimitador)
        autores_validos: list[FilaAutorCSV] = []
        errores: list[dict[str, Any]] = []

        for num_fila, fila in enumerate(reader, start=2):
            try:
                datos_fila: dict[str, Any] = {}
                for k, v in fila.items():
                    if k is None:
                        continue
                    k_limpio = k.strip()
                    val = v.strip() if isinstance(v, str) else v
                    datos_fila[k_limpio] = val

                fila_validada = FilaAutorCSV.model_validate(datos_fila)
                autores_validos.append(fila_validada)
            except Exception as err:
                errores.append({
                    "fila": num_fila,
                    "datos": fila,
                    "error": str(err),
                })

        return autores_validos, errores
