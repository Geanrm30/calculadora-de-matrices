# -*- coding: utf-8 -*-
"""
Ejemplos listos para cargar con un clic (los valores se escriben como texto).
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

SISTEMAS = [
    ("Solución única (3×3)",
     "Sistema consistente determinado: x = 5, y = 3, z = −2.",
     3, 3, [["1", "1", "1", "6"],
            ["0", "2", "5", "-4"],
            ["2", "5", "-1", "27"]]),
    ("Infinitas soluciones (3×4)",
     "Consistente indeterminado: hay variables libres y forma vectorial.",
     3, 4, [["1", "2", "-1", "1", "3"],
            ["2", "4", "-1", "3", "8"],
            ["1", "2", "0", "2", "5"]]),
    ("Sin solución (3×2)",
     "Sistema inconsistente: la última fila queda 0 = c.",
     3, 2, [["1", "1", "2"],
            ["1", "-1", "0"],
            ["2", "0", "3"]]),
    ("Homogéneo con solución no trivial",
     "A·x = 0 con columnas linealmente dependientes.",
     3, 3, [["1", "2", "3", "0"],
            ["2", "4", "6", "0"],
            ["1", "1", "1", "0"]]),
    ("Con fracciones (2×2)",
     "Aritmética exacta: coeficientes racionales.",
     2, 2, [["1/2", "1/3", "1"],
            ["3/4", "-1", "2"]]),
]

MATRICES = [
    {
        "nombre": "Invertible 3×3 con vector b",
        "sugerencia": "Prueba det(A), A⁻¹ (ambos métodos) o la Regla de Cramer.",
        "A": [["2", "1", "0"], ["1", "3", "1"], ["0", "1", "4"]],
        "B": [["1"], ["2"], ["3"]],
        "C": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "escalar": "2", "s": "3",
    },
    {
        "nombre": "Matriz singular 3×3 (det = 0)",
        "sugerencia": "Prueba det(A) y A⁻¹: no tiene inversa.",
        "A": [["1", "2", "3"], ["2", "4", "6"], ["1", "0", "1"]],
        "B": [["1"], ["2"], ["3"]],
        "C": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "escalar": "2", "s": "3",
    },
    {
        "nombre": "Producto A × B (2×3 por 3×2)",
        "sugerencia": "Prueba A × B y mira el producto como combinación de columnas.",
        "A": [["1", "2", "3"], ["4", "5", "6"]],
        "B": [["7", "8"], ["9", "10"], ["11", "12"]],
        "C": [["1", "0"], ["0", "1"]],
        "escalar": "2", "s": "3",
    },
    {
        "nombre": "Propiedades con matrices 2×2",
        "sugerencia": "Ve a la pestaña Propiedades y pulsa «Verificar todas».",
        "A": [["1", "2"], ["3", "4"]],
        "B": [["0", "1"], ["1", "0"]],
        "C": [["2", "-1"], ["0", "3"]],
        "escalar": "2", "s": "3",
    },
    {
        "nombre": "Con fracciones",
        "sugerencia": "Todo se calcula con fracciones exactas.",
        "A": [["1/2", "1/3"], ["1/4", "2/3"]],
        "B": [["3/2", "0"], ["1", "1/5"]],
        "C": [["1", "1/2"], ["0", "1"]],
        "escalar": "1/2", "s": "3",
    },
]

EJEMPLOS_LU = [
    {"nombre": "Sistema 3×3 con vector b",
     "sugerencia": "Pulsa «Factorizar»: obtiene L, U, y y x.",
     "A": [["2", "1", "1"], ["4", "3", "3"], ["8", "7", "9"]],
     "b": [["4"], ["10"], ["24"]]},
    {"nombre": "Sistema 2×2 con fracciones",
     "sugerencia": "Todo se calcula con fracciones exactas.",
     "A": [["1/2", "1/3"], ["1/4", "2/3"]],
     "b": [["1"], ["2"]]},
    {"nombre": "Requiere permutación (PA = LU)",
     "sugerencia": "Hay un cero en el primer pivote: LU sin permutación no existe.",
     "A": [["0", "1"], ["1", "0"]],
     "b": [["1"], ["2"]]},
    {"nombre": "Matriz no cuadrada 2×3",
     "sugerencia": "Solo se factoriza A = L·U; no se resuelve el sistema.",
     "A": [["1", "2", "3"], ["4", "5", "6"]],
     "b": [["1"], ["2"]]},
]


EJEMPLOS_BISECCION = [
    {"nombre": "x⁴ − 5x³ + 0.5x² − 11x + 10 en [0.55, 1.1]",
     "sugerencia": "13 iteraciones y xᵣ ≈ 0.763971; la tabla se va armando paso a paso.",
     "f": "x**4 - 5*x**3 + 0.5*x**2 - 11*x + 10",
     "a": "0.55", "b": "1.1", "E": "0.0001", "nmax": "100"},
    {"nombre": "x³ − 2x − 5 en [2, 3]",
     "sugerencia": "Raíz de referencia 2.09455148; n teórico = 14.",
     "f": "x**3 - 2*x - 5", "a": "2", "b": "3", "E": "0.0001", "nmax": "100"},
    {"nombre": "cos(x) − x en [0, 1]",
     "sugerencia": "Raíz de referencia 0.73908513; n teórico = 14.",
     "f": "cos(x) - x", "a": "0", "b": "1", "E": "0.0001", "nmax": "100"},
    {"nombre": "x² − 2 en [1, 2]",
     "sugerencia": "Aproxima √2 ≈ 1.41421356; n teórico = 14.",
     "f": "x**2 - 2", "a": "1", "b": "2", "E": "0.0001", "nmax": "100"},
    {"nombre": "x³ + x − 1 en [0, 1]",
     "sugerencia": "Raíz de referencia 0.68232780; n teórico = 14.",
     "f": "x**3 + x - 1", "a": "0", "b": "1", "E": "0.0001", "nmax": "100"},
    {"nombre": "x³ − 4x − 1 en [2, 3]",
     "sugerencia": "Mira cómo se reduce el intervalo en las primeras iteraciones.",
     "f": "x**3 - 4*x - 1", "a": "2", "b": "3", "E": "0.0001", "nmax": "100"},
    {"nombre": "Sin cambio de signo: x² + 1 en [−1, 1]",
     "sugerencia": "El intervalo se rechaza: f(a)·f(b) > 0.",
     "f": "x**2 + 1", "a": "-1", "b": "1", "E": "0.0001", "nmax": "100"},
    {"nombre": "Raíz en un extremo: x² − 1 en [1, 2]",
     "sugerencia": "Reconoce x = 1 como raíz exacta y termina.",
     "f": "x**2 - 1", "a": "1", "b": "2", "E": "0.0001", "nmax": "100"},
    {"nombre": "Discontinuidad: 1/x en [−1, 1]",
     "sugerencia": "Hay cambio de signo, pero por una asíntota: no hay raíz.",
     "f": "1/x", "a": "-1", "b": "1", "E": "0.0001", "nmax": "100"},
    {"nombre": "Máximo de iteraciones insuficiente",
     "sugerencia": "Con máximo 5 no se alcanza la tolerancia y el programa lo avisa.",
     "f": "x**3 - 2*x - 5", "a": "2", "b": "3", "E": "0.0001", "nmax": "5"},
]

EJEMPLOS_GRAFICA = [
    {"nombre": "Racional: 1/x", "sugerencia": "La asíntota en x = 0 no se une.",
     "f": "1/x", "xmin": "-5", "xmax": "5"},
    {"nombre": "Racional: (x² − 1)/(x − 1)", "sugerencia": "Hueco en x = 1.",
     "f": "(x**2 - 1)/(x - 1)", "xmin": "-3", "xmax": "4"},
    {"nombre": "Radical: sqrt(x)", "sugerencia": "Solo se grafica donde x ≥ 0.",
     "f": "sqrt(x)", "xmin": "-4", "xmax": "9"},
    {"nombre": "Logarítmica: log(x)", "sugerencia": "Solo se grafica donde x > 0.",
     "f": "log(x)", "xmin": "-2", "xmax": "10"},
    {"nombre": "Trigonométrica: tan(x)", "sugerencia": "Asíntotas en π/2 + kπ.",
     "f": "tan(x)", "xmin": "-6", "xmax": "6"},
    {"nombre": "Valor absoluto: abs(x − 2)", "sugerencia": "Vértice en x = 2.",
     "f": "abs(x - 2)", "xmin": "-3", "xmax": "7"},
    {"nombre": "Exponencial: exp(x)", "sugerencia": "Crecimiento exponencial.",
     "f": "exp(x)", "xmin": "-3", "xmax": "3"},
    {"nombre": "Polinomial y lineal juntas", "sugerencia": "Varias funciones con «;».",
     "f": "x**3 - 2*x - 5; x - 3", "xmin": "-3", "xmax": "4"},
]

EJEMPLOS_POSICIONAL = [
    {"nombre": "(84506)₁₀ en base 10", "numero": "84506", "base": 10},
    {"nombre": "(11110011)₂ en base 2", "numero": "11110011", "base": 2},
    {"nombre": "Número negativo: −13 (base 10)", "numero": "-13", "base": 10},
    {"nombre": "(101101)₂ en base 2", "numero": "101101", "base": 2},
]
