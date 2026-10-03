-- ============================================================================
-- PEA-i: Migración Inicial de Esquema, Control de Revisión, RPC, Auth y RLS
-- Archivo: supabase/migrations/20261003055532_001_esquema_inicial.sql
-- ============================================================================

-- 1. EXTENSIONES Y CONFIGURACIÓN INICIAL
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. TABLA DE CONTROL DE REVISIÓN Y ENTORNO (meta)
CREATE TABLE IF NOT EXISTS public.meta (
    id integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    revision bigint NOT NULL DEFAULT 1,
    entorno varchar(32) NOT NULL DEFAULT 'produccion',
    ultima_modificacion timestamptz NOT NULL DEFAULT now(),
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now()
);

-- Fila única obligatoria
INSERT INTO public.meta (id, revision, entorno, ultima_modificacion, creado_en, actualizado_en)
VALUES (1, 1, 'produccion', now(), now(), now())
ON CONFLICT (id) DO NOTHING;

-- Función de incremento de meta.revision (ejecutada en triggers AFTER STATEMENT)
CREATE OR REPLACE FUNCTION public.fn_incrementar_meta_revision()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    UPDATE public.meta
    SET revision = revision + 1,
        ultima_modificacion = now(),
        actualizado_en = now()
    WHERE id = 1;
    RETURN NULL;
END;
$$;

-- Función de actualización de columna actualizado_en (FOR EACH ROW)
CREATE OR REPLACE FUNCTION public.fn_actualizar_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.actualizado_en = now();
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 3. TABLAS DEL DOMINIO PRINCIPAL
-- ============================================================================

-- 3.1 Grupos de Investigación
CREATE TABLE IF NOT EXISTS public.grupos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_gruplac varchar(30) NOT NULL,
    nombre varchar(255) NOT NULL,
    fecha_creacion varchar(10) NOT NULL,
    pais varchar(50) NOT NULL DEFAULT 'Colombia',
    departamento_ciudad varchar(100) NOT NULL,
    lider varchar(255) NOT NULL,
    institucion_principal varchar(255) NOT NULL,
    gran_area_ocde varchar(100) NOT NULL,
    area_ocde varchar(100) NOT NULL,
    categoria varchar(50) NOT NULL CHECK (categoria IN ('A1', 'A', 'B', 'C', 'Reconocido')),
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_grupos_codigo_gruplac UNIQUE (codigo_gruplac)
);

-- 3.2 Investigadores
CREATE TABLE IF NOT EXISTS public.investigadores (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_rh varchar(30) NOT NULL,
    nombre_completo varchar(255) NOT NULL,
    nombre_en_citas varchar(255),
    nacionalidad varchar(50) NOT NULL DEFAULT 'Colombia',
    sexo varchar(20) NOT NULL,
    categoria varchar(60) NOT NULL CHECK (
        categoria IN (
            'Investigador Emérito', 'Investigador Senior', 'Investigador Asociado',
            'Investigador Junior', 'Sin categoría / Vinculado',
            'Investigador Emerito', 'Sin categoria / Vinculado'
        )
    ),
    formacion_academica varchar(100) NOT NULL CHECK (
        formacion_academica IN ('Doctorado', 'Maestría', 'Especialización', 'Pregrado', 'Maestria', 'Especializacion')
    ),
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_investigadores_codigo_rh UNIQUE (codigo_rh)
);

-- 3.3 Integrantes de Grupo (Membresía / Vinculación)
CREATE TABLE IF NOT EXISTS public.integrantes_grupo (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grupo_id bigint NOT NULL REFERENCES public.grupos(id) ON DELETE CASCADE,
    investigador_id bigint NOT NULL REFERENCES public.investigadores(id) ON DELETE CASCADE,
    rol varchar(50) NOT NULL CHECK (rol IN ('Líder', 'Investigador', 'Estudiante', 'Lider')),
    fecha_inicio varchar(10) NOT NULL,
    fecha_fin varchar(10),
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_integrante_grupo UNIQUE (grupo_id, investigador_id, fecha_inicio)
);

