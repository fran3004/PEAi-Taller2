"""Extrae el catálogo de puntajes del Modelo original; no consulta ni modifica la BD."""

import json
import re
from pathlib import Path

import pdfplumber

RAIZ = Path(__file__).resolve().parents[2]


def generar() -> dict:
    texto = (RAIZ / "docs/entrada/Modelo-2024.md").read_text(encoding="utf-8")
    clases = {}
    titulos = [
        "3.7.1 Productos Tipo TOP",
        "3.7.2 Productos Tipo A",
        "3.7.3 Productos Tipo B",
        "3.7.4 Productos de Apropiación",
        "3.7.5 Productos de Divulgación",
        "3.7.6 Productos de Actividades",
        "3.7.7 Productos de Actividades",
        "3.8 Cálculo de Indicadores",
    ]
    posiciones = [texto.index(t, texto.index("## Página 119")) for t in titulos]
    for clase, inicio, fin in zip(
        ["Nc.Top", "Nc.A", "Nc.B", "AP", "DPC", "Fr.A", "Fr.B"], posiciones, posiciones[1:], strict=False
    ):
        for codigo in re.findall(r"● ([A-Z][A-Z0-9_]+), Número", texto[inicio:fin]):
            clases[codigo] = clase
    # Tabla IX presenta P y M en columnas distintas y el código combinado.
    patentes = [
        ("A1", 10, 6),
        ("A2", 7, 4.2),
        ("A3", 6, 3.6),
        ("A4", 5.5, 3.33),
        ("B1", 5, 3),
        ("B2", 3.5, 2.1),
        ("B3", 3, 1.8),
        ("B4", 2.6, 1.7),
        ("B5", 2.5, 1.5),
        ("C", 1.8, 1.1),
    ]
    pesos = {
        prefijo + sufijo: (peso, 142 if sufijo.startswith("A") else 143)
        for sufijo, p, m in patentes
        for prefijo, peso in [("P", p), ("M", m)]
    }
    with pdfplumber.open(RAIZ / "docs/entrada/Modelo-2024.original.pdf") as pdf:
        for indice in range(130, 169):
            for tabla in pdf.pages[indice].extract_tables():
                for fila in tabla:
                    for col, celda in enumerate(fila):
                        codigo = (celda or "").replace("\n", "").replace(" ", "")
                        if codigo not in clases:
                            continue
                        numeros = [
                            c.strip() for c in fila[col + 1 :] if c and re.fullmatch(r"\d+(?:[.,]\d+)?", c.strip())
                        ]
                        if numeros:
                            pesos[codigo] = (float(numeros[-1].replace(",", ".")), indice + 1)
    # Tabla 6: peso base por familia. Las categorías de menor calidad usan el
    # mismo peso base que la de mayor calidad de su familia (sección 3.6).
    bases = {
        "ART": 100,
        "ART_D": 5,
        "ART_OPEN_D": 5,
        "N": 4,
        "LIB": 300,
        "LIB_C": 15,
        "CAP_LIB": 60,
        "CAP_LIB_C": 3,
        "LIB_FOR1": 60,
        "LIB_FOR2": 100,
        "LIB_FOR3": 100,
        "PA": 500,
        "PB": 500,
        "PC": 500,
        "MA": 500,
        "MB": 500,
        "MC": 500,
        "VV": 300,
        "VA": 300,
        "AAD": 100,
        "DI": 35,
        "ECI": 35,
        "SF": 35,
        "PP": 35,
        "PI": 35,
        "SD": 35,
        "PN": 35,
        "CC": 35,
        "NRC": 35,
        "SE": 100,
        "EBT": 100,
        "ICC": 100,
        "IG": 100,
        "IPP": 100,
        "RNL": 100,
        "RNR": 100,
        "RNT": 100,
        "RNPC": 100,
        "GMCF": 100,
        "MADV": 100,
        "PAU": 100,
        "PVE": 100,
        "AL": 100,
        "RNPL": 100,
        "CT": 15,
        "MR": 14,
        "FIS": 200,
        "GPP": 200,
        "FCP": 200,
        "TCCG": 200,
        "TD": 160,
        "TM": 70,
        "TP": 20,
        "PID": 50,
        "PIC": 50,
        "PF": 50,
        "PE": 100,
        "AP": 100,
        "APO": 30,
    }
    reglas = []
    faltantes = []
    for codigo, clase in clases.items():
        if codigo not in pesos:
            faltantes.append(codigo)
            continue
        familia = next(
            (
                k
                for k in sorted(bases, key=len, reverse=True)
                if codigo == k or codigo.startswith(k + "_") or (k in {"PA", "PB", "MA", "MB"} and codigo.startswith(k))
            ),
            None,
        )
        base = bases[familia] if familia else 100 if clase == "DPC" else None
        if base is None:
            raise ValueError(f"Falta peso base para {codigo}")
        tipo = "FRH" if clase.startswith("Fr.") else "ASC" if clase in {"AP", "DPC"} else "GNC"
        if codigo.split("_")[0] in {
            "DI",
            "ECI",
            "SF",
            "PP",
            "PI",
            "SD",
            "PN",
            "CC",
            "NRC",
            "SE",
            "EBT",
            "ICC",
            "IG",
            "IPP",
            "RNL",
            "RNR",
            "RNT",
            "RNPC",
            "GMCF",
            "MADV",
            "PAU",
            "PVE",
            "AL",
            "RNPL",
            "CT",
            "MR",
        }:
            tipo = "DTI"
        relativo, pagina = pesos[codigo]
        reglas.append(
            {
                "codigo": codigo,
                "clase": clase,
                "tipo_mayor": tipo,
                "peso_relativo": relativo,
                "peso_base": base,
                "ventana": (
                    7
                    if (codigo.startswith("ART_") and not codigo.endswith("_D"))
                    or codigo in {"LIB_A1", "LIB_A", "LIB_B", "LIB_C"}
                    else 10
                    if re.fullmatch(r"[PM](?:A[1-4]|B[1-5]|C)", codigo) or codigo.startswith(("VV_", "VA_", "AAD_"))
                    else 5
                ),
                "pagina": pagina,
            }
        )
    if faltantes:
        raise ValueError(f"Categorías sin peso extraíble: {faltantes}")
    return {
        "version": "M601PR04G01-v02-2024",
        "fuente": "Modelo-2024.original.pdf, secciones 3.5-3.10 y tablas del Anexo 1",
        "coeficientes": {
            "Nc.Top": 3.7,
            "Nc.A": 2.3,
            "Nc.B": 0.4,
            "AP": 1.5,
            "DPC": 0.5,
            "Fr.A": 1.0,
            "Fr.B": 0.2,
            "Cohe": 0.1,
            "Coop": 0.3,
        },
        "categorias": reglas,
    }


if __name__ == "__main__":
    datos = generar()
    destino = RAIZ / "src/pea/recursos/modelo_2024.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(datos['categorias'])} categorías: {destino}")
