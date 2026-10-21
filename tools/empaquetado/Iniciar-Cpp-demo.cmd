@echo off
cd /d "%~dp0"
chcp 65001 >nul
"PEAi-Cpp\pea-cpp.exe" --demo
if errorlevel 1 pause
