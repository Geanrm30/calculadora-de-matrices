# -*- coding: utf-8 -*-
"""
Operaciones básicas del álgebra de matrices para el Proyecto Integrador.
Implementa suma, resta, producto escalar, producto matricial y transposición
usando listas anidadas y Fraccion para aritmética exacta. Sin NumPy ni SciPy.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

from core.fraccion import Fraccion


def sumar_matrices(A, B):
    """Devuelve A + B entrada por entrada: (A+B)_{ij} = a_{ij} + b_{ij}.
    Requiere A y B del mismo tamaño m×n; lanza ValueError si no coinciden."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(
            "No se pueden sumar: A es {}x{} y B es {}x{}. "
            "La suma exige el mismo tamano.".format(
                len(A), len(A[0]), len(B), len(B[0])))

    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def restar_matrices(A, B):
    """Devuelve A − B entrada por entrada: (A−B)_{ij} = a_{ij} − b_{ij}.
    Requiere A y B del mismo tamaño m×n; lanza ValueError si no coinciden."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(
            "No se pueden restar: A es {}x{} y B es {}x{}. "
            "La resta exige el mismo tamano.".format(
                len(A), len(A[0]), len(B), len(B[0])))

    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def multiplicar_escalar(k, A):
    """Devuelve k·A: el escalar multiplica a todas las entradas de A.
    Sin restricción de tamaño; el resultado conserva las dimensiones de A."""
    return [[A[i][j] * k for j in range(len(A[0]))] for i in range(len(A))]


def multiplicar_matrices(A, B):
    """Devuelve A(m×n)·B(n×p) = C(m×p) donde c_{ij} = fila_i(A) · col_j(B).
    Requiere columnas de A igual a filas de B; lanza ValueError si no coinciden."""
    if len(A[0]) != len(B):
        raise ValueError(
            "No se pueden multiplicar: A es {}x{} y B es {}x{}. "
            "Las columnas de A ({}) deben ser iguales a las filas de B ({}).".format(
                len(A), len(A[0]), len(B), len(B[0]), len(A[0]), len(B)))

    C = [[Fraccion(0) for _ in range(len(B[0]))] for _ in range(len(A))]

    for i in range(len(A)):
        for j in range(len(B[0])):
            for k in range(len(B)):
                # Elemento (i,j) = fila i de A · columna j de B (producto punto)
                C[i][j] = C[i][j] + (A[i][k] * B[k][j])

    return C


def transponer(A):
    """Devuelve Aᵀ: convierte la fila i de A en la columna i del resultado.
    Una matriz m×n produce una n×m."""
    filas = len(A)
    cols = len(A[0])
    return [[A[i][j] for i in range(filas)] for j in range(cols)]
