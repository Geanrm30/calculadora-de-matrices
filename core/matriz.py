# -*- coding: utf-8 -*-
"""
Estructura de la matriz aumentada [A|b] y las tres operaciones elementales
por filas: intercambio, escalado y suma de múltiplo de fila.
Unidad: Proyecto Integrador (Sesiones 1-11).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

def copiar(M):
    """Copia profunda de la matriz.
    La eliminación modifica la matriz en sitio y cada paso guardado necesita su copia.
    """
    return [[valor for valor in fila] for fila in M]


def intercambiar_filas(M, i, j):
    """f_i <-> f_j"""
    M[i], M[j] = M[j], M[i]
    return "f{} <-> f{}".format(i + 1, j + 1)


def escalar_fila(M, i, k):
    """f_i -> k * f_i"""
    if k.es_cero():
        raise ValueError("No se puede multiplicar una fila por cero.")

    for c in range(len(M[i])):
        M[i][c] = M[i][c] * k

    return "f{} -> ({}) * f{}".format(i + 1, k, i + 1)


def sumar_multiplo(M, i, j, k):
    """f_i -> f_i + k * f_j"""
    for c in range(len(M[i])):
        M[i][c] = M[i][c] + k * M[j][c]

    return "f{} -> f{} + ({}) * f{}".format(i + 1, i + 1, k, j + 1)


def fila_de_coeficientes_nulos(M, i, n_vars):
    """
    Indica si la fila i tiene todos los coeficientes de A iguales a cero,
    sin importar el termino independiente.
    """
    for c in range(n_vars):
        if not M[i][c].es_cero():
            return False
    return True
