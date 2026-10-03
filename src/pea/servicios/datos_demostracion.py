"""Datos de demostración ficticios para el modo sin base de datos y la autoprueba de la GUI.

Todos los registros son inventados, llevan es_ejemplo=True y el prefijo PRUEBA- en su código,
de modo que, aunque alguien los persistiera por error, cumplirían la regla del modo prueba
(AGENTS.md: solo filas es_ejemplo=true con prefijo PRUEBA-). Ningún nombre corresponde a
personas reales. El conjunto es determinista: siempre produce las mismas entidades.
"""

from __future__ import annotations

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.servicios.servicio_dominio import CatalogoInvestigacion

# Tablas de semillas (variables temporales de construcción, no almacenamiento de entidades).
_GRUPOS: tuple[tuple[str, str, str, str], ...] = (
    ("PRUEBA-GRP-001", "Grupo Ficticio de Ingeniería de Software", "A1", "Investigadora Ficticia Uno"),
    ("PRUEBA-GRP-002", "Grupo Ficticio de Ciencias Agropecuarias", "B", "Investigador Ficticio Cinco"),
    ("PRUEBA-GRP-003", "Grupo Ficticio de Estudios Sociales", "C", "Investigadora Ficticia Nueve"),
)

_CATEGORIAS_INV: tuple[str, ...] = ("Senior", "Asociado", "Junior", "Sin categoria")
_FORMACION: tuple[str, ...] = ("Doctorado", "Maestria", "Especializacion", "Pregrado")
_NOMBRES: tuple[str, ...] = (
    "Investigadora Ficticia Uno",
    "Investigador Ficticio Dos",
    "Investigadora Ficticia Tres",
    "Investigador Ficticio Cuatro",
    "Investigador Ficticio Cinco",
    "Investigadora Ficticia Seis",
    "Investigador Ficticio Siete",
    "Investigadora Ficticia Ocho",
    "Investigadora Ficticia Nueve",
    "Investigador Ficticio Diez",
    "Investigadora Ficticia Once",
    "Investigador Ficticio Doce",
)

# (tipo_mayor, subtipo) evitando subtipos ambiguos para la heurística libro/patente del hipercubo.
_TIPOS: tuple[tuple[str, str], ...] = (
    ("GNC", "Artículo de investigación"),
    ("GNC", "Libro resultado de investigación"),
    ("GNC", "Capítulo de investigación"),
    ("DTI", "Software registrado"),
    ("DTI", "Prototipo industrial"),
    ("ASC", "Evento científico"),
    ("ASC", "Comunicación del conocimiento"),
    ("FRH", "Tesis de maestría dirigida"),
    ("FRH", "Trabajo de grado dirigido"),
)
_VALIDACIONES: tuple[str, ...] = ("Avalado", "Con soporte", "No avalado")

TOTAL_GRUPOS_DEMO = len(_GRUPOS)
TOTAL_INVESTIGADORES_DEMO = len(_NOMBRES)
TOTAL_PRODUCTOS_DEMO = 42


def cargar_datos_demostracion(catalogo: CatalogoInvestigacion) -> None:
    """Puebla el catálogo en memoria (sin persistir) con el conjunto ficticio determinista."""
    for codigo, nombre, categoria, lider in _GRUPOS:
        catalogo.crear_grupo(
            Grupo(
                codigo_gruplac=codigo,
                nombre=nombre,
                categoria=categoria,
                lider=lider,
                departamento_ciudad="Cesar - Valledupar",
                es_ejemplo=True,
            ),
            persistir=False,
        )

    for indice, nombre in enumerate(_NOMBRES):
        codigo_rh = f"PRUEBA-INV-{indice + 1:03d}"
        catalogo.crear_investigador(
            Investigador(
                codigo_rh=codigo_rh,
                nombre_completo=nombre,
                categoria=_CATEGORIAS_INV[indice % len(_CATEGORIAS_INV)],
                formacion_academica=_FORMACION[indice % len(_FORMACION)],
                es_ejemplo=True,
            ),
            persistir=False,
        )
        # Cuatro investigadores por grupo; el primero de cada bloque es líder.
        codigo_grupo = _GRUPOS[indice // 4][0]
        rol = "Lider" if indice % 4 == 0 else "Investigador"
        catalogo.vincular_integrante(codigo_grupo, codigo_rh, rol=rol, persistir=False)

    for n in range(TOTAL_PRODUCTOS_DEMO):
        tipo_mayor, subtipo = _TIPOS[(n * 5) % len(_TIPOS)]
        indice_grupo = n % len(_GRUPOS)
        codigo_grupo = _GRUPOS[indice_grupo][0]
        # Autor principal dentro del grupo y, cada tercer producto, un coautor del mismo grupo.
        base = indice_grupo * 4
        autor_principal = f"PRUEBA-INV-{base + (n % 4) + 1:03d}"
        autores = [autor_principal]
        if n % 3 == 0:
            autores.append(f"PRUEBA-INV-{base + ((n + 1) % 4) + 1:03d}")
        producto = Producto(
            codigo_identificador=f"PRUEBA-PROD-{n + 1:03d}",
            titulo=f"Producto ficticio {n + 1:02d}: {subtipo.lower()}",
            tipo_mayor=tipo_mayor,
            subtipo=subtipo,
            ano=2015 + (n * 7) % 11,
            estado_validacion=_VALIDACIONES[(n * 2) % len(_VALIDACIONES)],
            es_ejemplo=True,
        )
        catalogo.crear_producto(producto, codigo_gruplac=codigo_grupo, codigos_rh_autores=autores, persistir=False)

    # Un producto desactivado para que la interfaz muestre ambos estados.
    catalogo.desactivar_producto("PRUEBA-PROD-042", persistir=False)

    # La carga de demostración no es una acción del usuario: no debe poder deshacerse.
    catalogo.pila_deshacer.limpiar()
    catalogo.sincronizar_hipercubo()
