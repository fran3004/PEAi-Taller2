"""Pruebas unitarias completas para el subsistema de Ingesta (URL, PDF, CSV, Cola y Catálogo)."""

import csv
import io
from pathlib import Path

import pytest
from PIL import Image

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.estructuras.cola import EstadoTarea
from pea.ingesta.extractor_pdf import ExtractorPDF
from pea.ingesta.extractor_url import (
    ExtractorURL,
    anonimizar_datos_personales,
    normalizar_texto,
)
from pea.ingesta.lector_csv import LectorCSV
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.servicio_dominio import CatalogoInvestigacion

# =============================================================================
# PRUEBAS DE EXTRACCIÓN URL
# =============================================================================

class TestExtractorURL:
    """Verifica la extracción web responsable, validación de host, normalización y fixtures."""

    def test_seguridad_host_y_protocolo(self, tmp_path: Path):
        extractor = ExtractorURL(cache_dir=tmp_path)

        # 1. Debe rechazar esquemas no seguros (HTTP)
        with pytest.raises(ValueError, match="Solo se permite HTTPS"):
            extractor.validar_url("http://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099")

        # 2. Debe rechazar hosts ajenos
        with pytest.raises(ValueError, match="Host no permitido"):
            extractor.validar_url("https://otro-dominio.com/gruplac")

        # 3. Debe rechazar URLs no reconocidas
        with pytest.raises(ValueError, match="no reconocida"):
            extractor.validar_url("https://scienti.minciencias.gov.co/pagina_desconocida")

        # 4. URLs válidas
        tipo_g, _ = extractor.validar_url("https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099")
        assert tipo_g == "gruplac"

        tipo_c, _ = extractor.validar_url("https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917")
        assert tipo_c == "cvlac"

    def test_normalizacion_texto_y_anonimizacion(self):
        texto_sucio = "  Texto   con   espacios  \n\r  múltiples  y   tildes: programación  "
        norm = normalizar_texto(texto_sucio)
        assert norm == "Texto con espacios múltiples y tildes: programación"

        texto_sensible = "Contacto: docente@unicesar.edu.co o alterno@gmail.com para coordinar."
        anon = anonimizar_datos_personales(texto_sensible)
        assert "[CORREO-INSTITUCIONAL-UPC]" in anon
        assert "[CORREO-PROTEGIDO]" in anon
        assert "@unicesar.edu.co" not in anon
        assert "@gmail.com" not in anon

    def test_parsear_gruplac_offline_fixture(self, tmp_path: Path):
        fixture_html = Path("tests/fixtures/scienti/gruplac_00000000002099.html")
        assert fixture_html.exists(), "El fixture HTML de GrupLAC debe existir"

        html_text = fixture_html.read_text(encoding="iso-8859-1")
        extractor = ExtractorURL(cache_dir=tmp_path)
        meta = {
            "url": "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099",
            "alias": "gruplac_00000000002099",
            "sha256": "dummy_sha",
            "fecha_descarga": "2026-10-02T20:00:00Z",
            "codigo_http": 200,
            "encoding_utilizada": "ISO-8859-1",
        }

        grupo, md_text, metricas = extractor.parsear_gruplac(html_text, meta, anonimizar=False)

        assert grupo.codigo_gruplac == "00000000002099"
        assert len(grupo.instituciones) >= 1
        assert len(grupo.integrantes) >= 1
        assert len(grupo.articulos) >= 1
        assert "Transcripción Integral GrupLAC" in md_text
        assert metricas["articulos"] >= 1

        # Probar exportación a CSV canónico
        csv_archivos = extractor.exportar_a_csv_canonico(tmp_path / "csv", grupo=grupo)
        assert Path(csv_archivos["grupos_csv"]).exists()
        assert Path(csv_archivos["productos_csv"]).exists()

    def test_parsear_cvlac_offline_fixture(self, tmp_path: Path):
        fixture_html = Path("tests/fixtures/scienti/cvlac_0000494917.html")
        assert fixture_html.exists(), "El fixture HTML de CvLAC debe existir"

        html_text = fixture_html.read_text(encoding="iso-8859-1")
        extractor = ExtractorURL(cache_dir=tmp_path)
        meta = {
            "url": "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917",
            "alias": "cvlac_0000494917",
            "sha256": "dummy_sha_cvlac",
            "fecha_descarga": "2026-10-02T20:00:00Z",
            "codigo_http": 200,
            "encoding_utilizada": "ISO-8859-1",
        }

        inv, md_text, metricas = extractor.parsear_cvlac(html_text, meta, anonimizar=True)

        assert inv.codigo_rh == "0000494917"
        assert "[INVESTIGADOR-CVLAC-PROTEGIDO]" in md_text
        assert len(inv.formacion) >= 1
        assert len(inv.articulos) >= 1
        assert metricas["articulos"] >= 1

        # Probar exportación a CSV canónico
        csv_archivos = extractor.exportar_a_csv_canonico(tmp_path / "csv", investigador=inv)
        assert Path(csv_archivos["investigadores_csv"]).exists()

    @pytest.mark.red
    def test_conexion_real_scienti_red(self, tmp_path: Path):
        """Prueba real de scraping marcada con 'red' que consulta scienti.minciencias.gov.co."""
        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=1.0)
        url_real = "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099"
        raw_bytes, meta = extractor.descargar_o_cargar_cache(url_real, forzar_descarga=True)
        assert len(raw_bytes) > 1000
        assert meta["codigo_http"] == 200
        assert meta["sha256"] is not None


