# Calculadora de Álgebra Lineal

Proyecto integrador de MTM0120 Álgebra Lineal — Universidad Americana.
Implementa las Unidades I–III del curso: sistemas de ecuaciones, operaciones
con matrices y vectores, propiedades algebraicas, determinantes e inversas.

**Elaborado por:** Anthony Sying González Chow, Jose Maria Moncada Maya,
Geanfranco Alexander Rodriguez Mendieta

---

## Ejecución

```
python main.py
```

La **primera vez** el programa descarga e instala solo el componente gráfico
(PySide6-Essentials, unos 80 MB) y muestra una ventana de espera con una barra
de progreso; hace falta conexión a internet y después ya no. Si la instalación
fallara, la propia ventana lo explica y se puede hacer a mano con
`pip install -r requirements.txt`.

Se abre una única ventana (PySide6) con menú lateral —atajos `Ctrl+1` a
`Ctrl+4`— que da acceso a:

1. **Solucionador (Gauss / Gauss-Jordan)** — ecuación matricial `A·x = b`,
   combinación lineal e independencia lineal.
2. **Operaciones con matrices y vectores** — tres pestañas:
   - *Operaciones*: suma, resta, escalar, producto, transpuesta,
     determinante e inversa (dos métodos), factorización LU y Regla de
     Cramer, con desarrollo paso a paso.
   - *Propiedades*: verifica las 31 propiedades algebraicas de las
     Sesiones 9–11 con aritmética exacta de fracciones.
   - *Solucionador*: envía el sistema al solucionador o resuelve
     `A·x = b` por la Regla de Cramer.
3. **Teoremas clave** — catálogo de los teoremas del curso con buscador.

La primera vez que se abre aparece un **recorrido guiado** que explica las
partes principales; se puede repetir desde **Ayuda** (`F1`). Los errores de
datos no abren ventanas: la celda inválida se pone en **rojo** mientras
escribes (con el motivo al pasar el cursor) y una franja bajo el título explica
el problema. La letra de cuadrículas e informes se ajusta con **A− / A+**.

Lo que se escribe **no se pierde**: al pasar de una herramienta a otra cada
página se conserva, y al cerrar el programa se guardan las cuadrículas, las
opciones, el último resultado, el tamaño de la ventana y el tema, que se
recuperan al volver a abrirlo.

---

---

## Dependencias

No se utiliza **NumPy**, **SciPy** ni funciones de álgebra lineal de **math**.
La única dependencia externa es **PySide6** (en su versión ligera
`PySide6-Essentials`: interfaz gráfica y exportación a PDF); toda la parte
matemática usa solo módulos propios.

La implementación se apoya en estructuras nativas del lenguaje: listas
anidadas, condicionales, bucles y funciones. El máximo común divisor se
implementa mediante el algoritmo de Euclides en lugar de `math.gcd`.

---

## Estructura

