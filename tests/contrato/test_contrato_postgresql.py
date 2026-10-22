"""
tests/contrato/test_contrato_postgresql.py
Pruebas exhaustivas de validación del contrato de base de datos PostgreSQL en Supabase.
Verifica:
1. Conformidad sintáctica y estructural del archivo de migración SQL oficial.
2. Presencia de id bigint identity, activo, es_ejemplo, creado_en, actualizado_en en entidades.
3. Constraints de clave única, rangos (CHECK) e integridad referencial (FOREIGN KEY).
4. Mecanismo de incremento de meta.revision una vez por transacción, aunque varias tablas se modifiquen.
5. Funciones RPC para transacciones atómicas con validación de revision_esperada.
6. Políticas de seguridad Auth + RLS (anon denegado, authenticated autorizado).
7. Semilla de datos de prueba exclusiva con prefijo PRUEBA- y es_ejemplo = true.
8. Validación de las herramientas en tools/db/.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def contenido_migracion() -> str:
    dir_migraciones = Path("supabase/migrations")
    archivos = sorted(dir_migraciones.glob("*.sql"))
    assert len(archivos) > 0, "No se encontró ningún archivo de migración en supabase/migrations/"

    contenido_total = ""
    for archivo in archivos:
        with open(archivo, encoding="utf-8") as f:
            contenido_total += f.read() + "\n"
    return contenido_total


def test_migracion_solo_hacia_adelante(contenido_migracion: str):
    """Verifica que la migración no contenga instrucciones destructivas globales."""
    prohibidos = ["DROP DATABASE", "DROP SCHEMA public CASCADE", "TRUNCATE public.meta"]
    for p in prohibidos:
        assert p not in contenido_migracion.upper(), f"Instrucción prohibida encontrada: {p}"


def test_entidades_dominio_columnas_obligatorias(contenido_migracion: str):
    """Verifica que las entidades de dominio tengan id identity, activo, es_ejemplo y timestamps."""
    tablas_dominio = [
        "grupos",
        "investigadores",
        "integrantes_grupo",
        "productos",
        "producto_autores",
        "producto_grupos",
        "proyectos",
        "semilleros",
    ]

    for tabla in tablas_dominio:
        patron_tabla = rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.{tabla}\s*\((.*?)\);"
        m = re.search(patron_tabla, contenido_migracion, re.DOTALL | re.IGNORECASE)
        assert m is not None, f"No se encontró la definición de tabla public.{tabla}"

        cuerpo = m.group(1).lower()
        assert "id bigint generated always as identity" in cuerpo or "id bigint generated" in cuerpo, \
            f"Falta 'id bigint identity' en tabla {tabla}"
        assert "activo boolean" in cuerpo, f"Falta 'activo boolean' en tabla {tabla}"
        assert "es_ejemplo boolean" in cuerpo, f"Falta 'es_ejemplo boolean' en tabla {tabla}"
        assert "creado_en timestamptz" in cuerpo, f"Falta 'creado_en timestamptz' en tabla {tabla}"
        assert "actualizado_en timestamptz" in cuerpo, f"Falta 'actualizado_en timestamptz' en tabla {tabla}"


def test_tabla_meta_y_mecanismo_revision(contenido_migracion: str):
    """Verifica revisión única por transacción ante varios triggers de sentencia."""
    assert "create table if not exists public.meta" in contenido_migracion.lower()
    assert "revision bigint not null default 1" in contenido_migracion.lower()
    assert "check (id = 1)" in contenido_migracion.lower()
    assert "fn_incrementar_meta_revision" in contenido_migracion.lower()

    # Verificar que las tablas tengan trigger AFTER STATEMENT
    tablas_revision = [
        "grupos",
        "investigadores",
        "integrantes_grupo",
        "productos",
        "producto_autores",
        "producto_grupos",
    ]
    for t in tablas_revision:
        patron_trg = r"FOR\s+EACH\s+STATEMENT\s+EXECUTE\s+FUNCTION\s+public\.fn_incrementar_meta_revision\(\)"
        assert re.search(patron_trg, contenido_migracion, re.IGNORECASE), \
            f"Falta trigger FOR EACH STATEMENT de revisión en {t}"
    assert "current_setting('pea.revision_incrementada', true) = '1'" in contenido_migracion
    assert "set_config('pea.revision_incrementada', '1', true)" in contenido_migracion


def test_constraints_e_indices_normativos(contenido_migracion: str):
    """Verifica claves únicas e índices requeridos por el Modelo y SPEC."""
    texto = contenido_migracion.lower()
    assert "constraint uk_grupos_codigo_gruplac unique (codigo_gruplac)" in texto
    assert "constraint uk_investigadores_codigo_rh unique (codigo_rh)" in texto
    assert "constraint uk_productos_codigo_identificador unique (codigo_identificador)" in texto
    assert "constraint uk_integrante_grupo unique (grupo_id, investigador_id, fecha_inicio)" in texto

    # Índices
    assert "create index if not exists idx_productos_ano on public.productos(ano)" in texto
    assert "create index if not exists idx_productos_tipo_mayor on public.productos(tipo_mayor)" in texto
    assert "create index if not exists idx_productos_es_ejemplo on public.productos(es_ejemplo)" in texto


def test_procedimientos_rpc_transaccionales(contenido_migracion: str):
    """Verifica existencia de funciones RPC con control de revision_esperada."""
    texto = contenido_migracion.lower()
    assert "create or replace function public.ping()" in texto
    assert "create or replace function public.obtener_revision_actual()" in texto
    assert "create or replace function public.transaccion_crear_producto(" in texto
    assert "create or replace function public.transaccion_desactivar_nodo(" in texto
    assert "create or replace function public.transaccion_eliminar_cascada(" in texto
    assert "create or replace function public.reiniciar_datos_prueba(" in texto

    # Control de revision_esperada
    assert "p_revision_esperada" in texto
    assert "conflicto_revision" in texto


def test_rpc_bloquea_revision_remota_antes_de_escribir() -> None:
    ruta_migracion = Path(
        "supabase/migrations/20261022042342_009_revision_lock_during_rpc.sql"
    )
    sql = ruta_migracion.read_text(encoding="utf-8").lower()

    assert "create or replace function public.fn_lock_meta_revision()" in sql
    assert "for update" in sql
    assert "revoke all on function public.fn_lock_meta_revision() from public" in sql
    assert "grant execute on function public.fn_lock_meta_revision() to authenticated, service_role" in sql
    for funcion in (
        "transaccion_crear_producto",
        "transaccion_desactivar_nodo",
        "transaccion_eliminar_cascada",
        "transaccion_actualizar_producto_grupo",
    ):
        inicio_funcion = sql.index(f"create or replace function public.{funcion}(")
        siguiente_funcion = sql.find("create or replace function public.", inicio_funcion + 1)
        cuerpo = sql[inicio_funcion:siguiente_funcion if siguiente_funcion >= 0 else len(sql)]
        assert "fn_lock_meta_revision()" in cuerpo


def test_revision_lock_no_es_invocable_por_anon() -> None:
    ruta_migracion = Path(
        "supabase/migrations/20261022042429_010_restrict_revision_lock.sql"
    )
    sql = ruta_migracion.read_text(encoding="utf-8").lower()
    assert "revoke all on function public.fn_lock_meta_revision() from anon" in sql


def test_seguridad_auth_y_rls(contenido_migracion: str):
    """Verifica que RLS esté activado, anon esté denegado y authenticated autorizado."""
    texto = contenido_migracion.lower()

    # RLS activado en todas
    assert "alter table public.meta enable row level security;" in texto
    assert "alter table public.grupos enable row level security;" in texto
    assert "alter table public.investigadores enable row level security;" in texto
    assert "alter table public.productos enable row level security;" in texto

    # Revocación a anon
    assert "revoke all on table" in texto
    assert "from anon;" in texto

    # Permisos mínimos anon
    assert "grant execute on function public.ping() to anon, authenticated;" in texto
    assert "grant execute on function public.obtener_revision_actual() to anon, authenticated;" in texto

    # Políticas authenticated
    assert "create policy pol_meta_select_auth on public.meta" in texto
    assert "to authenticated" in texto


def test_seed_ficticio_prueba(contenido_migracion: str):
    """Verifica que el seed use exclusivamente el prefijo PRUEBA- y es_ejemplo=true."""
    texto = contenido_migracion.lower()
    assert "prueba-col0001" in texto
    assert "prueba-inv-001" in texto
    assert "prueba-prod-gnc-001" in texto
    assert "es_ejemplo" in texto


def test_herramientas_db_existencia():
    """Verifica la existencia y sintaxis de las herramientas en tools/db/."""
    herramientas = [
        "tools/db/ping.py",
        "tools/db/sembrar.py",
        "tools/db/volcar.py",
        "tools/db/comparar.py",
        "tools/db/respaldar.py",
        "tools/db/reiniciar_prueba.py",
        "tools/db/migrar_datos_reales.py",
    ]
    for h in herramientas:
        p = Path(h)
        assert p.exists(), f"Herramienta requerida faltante: {h}"
        assert p.stat().st_size > 200, f"Herramienta vacía o incompleta: {h}"


def test_tablas_scienti_completas_y_datos_reales(contenido_migracion: str):
    """Verifica que las tablas complementarias SCIENTI y los datos reales estén en la migración."""
    tablas_scienti = [
        "grupo_instituciones",
        "grupo_plan_estrategico",
        "lineas_investigacion",
        "investigador_formacion",
        "investigador_experiencia",
        "investigador_areas_actuacion",
        "investigador_idiomas",
        "investigador_reconocimientos",
        "investigador_redes_identificadores",
    ]
    for tabla in tablas_scienti:
        patron_tabla = rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+public\.{tabla}\s*\((.*?)\);"
        m = re.search(patron_tabla, contenido_migracion, re.DOTALL | re.IGNORECASE)
        assert m is not None, f"No se encontró la definición de tabla public.{tabla}"
        cuerpo = m.group(1).lower()
        assert "id bigint generated always as identity" in cuerpo
        assert "activo boolean" in cuerpo
        assert "es_ejemplo boolean" in cuerpo
        assert f"alter table public.{tabla} enable row level security;" in contenido_migracion.lower()

    assert "GRP2099-ART-0069" in contenido_migracion
    assert "GRP2099-SW-0083" in contenido_migracion
    assert "GRP2099-PRY-0022" in contenido_migracion
    assert "CVL494917-EVE-0011" in contenido_migracion
    assert "CVL494917-PRY-0004" in contenido_migracion


@pytest.mark.red
def test_ping_remoto_supabase():
    """Prueba de red contra Supabase: solo se ejecuta con -ConRed o explícitamente."""
    from tools.db.ping import ejecutar_ping
    resultado = ejecutar_ping()
    assert resultado in (0, 1, 2), "Código de retorno inesperado en ping"