# =============================================================================
# PRUEBAS DE EXTRACCIÓN PDF
# =============================================================================

class TestExtractorPDF:
    """Verifica el procesamiento página a página, tablas y detección de escaneado con pdfplumber."""

    def test_extraccion_pdf_vectorial(self, tmp_path: Path):
        pdf_path = Path("docs/entrada/Modelo-2024.original.pdf")
        if not pdf_path.exists():
            pytest.skip("Modelo-2024.original.pdf no encontrado en docs/entrada/")

        extractor = ExtractorPDF()
        # Limitar a las 2 primeras páginas para que sea instantáneo en pruebas unitarias
        doc = extractor.procesar_archivo(pdf_path, max_paginas=2)

        assert doc.total_paginas == 2
        assert doc.total_caracteres > 100
        assert not doc.es_escaneado, "El PDF del Modelo es texto vectorial, no debe clasificarse como escaneado"
        assert len(doc.paginas) == 2

        # Exportar a Markdown
        ruta_md = tmp_path / "modelo_resumen.md"
        extractor.exportar_a_markdown(doc, ruta_md)
        assert ruta_md.exists()
        assert len(ruta_md.read_text(encoding="utf-8")) > 100

    def test_deteccion_pdf_escaneado_y_no_inventar_datos(self, tmp_path: Path):
        # Crear un PDF puramente rasterizado / escaneado usando PIL (sin capa de texto)
        pdf_escaneado_path = tmp_path / "documento_escaneado.pdf"
        img = Image.new("RGB", (300, 300), color="blue")
        img.save(str(pdf_escaneado_path), format="PDF")

        extractor = ExtractorPDF(umbral_caracteres_escaneo=15)
        doc = extractor.procesar_archivo(pdf_escaneado_path)

        assert doc.total_paginas == 1
        assert doc.total_caracteres == 0
        assert doc.es_escaneado, "Debe clasificarse como escaneado al carecer de texto y poseer imagen"
        assert len(doc.advertencias) >= 1
        assert "escaneada" in doc.advertencias[0].lower() or "escaneado" in doc.advertencias[0].lower()

        # REGLA: No inventar datos
        assert doc.paginas[0].texto == ""
        assert doc.paginas[0].tablas == []


# =============================================================================
# PRUEBAS DE LECTOR CSV
# =============================================================================

