#!/usr/bin/env python3
"""
tools/brain/verificar_brain.py
Validador de la bóveda de documentación viva brain/ para PEA-i.
Verifica:
- Propiedades obligatorias en el frontmatter YAML (tipo, estado, creado, actualizado, relacionado, origen).
- Valores válidos para tipo y estado.
- Formato de fechas (AAAA-MM-DD).
- Convención de nombres de archivo (sin espacios ni tildes).
- Enlaces internos [[wikienlaces]] rotos.
- Numeración consecutiva de notas ADR en brain/30-Decisiones/.
- Codificación UTF-8 sin BOM y finales de línea LF.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

TIPOS_VALIDOS = {
    "adr",
    "bitacora",
    "requisito",
    "historia-de-usuario",
    "caso-de-uso",
    "fuente",
    "nota-de-diseno",
    "resultado-de-pruebas",
    "informe-de-extraccion",
    "indice",
}

ESTADOS_VALIDOS = {"borrador", "revisado", "aprobado"}
FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
NOMBRE_ARCHIVO_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def parse_frontmatter(texto: str) -> tuple[dict[str, Any] | None, str]:
    """Extrae propiedades simples del frontmatter YAML sin depender de pyyaml."""
    if not texto.startswith("---"):
        return None, "No inicia con delimitador YAML '---'"

    partes = texto.split("---", 2)
    if len(partes) < 3:
        return None, "Frontmatter YAML incompleto o sin cierre '---'"

    yaml_block = partes[1]
    data: dict[str, Any] = {}
    current_key: str | None = None

    for line in yaml_block.splitlines():
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            continue

        # Lista de elementos bajo una clave
        if line.startswith("  - ") or line.startswith("- "):
            item = line_strip[2:].strip().strip('"').strip("'")
            if current_key:
                if not isinstance(data.get(current_key), list):
                    data[current_key] = []
                data[current_key].append(item)
            continue

        # Par clave: valor
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            current_key = key
            if val:
                data[key] = val
            else:
                data[key] = []
        else:
            current_key = None

    return data, ""


def verificar_boveda(raiz_repo: Path, restaurar: bool = False) -> int:
    boveda = raiz_repo / "brain"
    if not boveda.exists():
        print(f"ERROR: No se encontró la carpeta brain/ en {raiz_repo}")
        return 1

    errores: list[str] = []
    advertencias: list[str] = []
    notas_verificadas = 0

    # Construir mapa de notas existentes en brain/ (ignorando .obsidian y 90-Plantillas)
    todas_notas = list(boveda.rglob("*.md"))
    nombres_notas: dict[str, Path] = {}

    for nota in todas_notas:
        rel = nota.relative_to(boveda)
        if any(part in {".obsidian", "90-Plantillas"} for part in rel.parts):
            continue
        nombres_notas[nota.stem.lower()] = nota
        # Soportar enlaces relativos de carpeta como [[10-Requisitos/_Indice]]
        rel_str = str(rel.with_suffix("")).lower().replace("\\", "/")
        nombres_notas[rel_str] = nota
        # Soportar también la última parte de la carpeta + archivo
        if len(rel.parts) > 1:
            sub_rel = f"{rel.parts[-2].lower()}/{nota.stem.lower()}"
            nombres_notas[sub_rel] = nota

    # 1. Validar cada nota
    for nota in todas_notas:
        rel = nota.relative_to(boveda)
        if any(part in {".obsidian", "90-Plantillas"} for part in rel.parts):
            continue

        notas_verificadas += 1
        nombre = nota.name

        # Nombre de archivo sin tildes ni espacios
        if not NOMBRE_ARCHIVO_RE.match(nombre):
            errores.append(f"[{rel}] Nombre de archivo inválido (contiene espacios, tildes o caracteres no ASCII): '{nombre}'")

        # Codificación UTF-8 sin BOM y LF
        raw_bytes = nota.read_bytes()

        # Detección y auto-recuperación de archivos vacíos (0 bytes)
        if len(raw_bytes) == 0:
            if restaurar:
                import subprocess
                subprocess.run(["git", "checkout", "HEAD", "--", str(nota)], cwd=raiz_repo, capture_output=True)
                raw_bytes = nota.read_bytes()
                if len(raw_bytes) > 0:
                    advertencias.append(f"[{rel}] Archivo estaba vacío en disco y fue RESTAURADO automáticamente desde Git HEAD.")
                else:
                    errores.append(f"[{rel}] Archivo vacío (0 bytes) en disco y no existe en Git HEAD.")
                    continue
            else:
                errores.append(f"[{rel}] Archivo vacío (0 bytes). Recuperar con 'git checkout HEAD -- {nota.relative_to(raiz_repo)}' o ejecutar 'python tools/brain/verificar_brain.py --restaurar'")
                continue

        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            errores.append(f"[{rel}] Archivo contiene BOM UTF-8 (debe ser UTF-8 sin BOM)")
        if b"\r\n" in raw_bytes:
            errores.append(f"[{rel}] Contiene saltos de línea CRLF (debe ser LF)")

        try:
            contenido = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            errores.append(f"[{rel}] Error decodificando UTF-8: {e}")
            continue

        # Frontmatter
        data, err_fm = parse_frontmatter(contenido)
        if data is None:
            errores.append(f"[{rel}] Error de frontmatter: {err_fm}")
            continue

        # Propiedades obligatorias: tipo, estado, creado, actualizado, relacionado, origen
        propiedades_obligatorias = ["tipo", "estado", "creado", "actualizado", "relacionado", "origen"]
        for prop in propiedades_obligatorias:
            if prop not in data:
                errores.append(f"[{rel}] Falta la propiedad obligatoria '{prop}'")

        # Validación de tipo
        tipo = data.get("tipo")
        if tipo not in TIPOS_VALIDOS:
            errores.append(f"[{rel}] Tipo inválido '{tipo}'. Debe ser uno de: {sorted(TIPOS_VALIDOS)}")

        # Validación de estado
        estado = data.get("estado")
        if estado not in ESTADOS_VALIDOS:
            errores.append(f"[{rel}] Estado inválido '{estado}'. Debe ser uno de: {sorted(ESTADOS_VALIDOS)}")

        # Fechas
        for fprop in ["creado", "actualizado"]:
            fval = str(data.get(fprop, ""))
            if not FECHA_RE.match(fval):
                errores.append(f"[{rel}] Formato de fecha inválido en '{fprop}': '{fval}' (se espera AAAA-MM-DD)")

        # Enlaces
        relacionados = data.get("relacionado")
        if not isinstance(relacionados, list):
            errores.append(f"[{rel}] 'relacionado' debe ser una lista de enlaces")

        # Enlaces rotos en todo el contenido
        for link in WIKILINK_RE.findall(contenido):
            link_clean = link.strip().lower()
            if link_clean and link_clean not in nombres_notas:
                # Si el enlace apunta a un archivo que aún no existe
                advertencias.append(f"[{rel}] Enlace a nota no encontrada: [[{link}]]")

    # 2. Validar numeración consecutiva de ADR
    dir_adr = boveda / "30-Decisiones"
    if dir_adr.exists():
        adrs = sorted(dir_adr.glob("ADR-*.md"))
        esperado = 1
        for adr in adrs:
            m = re.match(r"^ADR-(\d{4})-", adr.name)
            if not m:
                errores.append(f"[30-Decisiones] Archivo ADR no sigue convención ADR-NNNN-titulo: {adr.name}")
            else:
                num = int(m.group(1))
                if num != esperado:
                    errores.append(f"[30-Decisiones] Salto en numeración de ADR. Se esperaba ADR-{esperado:04d}, encontrado {adr.name}")
                esperado = num + 1

    # Imprimir reporte
    print("=" * 60)
    print("REPORTE DE VERIFICACIÓN DE BOVEDA (PEA-i / brain)")
    print("=" * 60)
    print(f"Notas inspeccionadas: {notas_verificadas}")
    print(f"Errores encontrados: {len(errores)}")
    print(f"Advertencias encontradas: {len(advertencias)}")
    print("-" * 60)

    if advertencias:
        print("ADVERTENCIAS (enlaces pendientes o no resueltos):")
        for adv in advertencias:
            print(f"  [AVISO] {adv}")
        print("-" * 60)

    if errores:
        print("ERRORES:")
        for err in errores:
            print(f"  [FALLA] {err}")
        print("=" * 60)
        return 1

    print("Bóveda íntegra: todas las propiedades, formatos y reglas validadas correctamente.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent.parent
    restaurar = "--restaurar" in sys.argv
    sys.exit(verificar_boveda(raiz, restaurar=restaurar))

