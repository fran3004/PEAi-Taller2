@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo PEA-i: elija el origen de los datos.
choice /c SAV /n /m "[S] Supabase  [A] Archivo local  [V] Sin datos: "
if errorlevel 3 goto vacio
if errorlevel 2 goto archivo
"PEAi-Cpp\pea-cpp.exe"
goto fin
:archivo
echo Dentro del programa presione o para abrir el archivo JSON.
:vacio
"PEAi-Cpp\pea-cpp.exe" --vacio
:fin
