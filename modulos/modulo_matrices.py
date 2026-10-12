# -*- coding: utf-8 -*-
"""
Módulo de matrices para el Proyecto Integrador: Calculadora de Álgebra Lineal.
Implementa el Módulo III (Sesiones 10-11): determinante por expansión de cofactores,
regla de Sarrus (3×3) y reducción triangular; inversa por Gauss-Jordan y por la
fórmula A⁻¹ = (1/det(A))·adj(A). MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

from core.fraccion import Fraccion
import core.algebra as alg


def submatriz(A, fila_excluida, col_excluida):
    """Devuelve la submatriz de A eliminando la fila y columna indicadas.
    Es el menor que se usa para calcular cofactores."""
    return [
        [A[i][j] for j in range(len(A[0])) if j != col_excluida]
        for i in range(len(A)) if i != fila_excluida
    ]


def determinante(A):
    """Determinante por expansión de cofactores a lo largo de la primera fila.
    Válido para cualquier n≥1. Lanza ValueError si A no es cuadrada."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError(
            "El determinante solo está definido para matrices cuadradas "
            "(A es {}×{}).".format(n, len(A[0])))
    if n == 1:
        return A[0][0]
    if n == 2:
        return A[0][0] * A[1][1] - A[0][1] * A[1][0]

    resultado = Fraccion(0)
    for j in range(n):
        # El signo (-1)^(0+j) sigue el patrón de cofactores: alterna por posición de columna
        signo = Fraccion(1) if j % 2 == 0 else Fraccion(-1)
        resultado = resultado + signo * A[0][j] * determinante(submatriz(A, 0, j))
    return resultado


def determinante_sarrus(A):
    """Determinante de una matriz 3×3 por la regla de Sarrus.
    Suma 3 diagonales principales y resta 3 secundarias. Solo válido para n=3."""
    if len(A) != 3 or len(A[0]) != 3:
        raise ValueError("La regla de Sarrus solo aplica a matrices 3×3.")

    pos = (A[0][0] * A[1][1] * A[2][2]
           + A[0][1] * A[1][2] * A[2][0]
           + A[0][2] * A[1][0] * A[2][1])
    neg = (A[2][0] * A[1][1] * A[0][2]
           + A[2][1] * A[1][2] * A[0][0]
           + A[2][2] * A[1][0] * A[0][1])
    return pos - neg