-- 3.4 Productos de Investigación
CREATE TABLE IF NOT EXISTS public.productos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_identificador varchar(100) NOT NULL,
    titulo text NOT NULL,
    tipo_mayor varchar(10) NOT NULL CHECK (tipo_mayor IN ('GNC', 'DTI', 'ASC', 'FRH')),
    subtipo varchar(100) NOT NULL,
    ano integer NOT NULL CHECK (ano >= 1970 AND ano <= 2100),
    mes integer CHECK (mes IS NULL OR (mes >= 1 AND mes <= 12)),
    pais varchar(50),
    estado_validacion varchar(50) NOT NULL CHECK (estado_validacion IN ('Avalado', 'Con soporte', 'No avalado')),
    detalles jsonb NOT NULL DEFAULT '{}'::jsonb,
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_productos_codigo_identificador UNIQUE (codigo_identificador)
);

-- 3.5 Autores de Producto (Coautoría cruzada)
CREATE TABLE IF NOT EXISTS public.producto_autores (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    producto_id bigint NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    investigador_id bigint NOT NULL REFERENCES public.investigadores(id) ON DELETE CASCADE,
    orden_autoria integer NOT NULL DEFAULT 1,
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_producto_autor UNIQUE (producto_id, investigador_id)
);

-- 3.6 Grupos que declaran el Producto
CREATE TABLE IF NOT EXISTS public.producto_grupos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    producto_id bigint NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    grupo_id bigint NOT NULL REFERENCES public.grupos(id) ON DELETE CASCADE,
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_producto_grupo UNIQUE (producto_id, grupo_id)
);

-- 3.7 Proyectos (Vistas secundarias P2)
CREATE TABLE IF NOT EXISTS public.proyectos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grupo_id bigint NOT NULL REFERENCES public.grupos(id) ON DELETE CASCADE,
    codigo_proyecto varchar(100),
    nombre text NOT NULL,
    tipo varchar(100),
    ano_inicio integer,
    ano_fin integer,
    estado varchar(50),
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now()
);

-- 3.8 Semilleros (Vistas secundarias P2)
CREATE TABLE IF NOT EXISTS public.semilleros (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grupo_id bigint NOT NULL REFERENCES public.grupos(id) ON DELETE CASCADE,
    nombre varchar(255) NOT NULL,
    lider varchar(255),
    activo boolean NOT NULL DEFAULT true,
    es_ejemplo boolean NOT NULL DEFAULT false,
    creado_en timestamptz NOT NULL DEFAULT now(),
    actualizado_en timestamptz NOT NULL DEFAULT now()
);

