# Solucionador de sistemas de ecuaciones lineales

Resolución de sistemas por el método matricial, aplicando operaciones
elementales por filas hasta la forma escalonada, con clasificación del
sistema y verificación automática de la solución.

Álgebra Lineal — Unidad I: Ecuaciones lineales en álgebra lineal.

---

## Ejecución

Todos los archivos `.py` deben estar en la **misma carpeta**. Luego:

```
python gui.py
```

`gui.py` es el único archivo que se ejecuta; los demás son módulos que él
importa.

---

## Dependencias

No se utiliza **NumPy**, **SciPy** ni funciones de álgebra lineal de **math**.
El proyecto no declara ninguna dependencia externa: las únicas
importaciones corresponden a módulos propios y a `tkinter`, incluido en la
biblioteca estándar de Python y empleado exclusivamente para la interfaz.

La implementación se apoya en estructuras nativas del lenguaje: listas
anidadas, condicionales, bucles y funciones. El máximo común divisor se
implementa mediante el algoritmo de Euclides en lugar de recurrir a
`math.gcd`.

---

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `gui.py` | Interfaz gráfica (tkinter). |
| `fraccion.py` | Aritmética exacta con números racionales. |
| `matriz.py` | Matriz aumentada y las tres operaciones elementales por filas. |
| `eliminacion.py` | Reducción a forma escalonada y a forma escalonada reducida. |
| `clasificacion.py` | Determina el tipo de sistema (Rouché-Frobenius). |
| `solucion.py` | Sustitución regresiva numérica y simbólica. |
| `verificacion.py` | Sustituye la solución en el sistema original. |
| `resolutor.py` | Coordina el proceso y devuelve el resultado completo. |
| `reporte.py` | Arma el informe de texto. |
| `formato.py` | Construye las cadenas de matrices y ecuaciones. |

Dependencias entre módulos (sin ciclos):

```
gui.py
      |
      |--  resolutor.py  ->  eliminacion.py  ->  matriz.py  ->  fraccion.py
      |                      clasificacion.py
      |                      solucion.py
      |                      verificacion.py
      |--  reporte.py    ->  formato.py
```

`resolutor.py` no imprime ni pide datos: solo resuelve y devuelve un
diccionario. La interfaz y el informe leen ese mismo resultado, así que no
existe el riesgo de que muestren cosas distintas.

---

## Qué hace el programa

1. **Entrada de datos.** Número de ecuaciones y de variables, luego los
   coeficientes de A y los términos independientes de b. Se aceptan enteros
   (`-7`), fracciones (`3/4`) y decimales (`2.5`).
2. **Procesamiento.** Muestra la matriz aumentada inicial y aplica las
   operaciones elementales por filas, imprimiendo la matriz después de cada
   paso con la operación aplicada.
3. **Clasificación.** Compara rango(A), rango([A|b]) y el número de
   variables, e imprime una de las tres clasificaciones. En el caso
   indeterminado identifica las variables libres.
4. **Salida y verificación.** Muestra el valor de cada variable y sustituye
   la solución en el sistema original para comprobar la igualdad.

Opcionalmente continúa hasta la **forma escalonada reducida (Gauss-Jordan)**,
donde cada fila queda expresada directamente como `xi = valor`.

---

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
correctamente durante el despeje. Para el sistema `x1+2x2+3x3=6`,
`2x1+4x2+7x3=13` la solución general es `x1 = 3 - 2x2`, `x3 = 1`; omitir el
término correspondiente a `x3` produciría `x1 = 13/2 - 2x2`, resultado
incorrecto.

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

---

## Casos de prueba

Sistemas empleados para validar el programa y resultado esperado:

| Sistema | Resultado |
|---|---|
| `2x1+3x2+x3=1` ; `5x1+3x2+4x3=2` ; `x1+x2-x3=1` | Determinado: `x1=2/3`, `x2=0`, `x3=-1/3` |
| `2x1-3x2-4x3=3` ; `3x1+x2-x3=1` ; `x1+2x2-3x3=16` | Determinado: `x1=-2`, `x2=3`, `x3=-4` |
| `2x1+x2+x3=2` ; `x1-x2+2x3=3` ; `3x1+x2-x3=1` | Determinado: `x1=7/9`, `x2=-4/9`, `x3=8/9` |
| `x2-4x3=8` ; `2x1-3x2+2x3=1` ; `5x1-8x2+7x3=1` | Inconsistente: la eliminación conduce a `0 = 5/2` |
| `x1+2x2+3x3=6` ; `2x1+4x2+7x3=13` | Indeterminado: `x1 = 3 - 2x2`, `x3 = 1` |
| `x1+2x2+3x3=0` ; `2x1+4x2+6x3=0` ; `x1+x2+x3=0` | Homogéneo indeterminado |

Casos límite verificados: sistema 1x1, matriz nula, más variables que
ecuaciones, filas de ceros, coeficientes fraccionarios y sistemas de 8x8.

---

## Notas de uso

- Al ejecutar, Python genera una carpeta `__pycache__` con los módulos
  compilados. Es normal y no forma parte de la entrega.
- El programa admite sistemas de hasta 8 x 8.
- La casilla **Incluir forma escalonada reducida** decide si el programa
  continúa hasta la matriz identidad y muestra esos pasos en el informe.
- El botón **Guardar informe** exporta todo el desarrollo a un archivo
  `.txt`, útil para adjuntarlo al reporte de la actividad.