def determinante_triangular(A):
    """Determinante por reducción a forma triangular superior (método eficiente).
    Rastrea cada intercambio de fila para corregir el signo. Lanza ValueError si A no es cuadrada."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError(
            "El determinante solo está definido para matrices cuadradas "
            "(A es {}×{}).".format(n, len(A[0])))

    M = [[A[i][j] for j in range(n)] for i in range(n)]
    signo = Fraccion(1)

    for col in range(n):
        pivote_fila = next(
            (f for f in range(col, n) if not M[f][col].es_cero()), None)

        if pivote_fila is None:
            return Fraccion(0)  # columna de ceros → det = 0

        if pivote_fila != col:
            M[col], M[pivote_fila] = M[pivote_fila], M[col]
            signo = signo * Fraccion(-1)  # cada intercambio invierte el signo del resultado

        for fila in range(col + 1, n):
            if not M[fila][col].es_cero():
                factor = M[fila][col] / M[col][col]
                for k in range(col, n):
                    M[fila][k] = M[fila][k] - factor * M[col][k]

    producto = signo
    for i in range(n):
        producto = producto * M[i][i]
    return producto


def cofactor_elemento(A, i, j):
    """Cofactor C_{ij} = (-1)^(i+j) · det(submatriz sin fila i y columna j)."""
    signo = Fraccion(1) if (i + j) % 2 == 0 else Fraccion(-1)
    return signo * determinante(submatriz(A, i, j))


def matriz_cofactores(A):
    """Devuelve la matriz n×n donde la entrada (i,j) es el cofactor C_{ij} de A."""
    n = len(A)
    return [[cofactor_elemento(A, i, j) for j in range(n)] for i in range(n)]


def adjunta(A):
    """Devuelve la adjunta de A (transpuesta de la matriz de cofactores)."""
    return alg.transponer(matriz_cofactores(A))


def inversa_gauss_jordan(A):
    """Devuelve A⁻¹ construyendo [A|I] y reduciéndola a [I|A⁻¹] por Gauss-Jordan.
    Usa pivoteo parcial. Lanza ValueError si A no es cuadrada o es singular."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError(
            "La inversa solo está definida para matrices cuadradas "
            "(A es {}×{}).".format(n, len(A[0])))

    cer = Fraccion(0)
    uno = Fraccion(1)
    M = [
        [A[i][j] for j in range(n)] + [uno if i == k else cer for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Sin pivote no nulo en esta columna la matriz es singular: no existe A⁻¹
        pivote = next(
            (f for f in range(col, n) if not M[f][col].es_cero()), None)
        if pivote is None:
            raise ValueError(
                "La matriz A es singular (det = 0): no tiene inversa.")

        if pivote != col:
            M[col], M[pivote] = M[pivote], M[col]

        p = M[col][col]
        M[col] = [v / p for v in M[col]]

        for fila in range(n):
            if fila != col and not M[fila][col].es_cero():
                factor = M[fila][col]
                M[fila] = [M[fila][k] - factor * M[col][k]
                           for k in range(2 * n)]

    return [[M[i][n + j] for j in range(n)] for i in range(n)]


def inversa_adjunta(A):
    """Devuelve A⁻¹ usando la fórmula A⁻¹ = (1/det(A)) · adj(A).
    Lanza ValueError si det(A) = 0 o si A no es cuadrada."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError(
            "La inversa solo está definida para matrices cuadradas "
            "(A es {}×{}).".format(n, len(A[0])))

    det = determinante(A)
    if det.es_cero():
        raise ValueError(
            "La matriz A es singular: det(A) = 0 y no existe la inversa.")

    return alg.multiplicar_escalar(Fraccion(1) / det, adjunta(A))


def cramer(A, b):
    """Resuelve A·x = b por la Regla de Cramer: xᵢ = det(Aᵢ) / det(A).
    Aᵢ es A con la columna i reemplazada por b. Devuelve la lista de Fracciones [x₁,...,xₙ].
    Lanza ValueError si A no es cuadrada n×n, b no tiene n entradas, o det(A) = 0."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError(
            "Cramer solo aplica a sistemas cuadrados (A es {}×{}).".format(n, len(A[0])))
    if len(b) != n:
        raise ValueError(
            "b debe tener {} componentes (una por fila de A), tiene {}.".format(n, len(b)))

    det_A = determinante(A)
    if det_A.es_cero():
        raise ValueError(
            "Cramer no aplica: det(A) = 0. "
            "El sistema puede ser inconsistente o tener infinitas soluciones.")

    solucion = []
    for i in range(n):
        # Construir Aᵢ: copia de A con la columna i reemplazada por el vector b
        Ai = [[A[fila][col] if col != i else b[fila]
               for col in range(n)]
              for fila in range(n)]
        solucion.append(determinante(Ai) / det_A)

    return solucion


def es_identidad(M):
    """Devuelve True si M es la matriz identidad n×n (comparación exacta de fracciones)."""
    n = len(M)
    return (n == len(M[0]) and
            all(M[i][j] == (Fraccion(1) if i == j else Fraccion(0))
                for i in range(n) for j in range(n)))


def rango(A):
    """Número de pivotes de A (rango de la matriz) calculado por escalonamiento."""
    n = len(A)
    m = len(A[0])
    M = [[A[i][j] for j in range(m)] for i in range(n)]
    fila_actual = 0
    for col in range(m):
        pivote = next(
            (f for f in range(fila_actual, n) if not M[f][col].es_cero()), None)
        if pivote is None:
            continue
        M[fila_actual], M[pivote] = M[pivote], M[fila_actual]
        p = M[fila_actual][col]
        M[fila_actual] = [v / p for v in M[fila_actual]]
        for fila in range(n):
            if fila != fila_actual and not M[fila][col].es_cero():
                factor = M[fila][col]
                M[fila] = [M[fila][k] - factor * M[fila_actual][k]
                           for k in range(m)]
        fila_actual += 1
    return fila_actual
