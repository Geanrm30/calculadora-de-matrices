# Solucionador de sistemas de ecuaciones lineales

Resolución de sistemas por el método matricial, aplicando operaciones
elementales por filas hasta la forma escalonada, con clasificación del
sistema y verificación automática de la solución.

Álgebra Lineal — Unidad I: Ecuaciones lineales en álgebra lineal.

---

## Ejecución

```
python main.py
```

También funciona el acceso directo anterior:

```
python gui.py
```

---

## Dependencias

No se utiliza **NumPy**, **SciPy** ni funciones de álgebra lineal de **math**.
El proyecto no declara ninguna dependencia externa: las únicas
importaciones corresponden a módulos propios y a `tkinter`, incluido en la
biblioteca estándar de Python.

La implementación se apoya en estructuras nativas del lenguaje: listas
anidadas, condicionales, bucles y funciones. El máximo común divisor se
implementa mediante el algoritmo de Euclides en lugar de recurrir a
`math.gcd`.

---

## Estructura

El código está organizado en cuatro paquetes más un punto de entrada:

```
calculadora-de-matrices/
├── main.py              ← punto de entrada
├── gui.py               ← acceso alternativo (compatibilidad)
│
├── core/                ← estructuras de datos fundamentales
│   ├── fraccion.py      Aritmética exacta con números racionales.
│   ├── matriz.py        Matriz aumentada y operaciones elementales.
│   └── formato.py       Construcción de cadenas (matrices, ecuaciones).
│
├── solver/              ← lógica de resolución
│   ├── clasificacion.py Clasifica el sistema (Rouché-Frobenius).
│   ├── eliminacion.py   Reducción a forma escalonada y escalonada reducida.
│   ├── solucion.py      Sustitución regresiva numérica y simbólica.
│   ├── verificacion.py  Sustituye la solución en el sistema original.
│   └── resolutor.py     Coordina el proceso y devuelve el resultado.
│
├── output/              ← presentación
│   └── reporte.py       Arma el informe de texto completo.
│
└── ui/                  ← interfaz gráfica
    └── app.py           Ventana tkinter: entrada, validación, visualización.
```

Dependencias entre paquetes (sin ciclos):

```
ui/  →  output/  →  solver/  →  core/
ui/  →            →  solver/  →  core/
ui/  →                          core/
```

`solver/resolutor.py` no imprime ni pide datos: solo resuelve y devuelve un
diccionario. La interfaz y el informe leen ese mismo resultado, así que no
existe el riesgo de que muestren cosas distintas.

---

## Qué hace el programa

1. **Entrada de datos.** Número de ecuaciones y de variables (hasta 20×20),
   luego los coeficientes de A y los términos independientes de b.
   Se aceptan enteros (`-7`), fracciones (`3/4`), decimales (`2.5`)
   y raíces (`√4`, `sqrt(2)`).
2. **Procesamiento.** Muestra la matriz aumentada inicial y aplica las
   operaciones elementales por filas, mostrando la matriz después de cada
   paso con la operación aplicada.
3. **Clasificación.** Compara rango(A), rango([A|b]) y el número de
   variables, e imprime una de las tres clasificaciones. En el caso
   indeterminado identifica las variables libres.
4. **Salida y verificación.** Muestra el valor de cada variable con notación
   de subíndice (x₁, x₂…) y sustituye la solución en el sistema original
   para comprobar la igualdad de forma exacta.

Opcionalmente continúa hasta la **forma escalonada reducida (Gauss-Jordan)**,
donde cada fila queda expresada directamente como `xᵢ = valor`.

---

## Atajos y funciones de la interfaz

| Acción | Cómo |
|--------|------|
| Resolver el sistema | Botón **RESOLVER** o `Ctrl+Enter` |
| Limpiar la cuadrícula | Botón **Limpiar** |
| Copiar el informe | Botón **Copiar informe** |
| Incluir forma reducida | Casilla **Gauss-Jordan** |

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

