-- Sesiones automaticas: lectura real, escritura solo sobre registros de evaluacion.
-- No se desactiva RLS ni se conceden permisos al rol anon. Auth crea una sesion
-- authenticated con is_anonymous=true. Los usuarios permanentes conservan permisos.
CREATE FUNCTION public.fn_fila_evaluacion_permitida(p_tabla text, p_fila jsonb)
RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
    IF (p_fila->>'es_ejemplo')::boolean IS DISTINCT FROM true THEN
        RETURN false;
    END IF;
    IF p_tabla = 'grupos' THEN
        RETURN p_fila->>'codigo_gruplac' LIKE 'PRUEBA-%';
    ELSIF p_tabla = 'investigadores' THEN
        RETURN p_fila->>'codigo_rh' LIKE 'PRUEBA-%';
    ELSIF p_tabla = 'productos' THEN
        RETURN p_fila->>'codigo_identificador' LIKE 'PRUEBA-%';
    ELSIF p_tabla IN ('producto_autores', 'producto_grupos') THEN
        RETURN EXISTS (SELECT 1 FROM public.productos WHERE id = (p_fila->>'producto_id')::bigint
                       AND es_ejemplo AND codigo_identificador LIKE 'PRUEBA-%');
    ELSIF p_tabla = 'integrantes_grupo' THEN
        RETURN EXISTS (SELECT 1 FROM public.grupos WHERE id = (p_fila->>'grupo_id')::bigint
                       AND es_ejemplo AND codigo_gruplac LIKE 'PRUEBA-%')
           AND EXISTS (SELECT 1 FROM public.investigadores WHERE id = (p_fila->>'investigador_id')::bigint
                       AND es_ejemplo AND codigo_rh LIKE 'PRUEBA-%');
    END IF;
    -- Las fichas complementarias oficiales y la auditoria son de solo lectura.
    RETURN false;
END;
$$;

CREATE FUNCTION public.fn_proteger_datos_reales_evaluacion()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE
    v_vieja jsonb;
    v_nueva jsonb;
    v_permitida boolean;
BEGIN
    IF coalesce((auth.jwt()->>'is_anonymous')::boolean, false) THEN
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            v_vieja := to_jsonb(OLD);
            v_permitida := public.fn_fila_evaluacion_permitida(TG_TABLE_NAME, v_vieja);
            -- En cascada el padre ya no es visible; solo se permiten relaciones de
            -- evaluacion. Cualquier fila real provoca rollback de toda la operacion.
            IF TG_OP = 'DELETE' AND pg_trigger_depth() > 1
               AND TG_TABLE_NAME IN ('producto_autores', 'producto_grupos', 'integrantes_grupo') THEN
                v_permitida := (v_vieja->>'es_ejemplo')::boolean;
            END IF;
            IF v_permitida IS DISTINCT FROM true THEN
                RAISE EXCEPTION 'Los datos reales son de solo lectura en la entrega. Cree un registro de evaluacion para probar cambios.'
                    USING ERRCODE = '42501';
            END IF;
        END IF;
        IF TG_OP IN ('INSERT', 'UPDATE') THEN
            v_nueva := to_jsonb(NEW);
            IF public.fn_fila_evaluacion_permitida(TG_TABLE_NAME, v_nueva) IS DISTINCT FROM true THEN
                RAISE EXCEPTION 'La entrega solo permite escribir registros es_ejemplo=true con codigo PRUEBA- y sus relaciones.'
                    USING ERRCODE = '42501';
            END IF;
        END IF;
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

DO $$
DECLARE v_tabla text;
BEGIN
    FOREACH v_tabla IN ARRAY ARRAY[
        'grupos', 'investigadores', 'productos', 'integrantes_grupo', 'producto_autores',
        'producto_grupos', 'proyectos', 'semilleros', 'grupo_instituciones',
        'grupo_plan_estrategico', 'lineas_investigacion', 'investigador_formacion',
        'investigador_experiencia', 'investigador_areas_actuacion', 'investigador_idiomas',
        'investigador_reconocimientos', 'investigador_redes_identificadores', 'auditoria_cambios'
    ] LOOP
        EXECUTE format('CREATE TRIGGER trg_proteger_evaluacion BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.fn_proteger_datos_reales_evaluacion()', v_tabla);
        -- RLS adicional: no sustituye las politicas de usuarios permanentes.
        EXECUTE format('CREATE POLICY pol_evaluacion_insert ON public.%I AS RESTRICTIVE FOR INSERT TO authenticated WITH CHECK (NOT coalesce((auth.jwt()->>''is_anonymous'')::boolean, false) OR public.fn_fila_evaluacion_permitida(%L, to_jsonb(%I)))', v_tabla, v_tabla, v_tabla);
        EXECUTE format('CREATE POLICY pol_evaluacion_update ON public.%I AS RESTRICTIVE FOR UPDATE TO authenticated WITH CHECK (NOT coalesce((auth.jwt()->>''is_anonymous'')::boolean, false) OR public.fn_fila_evaluacion_permitida(%L, to_jsonb(%I)))', v_tabla, v_tabla, v_tabla);
    END LOOP;
END;
$$;

REVOKE ALL ON FUNCTION public.fn_fila_evaluacion_permitida(text, jsonb) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fn_fila_evaluacion_permitida(text, jsonb) TO authenticated;
REVOKE ALL ON FUNCTION public.fn_proteger_datos_reales_evaluacion() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fn_proteger_datos_reales_evaluacion() TO authenticated;
NOTIFY pgrst, 'reload schema';
