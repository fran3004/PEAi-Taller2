-- Evita eludir las restricciones convirtiendo una sesion anonima en una cuenta
-- nueva por correo/OAuth. Solo las cuentas permanentes ya existentes conservan
-- permisos de usuario institucional. No se cambian sus credenciales ni sus datos.
CREATE TABLE public.usuarios_autorizados (
    id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE
);
INSERT INTO public.usuarios_autorizados(id)
SELECT id FROM auth.users WHERE NOT coalesce(is_anonymous, false);

ALTER TABLE public.usuarios_autorizados ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.usuarios_autorizados FROM anon, authenticated;
GRANT SELECT ON TABLE public.usuarios_autorizados TO authenticated;
CREATE POLICY pol_usuario_ve_su_autorizacion ON public.usuarios_autorizados
FOR SELECT TO authenticated USING (id = (SELECT auth.uid()));

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
        EXECUTE format('CREATE POLICY pol_sesion_autorizada ON public.%I AS RESTRICTIVE FOR ALL TO authenticated USING (coalesce((auth.jwt()->>''is_anonymous'')::boolean, false) OR EXISTS (SELECT 1 FROM public.usuarios_autorizados WHERE id = (SELECT auth.uid()))) WITH CHECK (coalesce((auth.jwt()->>''is_anonymous'')::boolean, false) OR EXISTS (SELECT 1 FROM public.usuarios_autorizados WHERE id = (SELECT auth.uid())))', v_tabla);
    END LOOP;
END;
$$;
NOTIFY pgrst, 'reload schema';
