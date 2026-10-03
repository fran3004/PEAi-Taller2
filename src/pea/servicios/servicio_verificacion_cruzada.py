"""Verificación cruzada: ejecuta la CLI de Python y la de C++ con los mismos comandos y compara.

Es la prueba observable del principio de equivalencia (brain/20-Diseno/Interoperabilidad.md):
el resumen JSON canónico debe coincidir byte a byte (solo se normaliza el fin de línea,
porque Windows escribe CRLF en la consola) y el escenario de mutaciones debe terminar igual.

Se ejecuta en un hilo de trabajo (nunca en el hilo de la interfaz). Por defecto se quitan del
entorno del proceso hijo las variables PEA_SUPABASE_* y PEA_USUARIO_* para que ambas CLI
trabajen sin red y de forma determinista; con usar_base=True se conservan.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import pea


class Comparacion(StrEnum):
    EXACTA = "exacta"
    PRIMERA_LINEA = "primera_linea"
    ULTIMA_LINEA = "ultima_linea"


@dataclass(frozen=True)
class PasoVerificacion:
    nombre: str
    argumentos: tuple[str, ...]
    comparacion: Comparacion


PASOS_POR_DEFECTO: tuple[PasoVerificacion, ...] = (
    PasoVerificacion("Versión de la aplicación", ("--version",), Comparacion.PRIMERA_LINEA),
    PasoVerificacion("Resumen JSON canónico", ("resumen", "--json"), Comparacion.EXACTA),
    PasoVerificacion("Escenario de mutaciones y deshacer", ("aplicar-escenario",), Comparacion.ULTIMA_LINEA),
)


@dataclass(frozen=True)
class ResultadoPaso:
    nombre: str
    comando: str
    codigo_python: int | None
    codigo_cpp: int | None
    salida_python: str
    salida_cpp: str
    coincide: bool
    detalle: str


@dataclass(frozen=True)
class ResultadoVerificacionCruzada:
    comando_python: str
    comando_cpp: str | None
    pasos: tuple[ResultadoPaso, ...]
    mensaje: str

    @property
    def exito(self) -> bool:
        return self.comando_cpp is not None and len(self.pasos) > 0 and all(p.coincide for p in self.pasos)


# Firma del ejecutor de procesos: (argv, entorno, directorio) -> (código, stdout, stderr)
EjecutorProcesos = Callable[[list[str], dict[str, str], Path], tuple[int, str, str]]


def _ejecutar_proceso(argv: list[str], entorno: dict[str, str], directorio: Path) -> tuple[int, str, str]:
    banderas = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    completado = subprocess.run(  # noqa: S603 - argv construido internamente, sin shell
        argv,
        cwd=str(directorio),
        env=entorno,
        capture_output=True,
        timeout=90,
        creationflags=banderas,
        check=False,
    )
    salida = completado.stdout.decode("utf-8", errors="replace")
    error = completado.stderr.decode("utf-8", errors="replace")
    return completado.returncode, salida, error


def _normalizar(texto: str) -> str:
    return "\n".join(linea.rstrip() for linea in texto.replace("\r\n", "\n").split("\n")).strip()


def _linea(texto: str, ultima: bool) -> str:
    lineas = [ln for ln in _normalizar(texto).split("\n") if ln.strip()]
    if not lineas:
        return ""
    return lineas[-1] if ultima else lineas[0]


class ServicioVerificacionCruzada:
    """Localiza ambas CLI, las ejecuta con los mismos argumentos y compara sus salidas."""

    def __init__(
        self,
        raiz_proyecto: Path | None = None,
        ejecutor: EjecutorProcesos | None = None,
        pasos: tuple[PasoVerificacion, ...] = PASOS_POR_DEFECTO,
    ) -> None:
        self.raiz = raiz_proyecto or Path(pea.__file__).resolve().parents[2]
        self._ejecutor = ejecutor or _ejecutar_proceso
        self.pasos = pasos

    # ------------------------------------------------------------------ localización
    def comando_python(self) -> list[str]:
        return [sys.executable, "-m", "pea.cli"]

    def ruta_cpp(self) -> Path | None:
        explicita = os.environ.get("PEA_CPP_EXE")
        candidatos: list[Path] = []
        if explicita:
            candidatos.append(Path(explicita))
        nombre = "pea-cpp.exe" if os.name == "nt" else "pea-cpp"
        candidatos.append(self.raiz / "cpp" / "build" / nombre)
        for candidato in candidatos:
            if candidato.is_file():
                return candidato
        return None

    def _entorno_hijo(self, usar_base: bool) -> dict[str, str]:
        entorno = dict(os.environ)
        if not usar_base:
            for clave in list(entorno):
                if clave.startswith("PEA_SUPABASE_") or clave.startswith("PEA_USUARIO_"):
                    del entorno[clave]
        entorno["PYTHONIOENCODING"] = "utf-8"
        ruta_src = str(Path(pea.__file__).resolve().parents[1])
        entorno["PYTHONPATH"] = ruta_src + os.pathsep + entorno.get("PYTHONPATH", "")
        if os.name == "nt":
            msys = os.environ.get("PEA_MSYS2_BIN") or r"C:\msys64\ucrt64\bin"
            if Path(msys).is_dir():
                entorno["PATH"] = msys + os.pathsep + entorno.get("PATH", "")
        return entorno

    # ------------------------------------------------------------------ ejecución
    def ejecutar(self, usar_base: bool = False) -> ResultadoVerificacionCruzada:
        cmd_py = self.comando_python()
        exe_cpp = self.ruta_cpp()
        texto_py = " ".join(cmd_py)
        if exe_cpp is None:
            return ResultadoVerificacionCruzada(
                comando_python=texto_py,
                comando_cpp=None,
                pasos=(),
                mensaje=(
                    "No se encontró el ejecutable C++ (cpp/build/pea-cpp.exe). "
                    "Compílelo con CMake o indique su ruta en la variable PEA_CPP_EXE."
                ),
            )

        entorno = self._entorno_hijo(usar_base)
        resultados: list[ResultadoPaso] = []
        for paso in self.pasos:
            resultados.append(self._ejecutar_paso(paso, cmd_py, exe_cpp, entorno))

        coinciden = sum(1 for r in resultados if r.coincide)
        mensaje = f"{coinciden} de {len(resultados)} comprobaciones coinciden entre Python y C++."
        return ResultadoVerificacionCruzada(
            comando_python=texto_py,
            comando_cpp=str(exe_cpp),
            pasos=tuple(resultados),
            mensaje=mensaje,
        )

    def _ejecutar_paso(
        self,
        paso: PasoVerificacion,
        cmd_py: list[str],
        exe_cpp: Path,
        entorno: dict[str, str],
    ) -> ResultadoPaso:
        args = list(paso.argumentos)
        try:
            cod_py, out_py, err_py = self._ejecutor(cmd_py + args, entorno, self.raiz)
        except (OSError, subprocess.SubprocessError) as err:
            cod_py, out_py, err_py = None, "", f"No se pudo ejecutar Python: {err}"
        try:
            cod_cpp, out_cpp, err_cpp = self._ejecutor([str(exe_cpp), *args], entorno, self.raiz)
        except (OSError, subprocess.SubprocessError) as err:
            cod_cpp, out_cpp, err_cpp = None, "", f"No se pudo ejecutar C++: {err}"

        if paso.comparacion == Comparacion.EXACTA:
            a, b = _normalizar(out_py), _normalizar(out_cpp)
        elif paso.comparacion == Comparacion.PRIMERA_LINEA:
            a, b = _linea(out_py, ultima=False), _linea(out_cpp, ultima=False)
        else:
            a, b = _linea(out_py, ultima=True), _linea(out_cpp, ultima=True)

        codigos_ok = cod_py == 0 and cod_cpp == 0
        coincide = codigos_ok and a == b and a != ""
        if coincide:
            detalle = "Coinciden" if paso.comparacion == Comparacion.EXACTA else "Coinciden (línea comparada)"
        elif not codigos_ok:
            detalle = f"Código de salida distinto de 0 (Python={cod_py}, C++={cod_cpp}). {err_py or err_cpp}".strip()
        else:
            detalle = "Las salidas difieren"

        return ResultadoPaso(
            nombre=paso.nombre,
            comando=" ".join(args),
            codigo_python=cod_py,
            codigo_cpp=cod_cpp,
            salida_python=_normalizar(out_py) or _normalizar(err_py),
            salida_cpp=_normalizar(out_cpp) or _normalizar(err_cpp),
            coincide=coincide,
            detalle=detalle,
        )
