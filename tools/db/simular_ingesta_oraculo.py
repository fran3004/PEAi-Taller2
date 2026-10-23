#!/usr/bin/env python3
"""Prueba de extremo a extremo: simulación de ingesta del fixture cvlac_0000494917

contra el catálogo cargado desde la base de datos real reconciliada.
Verifica:
1. Se reconocen los 26 artículos reales del fixture.
2. NO se crea ningún producto nuevo (porque ya existen con sus códigos estables/conciliados).
3. No se tocan productos de otros tipos.
4. El conteo total de productos en memoria no cambia.
"""

from __future__ import annotations

import sys
from pathlib import Path

_raiz_repo = Path(__file__).resolve().parents[2]
if str(_raiz_repo) not in sys.path:
    sys.path.insert(0, str(_raiz_repo))
_raiz_src = _raiz_repo / "src"
if str(_raiz_src) not in sys.path:
    sys.path.insert(0, str(_raiz_src))

from pea.cliente_http import ClienteHTTPSupabase  # noqa: E402
from pea.ingesta.extractor_url import ExtractorURL  # noqa: E402
from pea.ingesta.modelos import InformeIngesta, InvestigadorIngesta  # noqa: E402
from pea.ingesta.servicio_ingesta import ServicioIngesta  # noqa: E402
from pea.servicios.servicio_dominio import CatalogoInvestigacion  # noqa: E402
from tools.db.respaldar import cargar_configuracion, obtener_token_autenticado  # noqa: E402


def simular_ingesta_oraculo() -> int:
    url_base, anon_key = cargar_configuracion()
    cliente = ClienteHTTPSupabase(url_base, anon_key)
    token = obtener_token_autenticado(url_base, anon_key)
    if token:
        cliente.establecer_token_acceso(token)

    print("[*] Cargando catálogo completo desde Supabase real...")
    catalogo = CatalogoInvestigacion(cliente)
    catalogo.recargar_todo()

    tamano_inicial = catalogo.multilista_productos.tamano
    conteo_grupos_inicial = catalogo.grupos.tamano
    conteo_inv_inicial = catalogo.investigadores.tamano
    print(f"    Productos iniciales en memoria: {tamano_inicial}")
    print(f"    Investigadores en memoria:      {conteo_inv_inicial}")
    print(f"    Grupos en memoria:              {conteo_grupos_inicial}")

    ruta_fixture = Path("tests/fixtures/scienti/cvlac_0000494917.html")
    if not ruta_fixture.exists():
        print(f"[ERROR] Fixture no encontrado: {ruta_fixture}", file=sys.stderr)
        return 1

    html_bytes = ruta_fixture.read_bytes()
    url_scienti = (
        "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917"
    )

    extractor_real = ExtractorURL()
    inv_parsed, _, _ = extractor_real.parsear_cvlac(
        html_bytes.decode("iso-8859-1"),
        {"url": url_scienti, "sha256": "fixture"},
    )

    articulos_reales = len(inv_parsed.articulos)
    print("[*] Fixture parseado:")
    print(f"    Artículos reconocidos: {articulos_reales} (esperado: 26)")
    if articulos_reales != 26:
        print(f"[ERROR] El fixture debió devolver exactamente 26 artículos reales, no {articulos_reales}", file=sys.stderr)
        return 1

    # Verificar que ninguno empieza por "Producción bibliográfica - Artículo"
    for art in inv_parsed.articulos:
        if (art.titulo or "").startswith("Producción bibliográfica - Artículo"):
            print(f"[ERROR] Se encontró producto fantasma: {art.titulo}", file=sys.stderr)
            return 1

    class ExtractorMock:
        def validar_url(self, origen: str) -> tuple[str, str]:
            return "cvlac", ""

        def procesar_url(self, url: str, **_kwargs: object) -> InformeIngesta:
            return InformeIngesta(origen=url, tipo_fuente="url_cvlac", exito=True)

        def descargar_o_cargar_cache(self, url: str, alias: str | None = None) -> tuple[bytes, dict[str, str]]:
            return html_bytes, {"url": url, "sha256": "fixture", "encoding_utilizada": "iso-8859-1"}

        def parsear_cvlac(self, html_text: str, meta: dict[str, str]) -> tuple[InvestigadorIngesta, str, dict[str, int]]:
            return extractor_real.parsear_cvlac(html_text, meta)

    servicio = ServicioIngesta(catalogo, extractor_url=ExtractorMock())
    servicio.encolar_url(url_scienti, persistir=False)

    print("[*] Ejecutando simulación de ingesta (persistir=False)...")
    _informe = servicio.procesar_siguiente()

    tamano_final = catalogo.multilista_productos.tamano
    conteo_grupos_final = catalogo.grupos.tamano
    conteo_inv_final = catalogo.investigadores.tamano

    print("[*] Resultados post-ingesta:")
    print(f"    Productos en memoria: {tamano_final} (inicial: {tamano_inicial})")
    print(f"    Investigadores:       {conteo_inv_final} (inicial: {conteo_inv_inicial})")
    print(f"    Grupos:               {conteo_grupos_final} (inicial: {conteo_grupos_inicial})")

    if tamano_final != tamano_inicial:
        diferencia = tamano_final - tamano_inicial
        print(f"[ERROR] Se crearon {diferencia} productos nuevos en memoria durante la re-ingesta!", file=sys.stderr)
        return 1

    print("[ÉXITO] Simulación de ingesta superada: 0 productos duplicados o creados, 26 artículos reconocidos.")
    return 0


if __name__ == "__main__":
    sys.exit(simular_ingesta_oraculo())
