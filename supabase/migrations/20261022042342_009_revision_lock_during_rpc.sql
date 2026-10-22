CREATE OR REPLACE FUNCTION public.fn_lock_meta_revision()
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_revision bigint;
BEGIN
    SELECT revision
    INTO v_revision
    FROM public.meta
    WHERE id = 1
    FOR UPDATE;
    RETURN v_revision;
END;
$$;

REVOKE ALL ON FUNCTION public.fn_lock_meta_revision() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.fn_lock_meta_revision() TO authenticated, service_role;

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
    SELECT public.fn_lock_meta_revision() INTO v_rev_actual;
    IF v_rev_actual IS DISTINCT FROM p_revision_esperada THEN
        RAISE EXCEPTION 'CONFLICTO_REVISION: La base de datos cambio (remota %, esperada %)',
            v_rev_actual, p_revision_esperada
            USING ERRCODE = 'P0001';
    END IF;

    INSERT INTO public.productos (
        codigo_identificador, titulo, tipo_mayor, subtipo, ano, mes, pais,
        estado_validacion, detalles, activo, es_ejemplo
    ) VALUES (
        p_codigo_identificador, p_titulo, p_tipo_mayor, p_subtipo, p_ano, p_mes, p_pais,
        p_estado_validacion, coalesce(p_detalles, '{}'::jsonb), true, p_es_ejemplo
    ) RETURNING id INTO v_producto_id;

    IF p_grupo_id IS NOT NULL THEN
        INSERT INTO public.producto_grupos (producto_id, grupo_id, activo, es_ejemplo)
        VALUES (v_producto_id, p_grupo_id, true, p_es_ejemplo);
    END IF;

    IF p_investigadores_ids IS NOT NULL THEN
        FOREACH v_inv_id IN ARRAY p_investigadores_ids LOOP
            INSERT INTO public.producto_autores (
                producto_id, investigador_id, orden_autoria, activo, es_ejemplo
            )
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
    SELECT public.fn_lock_meta_revision() INTO v_rev_actual;
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
    SELECT public.fn_lock_meta_revision() INTO v_rev_actual;
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

CREATE OR REPLACE FUNCTION public.transaccion_actualizar_producto_grupo(
    p_codigo_identificador varchar,
    p_datos jsonb,
    p_grupo_id bigint,
    p_revision_esperada bigint
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_revision_actual bigint;
    v_producto_id bigint;
    v_es_ejemplo boolean;
BEGIN
    SELECT public.fn_lock_meta_revision() INTO v_revision_actual;
    IF v_revision_actual IS DISTINCT FROM p_revision_esperada THEN
        RAISE EXCEPTION 'CONFLICTO_REVISION: La base de datos cambio (remota %, esperada %)',
            v_revision_actual, p_revision_esperada
            USING ERRCODE = 'P0001';
    END IF;

    IF jsonb_typeof(p_datos) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'Los datos del producto deben ser un objeto JSON.';
    END IF;

    IF (p_datos - ARRAY[
        'titulo', 'tipo_mayor', 'subtipo', 'ano', 'mes', 'pais',
        'estado_validacion', 'detalles'
    ]::text[]) <> '{}'::jsonb THEN
        RAISE EXCEPTION 'La actualizacion contiene campos de producto no permitidos.';
    END IF;

    SELECT id, es_ejemplo
    INTO v_producto_id, v_es_ejemplo
    FROM public.productos
    WHERE codigo_identificador = p_codigo_identificador;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Producto no encontrado: %', p_codigo_identificador;
    END IF;

    IF p_datos <> '{}'::jsonb THEN
        UPDATE public.productos
        SET titulo = CASE WHEN p_datos ? 'titulo' THEN p_datos->>'titulo' ELSE titulo END,
            tipo_mayor = CASE WHEN p_datos ? 'tipo_mayor' THEN p_datos->>'tipo_mayor' ELSE tipo_mayor END,
            subtipo = CASE WHEN p_datos ? 'subtipo' THEN p_datos->>'subtipo' ELSE subtipo END,
            ano = CASE WHEN p_datos ? 'ano' THEN (p_datos->>'ano')::integer ELSE ano END,
            mes = CASE WHEN p_datos ? 'mes' THEN (p_datos->>'mes')::integer ELSE mes END,
            pais = CASE WHEN p_datos ? 'pais' THEN p_datos->>'pais' ELSE pais END,
            estado_validacion = CASE
                WHEN p_datos ? 'estado_validacion' THEN p_datos->>'estado_validacion'
                ELSE estado_validacion
            END,
            detalles = CASE WHEN p_datos ? 'detalles' THEN p_datos->'detalles' ELSE detalles END
        WHERE id = v_producto_id;
    END IF;

    DELETE FROM public.producto_grupos
    WHERE producto_id = v_producto_id;

    IF p_grupo_id IS NOT NULL THEN
        INSERT INTO public.producto_grupos (producto_id, grupo_id, activo, es_ejemplo)
        VALUES (v_producto_id, p_grupo_id, true, v_es_ejemplo);
    END IF;

    SELECT revision INTO v_revision_actual
    FROM public.meta
    WHERE id = 1;

    RETURN jsonb_build_object(
        'resultado', 'actualizado',
        'producto_id', v_producto_id,
        'revision', v_revision_actual
    );
END;
$$;
