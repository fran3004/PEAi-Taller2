"""Pruebas unitarias completas para el subsistema de Ingesta (URL, PDF, CSV, Cola y Catálogo)."""

import csv
import io
import json
from datetime import date, datetime
from pathlib import Path

import pytest
from PIL import Image

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.estructuras.cola import EstadoTarea
from pea.excepciones import ConflictoRevision
from pea.ingesta.extractor_pdf import ExtractorPDF
from pea.ingesta.extractor_url import (
    ExtractorURL,
    anonimizar_datos_personales,
    normalizar_texto,
)
from pea.ingesta.lector_csv import LectorCSV
from pea.ingesta.modelos import (
    GrupoIngesta,
    InformeIngesta,
    IntegranteIngesta,
    InvestigadorIngesta,
    MetadatosOrigen,
    ProductoIngesta,
)
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
        for codigo_cvlac in ("0000406449", "0000494917"):
            tipo_cvlac, _ = extractor.validar_url(
                "https://scienti.minciencias.gov.co/cvlac/visualizador/"
                f"generarCurriculoCv.do?cod_rh={codigo_cvlac}"
            )
            assert tipo_cvlac == "cvlac"

    def test_gruplac_extrae_fecha_nombre_y_codigo_cvlac(self, tmp_path: Path) -> None:
        extractor = ExtractorURL(cache_dir=tmp_path)
        url = (
            "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/"
            "visualizagr.jsp?nro=00000000017353"
        )
        html = """
        <span class="celdaEncabezado">GICAV - Grupo Instrumento</span>
        <table><tr><td class="celdaEncabezado">Datos básicos</td></tr>
        <tr><td>Año y mes de formación</td><td>2015 - 5</td></tr>
        <tr><td>Departamento - Ciudad</td><td>BOGOTÁ - BOGOTÁ</td></tr></table>
        <table><tr><td class="celdaEncabezado">Integrantes del grupo</td></tr>
        <tr><td>Nombre</td><td>Vinculación</td><td>Horas</td><td>Período</td></tr>
        <tr><td><a href="/cvlac/visualizador/cv.do?cod_rh=000123">Ana Prueba</a></td>
        <td>Investigador</td><td>10</td><td>2018 - Actual</td></tr></table>
        """

        grupo, _, _ = extractor.parsear_gruplac(html, {"url": url, "sha256": "fixture"})

        assert grupo.nombre_grupo == "Grupo Instrumento"
        assert grupo.fecha_creacion == "2015-05-01"
        assert grupo.integrantes == [
            IntegranteIngesta(
                nombre="Ana Prueba",
                vinculacion="Investigador",
                codigo_rh="000123",
                url_cvlac="https://scienti.minciencias.gov.co/cvlac/visualizador/cv.do?cod_rh=000123",
                horas_dedicacion="10",
                inicio_vinculacion="2018",
                fin_vinculacion="Actual",
            )
        ]

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
        assert all(integrante.codigo_rh and integrante.url_cvlac for integrante in grupo.integrantes)
        assert len(grupo.articulos) >= 1
        assert grupo.articulos[0].ano == 2026
        assert all(
            producto.ano is None or 1970 <= producto.ano <= date.today().year
            for producto in grupo.articulos
        )
        assert "Transcripción Integral GrupLAC" in md_text
        assert metricas["articulos"] >= 1

        # Probar exportación a CSV canónico
        csv_archivos = extractor.exportar_a_csv_canonico(tmp_path / "csv", grupo=grupo)
        assert Path(csv_archivos["grupos_csv"]).exists()
        assert Path(csv_archivos["productos_csv"]).exists()

        grupo.articulos[0].ano = None
        csv_sin_ano = extractor.exportar_a_csv_canonico(
            tmp_path / "csv_sin_ano",
            grupo=grupo,
        )
        with Path(csv_sin_ano["productos_csv"]).open(
            encoding="utf-8",
            newline="",
        ) as archivo_productos:
            fila_producto = next(csv.DictReader(archivo_productos))
        assert fila_producto["tipo_mayor"] == "GNC"
        assert fila_producto["subtipo"] == "Articulo"
        assert fila_producto["anio"] == ""
        assert fila_producto["estado_validacion"] == "Avalado"

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
        assert all(
            producto.ano is None or 1970 <= producto.ano <= date.today().year
            for producto in inv.articulos + inv.capitulos + inv.softwares
        )

        # Probar exportación a CSV canónico
        csv_archivos = extractor.exportar_a_csv_canonico(tmp_path / "csv", investigador=inv)
        assert Path(csv_archivos["investigadores_csv"]).exists()

    def test_parsear_cvlac_articulos_descarta_etiquetas_y_extrae_26_reales(self, tmp_path: Path):
        fixture_html = Path("tests/fixtures/scienti/cvlac_0000494917.html")
        assert fixture_html.exists(), "El fixture HTML de CvLAC debe existir"

        html_text = fixture_html.read_text(encoding="iso-8859-1")
        extractor = ExtractorURL(cache_dir=tmp_path)
        meta = {
            "url": "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917",
            "alias": "cvlac_0000494917",
            "sha256": "dummy_sha_cvlac",
        }

        inv, _, _ = extractor.parsear_cvlac(html_text, meta)

        # 1. El resultado esperado es exactamente 26 artículos reales
        assert len(inv.articulos) == 26

        # 2. Ninguno cuyo título empiece por "Producción bibliográfica"
        for a in inv.articulos:
            assert not a.titulo.startswith("Producción bibliográfica")
            assert not a.titulo.startswith("Produccion bibliografica")
            assert not a.titulo.startswith("Producci")

        # 3. Cada uno con su año o listado aparte
        sin_ano = [a for a in inv.articulos if a.ano is None]
        assert len(sin_ano) == 0, f"Artículos sin año: {[a.titulo for a in sin_ano]}"

    def test_csv_canonico_relaciona_autores_con_productos_emitidos(self, tmp_path: Path):
        """Los vínculos de autoría deben apuntar a los códigos reales de productos."""
        investigador = InvestigadorIngesta(
            codigo_rh="0000494917",
            origen=MetadatosOrigen(
                url="https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917",
                sha256="fixture",
            ),
            articulos=[ProductoIngesta(tipo="Artículo", titulo="Artículo de prueba", ano=2024)],
            libros=[ProductoIngesta(tipo="Libro", titulo="Libro de prueba", ano=2022)],
        )
        extractor = ExtractorURL(cache_dir=tmp_path)

        archivos = extractor.exportar_a_csv_canonico(tmp_path / "csv", investigador=investigador)

        with Path(archivos["productos_csv"]).open(encoding="utf-8", newline="") as archivo:
            codigos_productos = {fila["codigo_identificador"] for fila in csv.DictReader(archivo)}
        with Path(archivos["autores_csv"]).open(encoding="utf-8", newline="") as archivo:
            codigos_autoria = {fila["producto_codigo"] for fila in csv.DictReader(archivo)}

        assert len(codigos_productos) == 2
        assert codigos_autoria == codigos_productos

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
            "Artículo Tipo A1",
            "2023",
            "Avalado",
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
            "PROD-001,Producto Válido 1,Artículo Tipo A1,2021,Avalado\n"
            "PROD-002,Producto Fila Rota,Artículo Tipo A1,AÑO_INVALIDO,Avalado\n"
            "PROD-003,Producto Válido 3,Software,2023,Con soporte\n"
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

    def test_url_cvlac_guarda_ficha_completa_y_productos(self, tmp_path: Path) -> None:
        ruta_fixture = Path("tests/fixtures/scienti/cvlac_0000494917.html")
        html = ruta_fixture.read_bytes()
        url = (
            "https://scienti.minciencias.gov.co/cvlac/visualizador/"
            "generarCurriculoCv.do?cod_rh=0000494917"
        )
        extractor_real = ExtractorURL(cache_dir=tmp_path)
        investigador_esperado, _, _ = extractor_real.parsear_cvlac(
            html.decode("iso-8859-1"),
            {"url": url, "sha256": "fixture"},
        )
        informe_extraccion = InformeIngesta(
            origen=url,
            tipo_fuente="url_cvlac",
            exito=True,
        )

        class ExtractorCvLac:
            def validar_url(self, origen: str) -> tuple[str, str]:
                return "cvlac", ""

            def procesar_url(self, url: str, **_kwargs: object) -> InformeIngesta:
                return informe_extraccion

            def descargar_o_cargar_cache(
                self,
                url: str,
                alias: str | None = None,
            ) -> tuple[bytes, dict[str, str]]:
                return html, {
                    "url": url,
                    "sha256": "fixture",
                    "encoding_utilizada": "iso-8859-1",
                }

            def parsear_cvlac(
                self,
                html_text: str,
                meta: dict[str, str],
            ) -> tuple[InvestigadorIngesta, str, dict[str, int]]:
                return extractor_real.parsear_cvlac(html_text, meta)

        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo, extractor_url=ExtractorCvLac())
        servicio.encolar_url(url, persistir=False, salida_dir=tmp_path)
        informe = servicio.procesar_siguiente()

        assert informe is not None and informe.exito
        investigador = catalogo.buscar_investigador("0000494917")
        assert investigador is not None
        assert investigador.nombre_completo == investigador_esperado.nombre_completo
        assert investigador.detalles["formacion"]
        assert isinstance(investigador.par_evaluador, bool)
        assert len(investigador.detalles["articulos"]) >= 10
        assert any(
            producto.codigo_identificador.startswith("PROD-CVLAC-0000494917-")
            for producto in catalogo.multilista_productos
        )

    def test_importar_dos_veces_cvlac_en_memoria_no_duplica_productos(self, tmp_path: Path) -> None:
        """(a) Importar dos veces el mismo CvLAC con repositorio en memoria no crea duplicados."""
        ruta_fixture = Path("tests/fixtures/scienti/cvlac_0000494917.html")
        html = ruta_fixture.read_bytes()
        url = "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917"
        extractor_real = ExtractorURL(cache_dir=tmp_path)

        class ExtractorMock:
            def validar_url(self, origen: str) -> tuple[str, str]:
                return "cvlac", ""

            def procesar_url(self, url: str, **_kwargs: object) -> InformeIngesta:
                return InformeIngesta(origen=url, tipo_fuente="url_cvlac", exito=True)

            def descargar_o_cargar_cache(self, url: str, alias: str | None = None) -> tuple[bytes, dict[str, str]]:
                return html, {"url": url, "sha256": "fixture", "encoding_utilizada": "iso-8859-1"}

            def parsear_cvlac(self, html_text: str, meta: dict[str, str]) -> tuple[InvestigadorIngesta, str, dict[str, int]]:
                return extractor_real.parsear_cvlac(html_text, meta)

        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo, extractor_url=ExtractorMock())

        # Primera importación
        servicio.encolar_url(url, persistir=False, salida_dir=tmp_path)
        info1 = servicio.procesar_siguiente()
        assert info1 is not None and info1.exito
        total_primera = catalogo.multilista_productos.tamano
        assert total_primera > 0

        # Segunda importación
        servicio.encolar_url(url, persistir=False, salida_dir=tmp_path)
        info2 = servicio.procesar_siguiente()
        assert info2 is not None and info2.exito
        total_segunda = catalogo.multilista_productos.tamano
        assert total_segunda == total_primera, f"Se crearon duplicados: antes {total_primera}, después {total_segunda}"

    def test_importar_cvlac_reconoce_producto_existente_con_codigo_antiguo_posicional(self, tmp_path: Path) -> None:
        """(b) Si ya existe un producto con código antiguo de posición y misma cita, no crea otro."""
        ruta_fixture = Path("tests/fixtures/scienti/cvlac_0000494917.html")
        html = ruta_fixture.read_bytes()
        url = "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917"
        extractor_real = ExtractorURL(cache_dir=tmp_path)
        inv_parsed, _, _ = extractor_real.parsear_cvlac(html.decode("iso-8859-1"), {"url": url, "sha256": "fixture"})

        primer_art = inv_parsed.articulos[0]
        cita_real = primer_art.detalles

        catalogo = CatalogoInvestigacion()
        # Pre-crear el investigador
        inv_obj = Investigador(codigo_rh="0000494917", nombre_completo="Adith Bismarck Pérez Orozco")
        catalogo.crear_investigador(inv_obj, persistir=False)

        # Pre-crear el producto bajo código antiguo de posición (en el lector viejo era posición 0002)
        codigo_antiguo = "PROD-CVLAC-0000494917-0002"
        prod_antiguo = Producto(
            codigo_identificador=codigo_antiguo,
            titulo=primer_art.titulo,
            tipo_mayor=primer_art.tipo_mayor,
            subtipo=primer_art.subtipo,
            ano=primer_art.ano or 2016,
            detalles={"origen": "CvLAC", "fuente": url, "referencia_original": cita_real},
        )
        catalogo.crear_producto(prod_antiguo, codigos_rh_autores=["0000494917"], persistir=False)
        assert catalogo.multilista_productos.tamano == 1

        class ExtractorMock:
            def validar_url(self, origen: str) -> tuple[str, str]:
                return "cvlac", ""

            def procesar_url(self, url: str, **_kwargs: object) -> InformeIngesta:
                return InformeIngesta(origen=url, tipo_fuente="url_cvlac", exito=True)

            def descargar_o_cargar_cache(self, url: str, alias: str | None = None) -> tuple[bytes, dict[str, str]]:
                return html, {"url": url, "sha256": "fixture", "encoding_utilizada": "iso-8859-1"}

            def parsear_cvlac(self, html_text: str, meta: dict[str, str]) -> tuple[InvestigadorIngesta, str, dict[str, int]]:
                return extractor_real.parsear_cvlac(html_text, meta)

        servicio = ServicioIngesta(catalogo, extractor_url=ExtractorMock())
        servicio.encolar_url(url, persistir=False, salida_dir=tmp_path)
        servicio.procesar_siguiente()

        # El producto con la misma cita no debe duplicarse: el nodo antiguo se preservó
        # y no existe un producto duplicado con el nuevo código para esa misma cita
        prods_con_esa_cita = [
            p for p in catalogo.multilista_productos
            if (p.detalles.get("referencia_original") or "").strip() == cita_real.strip()
        ]
        assert len(prods_con_esa_cita) == 1
        assert prods_con_esa_cita[0].codigo_identificador == codigo_antiguo

    def test_dos_citas_identicas_mismo_cv_reciben_codigos_distintos_y_estables(self) -> None:
        """(c) Dos citas idénticas dentro de un mismo CV reciben códigos distintos y estables."""
        from pea.dominio.producto import generar_codigo_producto_cvlac

        cita = "Pérez Orozco, Adith Bismarck. «Gestión de la innovación en servicios», 2016."
        codigo_1a = generar_codigo_producto_cvlac("0000494917", cita, ocurrencia=1)
        codigo_2a = generar_codigo_producto_cvlac("0000494917", cita, ocurrencia=2)
        codigo_3a = generar_codigo_producto_cvlac("0000494917", cita, ocurrencia=3)

        # Distintos entre sí
        assert codigo_1a != codigo_2a
        assert codigo_2a != codigo_3a
        assert codigo_2a.endswith("-2")
        assert codigo_3a.endswith("-3")

        # Estabilidad: segundas llamadas generan los mismos códigos exactos
        assert generar_codigo_producto_cvlac("0000494917", cita, ocurrencia=1) == codigo_1a
        assert generar_codigo_producto_cvlac("0000494917", cita, ocurrencia=2) == codigo_2a

    def test_paridad_codigo_estable_cvlac_con_tildes(self) -> None:
        """Prueba de paridad con 3 citas de ejemplo con tildes."""
        from pea.dominio.producto import calcular_hash_cita, generar_codigo_producto_cvlac

        c1 = "Pérez Orozco, Adith Bismarck. «Gestión de la innovación en servicios», 2016."
        c2 = "Álvarez, María & Núñez, José. «Inteligencia Artificial y Educación», vol. 5, 2021."
        c3 = "Investigación Aplicada en la Universidad Popular del Cesar (UPC): Guía Práctica, año 2023."

        # Verificación de hashes exactos
        assert calcular_hash_cita(c1) == "9d80335576e1"
        assert calcular_hash_cita(c2) == "d4966c27ca0c"
        assert calcular_hash_cita(c3) == "998b196deec0"

        assert generar_codigo_producto_cvlac("0000494917", c1) == "PROD-CVLAC-0000494917-9d80335576e1"
        assert generar_codigo_producto_cvlac("0000494917", c2) == "PROD-CVLAC-0000494917-d4966c27ca0c"
        assert generar_codigo_producto_cvlac("0000494917", c3) == "PROD-CVLAC-0000494917-998b196deec0"
        assert generar_codigo_producto_cvlac("0000494917", c1, ocurrencia=2) == "PROD-CVLAC-0000494917-9d80335576e1-2"

    def test_normalizar_cita_y_generar_codigo_casos_borde(self) -> None:
        """Prueba casos borde: tildes (NFC vs NFD), espacios múltiples, saltos de línea, mayúsculas, comillas, citas vacías."""
        import unicodedata

        from pea.dominio.producto import calcular_hash_cita, generar_codigo_producto_cvlac, normalizar_cita

        texto_base = "Pérez Orozco, Adith Bismarck. «Gestión de la innovación en servicios», 2016."
        nfd_texto = unicodedata.normalize("NFD", texto_base)
        nfc_texto = unicodedata.normalize("NFC", texto_base)

        # NFC vs NFD producen la misma normalización y hash
        assert normalizar_cita(nfd_texto) == normalizar_cita(nfc_texto)
        assert calcular_hash_cita(nfd_texto) == calcular_hash_cita(nfc_texto)

        # Espacios múltiples, tabulaciones y saltos de línea
        con_espacios = "   Pérez   \t  Orozco,   \n  Adith Bismarck.   «Gestión   de la innovación en servicios»,   2016. \n\n"
        assert normalizar_cita(con_espacios) == normalizar_cita(texto_base)
        assert calcular_hash_cita(con_espacios) == calcular_hash_cita(texto_base)

        # Mayúsculas vs minúsculas
        mayusculas = texto_base.upper()
        assert normalizar_cita(mayusculas) == normalizar_cita(texto_base)

        # Cita vacía o None: recurre a título normalizado
        cod_desde_titulo = generar_codigo_producto_cvlac(
            "0000494917",
            cita="",
            titulo="Gestión de la innovación",
        )
        cod_desde_titulo_none = generar_codigo_producto_cvlac(
            "0000494917",
            cita=None,
            titulo="Gestión de la innovación",
        )
        hash_titulo = calcular_hash_cita("Gestión de la innovación")
        assert cod_desde_titulo == f"PROD-CVLAC-0000494917-{hash_titulo}"
        assert cod_desde_titulo_none == cod_desde_titulo

        # Cita vacía y título None
        cod_vacio = generar_codigo_producto_cvlac("0000494917", cita="", titulo=None)
        hash_vacio = calcular_hash_cita("")
        assert cod_vacio == f"PROD-CVLAC-0000494917-{hash_vacio}"

    def test_url_gruplac_persiste_campos_obligatorios_integrantes_y_todas_las_secciones(
        self,
        tmp_path: Path,
    ) -> None:
        url = (
            "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/"
            "visualizagr.jsp?nro=00000000017353"
        )
        grupo = GrupoIngesta(
            codigo_gruplac="PRUEBA-URL-COMPLETA",
            nombre_grupo="Grupo completo",
            ano_mes_formacion="2015 - 5",
            fecha_creacion="2015-05-01",
            clasificacion="Categoría C",
            integrantes=[
                IntegranteIngesta(
                    nombre="Ana Prueba",
                    vinculacion="Investigador",
                    codigo_rh="000123",
                    inicio_vinculacion="2018-01-01",
                    horas_dedicacion="10 horas",
                )
            ],
            trabajos_dirigidos=[
                ProductoIngesta(tipo="TrabajoDirigido", titulo="Trabajo", ano=2023)
            ],
            proyectos=[ProductoIngesta(tipo="Proyecto", titulo="Proyecto", ano=2022)],
            origen=MetadatosOrigen(url=url, sha256="fixture"),
        )
        informe_extraccion = InformeIngesta(
            origen=url,
            tipo_fuente="url_gruplac",
            exito=True,
        )

        class ExtractorGrupoCompleto:
            def validar_url(self, origen: str) -> tuple[str, str]:
                return "gruplac", ""

            def procesar_url(self, url: str, **_kwargs: object) -> InformeIngesta:
                return informe_extraccion

            def descargar_o_cargar_cache(
                self,
                origen: str,
                alias: str | None = None,
            ) -> tuple[bytes, dict[str, str]]:
                return b"", {"encoding_utilizada": "utf-8"}

            def parsear_gruplac(
                self,
                html_text: str,
                meta: dict[str, str],
            ) -> tuple[GrupoIngesta, str, dict[str, int]]:
                return grupo, "", {}

        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo, extractor_url=ExtractorGrupoCompleto())
        servicio.encolar_url(url, salida_dir=tmp_path)
        informe = servicio.procesar_siguiente()

        assert informe is not None and informe.exito
        assert "1 perfiles CvLAC enlazados" in informe.mensaje
        assert catalogo.cola_importacion.esta_vacia() is False
        grupo_guardado = catalogo.buscar_grupo("PRUEBA-URL-COMPLETA")
        assert grupo_guardado is not None
        assert grupo_guardado.fecha_creacion == "2015-05-01"
        assert grupo_guardado.categoria == "C"
        assert grupo_guardado.detalles["integrantes"][0]["codigo_rh"] == "000123"
        assert catalogo.buscar_investigador("000123") is not None
        assert any(
            integrante.codigo_gruplac == "PRUEBA-URL-COMPLETA"
            and integrante.codigo_rh == "000123"
            and integrante.fecha_inicio == "2018-01-01"
            for integrante in catalogo.integrantes
        )
        assert catalogo.buscar_producto("PROD-PRUEBA-URL-COMPLETA-0001") is not None
        assert catalogo.buscar_producto("PROD-PRUEBA-URL-COMPLETA-0002") is not None

    def test_url_omite_productos_sin_ano_y_no_inventa_2024(
        self,
        tmp_path: Path,
    ) -> None:
        url = (
            "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/"
            "visualizagr.jsp?nro=00000000000001"
        )
        grupo = GrupoIngesta(
            codigo_gruplac="PRUEBA-URL-GRUPO",
            nombre_grupo="Grupo de prueba",
            articulos=[
                ProductoIngesta(
                    tipo="Articulo",
                    tipo_mayor="GNC",
                    subtipo="Artículo Tipo A1",
                    titulo="Producto sin año informado",
                    ano=None,
                )
            ],
            origen=MetadatosOrigen(url=url, sha256="fixture"),
        )
        informe_extraccion = InformeIngesta(
            origen=url,
            tipo_fuente="url_gruplac",
            exito=True,
        )

        class ExtractorSinAno:
            def validar_url(self, url: str) -> tuple[str, str]:
                return "gruplac", ""

            def procesar_url(self, url: str, **_kwargs: object) -> InformeIngesta:
                return informe_extraccion

            def descargar_o_cargar_cache(
                self,
                url: str,
                alias: str | None = None,
            ) -> tuple[bytes, dict[str, str]]:
                return b"", {"encoding_utilizada": "utf-8"}

            def parsear_gruplac(
                self,
                html_text: str,
                meta: dict[str, str],
            ) -> tuple[GrupoIngesta, str, dict[str, int]]:
                return grupo, "", {}

        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo, extractor_url=ExtractorSinAno())
        servicio.encolar_url(url, salida_dir=tmp_path)
        informe = servicio.procesar_siguiente()

        assert informe is not None
        assert informe.exito is True
        assert informe.advertencias == [
            "Se omitió el producto GrupLAC #1: la fuente no informa el año."
        ]
        assert catalogo.buscar_grupo("PRUEBA-URL-GRUPO") is not None
        assert catalogo.buscar_producto("PROD-PRUEBA-URL-GRUPO-0001") is None

    def test_informe_csv_completo_y_error_de_lectura_comparten_contrato(
        self, tmp_path: Path
    ) -> None:
        fixture_path = (
            Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_importacion.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        datos_invalidos = fixture["filas_invalidas"]
        ruta = tmp_path / "productos.csv"
        contenido = datos_invalidos["contenido"].replace("ANIO_ACTUAL", str(date.today().year))
        ruta.write_text(contenido, encoding="utf-8")

        catalogo = CatalogoInvestigacion()
        servicio = ServicioIngesta(catalogo)
        tarea = servicio.encolar_csv(ruta, tipo_entidad="productos")
        informe = servicio.procesar_siguiente()

        assert informe is not None
        assert tarea.tipo_fuente == "csv_productos"
        assert informe.origen == str(ruta.resolve())
        assert informe.tipo_fuente == "csv_productos"
        assert datetime.fromisoformat(informe.fecha).tzinfo is not None
        assert informe.exito is True
        assert informe.mensaje == "Importación de CSV tipo 'productos' procesada"
        assert informe.grupos_procesados == 0
        assert informe.investigadores_procesados == 0
        assert informe.productos_procesados == 3
        assert informe.autores_procesados == 0
        assert informe.advertencias == []
        assert informe.archivos_generados == {}
        assert [
            {"fila": error["fila"], "mensaje": error["error"]}
            for error in informe.filas_erroneas
        ] == datos_invalidos["errores"]
        assert [
            error["datos"]["codigo_identificador"] for error in informe.filas_erroneas
        ] == [
            "PRUEBA-PROD-ERR-01",
            "PRUEBA-PROD-ERR-02",
            "PRUEBA-PROD-ERR-03",
            "PRUEBA-PROD-ERR-04",
        ]

        ruta_inexistente = tmp_path / "inexistente.csv"
        servicio.encolar_csv(ruta_inexistente, tipo_entidad="productos")
        informe_error = servicio.procesar_siguiente()

        assert informe_error is not None
        error_lectura = f"El archivo CSV no existe en la ruta: {ruta_inexistente.resolve()}"
        assert informe_error.origen == str(ruta_inexistente.resolve())
        assert informe_error.tipo_fuente == "csv_productos"
        assert datetime.fromisoformat(informe_error.fecha).tzinfo is not None
        assert informe_error.exito is False
        assert informe_error.mensaje == f"Error durante la ingesta: {error_lectura}"
        assert informe_error.advertencias == [error_lectura]
        assert informe_error.filas_erroneas == []

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
            "P-001,Artículo Base,Artículo Tipo A1,2023,GRP-01\n",
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

    def test_conflicto_revision_detiene_procesamiento_y_conserva_tareas_pendientes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        servicio = ServicioIngesta(CatalogoInvestigacion())
        url_base = "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh="
        servicio.encolar_url(f"{url_base}0000000001", salida_dir=tmp_path)
        servicio.encolar_url(f"{url_base}0000000002", salida_dir=tmp_path)

        def fallar_por_conflicto(_tarea: object) -> InformeIngesta:
            raise ConflictoRevision("La base de datos cambió", "revisión remota 2, local 1")

        monkeypatch.setattr(servicio, "_procesar_tarea_url", fallar_por_conflicto)
        informes = servicio.procesar_todas()

        assert len(informes) == 1
        assert not informes[0].exito
        assert informes[0].requiere_recarga
        assert len(servicio.cola_tareas) == 1
