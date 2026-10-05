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

Se abre el menú principal con dos herramientas:

1. **Solucionador (Gauss / Gauss-Jordan)** — ecuación matricial `A·x = b`,
   combinación lineal e independencia lineal.
2. **Operaciones con matrices y vectores** — tres pestañas:
   - *Operaciones*: suma, resta, escalar, producto, transpuesta,
     determinante e inversa (dos métodos), con desarrollo paso a paso.
   - *Propiedades*: verifica las 29 propiedades algebraicas de las
     Sesiones 9–11 con aritmética exacta de fracciones.
   - *Solucionador*: envía el sistema al solucionador o resuelve
     `A·x = b` por la Regla de Cramer.

Lo que se escribe en una herramienta **no se pierde** al pasar a la otra:
`core/estado.py` conserva las cuadrículas mientras el programa esté abierto.

---

## Dependencias

No se utiliza **NumPy**, **SciPy** ni funciones de álgebra lineal de **math**.
El proyecto no declara ninguna dependencia externa: las únicas importaciones
corresponden a módulos propios y a `tkinter`, incluido en la biblioteca
estándar de Python.

La implementación se apoya en estructuras nativas del lenguaje: listas
anidadas, condicionales, bucles y funciones. El máximo común divisor se
implementa mediante el algoritmo de Euclides en lugar de `math.gcd`.

---

## Estructura

```
calculadora-de-matrices/
├── main.py               ← menú y navegación entre herramientas
│
├── core/                 ← estructuras de datos y álgebra básica
│   ├── fraccion.py       Aritmética exacta con números racionales.
│   ├── matriz.py         Matriz aumentada y operaciones elementales.
│   ├── algebra.py        Suma, resta, escalar, producto y transpuesta.
│   ├── vector.py         Operaciones en Rⁿ (un vector es una matriz n×1).
│   ├── procedimiento.py  Paso a paso escrito de cada operación.
│   ├── propiedades.py    Verificador de las 29 propiedades algebraicas.
│   ├── teoremas.py       Catálogo de teoremas del curso.
│   ├── estado.py         Memoria compartida entre las herramientas.
│   └── formato.py        Construcción de cadenas (matrices, ecuaciones).
│
├── modulos/              ← operaciones sobre matrices cuadradas
│   └── modulo_matrices.py  Determinante (3 métodos), inversa (2 métodos),
│                            cofactores, adjunta y Regla de Cramer.
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
└── ui/                   ← interfaz gráfica
    ├── app.py            Solucionador de sistemas.
    ├── app_matrices.py   Operaciones con matrices y vectores.
    └── app_teoremas.py   Visor de teoremas del curso.
```

Dependencias entre paquetes (sin ciclos):

```
ui/  →  output/  →  solver/   →  core/
ui/  →             modulos/   →  core/
ui/  →                           core/
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

Verifica las 29 propiedades algebraicas de las Sesiones 9–11 (producto
matriz-vector, vectores en Rⁿ, suma y escalar de matrices, transpuesta,
producto de matrices, inversa y determinante). Cada verificación calcula
los dos lados por caminos distintos y los compara con aritmética exacta.

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
| Resolver el sistema | Botón **RESOLVER** o `Ctrl+Enter` |
| Limpiar la cuadrícula | Botón **Limpiar** |
| Copiar el informe | Botón **Copiar informe** |
| Incluir forma reducida | Casilla **Gauss-Jordan** |
| Análisis en Rⁿ completo | Casilla **Incluir análisis en Rⁿ** |
| Mandar `[A \| b]` a operaciones | Botón **Enviar [A \| b] a Operaciones** |
| Mandar `A·x = b` al solucionador | Botón **Resolver la ecuación A·x = b** |
| Preguntar por combinación lineal | Botón **¿Es b combinación lineal…?** |
| Preguntar por independencia | Botón **¿Son las columnas… independientes?** |
| Resolver por Cramer | Botón **Resolver A·x = b (Regla de Cramer)** |
| Ver el desarrollo de una operación | Casilla **Mostrar el paso a paso** |
| Usar el resultado en otra operación | Botones **Resultado → A** / **→ B** / **→ C** |
| Intercambiar matrices | Botón **Intercambiar A ↔ B** |

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
- El programa admite sistemas de hasta **20×20** variables.
- La casilla **Incluir forma escalonada reducida** decide si el programa
  continúa hasta la matriz identidad y muestra esos pasos en el informe.