```
calculadora-de-matrices/
├── main.py               ← punto de entrada: crea la ventana PySide6
├── instalador.py         ← instala PySide6 la primera vez (con ventana de espera)
│
├── core/                 ← estructuras de datos y álgebra básica
│   ├── fraccion.py       Aritmética exacta con números racionales.
│   ├── matriz.py         Matriz aumentada y operaciones elementales.
│   ├── algebra.py        Suma, resta, escalar, producto y transpuesta.
│   ├── vector.py         Operaciones en Rⁿ (un vector es una matriz n×1).
│   ├── procedimiento.py  Paso a paso escrito de cada operación.
│   ├── propiedades.py    Verificador de las 31 propiedades algebraicas.
│   ├── teoremas.py       Catálogo de teoremas del curso.
│   └── formato.py        Construcción de cadenas (matrices, ecuaciones).
│
├── modulos/              ← operaciones sobre matrices
│   ├── modulo_matrices.py  Determinante (3 métodos), inversa (2 métodos),
│   │                        cofactores, adjunta y Regla de Cramer.
│   └── modulo_lu.py        Factorización LU (m×n) y solución de A·x = b
│                            con L·y = b y U·x = y.
│
├── solver/               ← lógica de resolución de sistemas
│   ├── clasificacion.py  Clasifica el sistema (Rouché-Frobenius).
│   ├── eliminacion.py    Reducción a forma escalonada y reducida.
│   ├── solucion.py       Sustitución regresiva numérica y simbólica.
│   ├── independencia.py  Dependencia lineal y relación de dependencia.
│   ├── verificacion.py   Sustituye la solución en el sistema original.
│   └── resolutor.py      Coordina el proceso y devuelve el resultado.
│
├── output/               ← presentación
│   └── reporte.py        Arma el informe de texto completo.
│
└── qt/                   ← interfaz gráfica (PySide6)
    ├── ventana_principal.py   Ventana, menú lateral, tema y sesión.
    ├── pagina_inicio.py       Pantalla de bienvenida.
    ├── pagina_solucionador.py Solucionador de sistemas.
    ├── pagina_matrices.py     Operaciones con matrices y vectores.
    ├── pagina_teoremas.py     Catálogo de teoremas con buscador.
    ├── componentes.py         Botones, interruptores, tarjetas y cuadrícula
    │                          de matriz (deshacer, copiar y pegar).
    ├── render.py              HTML de matrices, vectores e informe.
    ├── visor.py               Ventana aparte para leer un resultado (índice, búsqueda, zoom).
    ├── exportar.py            Exportación a PDF.
    ├── ayuda.py               Ayuda: atajos de teclado y «Acerca de».
    ├── tour.py                Recorrido guiado de la primera vez.
    ├── icono.py               Icono de la aplicación (dibujado por código).
    ├── ejemplos.py            Ejemplos precargados.
    ├── persistencia.py        Guardado de la sesión y el tema.
    └── tema.py                Paletas (oscuro, claro, impreso) y estilos.
```

Dependencias entre paquetes (sin ciclos):

```
qt/  →  output/  →  solver/   →  core/
qt/  →             modulos/   →  core/
qt/  →                           core/
```

`solver/resolutor.py` y `modulos/modulo_matrices.py` no imprimen ni piden
datos: solo calculan y devuelven resultados. La interfaz lee esos resultados,
así que no existe el riesgo de que muestren cosas distintas.

---

## Qué hace el programa

### Solucionador (Gauss / Gauss-Jordan)

1. **Entrada.** Número de ecuaciones y variables (hasta 20×20), coeficientes
   de A y términos independientes de b. Se aceptan enteros (`-7`), fracciones
   (`3/4`), decimales (`2.5`) y raíces (`√4`, `sqrt(2)`).
2. **Procesamiento.** Aplica operaciones elementales por filas mostrando la
   matriz después de cada paso con la operación aplicada.
3. **Clasificación.** Compara rango(A), rango([A|b]) y el número de variables
   e imprime el resultado. En el caso indeterminado identifica las variables
   libres.
4. **Verificación.** Muestra el valor de cada variable (x₁, x₂…) y sustituye
   la solución en el sistema original para comprobar la igualdad de forma exacta.

Opcionalmente continúa hasta la **forma escalonada reducida (Gauss-Jordan)**,
donde cada fila queda como `xᵢ = valor`.

### Operaciones con matrices y vectores

**Pestaña Operaciones**

- Suma, resta, producto, transpuesta y multiplicación por escalar `r`.
- `det(A)` — determinante por expansión de cofactores; para matrices 3×3
  muestra también el resultado por la Regla de Sarrus.
- `A⁻¹ G-J` — inversa por Gauss-Jordan con verificación `A·A⁻¹ = I`.
- `A⁻¹ Adj` — inversa por la fórmula `A⁻¹ = (1/det A) · adj(A)`.
- Casilla **Mostrar el paso a paso**: despliega el desarrollo completo para
  todas las operaciones, incluyendo los tres métodos del determinante, los dos
  de la inversa y la Regla de Cramer.

