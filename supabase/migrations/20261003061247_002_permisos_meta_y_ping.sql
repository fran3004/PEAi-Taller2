-- ============================================================================
-- PEA-i: Migración 002 - Ajuste de Permisos de Lectura en Meta y RPC Ping
-- Archivo: supabase/migrations/20261003061247_002_permisos_meta_y_ping.sql
-- ============================================================================

-- 1. Redefinir ping() como SECURITY DEFINER para permitir sondeo seguro sin sesión
CREATE OR REPLACE FUNCTION public.ping()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
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

-- 2. Redefinir obtener_revision_actual() como SECURITY DEFINER
CREATE OR REPLACE FUNCTION public.obtener_revision_actual()
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_rev bigint;
BEGIN
    SELECT revision INTO v_rev FROM public.meta WHERE id = 1;
    RETURN coalesce(v_rev, 1);
END;
$$;

-- 3. Conceder lectura mínima de la tabla meta al rol anónimo para sondeo de revisión
GRANT SELECT ON public.meta TO anon;

-- 4. Política RLS de lectura pública en meta
DROP POLICY IF EXISTS pol_meta_select_anon ON public.meta;
CREATE POLICY pol_meta_select_anon ON public.meta
    FOR SELECT TO anon
    USING (id = 1);

-- 5. Recarga de esquema PostgREST
NOTIFY pgrst, 'reload schema';
