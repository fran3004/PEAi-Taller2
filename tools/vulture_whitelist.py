"""Nombres que Vulture no puede reconocer como usados por introspección."""

# Pydantic consume la configuración y los campos al construir y serializar modelos.
class CamposPydantic:
    model_config = None
    fecha_creacion = None
    fecha_inicio = None
    fecha_fin = None
    ano_inicio = None
    ano_fin = None
    fecha_descarga = None
    encoding_utilizada = None
    codigo_http = None
    vinculacion = None
    horas_dedicacion = None
    inicio_vinculacion = None
    fin_vinculacion = None
    activa = None
    periodo = None
    doi_o_isbn = None
    persona_orientada = None
    ano_mes_formacion = None
    certificacion = None
    pagina_web = None
    email = None
    programa_nacional = None
    trabajos_dirigidos = None
    par_evaluador = None
    longitud_texto = None
    tablas_encontradas = None
    tiene_imagenes = None


# Qt invoca estos métodos como callbacks de eventos o comparadores virtuales.
class SobrescriturasQt:
    def paintEvent(self): ...

    def minimumSizeHint(self): ...

    def lessThan(self): ...

    def dragEnterEvent(self): ...

    def dropEvent(self): ...

    def drawBackground(self): ...

    def wheelEvent(self): ...