**Pestaña Propiedades**

Verifica las 31 propiedades algebraicas de las Sesiones 9–11 (producto
matriz-vector, vectores en Rⁿ, suma y escalar de matrices, transpuesta,
producto de matrices, inversa y determinante). Cada verificación calcula
los dos lados por caminos distintos y los compara con aritmética exacta.

El diagnóstico de cada propiedad es **[Se cumple]** o **[No se cumple]**.

**Factorización LU** (pestaña Operaciones)

- Factoriza cualquier `A` de m×n como `A = L·U` usando solo reemplazos de
  fila: `L` (m×m) guarda los multiplicadores y `U` es la forma escalonada.
  Si hiciera falta intercambiar filas, se detiene y avisa que la matriz no
  admite LU sin permutación (`PA = LU`).
- Si `A` es cuadrada y `B` es el vector `b`, resuelve `A·x = b` en dos
  etapas, reduciendo `[L | b]` a `[I | y]` y `[U | y]` a `[I | x]`, y
  comprueba `L·U == A` y `A·x == b` con fracciones exactas.

**Pestaña Solucionador**

- Envía `[A|b]` al solucionador para resolver `A·x = b`, preguntar si `b`
  es combinación lineal de las columnas de A, o analizar independencia lineal.
- **Regla de Cramer**: resuelve `A·x = b` mostrando `det(A)`, cada `Aᵢ` con
  su determinante y la fórmula `xᵢ = det(Aᵢ) / det(A)`.

---

## Las tres lecturas del mismo sistema

`A·x = b`, la combinación lineal y la independencia lineal son el mismo
cálculo leído con distinto enunciado, y el programa lo resuelve una sola vez
explicándolo de las tres maneras:

| Enunciado | Sistema que se resuelve | Respuesta |
|---|---|---|
| Ecuación matricial `A·x = b` | `[A \| b]` | valor de cada `xᵢ` |
| ¿Es `b` combinación lineal de las columnas de `A`? | `[A \| b]` | los escalares de la combinación, o que no existe |
| ¿Son las columnas de `A` linealmente independientes? | `[A \| 0]` | solución trivial única = independientes; si no, una relación de dependencia explícita |

Hay dos maneras de pedir estos análisis, y dan exactamente lo mismo:

- **Desde el solucionador**, marcando *Incluir análisis en Rⁿ*: se añaden
  las secciones de combinación lineal e independencia al sistema escrito.
- **Desde Operaciones con matrices**, con los botones de envío: el sistema
  viaja armado y se resuelve automáticamente.

La sección de combinación lineal se omite en un sistema homogéneo, porque
`b = 0` siempre es combinación de cualquier conjunto.

El producto `A·x` se muestra de las dos formas vistas en clase: como
**combinación lineal de las columnas** de `A` (`x₁·a₁ + … + xₙ·aₙ`) y con
la **regla fila-vector**.

---

## Atajos y funciones de la interfaz