class TestLectorCSV:
    """Verifica soporte de delimitadores (, y ;), BOM UTF-8, comillas y tolerancia a filas erróneas."""

    def test_delimitador_coma(self, tmp_path: Path):
        contenido = (
            "codigo_minciencias,nombre,clasificacion,institucion\n"
            "COL0008543,Grupo de Tecnologías UPC,A1,Universidad Popular del Cesar\n"
            "COL0009999,Grupo de Materiales,B,Universidad Popular del Cesar\n"
        )
        ruta = tmp_path / "grupos_coma.csv"
        ruta.write_text(contenido, encoding="utf-8")

        grupos, errores = LectorCSV.leer_grupos(ruta)
        assert len(errores) == 0
        assert len(grupos) == 2
        assert grupos[0].codigo_gruplac == "COL0008543"
        assert grupos[0].categoria == "A1"

    def test_delimitador_punto_y_coma(self, tmp_path: Path):
        contenido = (
            "codigo_cvlac;nombre_completo;categoria;nacionalidad\n"
            "0000494917;Pérez Juan Carlos;Investigador Senior;Colombia\n"
            "0000123456;Gómez María;Investigador Junior;Colombia\n"
        )
        ruta = tmp_path / "inv_punto_coma.csv"
        ruta.write_text(contenido, encoding="utf-8")

        invs, errores = LectorCSV.leer_investigadores(ruta)
        assert len(errores) == 0
        assert len(invs) == 2
        assert invs[0].codigo_rh == "0000494917"
        assert invs[1].categoria == "Investigador Junior"

    def test_soporte_bom_utf8(self, tmp_path: Path):
        # Crear archivo con BOM UTF-8 (\xef\xbb\xbf)
        bom_bytes = b"\xef\xbb\xbfcodigo_minciencias,nombre,clasificacion\nCOL001,Grupo Con BOM,A1\n"
        ruta = tmp_path / "grupos_bom.csv"
        ruta.write_bytes(bom_bytes)

        grupos, errores = LectorCSV.leer_grupos(ruta)
        assert len(errores) == 0
        assert len(grupos) == 1
        assert grupos[0].codigo_gruplac == "COL001"
        assert grupos[0].nombre == "Grupo Con BOM"

    def test_comillas_y_campos_escapados(self, tmp_path: Path):
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["codigo_identificador", "titulo", "tipo_categoria", "anio", "estado_validacion", "grupo_codigo"])
        writer.writerow([
            "PROD-001",
            'Análisis de "Redes Complejas", con comas y comillas',
            "Articulo",
            "2023",
            "Aprobado",
            "COL0008543",
        ])
        ruta = tmp_path / "prods_comillas.csv"
        ruta.write_text(buffer.getvalue(), encoding="utf-8")

        prods, errores = LectorCSV.leer_productos(ruta)
        assert len(errores) == 0
        assert len(prods) == 1
        prod, grp_cod = prods[0]
        assert prod.codigo_identificador == "PROD-001"
        assert 'Análisis de "Redes Complejas", con comas y comillas' in prod.titulo
        assert grp_cod == "COL0008543"

    def test_tolerancia_filas_invalidas_sin_romper_archivo(self, tmp_path: Path):
        # Archivo con 3 filas: fila 1 válida, fila 2 INVÁLIDA (año no numérico en productos), fila 3 válida
        contenido = (
            "codigo_identificador,titulo,tipo_categoria,anio,estado_validacion\n"
            "PROD-001,Producto Válido 1,Articulo,2021,Aprobado\n"
            "PROD-002,Producto Fila Rota,Articulo,AÑO_INVALIDO,Aprobado\n"
            "PROD-003,Producto Válido 3,Software,2023,Aprobado\n"
        )
        ruta = tmp_path / "prods_con_error.csv"
        ruta.write_text(contenido, encoding="utf-8")

        prods, errores = LectorCSV.leer_productos(ruta)
        # Debe recuperar las 2 filas válidas y registrar la fila 2 en errores
        assert len(prods) == 2
        assert len(errores) == 1
        assert errores[0]["fila"] == 3  # Encabezado es 1, fila 1 es 2, fila 2 es 3
        assert "AÑO_INVALIDO" in str(errores[0]["datos"])
        assert prods[0][0].codigo_identificador == "PROD-001"
        assert prods[1][0].codigo_identificador == "PROD-003"


