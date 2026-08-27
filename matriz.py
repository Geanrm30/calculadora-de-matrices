# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: matriz.py
#  Estructura de la matriz aumentada y las tres operaciones elementales
#  por filas.
#
#  Notacion empleada para describir cada operacion:
#      f_i <-> f_j          intercambio de dos filas
#      f_i -> k * f_i       multiplicar una fila por un escalar
#      f_i -> f_i + k * f_j sumar a una fila otra fila multiplicada por k
#
#  La matriz aumentada [A | b] se representa como una lista de listas de
#  objetos Fraccion. Cada sublista es una ecuacion y su ultimo elemento es
#  el termino independiente.
# =============================================================================

from fraccion import Fraccion


# ---------------------------------------------------------------------------
# Construccion y copia
# ---------------------------------------------------------------------------

def matriz_cero(n_filas, n_columnas):
    """Crea una matriz de ceros exactos del tamano indicado."""
    return [[Fraccion(0) for _ in range(n_columnas)] for _ in range(n_filas)]


def copiar(M):
    """
    Copia profunda de la matriz.

    Requerida porque la eliminacion modifica la matriz in situ: el sistema
    original debe conservarse intacto para la verificacion final, y cada
    paso registrado necesita su propia copia independiente.
    """
    return [[valor for valor in fila] for fila in M]


def dimensiones(M, n_vars):
    """Devuelve (numero de filas, numero de variables)."""
    return len(M), n_vars


# ---------------------------------------------------------------------------
# Operacion elemental 1: intercambio de filas
# ---------------------------------------------------------------------------

def intercambiar_filas(M, i, j):
    """
    f_i <-> f_j

    Devuelve la descripcion textual de la operacion aplicada.
    """
    M[i], M[j] = M[j], M[i]
    return "f{} <-> f{}".format(i + 1, j + 1)


# ---------------------------------------------------------------------------
# Operacion elemental 2: multiplicar una fila por un escalar
# ---------------------------------------------------------------------------

def escalar_fila(M, i, k):
    """
    f_i -> k * f_i
    El escalar k debe ser distinto de cero para que la operacion sea
    reversible y el sistema resultante sea equivalente.
    """
    if k.es_cero():
        raise ValueError("No se puede multiplicar una fila por cero.")

    for c in range(len(M[i])):
        M[i][c] = M[i][c] * k

    return "f{} -> ({}) * f{}".format(i + 1, k, i + 1)


# ---------------------------------------------------------------------------
# Operacion elemental 3: sumar a una fila un multiplo de otra
# ---------------------------------------------------------------------------

def sumar_multiplo(M, i, j, k):
    """
    f_i -> f_i + k * f_j
    Esta es la operacion que genera los ceros debajo (y encima) del pivote.
    """
    for c in range(len(M[i])):
        M[i][c] = M[i][c] + k * M[j][c]

    return "f{} -> f{} + ({}) * f{}".format(i + 1, i + 1, k, j + 1)


# ---------------------------------------------------------------------------
# Consultas sobre filas
# ---------------------------------------------------------------------------

def fila_de_coeficientes_nulos(M, i, n_vars):
    """
    Indica si la fila i tiene todos los coeficientes de A iguales a cero,
    sin importar el termino independiente.
    """
    for c in range(n_vars):
        if not M[i][c].es_cero():
            return False
    return True