| Acción | Cómo |
|--------|------|
| Ver todos los atajos y repetir el recorrido | `F1` o botón **Ayuda** |
| Rendimiento | Las páginas (Solucionador, Operaciones, Teoremas) se construyen cuando se usan y el resto se prepara en segundo plano solo cuando no estás usando el programa: la ventana abre en menos de un segundo y el cambio de tema es rápido. El tamaño de letra se cambia al instante. En Teoremas, «Expandir todo» anima solo lo que se ve y, si el equipo va justo, el despliegue termina de golpe en vez de arrastrarse |
| Recorrido guiado | 26 pasos que recorren el Solucionador, Operaciones (matrices, operaciones, Cramer, LU, propiedades, historial), Teoremas y los controles del menú. Se repite desde **Ayuda**; no pisa lo que tengas escrito |
| Volver a los valores por defecto | **Ayuda → Acerca de → Borrar todos los datos** (pide confirmación; borra matrices, resultados, historial, sesión, tema y tamaño de letra) |
| Cambiar de herramienta | Menú lateral o `Ctrl+1` … `Ctrl+4` |
| Animaciones | Inicio con fondo de color en movimiento y tarjetas con foco de luz; transición vertical entre secciones y horizontal entre pestañas; al quitar o agregar una matriz la tarjeta se encoge o crece; al limpiar, un barrido azul recorre las celdas; ola de luz solo en la cuadrícula que cambia; anillo de luz al enfocar una celda; onda al pulsar un botón y destello en RESOLVER; pulso en el borde del resultado; avisos con barra; el icono del menú salta al elegirse; la ventana abre y el cambio de tema se hacen con fundido, y las ventanas de Ayuda y «Acerca de» entran y salen con animación |
| Consultar teoremas | Pestaña **Teoremas**: tarjetas plegables con vista previa, filtros por categoría, búsqueda con `Ctrl+F` que resalta lo encontrado, «Expandir todo» y **Copiar**. **Abrir en…** te lleva a la herramienta y marca el botón exacto con anillos y una burbuja que dice qué hacer |
| Tema claro / oscuro | `Ctrl+Shift+T` o botón al pie del menú (se recuerda) |
| Tamaño de letra de cuadrículas e informes | `Ctrl++` / `Ctrl+−` / `Ctrl+0` o botones **A− A+** |
| Salir guardando la sesión | `Ctrl+Q` |
| Resolver el sistema | Botón **RESOLVER** o `Ctrl+Enter` |
| Limpiar | `Ctrl+L` o botón **Limpiar** |
| Reproducir / pausar los pasos | `Ctrl+R` o botón **Reproducir** |
| Guardar el informe (.txt) / exportar a PDF | `Ctrl+S` / `Ctrl+P` |
| Operaciones rápidas (A = cuadrada) | `Ctrl+D` det(A) · `Ctrl+I` A⁻¹ · `Ctrl+M` A × B |
| Cargar un ejemplo | Botón **Probar un ejemplo** (Solucionador y Operaciones) |
| Moverse por la cuadrícula | `Enter` / `↓` / `↑` o `Tab` |
| Deshacer / rehacer en una matriz | `Ctrl+Z` / `Ctrl+Y`, o los botones ↶ ↷ de la tarjeta |
| Copiar una matriz | Menú **Tabla → Copiar como tabla** (se pega en Excel) o **Copiar como imagen** (se pega en Word o PowerPoint) |
| Pegar una matriz | `Ctrl+V` sobre una celda, o **Tabla → Pegar tabla**; sirve lo copiado de Excel, de una tabla de PowerPoint o Word, o de texto |
| Reproducir los pasos solos | Botón **Reproducir** (velocidad lenta, normal o rápida) |
| Recorrer los pasos a mano | **Inicio / Anterior / Siguiente / Final** o `←` `→` |
| Copiar el informe o resultado | Botón **Copiar informe** / **Copiar**: como texto, como imagen o, en Operaciones, solo la matriz resultado como imagen |
| Guardar el informe | **Guardar informe → Texto (.txt)** o **PDF (.pdf)** |
| Leer el resultado en grande | Botón **Abrir en ventana**: ventana propia (botón en la barra de tareas) con el informe a color y las matrices dibujadas; en el Solucionador, una tarjeta arriba con el tipo de sistema, la solución y si quedó verificada. Índice lateral para saltar a cada sección (también en operaciones, propiedades, Cramer y LU), búsqueda con `Ctrl+F` (`F3` / `Mayús+F3` para moverse entre coincidencias), zoom con A− / A+ o `Ctrl`+rueda, **Líneas** (parte las líneas largas) y **Ancho** (elige la letra para que todo quepa), barras de desplazamiento horizontal y vertical, y guardado en .txt o PDF. Los resultados de Operaciones también salen a color: títulos en azul, pasos en naranja, lo que se cumple en verde, lo que falla en rojo y las matrices dibujadas con corchetes. Se cierra al cerrar la calculadora |
| Volver a un resultado anterior | Botón **Historial** (Operaciones) |
| Incluir forma reducida | Interruptor **Gauss-Jordan** |
| Análisis en Rⁿ completo | Interruptor **Incluir análisis en Rⁿ** |
| Mandar `[A \| b]` a operaciones | Botón **Enviar [A \| b] a Operaciones** |
| Mandar `A·x = b` al solucionador | Botón **Resolver la ecuación A·x = b** |
| Preguntar por combinación lineal | Botón **¿Es b combinación lineal…?** |
| Preguntar por independencia | Botón **¿Son las columnas… independientes?** |
| Resolver por Cramer | Botón **Resolver A·x = b (Regla de Cramer)** |
| Ver el desarrollo de una operación | Interruptor **Mostrar el paso a paso** |
| Usar el resultado en otra operación | **Usar como → A / B / C** |
| Intercambiar matrices | Botón **Intercambiar A ↔ B** |
| Quitar o volver a poner B o C | Botones **Quitar / Agregar matriz B** y **C** |

