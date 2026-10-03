cmake_minimum_required(VERSION 3.20)
project(pea-cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)
find_package(doctest REQUIRED)

if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

add_library(pea_core STATIC
    include/pea/version.hpp
    include/pea/excepciones.hpp
    include/pea/cliente_http.hpp
    include/pea/gui/ventana_principal.hpp
    src/cliente_http.cpp
    src/gui/ventana_principal.cpp
)

target_link_libraries(pea_core PUBLIC
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
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
    tests/test_gui.cpp
)

target_link_libraries(pruebas_cpp PRIVATE
    pea_core
    doctest::doctest
)

add_test(NAME pruebas_cpp COMMAND pruebas_cpp)
