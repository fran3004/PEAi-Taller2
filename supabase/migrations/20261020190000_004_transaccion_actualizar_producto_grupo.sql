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
    SELECT revision INTO v_revision_actual
    FROM public.meta
    WHERE id = 1;

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
        RAISE EXCEPTION 'La actualización contiene campos de producto no permitidos.';
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
