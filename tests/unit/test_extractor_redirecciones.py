"""Pruebas unitarias para el manejo seguro de redirecciones en ExtractorURL."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
import requests

from pea.ingesta.extractor_url import ExtractorURL


class MockResponse:
    """Respuesta simulada para requests.get."""

    def __init__(
        self,
        status_code: int = 200,
        content: bytes = b"<html>OK</html>",
        headers: dict[str, str] | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.encoding = encoding
        self.apparent_encoding = encoding

    @property
    def is_redirect(self) -> bool:
        return "location" in {k.lower(): v for k, v in self.headers.items()} and self.status_code in (
            301,
            302,
            303,
            307,
            308,
        )


URL_BASE = (
    "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099"
)


class TestExtractorRedirecciones:
    """Verifica el seguimiento manual, seguro y acotado de redirecciones HTTP."""

    def test_redireccion_otro_host_rechazada_sin_reintentos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(a) Redirección 302 hacia otro host debe rechazarse con mensaje claro y SIN reintentos."""
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            assert kwargs.get("allow_redirects") is False
            return MockResponse(
                status_code=302,
                headers={"Location": "https://malicioso.com/gruplac/visualiza.jsp"},
            )

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)

        with pytest.raises(ValueError, match="Host no permitido"):
            extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

        # Debe fallar inmediatamente en el primer intento sin reintentar
        assert len(llamadas) == 1

    def test_redireccion_hacia_http_rechazada_sin_reintentos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(b) Redirección hacia http:// debe rechazarse sin reintentos."""
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            assert kwargs.get("allow_redirects") is False
            return MockResponse(
                status_code=301,
                headers={"Location": "http://scienti.minciencias.gov.co/gruplac/seguro.jsp"},
            )

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)

        with pytest.raises(ValueError, match="Solo se permite HTTPS"):
            extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

        assert len(llamadas) == 1

    def test_redireccion_valida_mismo_host_se_sigue_y_guarda_url_final(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(c) Redirección en el mismo host y con ruta válida debe seguirse y guardar url_final."""
        url_destino_relativo = "/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099&lang=es"
        url_destino_absoluto = f"https://scienti.minciencias.gov.co{url_destino_relativo}"
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            assert kwargs.get("allow_redirects") is False
            if len(llamadas) == 1:
                return MockResponse(status_code=302, headers={"Location": url_destino_relativo})
            return MockResponse(status_code=200, content=b"<html>Contenido Final</html>")

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)
        content, meta = extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

        assert len(llamadas) == 2
        assert llamadas[0] == URL_BASE
        assert llamadas[1] == url_destino_absoluto
        assert content == b"<html>Contenido Final</html>"
        assert meta["url"] == URL_BASE
        assert meta["url_final"] == url_destino_absoluto
        assert meta["codigo_http"] == 200

        # La clave de caché debe seguir siendo el hash de la URL original
        hash_esperado = hashlib.sha256(URL_BASE.encode("utf-8")).hexdigest()
        assert (tmp_path / f"{hash_esperado}.html").exists()
        assert (tmp_path / f"{hash_esperado}.meta.json").exists()

    def test_mas_de_tres_saltos_falla(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(d) Más de 3 saltos debe fallar."""
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            salto_num = len(llamadas)
            # Cada salto devuelve un nuevo 302 válido
            return MockResponse(
                status_code=302,
                headers={
                    "Location": f"/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099&paso={salto_num}"
                },
            )

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)

        with pytest.raises(Exception, match="(?i)(redireccion|saltos|l[ií]mite)"):
            extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

    def test_caso_normal_sin_redireccion_mantiene_comportamiento(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """(e) El caso normal sin redirección sigue funcionando igual."""
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            assert kwargs.get("allow_redirects") is False
            return MockResponse(status_code=200, content=b"<html>Respuesta Directa</html>")

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)
        content, meta = extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

        assert len(llamadas) == 1
        assert content == b"<html>Respuesta Directa</html>"
        assert meta["url"] == URL_BASE
        assert meta["url_final"] == URL_BASE
        assert meta["codigo_http"] == 200

    def test_redireccion_ruta_no_reconocida_rechazada_sin_reintentos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Redirección hacia ruta que no es GrupLAC ni CvLAC se rechaza sin reintentos."""
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            assert kwargs.get("allow_redirects") is False
            return MockResponse(
                status_code=302,
                headers={"Location": "/pagina_arbitraria.jsp"},
            )

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)

        with pytest.raises(ValueError, match="no reconocida como GrupLAC ni CvLAC"):
            extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

        assert len(llamadas) == 1

    def test_redireccion_sin_cabecera_location_falla(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Respuesta 302 sin cabecera Location debe fallar."""
        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            return MockResponse(status_code=302, headers={})

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)

        with pytest.raises(RuntimeError, match="sin cabecera Location"):
            extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

    def test_error_red_temporal_si_se_reintenta(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Errores de red y códigos HTTP temporales sí entran al ciclo de reintentos."""
        llamadas: list[str] = []

        def mock_get(url: str, **kwargs: Any) -> MockResponse:
            llamadas.append(url)
            if len(llamadas) < 3:
                raise requests.ConnectionError("Fallo temporal de conexión")
            return MockResponse(status_code=200, content=b"<html>Recuperado</html>")

        monkeypatch.setattr(requests, "get", mock_get)

        extractor = ExtractorURL(cache_dir=tmp_path, pausa_segundos=0.0)
        content, meta = extractor.descargar_o_cargar_cache(URL_BASE, forzar_descarga=True)

        assert len(llamadas) == 3
        assert content == b"<html>Recuperado</html>"
        assert meta["codigo_http"] == 200