-- 3.9 Tabla de Auditoría
CREATE TABLE IF NOT EXISTS public.auditoria_cambios (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id uuid,
    tabla_nombre varchar(60) NOT NULL,
    operacion varchar(20) NOT NULL,
    registro_id bigint,
    datos_anteriores jsonb,
    datos_nuevos jsonb,
    creado_en timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- 4. ÍNDICES DE RENDIMIENTO Y CONSULTA
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_grupos_es_ejemplo ON public.grupos(es_ejemplo);
CREATE INDEX IF NOT EXISTS idx_investigadores_es_ejemplo ON public.investigadores(es_ejemplo);
CREATE INDEX IF NOT EXISTS idx_productos_ano ON public.productos(ano);
CREATE INDEX IF NOT EXISTS idx_productos_tipo_mayor ON public.productos(tipo_mayor);
CREATE INDEX IF NOT EXISTS idx_productos_estado_val ON public.productos(estado_validacion);
CREATE INDEX IF NOT EXISTS idx_productos_es_ejemplo ON public.productos(es_ejemplo);
CREATE INDEX IF NOT EXISTS idx_integrantes_grupo_grupo ON public.integrantes_grupo(grupo_id);
CREATE INDEX IF NOT EXISTS idx_integrantes_grupo_inv ON public.integrantes_grupo(investigador_id);
CREATE INDEX IF NOT EXISTS idx_producto_autores_prod ON public.producto_autores(producto_id);
CREATE INDEX IF NOT EXISTS idx_producto_autores_inv ON public.producto_autores(investigador_id);
CREATE INDEX IF NOT EXISTS idx_producto_grupos_prod ON public.producto_grupos(producto_id);
CREATE INDEX IF NOT EXISTS idx_producto_grupos_grupo ON public.producto_grupos(grupo_id);

-- ============================================================================
-- 5. TRIGGERS DE ACTUALIZACIÓN DE TIMESTAMPS (FOR EACH ROW)
-- ============================================================================

CREATE OR REPLACE TRIGGER trg_grupos_timestamp
    BEFORE UPDATE ON public.grupos
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_investigadores_timestamp
    BEFORE UPDATE ON public.investigadores
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_integrantes_timestamp
    BEFORE UPDATE ON public.integrantes_grupo
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_productos_timestamp
    BEFORE UPDATE ON public.productos
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_producto_autores_timestamp
    BEFORE UPDATE ON public.producto_autores
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_producto_grupos_timestamp
    BEFORE UPDATE ON public.producto_grupos
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_proyectos_timestamp
    BEFORE UPDATE ON public.proyectos
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE TRIGGER trg_semilleros_timestamp
    BEFORE UPDATE ON public.semilleros
    FOR EACH ROW EXECUTE FUNCTION public.fn_actualizar_timestamp();

-- ============================================================================
-- 6. TRIGGERS DE INCREMENTO DE REVISIÓN GLOBAL (FOR EACH STATEMENT)
-- ============================================================================

CREATE OR REPLACE TRIGGER trg_stmt_grupos_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.grupos
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_investigadores_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.investigadores
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_integrantes_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.integrantes_grupo
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_productos_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.productos
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_producto_autores_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.producto_autores
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_producto_grupos_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.producto_grupos
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_proyectos_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.proyectos
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

CREATE OR REPLACE TRIGGER trg_stmt_semilleros_revision
    AFTER INSERT OR UPDATE OR DELETE ON public.semilleros
    FOR EACH STATEMENT EXECUTE FUNCTION public.fn_incrementar_meta_revision();

-- ============================================================================
-- 7. PROCEDIMIENTOS ALMACENADOS (RPC) TRANSACCIONALES
-- ============================================================================

-- 7.1 ping() - Estado del servidor y keep-alive
CREATE OR REPLACE FUNCTION public.ping()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_rev bigint;
BEGIN
    SELECT revision INTO v_rev FROM public.meta WHERE id = 1;
    RETURN jsonb_build_object(
        'estado', 'ok',
        'revision', coalesce(v_rev, 1),
        'hora', now()
    );
END;
$$;

-- 7.2 obtener_revision_actual() - Consulta rápida de versión
CREATE OR REPLACE FUNCTION public.obtener_revision_actual()
RETURNS bigint
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_rev bigint;
BEGIN
    SELECT revision INTO v_rev FROM public.meta WHERE id = 1;
    RETURN coalesce(v_rev, 1);
END;
$$;

-- 7.3 transaccion_crear_producto() - Creación atómica con autores y grupos
CREATE OR REPLACE FUNCTION public.transaccion_crear_producto(
    p_codigo_identificador varchar,
    p_titulo text,
    p_tipo_mayor varchar,
    p_subtipo varchar,
    p_ano integer,
    p_mes integer,
    p_pais varchar,
    p_estado_validacion varchar,
    p_detalles jsonb,
    p_es_ejemplo boolean,
    p_grupo_id bigint,
    p_investigadores_ids bigint[],
    p_revision_esperada bigint
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_rev_actual bigint;
    v_producto_id bigint;
    v_inv_id bigint;
    v_orden integer := 1;
BEGIN
    -- Verificación de revisión optimista
    SELECT revision INTO v_rev_actual FROM public.meta WHERE id = 1;
    IF v_rev_actual IS DISTINCT FROM p_revision_esperada THEN
        RAISE EXCEPTION 'CONFLICTO_REVISION: La base de datos cambio (remota %, esperada %)',
            v_rev_actual, p_revision_esperada
            USING ERRCODE = 'P0001';
    END IF;

    -- Inserción de producto
    INSERT INTO public.productos (
        codigo_identificador, titulo, tipo_mayor, subtipo, ano, mes, pais,
        estado_validacion, detalles, activo, es_ejemplo
    ) VALUES (
        p_codigo_identificador, p_titulo, p_tipo_mayor, p_subtipo, p_ano, p_mes, p_pais,
        p_estado_validacion, coalesce(p_detalles, '{}'::jsonb), true, p_es_ejemplo
    ) RETURNING id INTO v_producto_id;

    -- Vinculación con grupo
    IF p_grupo_id IS NOT NULL THEN
        INSERT INTO public.producto_grupos (producto_id, grupo_id, activo, es_ejemplo)
        VALUES (v_producto_id, p_grupo_id, true, p_es_ejemplo);
    END IF;

    -- Vinculación con coautores
    IF p_investigadores_ids IS NOT NULL THEN
        FOREACH v_inv_id IN ARRAY p_investigadores_ids LOOP
            INSERT INTO public.producto_autores (producto_id, investigador_id, orden_autoria, activo, es_ejemplo)
            VALUES (v_producto_id, v_inv_id, v_orden, true, p_es_ejemplo)
            ON CONFLICT (producto_id, investigador_id) DO NOTHING;
            v_orden := v_orden + 1;
        END LOOP;
    END IF;

    RETURN jsonb_build_object(
        'resultado', 'creado',
        'producto_id', v_producto_id,
        'codigo_identificador', p_codigo_identificador
    );
END;
$$;

-- 7.4 transaccion_desactivar_nodo() - Desactivación lógica reversible
CREATE OR REPLACE FUNCTION public.transaccion_desactivar_nodo(
    p_tipo varchar,
    p_id bigint,
    p_revision_esperada bigint
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_rev_actual bigint;
    v_afectados integer := 0;
BEGIN
    SELECT revision INTO v_rev_actual FROM public.meta WHERE id = 1;
    IF v_rev_actual IS DISTINCT FROM p_revision_esperada THEN
        RAISE EXCEPTION 'CONFLICTO_REVISION: La base de datos cambio (remota %, esperada %)',
            v_rev_actual, p_revision_esperada
            USING ERRCODE = 'P0001';
    END IF;

    IF p_tipo = 'grupo' THEN
        UPDATE public.grupos SET activo = false WHERE id = p_id;
        GET DIAGNOSTICS v_afectados = ROW_COUNT;
    ELSIF p_tipo = 'investigador' THEN
        UPDATE public.investigadores SET activo = false WHERE id = p_id;
        GET DIAGNOSTICS v_afectados = ROW_COUNT;
    ELSIF p_tipo = 'producto' THEN
        UPDATE public.productos SET activo = false WHERE id = p_id;
        GET DIAGNOSTICS v_afectados = ROW_COUNT;
    ELSE
        RAISE EXCEPTION 'Tipo de entidad no soportada para desactivacion: %', p_tipo;
    END IF;

    RETURN jsonb_build_object(
        'resultado', 'desactivado',
        'tipo', p_tipo,
        'id', p_id,
        'filas_afectadas', v_afectados
    );
END;
$$;

-- 7.5 transaccion_eliminar_cascada() - Eliminación física controlada
CREATE OR REPLACE FUNCTION public.transaccion_eliminar_cascada(
    p_tipo varchar,
    p_id bigint,
    p_revision_esperada bigint
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_rev_actual bigint;
    v_afectados integer := 0;
BEGIN
    SELECT revision INTO v_rev_actual FROM public.meta WHERE id = 1;
    IF v_rev_actual IS DISTINCT FROM p_revision_esperada THEN
        RAISE EXCEPTION 'CONFLICTO_REVISION: La base de datos cambio (remota %, esperada %)',
            v_rev_actual, p_revision_esperada
            USING ERRCODE = 'P0001';
    END IF;

    IF p_tipo = 'producto' THEN
        DELETE FROM public.productos WHERE id = p_id;
        GET DIAGNOSTICS v_afectados = ROW_COUNT;
    ELSIF p_tipo = 'investigador' THEN
        DELETE FROM public.investigadores WHERE id = p_id;
        GET DIAGNOSTICS v_afectados = ROW_COUNT;
    ELSIF p_tipo = 'grupo' THEN
        DELETE FROM public.grupos WHERE id = p_id;
        GET DIAGNOSTICS v_afectados = ROW_COUNT;
    ELSE
        RAISE EXCEPTION 'Tipo de entidad no soportada para eliminacion: %', p_tipo;
    END IF;

    RETURN jsonb_build_object(
        'resultado', 'eliminado',
        'tipo', p_tipo,
        'id', p_id,
        'filas_afectadas', v_afectados
    );
END;
$$;

-- 7.6 reiniciar_datos_prueba() - Operación segura de limpieza de pruebas
CREATE OR REPLACE FUNCTION public.reiniciar_datos_prueba(
    p_confirmacion text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_prod_borrados integer := 0;
    v_inv_borrados integer := 0;
    v_grp_borrados integer := 0;
BEGIN
    IF p_confirmacion IS DISTINCT FROM 'REINICIAR-PRUEBAS' THEN
        RAISE EXCEPTION 'Confirmacion invalida. Debe especificar exactamente: REINICIAR-PRUEBAS';
    END IF;

    -- 1. Borrar productos de prueba (ON DELETE CASCADE limpia autores y grupos)
    DELETE FROM public.productos
    WHERE es_ejemplo = true
      AND codigo_identificador LIKE 'PRUEBA-%';
    GET DIAGNOSTICS v_prod_borrados = ROW_COUNT;

    -- 2. Borrar integrantes de prueba residuales si hubiere
    DELETE FROM public.integrantes_grupo
    WHERE es_ejemplo = true;

    -- 3. Borrar investigadores de prueba
    DELETE FROM public.investigadores
    WHERE es_ejemplo = true
      AND (codigo_rh LIKE 'PRUEBA-%' OR nombre_completo LIKE 'PRUEBA-%');
    GET DIAGNOSTICS v_inv_borrados = ROW_COUNT;

    -- 4. Borrar grupos de prueba
    DELETE FROM public.grupos
    WHERE es_ejemplo = true
      AND (codigo_gruplac LIKE 'PRUEBA-%' OR nombre LIKE 'PRUEBA-%');
    GET DIAGNOSTICS v_grp_borrados = ROW_COUNT;

    RETURN jsonb_build_object(
        'resultado', 'limpieza_exitosa',
        'productos_borrados', v_prod_borrados,
        'investigadores_borrados', v_inv_borrados,
        'grupos_borrados', v_grp_borrados
    );
END;
$$;

-- ============================================================================
-- 8. SEGURIDAD, AUTENTICACIÓN Y ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE public.meta ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grupos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investigadores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integrantes_grupo ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.producto_autores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.producto_grupos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proyectos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.semilleros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auditoria_cambios ENABLE ROW LEVEL SECURITY;

-- Revocar privilegios por defecto a rol anónimo (anon)
REVOKE ALL ON TABLE public.grupos, public.investigadores, public.integrantes_grupo,
    public.productos, public.producto_autores, public.producto_grupos,
    public.proyectos, public.semilleros, public.auditoria_cambios, public.meta
FROM anon;

-- Conceder permisos de ejecución para funciones públicas básicas
GRANT EXECUTE ON FUNCTION public.ping() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.obtener_revision_actual() TO anon, authenticated;

-- Conceder permisos a rol autenticado (authenticated)
GRANT SELECT ON TABLE public.meta TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.grupos, public.investigadores,
    public.integrantes_grupo, public.productos, public.producto_autores,
    public.producto_grupos, public.proyectos, public.semilleros, public.auditoria_cambios
TO authenticated;

GRANT EXECUTE ON FUNCTION public.transaccion_crear_producto(varchar, text, varchar, varchar, integer, integer, varchar, varchar, jsonb, boolean, bigint, bigint[], bigint) TO authenticated;
GRANT EXECUTE ON FUNCTION public.transaccion_desactivar_nodo(varchar, bigint, bigint) TO authenticated;
GRANT EXECUTE ON FUNCTION public.transaccion_eliminar_cascada(varchar, bigint, bigint) TO authenticated;
GRANT EXECUTE ON FUNCTION public.reiniciar_datos_prueba(text) TO authenticated;

-- Políticas RLS para meta
CREATE POLICY pol_meta_select_auth ON public.meta
    FOR SELECT TO authenticated
    USING (true);

-- Políticas RLS para entidades de dominio (restringidas a authenticated)
CREATE POLICY pol_grupos_auth ON public.grupos
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_investigadores_auth ON public.investigadores
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_integrantes_auth ON public.integrantes_grupo
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_productos_auth ON public.productos
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_producto_autores_auth ON public.producto_autores
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_producto_grupos_auth ON public.producto_grupos
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_proyectos_auth ON public.proyectos
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_semilleros_auth ON public.semilleros
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY pol_auditoria_auth ON public.auditoria_cambios
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- 9. DATOS DE EJEMPLO PARA PRUEBAS (Seed Ficticio con Prefijo PRUEBA-)
-- ============================================================================

INSERT INTO public.grupos (
    codigo_gruplac, nombre, fecha_creacion, pais, departamento_ciudad,
    lider, institucion_principal, gran_area_ocde, area_ocde, categoria,
    activo, es_ejemplo
) VALUES (
    'PRUEBA-COL0001', 'PRUEBA-Grupo de Tecnologias Avanzadas', '2015-06',
    'Colombia', 'Cesar - Valledupar', 'PRUEBA-Investigador Lider',
    'Universidad Popular del Cesar', 'Ingenieria y Tecnologia',
    'Ingenieria de Sistemas y Comunicaciones', 'A1', true, true
) ON CONFLICT (codigo_gruplac) DO NOTHING;

INSERT INTO public.investigadores (
    codigo_rh, nombre_completo, nombre_en_citas, nacionalidad, sexo,
    categoria, formacion_academica, activo, es_ejemplo
) VALUES 
(
    'PRUEBA-INV-001', 'PRUEBA-Investigador Senior Uno', 'P. Senior-Uno',
    'Colombia', 'Masculino', 'Investigador Senior', 'Doctorado', true, true
),
(
    'PRUEBA-INV-002', 'PRUEBA-Investigador Asociado Dos', 'P. Asociado-Dos',
    'Colombia', 'Femenino', 'Investigador Asociado', 'Maestria', true, true
) ON CONFLICT (codigo_rh) DO NOTHING;

-- Integrantes de grupo de prueba
INSERT INTO public.integrantes_grupo (
    grupo_id, investigador_id, rol, fecha_inicio, fecha_fin, activo, es_ejemplo
)
SELECT g.id, i.id, 'Lider', '2018-01', NULL, true, true
FROM public.grupos g, public.investigadores i
WHERE g.codigo_gruplac = 'PRUEBA-COL0001' AND i.codigo_rh = 'PRUEBA-INV-001'
ON CONFLICT (grupo_id, investigador_id, fecha_inicio) DO NOTHING;

INSERT INTO public.integrantes_grupo (
    grupo_id, investigador_id, rol, fecha_inicio, fecha_fin, activo, es_ejemplo
)
SELECT g.id, i.id, 'Investigador', '2020-02', NULL, true, true
FROM public.grupos g, public.investigadores i
WHERE g.codigo_gruplac = 'PRUEBA-COL0001' AND i.codigo_rh = 'PRUEBA-INV-002'
ON CONFLICT (grupo_id, investigador_id, fecha_inicio) DO NOTHING;

-- Productos de prueba
INSERT INTO public.productos (
    codigo_identificador, titulo, tipo_mayor, subtipo, ano, mes, pais,
    estado_validacion, detalles, activo, es_ejemplo
) VALUES
(
    'PRUEBA-PROD-GNC-001', 'PRUEBA-Articulo en Redes Neuronales y Grafos',
    'GNC', 'Articulo', 2023, 5, 'Colombia', 'Avalado',
    '{"revista": "Revista Cientifica", "volumen": 12}'::jsonb, true, true
),
(
    'PRUEBA-PROD-DTI-001', 'PRUEBA-Software de Optimizacion Algoritmica',
    'DTI', 'Software', 2024, 2, 'Colombia', 'Avalado',
    '{"registro": "SOP-12345"}'::jsonb, true, true
) ON CONFLICT (codigo_identificador) DO NOTHING;

-- Vinculaciones de autores y grupos de prueba
INSERT INTO public.producto_autores (producto_id, investigador_id, orden_autoria, activo, es_ejemplo)
SELECT p.id, i.id, 1, true, true
FROM public.productos p, public.investigadores i
WHERE p.codigo_identificador = 'PRUEBA-PROD-GNC-001' AND i.codigo_rh = 'PRUEBA-INV-001'
ON CONFLICT (producto_id, investigador_id) DO NOTHING;

INSERT INTO public.producto_autores (producto_id, investigador_id, orden_autoria, activo, es_ejemplo)
SELECT p.id, i.id, 2, true, true
FROM public.productos p, public.investigadores i
WHERE p.codigo_identificador = 'PRUEBA-PROD-GNC-001' AND i.codigo_rh = 'PRUEBA-INV-002'
ON CONFLICT (producto_id, investigador_id) DO NOTHING;

INSERT INTO public.producto_autores (producto_id, investigador_id, orden_autoria, activo, es_ejemplo)
SELECT p.id, i.id, 1, true, true
FROM public.productos p, public.investigadores i
WHERE p.codigo_identificador = 'PRUEBA-PROD-DTI-001' AND i.codigo_rh = 'PRUEBA-INV-002'
ON CONFLICT (producto_id, investigador_id) DO NOTHING;

INSERT INTO public.producto_grupos (producto_id, grupo_id, activo, es_ejemplo)
SELECT p.id, g.id, true, true
FROM public.productos p, public.grupos g
WHERE p.codigo_identificador = 'PRUEBA-PROD-GNC-001' AND g.codigo_gruplac = 'PRUEBA-COL0001'
ON CONFLICT (producto_id, grupo_id) DO NOTHING;

INSERT INTO public.producto_grupos (producto_id, grupo_id, activo, es_ejemplo)
SELECT p.id, g.id, true, true
FROM public.productos p, public.grupos g
WHERE p.codigo_identificador = 'PRUEBA-PROD-DTI-001' AND g.codigo_gruplac = 'PRUEBA-COL0001'
ON CONFLICT (producto_id, grupo_id) DO NOTHING;

-- Notificar recarga de esquema a PostgREST
NOTIFY pgrst, 'reload schema';
