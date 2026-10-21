-- Autorizacion explicita del propietario para la entrega academica:
-- acceso completo a los datos reales, sin las limitaciones de evaluacion 005/006.
-- Cualquier usuario que obtenga el paquete podra operar con estos permisos.
-- Se conserva Auth, RLS y las politicas authenticated originales de 001/003.
-- No se borra ninguna fila ni se elimina la tabla de autorizaciones existente.
DO $$
DECLARE v_tabla text;
BEGIN
    FOREACH v_tabla IN ARRAY ARRAY[
        'meta', 'grupos', 'investigadores', 'productos', 'integrantes_grupo',
        'producto_autores', 'producto_grupos', 'proyectos', 'semilleros',
        'grupo_instituciones', 'grupo_plan_estrategico', 'lineas_investigacion',
        'investigador_formacion', 'investigador_experiencia', 'investigador_areas_actuacion',
        'investigador_idiomas', 'investigador_reconocimientos',
        'investigador_redes_identificadores', 'auditoria_cambios'
    ] LOOP
        EXECUTE format('DROP POLICY IF EXISTS pol_sesion_autorizada ON public.%I', v_tabla);
        IF v_tabla <> 'meta' THEN
            EXECUTE format('DROP POLICY IF EXISTS pol_evaluacion_insert ON public.%I', v_tabla);
            EXECUTE format('DROP POLICY IF EXISTS pol_evaluacion_update ON public.%I', v_tabla);
            EXECUTE format('DROP TRIGGER IF EXISTS trg_proteger_evaluacion ON public.%I', v_tabla);
        END IF;
    END LOOP;
END;
$$;
NOTIFY pgrst, 'reload schema';
