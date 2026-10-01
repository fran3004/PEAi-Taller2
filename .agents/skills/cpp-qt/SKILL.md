---
name: cpp-qt
description: Usar al escribir o depurar código C++17 del proyecto con CMake, Ninja, MSYS2 UCRT64 y Qt 6 (Widgets, QtNetwork, TLS, QJsonDocument, QPainter), incluida la memoria y las plantillas de estructuras.
---
# C++17 y Qt 6 en PEA-i

## Entorno
- Compilador y herramientas de MSYS2 UCRT64 en `C:/msys64/ucrt64/bin`. Generador Ninja. Presets `ucrt64-debug` y `ucrt64-release` (carpeta `build/<preset>`).
- Estándar C++17. Advertencias `-Wall -Wextra -Wpedantic` y cero advertencias.
- Qt: `find_package(Qt6 REQUIRED COMPONENTS Widgets Network)`. Con QObject o señales: `set(CMAKE_AUTOMOC ON)`.
- Librerías estáticas por módulo; estructuras como librería INTERFACE de solo cabeceras; `target_link_libraries` con PUBLIC o PRIVATE bien elegidos.

## Memoria
- Regla de los cinco: destructor, copia y movimiento definidos o prohibidos (`= delete`).
- Propiedad clara: quien crea un nodo es quien lo libera. Preferir `std::unique_ptr` para propiedad; punteros crudos solo para enlaces no propietarios (anterior, hermano).
- Tras eliminar un nodo, ningún puntero debe quedar apuntando a él.
- Probar con `-fsanitize=address,undefined` si el g++ lo permite.

## Red y JSON (Qt)
- `QNetworkAccessManager`, `QNetworkRequest` y `QNetworkReply`. Cabeceras `apikey` y `Authorization` según la skill postgresql-supabase.
- Versión síncrona con `QEventLoop` (para la CLI) y asíncrona con señales (para la GUI). Siempre con tiempo límite.
- JSON con `QJsonDocument`, `QJsonObject` y `QJsonArray`. Cuidado con enteros grandes (ids bigint): usar `toVariant().toLongLong()` o `qint64`.
- Paginación: leer `Content-Range` de la respuesta.
- TLS: probar `QSslSocket::supportsSsl()` y mostrar los backends. Si falla, instalar `mingw-w64-ucrt-x86_64-openssl` en MSYS2 y desplegar las DLL de OpenSSL junto al ejecutable.

## Interfaz
- Qt Widgets. Tablas con un modelo `QAbstractTableModel` (no `QTableWidget` con miles de filas).
- Gráficos dibujados con `QPainter` (barras, histogramas, apiladas) con paleta de la UPC y contraste mínimo 4.5:1.
- Todo texto en español; la interfaz nunca se bloquea esperando la red.
- Modo `--autoprueba` con `QT_QPA_PLATFORM=offscreen` y `QWidget::grab()` para capturar la ventana.

## Lista de comprobación
- [ ] Compila sin advertencias en debug y release.
- [ ] Pruebas doctest en verde (y con sanitizers si se pudo).
- [ ] Sin `std::list`, `std::vector` ni `std::map` como almacenamiento principal de entidades.
- [ ] HTTPS funciona en una carpeta limpia (DLL de TLS incluidas).
- [ ] Misma salida que Python para la misma entrada.
