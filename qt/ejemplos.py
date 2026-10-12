# -*- coding: utf-8 -*-
"""Ejemplos listos para cargar con un clic (los valores se escriben como texto)."""

# Sistemas [A | b] para el Solucionador: (nombre, qué muestra, m, n, celdas)
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

# Matrices para Operaciones: dict con A, B, C, escalar, s y una sugerencia
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
