cmake_minimum_required(VERSION 3.20)
project(pea-cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Qt6 REQUIRED COMPONENTS Core Network)
find_package(doctest REQUIRED)

find_package(ftxui QUIET)
if(NOT TARGET ftxui::component)
    include(FetchContent)
    set(FTXUI_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(FTXUI_BUILD_DOCS OFF CACHE BOOL "" FORCE)
    set(FTXUI_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(
        ftxui
        GIT_REPOSITORY https://github.com/ArthurSonzogni/FTXUI.git
        GIT_TAG v5.0.0
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(ftxui)
endif()

if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

add_library(pea_core STATIC
    include/pea/version.hpp
    include/pea/excepciones.hpp
    include/pea/cliente_http.hpp
    include/pea/cli.hpp
    include/pea/aplicacion.hpp
    include/pea/tui/aplicacion_tui.hpp
    include/pea/estructuras/nodo.hpp
    include/pea/estructuras/lista_doble.hpp
    include/pea/estructuras/multilista.hpp
    include/pea/estructuras/pila.hpp
    include/pea/estructuras/cola.hpp
    include/pea/estructuras/hipercubo.hpp
    include/pea/dominio/grupo.hpp
    include/pea/dominio/investigador.hpp
    include/pea/dominio/integrante.hpp
    include/pea/dominio/producto.hpp
    include/pea/dominio/proyecto.hpp
    include/pea/dominio/plan.hpp
    include/pea/datos/sesion.hpp
    include/pea/datos/configuracion_conexion.hpp
    include/pea/datos/revision.hpp
    include/pea/datos/repositorios.hpp
    include/pea/datos/serializador_csv.hpp
    include/pea/servicios/catalogo_investigacion.hpp
    include/pea/servicios/filtro_anios.hpp
    include/pea/servicios/servicio_estadisticas.hpp
    include/pea/ingesta/modelos.hpp
    include/pea/ingesta/parser_html.hpp
    include/pea/ingesta/lector_csv.hpp
    include/pea/ingesta/extractor_url.hpp
    include/pea/ingesta/servicio_ingesta.hpp
    src/aplicacion.cpp
    src/tui/aplicacion_tui.cpp
    src/cliente_http.cpp
    src/datos/sesion.cpp
    src/datos/configuracion_conexion.cpp
    src/datos/revision.cpp
    src/datos/repositorios.cpp
    src/servicios/catalogo_investigacion.cpp
    src/servicios/servicio_estadisticas.cpp
    src/ingesta/parser_html.cpp
    src/ingesta/lector_csv.cpp
    src/ingesta/extractor_url.cpp
    src/ingesta/servicio_ingesta.cpp
    src/cli.cpp
)

target_link_libraries(pea_core PUBLIC
    Qt6::Core
    Qt6::Network
    ftxui::component
)

target_include_directories(pea_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

add_executable(pea-cpp
    src/main.cpp
)

target_link_libraries(pea-cpp PRIVATE
    pea_core
)

enable_testing()

add_executable(pruebas_cpp
    tests/test_version.cpp
    tests/test_cliente_http.cpp
    tests/test_estructuras.cpp
    tests/test_cascadas.cpp
    tests/test_deshacer.cpp
    tests/test_resiliencia.cpp
    tests/test_ingesta.cpp
    tests/test_hipercubo.cpp
    tests/test_filtro_estadisticas.cpp
    tests/test_serializador_csv.cpp
)

target_link_libraries(pruebas_cpp PRIVATE
    pea_core
    doctest::doctest
)
target_compile_definitions(pruebas_cpp PRIVATE
    PEA_TEST_FIXTURES_DIR="${CMAKE_CURRENT_SOURCE_DIR}/tests/fixtures"
)

add_test(NAME pruebas_cpp COMMAND pruebas_cpp)