# =============================================================================
# PRUEBAS DE SERVICIO DE INGESTA Y COLA PROPIA
# =============================================================================

class TestServicioIngestaYCola:
    """Verifica la Cola FIFO de tareas, transiciones de estado, desduplicación y Catálogo."""

    def test_ciclo_estados_cola_propia(self, tmp_path: Path):
        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo)

        csv_path = tmp_path / "grupos.csv"
        csv_path.write_text(
            "codigo_minciencias,nombre,clasificacion\n"
            "PRUEBA-GRP-ING-1,Grupo Ingesta 1,A1\n",
            encoding="utf-8",
        )

        tarea = servicio.encolar_csv(csv_path, tipo_entidad="grupos")
        assert tarea.estado == EstadoTarea.PENDIENTE
        assert not servicio.cola_tareas.esta_vacia()

        informe = servicio.procesar_siguiente()
        assert informe is not None
        assert informe.exito
        assert informe.grupos_procesados == 1
        assert tarea.estado == EstadoTarea.TERMINADA
        assert servicio.cola_tareas.esta_vacia()

        # Verificar que el grupo está en el catálogo en memoria
        g = catalogo.buscar_grupo("PRUEBA-GRP-ING-1")
        assert g is not None
        assert g.nombre == "Grupo Ingesta 1"

    def test_tarea_con_error_no_rompe_cola(self, tmp_path: Path):
        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo)

        # Encolar una tarea con ruta inexistente
        tarea_rota = servicio.encolar_csv("archivo_que_no_existe.csv", tipo_entidad="grupos")
        assert tarea_rota.estado == EstadoTarea.PENDIENTE

        informe = servicio.procesar_siguiente()
        assert informe is not None
        assert not informe.exito
        assert tarea_rota.estado == EstadoTarea.CON_ERROR
        assert tarea_rota.mensaje_error is not None

    def test_desduplicacion_y_enlace_multilista(self, tmp_path: Path):
        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo)

        # 1. Crear grupo
        catalogo.crear_grupo(Grupo(codigo_gruplac="GRP-01", nombre="Grupo 01"), persistir=False)
        # 2. Crear investigador
        catalogo.crear_investigador(Investigador(codigo_rh="INV-01", nombre_completo="Investigador 01"), persistir=False)

        # 3. CSV de productos y autores
        csv_prods = tmp_path / "prods.csv"
        csv_prods.write_text(
            "codigo_identificador,titulo,tipo_categoria,anio,grupo_codigo\n"
            "P-001,Artículo Base,Articulo,2023,GRP-01\n",
            encoding="utf-8",
        )
        csv_autores = tmp_path / "autores.csv"
        csv_autores.write_text(
            "producto_codigo,investigador_codigo,orden_autoria\n"
            "P-001,INV-01,1\n",
            encoding="utf-8",
        )

        servicio.encolar_csv(csv_prods, tipo_entidad="productos")
        servicio.encolar_csv(csv_autores, tipo_entidad="autores")

        informes = servicio.procesar_todas()
        assert len(informes) == 2

        # Comprobar producto en multilista y vinculado al autor e investigación
        p = catalogo.buscar_producto("P-001")
        assert p is not None
        nodo_p = catalogo.multilista_productos.buscar_nodo("P-001")
        assert nodo_p is not None
        assert nodo_p.grupo is not None
        assert nodo_p.grupo.codigo_gruplac == "GRP-01"
        assert len(nodo_p.autores) == 1
        assert nodo_p.autores[0].codigo_rh == "INV-01"