**Intercambio de filas condicionado.** Las filas se permutan únicamente
cuando el pivote candidato es cero, tomando la primera fila inferior con
valor no nulo en esa columna. El pivoteo parcial por mayor magnitud controla
la propagación del error de redondeo en aritmética de punto flotante y
carece de utilidad sobre aritmética racional exacta, donde solo incrementa
el tamaño de numeradores y denominadores.

**Normalización del pivote.** Una vez seleccionado el pivote, la fila se
divide entre él. La matriz escalonada resultante presenta unos en las
posiciones pivote y la sustitución regresiva se simplifica al evitar la
división final.

**Sustitución regresiva simbólica.** En forma escalonada, no reducida, una
fila puede contener a la derecha del pivote otras variables pivote además de
las libres. Cada variable se representa por ello como el vector
`[constante, coef_libre_1, ...]`, de modo que esos coeficientes se propagan
correctamente durante el despeje. Para el sistema `x₁+2x₂+3x₃=6`,
`2x₁+4x₂+7x₃=13` la solución general es `x₁ = 3 - 2x₂`, `x₃ = 1`; omitir
el término correspondiente a `x₃` produciría `x₁ = 13/2 - 2x₂`, incorrecto.

**Verificación simbólica en el caso indeterminado.** Además de comprobar una
solución particular, el programa sustituye la solución general en el sistema
original y verifica que los coeficientes de los parámetros se anulen. Esto
establece que la igualdad se satisface para cualquier valor de las variables
libres, condición que la comprobación de un único punto no permite
establecer.

**Verificación contra el sistema original.** Se conserva una copia intacta
previa al escalonamiento. La sustitución en la matriz reducida carecería de
valor probatorio, al ser el resultado del mismo procedimiento que se desea
comprobar.

**Notación con subíndices Unicode.** Las variables se muestran como x₁, x₂,
x₃… en la interfaz y en el informe, usando dígitos subíndice del estándar
Unicode (₀–₉). Esto permite representar correctamente sistemas con 10 o más
variables (x₁₀, x₁₁…) sin ambigüedad.

---

## Casos de prueba

Sistemas empleados para validar el programa y resultado esperado:

| Sistema | Resultado |
|---|---|
| `2x₁+3x₂+x₃=1` ; `5x₁+3x₂+4x₃=2` ; `x₁+x₂-x₃=1` | Determinado: `x₁=2/3`, `x₂=0`, `x₃=-1/3` |
| `2x₁-3x₂-4x₃=3` ; `3x₁+x₂-x₃=1` ; `x₁+2x₂-3x₃=16` | Determinado: `x₁=-2`, `x₂=3`, `x₃=-4` |
| `2x₁+x₂+x₃=2` ; `x₁-x₂+2x₃=3` ; `3x₁+x₂-x₃=1` | Determinado: `x₁=7/9`, `x₂=-4/9`, `x₃=8/9` |
| `x₂-4x₃=8` ; `2x₁-3x₂+2x₃=1` ; `5x₁-8x₂+7x₃=1` | Inconsistente: la eliminación conduce a `0 = 5/2` |
| `x₁+2x₂+3x₃=6` ; `2x₁+4x₂+7x₃=13` | Indeterminado: `x₁ = 3 - 2x₂`, `x₃ = 1` |
| `x₁+2x₂+3x₃=0` ; `2x₁+4x₂+6x₃=0` ; `x₁+x₂+x₃=0` | Homogéneo indeterminado |

Casos límite verificados: sistema 1×1, matriz nula, más variables que
ecuaciones, filas de ceros, coeficientes fraccionarios y sistemas hasta 20×20.

---

## Notas de uso

- Al ejecutar, Python genera una carpeta `__pycache__` con los módulos
  compilados en cada paquete. Es normal y no forma parte de la entrega.
- El programa admite sistemas de hasta **20×20** variables.
- La casilla **Incluir forma escalonada reducida** decide si el programa
  continúa hasta la matriz identidad y muestra esos pasos en el informe.
