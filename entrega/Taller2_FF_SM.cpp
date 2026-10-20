/*
Universidad Popular del Cesar (UPC)
Facultad de Ingenierías y Tecnologías
Ingeniería de Sistemas · Estructura de Datos · Taller 2 · Grupo 8
Integrantes: franier fernandez (FF), santiago moreno (SM)

Índice de implementación del enunciado:
1. Grupos: pea::servicios::CatalogoInvestigacion::crear_grupo
2. Investigadores: pea::servicios::CatalogoInvestigacion::crear_investigador
3. Productos y relaciones: CatalogoInvestigacion::crear_producto
4. Estructuras de datos: cpp/include/pea/estructuras/
5. Persistencia REST/RPC: cpp/src/datos/repositorios.cpp
6. Revisión concurrente: CatalogoInvestigacion::verificar_revision
7. Importación CSV/URL: pea::ingesta::ServicioIngesta
8. Deshacer: CatalogoInvestigacion::deshacer
9. Estadísticas: pea::servicios::ServicioEstadisticas
10. Terminal interactiva: pea::tui::ejecutar
11. Resumen institucional: CatalogoInvestigacion::resumen_json
12. Conexión HTTPS: pea::ClienteHTTPSupabase
13. Interfaz de línea de comandos: pea::cli::ejecutar
14. Entrada única de la aplicación: pea::ejecutar_aplicacion

La matriz de paridad documenta las funciones todavía parciales o pendientes;
el índice identifica código existente, no certifica por sí solo cumplimiento
integral de cada punto.
*/

#include "pea/aplicacion.hpp"

int main(int argc, char* argv[]) {
    return pea::ejecutar_aplicacion(argc, argv);
}
