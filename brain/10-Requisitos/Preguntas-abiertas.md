---
tipo: requisito
estado: borrador
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SPEC]]"
  - "[[Variables-entrada-salida]]"
  - "[[00-Inicio]]"
origen: "Análisis de Requisitos y Extracción de Fuentes"
---

# Preguntas Abiertas e Incertidumbres de Diseño · PEA-i

Este documento registra formalmente las dudas, ambigüedades y decisiones metodológicas detectadas durante la fase de análisis de requisitos, las cuales requieren confirmación o definición por parte del usuario o docente antes de iniciar la implementación del esquema de base de datos y la arquitectura técnica.

---

## 1. Alcance de los Cálculos de Cohesión y Cooperación de Grupos

- **Contexto**: El Modelo Minciencias 2024 (Capítulo 4, páginas 67–68; [[Modelo-Estadisticas#1. Indicadores de Cohesión y Cooperación]]) define formalmente los indicadores de Cohesión y Cooperación mediante formulaciones matriciales que consideran pesos ponderados de coautoría entre integrantes de un mismo grupo frente a colaboraciones con investigadores externos o de otras instituciones.
- **Incertidumbre**: ¿Se espera que el sistema implemente en memoria la formulación matemática matricial ponderada exacta del Modelo 2024, o es suficiente una aproximación descriptiva y algorítmica sobre la multilista (ej. porcentaje de productos con coautorías internas del grupo vs. porcentaje de productos con coautores externos)?
- **Supuesto de partida (`[SUPUESTO]`)**: Se implementará un cálculo analítico directo sobre los enlaces de la Multilista que reportará:
  $$\text{Tasa de Cohesión Bruta} = \frac{\text{Productos con } \ge 2 \text{ autores del grupo}}{\text{Total de productos del grupo}}$$
  $$\text{Tasa de Cooperación Bruta} = \frac{\text{Productos con autores externos o intergrupales}}{\text{Total de productos del grupo}}$$
  Si el docente requiere la fórmula matricial exacta con matrices de ponderación, se incorporará mediante un ADR específico.

---

## 2. Reglas de Cascada en la Eliminación Física de Investigadores con Producción

- **Contexto**: En la estructura de Multilista (R4), un nodo `Producto` es compartido entre el grupo y todos los investigadores coautores. Al ejecutar un borrado físico (`DELETE` en Supabase y remoción de nodo):
- **Incertidumbre**: ¿Qué política de integridad referencial debe aplicarse si se solicita eliminar físicamente a un investigador que figura como coautor en productos compartidos con otros investigadores activos? ¿Y qué ocurre si era el único autor del producto?
- **Supuesto de partida (`[SUPUESTO]`)**:
  1. Si el investigador es el **único autor** registrado del producto, se bloquea la eliminación física hasta que el producto sea reasignado o eliminado explícitamente, o se sugiere la **desactivación lógica** (`activo=false`).
  2. Si el producto tiene **múltiples coautores**, al eliminar físicamente al investigador se retira su enlace de la multilista y de la tabla relacional, pero el producto y sus enlaces con los demás coautores y con el grupo se preservan intactos.
  3. Si el investigador es el **único Líder activo** de un grupo, la eliminación física se prohíbe terminantemente hasta que se designe un nuevo líder.

---

## 3. Rango Temporal y Ventana de Años del Hipercubo

- **Contexto**: En la dimensión temporal (Dimensión 4: Año) del Hipercubo, los datos reales de CvLAC y GrupLAC contienen registros históricos de producción desde 1990 o incluso antes. Minciencias, por su parte, evalúa grupos con ventanas móviles de 5 años.
- **Incertidumbre**: ¿El Hipercubo debe dimensionarse de forma fija para un rango histórico predeterminado (ej. 2010 a 2026), o debe soportar dimensiones dinámicas dispersas (*sparse array/tensor*) que se adapten a cualquier año encontrado en los datos?
- **Supuesto de partida (`[SUPUESTO]`)**: El Hipercubo se implementará como una estructura multidimensional dispersa basada en índices de mapeo o claves dimensionales, permitiendo almacenar cualquier año sin desperdiciar memoria en celdas vacías. En la interfaz gráfica, la ventana por defecto de visualización será de 5 años móviles (año actual menos 4), con opción de expandir a "Histórico Completo".

---

## 4. Estado de Validación Inicial para Datos Extraídos de GrupLAC

- **Contexto**: Las páginas HTML públicas de GrupLAC muestran la producción del grupo sin explicitar de forma textual la columna "Aval Institucional", ya que al estar publicada en el portal institucional avalado por Minciencias se sobreentiende su reconocimiento formal.
- **Incertidumbre**: Al importar productos mediante scraping web desde GrupLAC, ¿con qué estado de validación deben registrarse en la Dimensión 5 del Hipercubo?
- **Supuesto de partida (`[SUPUESTO]`)**: Todo producto extraído directamente de una URL oficial de GrupLAC se registrará inicialmente con el estado `Avalado`. Si se detecta que un producto carece de año o soporte mínimo en el texto, se asignará `Con soporte` para requerir verificación manual por parte del usuario.

---

## 5. Formato Estándar de los Archivos CSV de Contingencia (R12)

- **Contexto**: El requisito R12 exige la importación de datos desde archivos CSV para operar sin conexión o en pruebas masivas.
- **Incertidumbre**: ¿Se prefiere un único archivo consolidado desnormalizado (`investigacion_upc.csv` con columnas de grupo, investigador y producto en cada fila) o una estructura modular de 3 archivos CSV normalizados (`grupos.csv`, `investigadores.csv`, `productos.csv`)?
- **Supuesto de partida (`[SUPUESTO]`)**: El sistema soportará prioritariamente el paquete modular de 3 archivos CSV normalizados (facilitando la coincidencia 1 a 1 con las entidades del dominio y evitando redundancia de cadenas de texto). Adicionalmente, el módulo de importación admitirá un convertidor para archivos planos desnormalizados.

---

## 6. Autenticación y Cuentas de Acceso en Supabase

- **Contexto**: El sistema debe conectarse a Supabase con la clave pública (*publishable key*) y respetar políticas de Row Level Security (RLS).
- **Incertidumbre**: ¿Se espera que cada usuario (estudiante evaluador o docente) ingrese con un correo y contraseña propios en cada ejecución de la GUI, o se dispondrá de una cuenta técnica predeterminada de prueba en el archivo de configuración local para ingreso inmediato?
- **Supuesto de partida (`[SUPUESTO]`)**: La aplicación admitirá ambas modalidades: si existen credenciales válidas en las variables de entorno o archivo de configuración local, iniciará sesión automáticamente en segundo plano; en caso contrario, presentará un diálogo sencillo de inicio de sesión con opción de ingresar como "Usuario de Pruebas".