En el paso a paso del Solucionador, las filas que cambian en cada operación
se resaltan para seguir el procedimiento con la vista.

Al pegar una tabla se aceptan:

- las celdas de **Excel** (columnas separadas por tabulador);
- una **tabla de PowerPoint o Word**: en PowerPoint se selecciona la tabla y se copia
  con `Ctrl+C` (PowerPoint la deja como tabla, no como texto, y la calculadora
  la lee igual);
- una matriz de **ecuación de Office** copiada como texto, como `■(3&−7@−3&5)`;
- `1 2; 3 4`, `[[1,2],[3,4]]` y filas separadas por saltos de línea.

La cuadrícula crece sola hasta su tamaño máximo. Los símbolos de Excel, Word y
PDF (el menos largo «−», las rayas, la barra «∕», los dígitos matemáticos 𝟑 y
las fracciones ½ ¼ ¾) se aceptan como los del teclado, y una celda vacía se
toma como 0. Una **imagen** (captura de pantalla, foto de una matriz) no se puede
leer: el programa lo avisa y pide copiar la tabla en sí.

Las imágenes que se copian (matriz o informe) siguen el tema de la calculadora:
fondo oscuro con letra clara en el tema oscuro, y fondo blanco con letra oscura
en el claro. Los PDF salen siempre en blanco, porque están pensados para imprimir.

---

## Notación de las operaciones elementales

| Operación | Notación |
|---|---|
| Intercambio de filas | `f1 <-> f2` |
| Multiplicar una fila por un escalar | `f1 -> (1/2) * f1` |
| Sumar a una fila un múltiplo de otra | `f3 -> f3 + (-5) * f1` |

Se emplean `<->` y `->` en lugar de flechas tipográficas para garantizar
una representación uniforme en cualquier codificación de salida.

---

## Decisiones técnicas

**Aritmética racional en lugar de punto flotante.** El algoritmo necesita
determinar si un elemento es exactamente cero para seleccionar pivotes y
detectar inconsistencias. En punto flotante, un valor teóricamente nulo
puede quedar en el orden de `1e-17`, lo que obliga a comparar contra una
tolerancia arbitraria y puede producir clasificaciones erróneas. La clase
`Fraccion` elimina el problema: la comparación con cero es exacta, los
resultados se expresan como fracciones irreducibles y la verificación final
es una igualdad estricta.

**Tres métodos para el determinante.** `modulo_matrices.py` implementa la
expansión de cofactores (válida para cualquier n≥1), la regla de Sarrus
(solo 3×3) y la reducción a forma triangular superior. Los tres producen el
mismo resultado; mostrarlos juntos permite comparar los procedimientos vistos
en clase.

