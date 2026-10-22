-- All domain-table triggers fire FOR EACH STATEMENT. A single RPC can modify
-- several tables, so count one revision per transaction rather than per statement.
CREATE OR REPLACE FUNCTION public.fn_incrementar_meta_revision()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF current_setting('pea.revision_incrementada', true) = '1' THEN
        RETURN NULL;
    END IF;

    PERFORM set_config('pea.revision_incrementada', '1', true);
    UPDATE public.meta
    SET revision = revision + 1,
        ultima_modificacion = now(),
        actualizado_en = now()
    WHERE id = 1;
    RETURN NULL;
END;
$$;