**Dos métodos para la inversa.** Gauss-Jordan construye `[A|I]` y reduce
hasta `[I|A⁻¹]`. La fórmula adjunta calcula primero cada cofactor `Cᵢⱼ`,
forma la matriz de cofactores, la transpone para obtener `adj(A)` y divide
entre `det(A)`. Ambos métodos incluyen la verificación `A·A⁻¹ = I`.

**Intercambio de filas condicionado.** Las filas se permutan únicamente
cuando el pivote candidato es cero, tomando la primera fila inferior con
valor no nulo en esa columna. El pivoteo parcial por mayor magnitud controla
la propagación del error de redondeo en aritmética de punto flotante y
carece de utilidad sobre aritmética racional exacta.

**Normalización del pivote.** Una vez seleccionado el pivote, la fila se
divide entre él. La matriz escalonada resultante presenta unos en las
posiciones pivote y la sustitución regresiva se simplifica.

**Sustitución regresiva simbólica.** En forma escalonada no reducida, cada
variable se representa como el vector `[constante, coef_libre_1, …]` para
propagar correctamente los coeficientes de las variables libres durante el
despeje.

**Verificación simbólica en el caso indeterminado.** Además de comprobar una
solución particular, el programa sustituye la solución general y verifica que
los coeficientes de los parámetros se anulen, estableciendo que la igualdad
se satisface para cualquier valor de las variables libres.

**Verificación contra el sistema original.** Se conserva una copia intacta
previa al escalonamiento. La sustitución en la matriz reducida carecería de
valor probatorio.

**Notación con subíndices Unicode.** Las variables se muestran como x₁, x₂…
usando dígitos subíndice Unicode (₀–₉), lo que permite representar
correctamente sistemas con 10 o más variables (x₁₀, x₁₁…).

---

## Casos de prueba

| Sistema | Resultado |
|---|---|
| `2x₁+3x₂+x₃=1` ; `5x₁+3x₂+4x₃=2` ; `x₁+x₂-x₃=1` | Determinado: `x₁=2/3`, `x₂=0`, `x₃=-1/3` |
| `2x₁-3x₂-4x₃=3` ; `3x₁+x₂-x₃=1` ; `x₁+2x₂-3x₃=16` | Determinado: `x₁=-2`, `x₂=3`, `x₃=-4` |
| `2x₁+x₂+x₃=2` ; `x₁-x₂+2x₃=3` ; `3x₁+x₂-x₃=1` | Determinado: `x₁=7/9`, `x₂=-4/9`, `x₃=8/9` |
| `x₂-4x₃=8` ; `2x₁-3x₂+2x₃=1` ; `5x₁-8x₂+7x₃=1` | Inconsistente: `0 = 5/2` |
| `x₁+2x₂+3x₃=6` ; `2x₁+4x₂+7x₃=13` | Indeterminado: `x₁ = 3 - 2x₂`, `x₃ = 1` |
| `x₁+2x₂+3x₃=0` ; `2x₁+4x₂+6x₃=0` ; `x₁+x₂+x₃=0` | Homogéneo indeterminado |

Casos límite verificados: sistema 1×1, matriz nula, más variables que
ecuaciones, filas de ceros, coeficientes fraccionarios y sistemas hasta 20×20.

---

## Notas de uso

- Al ejecutar, Python genera una carpeta `__pycache__` en cada paquete con
  los módulos compilados. Es normal y no forma parte de la entrega.
- El programa admite sistemas de hasta **20×20** variables y matrices de hasta
  **10×10** en Operaciones.
- Si una celda se ve en rojo, el valor no es válido: pasa el cursor para ver
  el motivo. Se corrige al escribir un valor válido.
- Las preferencias y la última sesión se guardan en la configuración del
  usuario del sistema (en Windows, el registro, bajo `UAM`).
- La casilla **Incluir forma escalonada reducida** decide si el programa
  continúa hasta la matriz identidad y muestra esos pasos en el informe.
