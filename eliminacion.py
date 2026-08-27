# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: eliminacion.py
#  Reduccion de la matriz aumentada mediante operaciones elementales por filas.
#
#  Se ofrecen dos niveles:
#    1. escalonar()        -> forma escalonada (ceros DEBAJO de cada pivote,
#                             con pivotes normalizados a 1).
#    2. reducir_jordan()   -> forma escalonada reducida (ademas ceros ENCIMA
#                             de cada pivote).
#
#  Criterio de pivoteo: se intercambian filas unicamente cuando el pivote
#  candidato es CERO, tomando la primera fila inferior con valor no nulo en
#  esa columna. No se aplica pivoteo parcial por mayor magnitud: esa tecnica
#  controla la propagacion del error de redondeo en aritmetica de punto
#  flotante y carece de utilidad sobre aritmetica racional exacta, donde solo
#  incrementaria el tamano de numeradores y denominadores.
# =============================================================================

from fraccion import Fraccion
from matriz import copiar, intercambiar_filas, escalar_fila, sumar_multiplo


def registrar(pasos, operacion, M, comentario=""):
    """
    Registra el estado de la matriz despues de una operacion elemental.
    Cada paso es un diccionario con la descripcion de la operacion, una
    copia de la matriz resultante y un comentario opcional.
    """
    pasos.append({
        "operacion": operacion,
        "matriz": copiar(M),
        "comentario": comentario,
    })


# ---------------------------------------------------------------------------
# Forma escalonada
# ---------------------------------------------------------------------------

def escalonar(M, n_vars):
    """
    Lleva M a forma escalonada por filas modificandola en su lugar.
    Devuelve (pasos, columnas_pivote).
    """
    n_filas = len(M)
    pasos = []
    columnas_pivote = []
    fila_actual = 0  # fila donde se colocara el proximo pivote

    # Se recorre columna por columna de izquierda a derecha
    for col in range(n_vars):
        if fila_actual >= n_filas:
            break  # ya no quedan filas disponibles

        # --- Buscar un pivote distinto de cero en esta columna ---
        fila_pivote = -1
        for f in range(fila_actual, n_filas):
            if not M[f][col].es_cero():
                fila_pivote = f
                break

        # Columna completamente nula: no genera pivote, la variable es libre
        if fila_pivote == -1:
            continue

        # --- Operacion 1: intercambio, solo si hace falta ---
        if fila_pivote != fila_actual:
            operacion = intercambiar_filas(M, fila_actual, fila_pivote)
            registrar(pasos, operacion, M,
                      "El pivote de la columna x{} era cero.".format(col + 1))

        # --- Operacion 2: normalizar el pivote a 1 ---
        pivote = M[fila_actual][col]
        if not pivote.es_uno():
            operacion = escalar_fila(M, fila_actual, pivote.inverso())
            registrar(pasos, operacion, M,
                      "Se normaliza el pivote de la columna x{} a 1.".format(col + 1))

        # --- Operacion 3: generar ceros debajo del pivote ---
        for f in range(fila_actual + 1, n_filas):
            if not M[f][col].es_cero():
                factor = -M[f][col]  # el pivote ya vale 1
                operacion = sumar_multiplo(M, f, fila_actual, factor)
                registrar(pasos, operacion, M,
                          "Se anula el elemento debajo del pivote.")

        columnas_pivote.append(col)
        fila_actual += 1

    return pasos, columnas_pivote


# ---------------------------------------------------------------------------
# Forma escalonada reducida (Gauss-Jordan)
# ---------------------------------------------------------------------------

def reducir_jordan(M, n_vars, columnas_pivote):
    """
    Parte de una matriz YA escalonada y genera ceros encima de cada pivote.
    Modifica M en su lugar y devuelve la lista de pasos.
    """
    pasos = []

    # De derecha a izquierda: se limpia la columna de cada pivote
    for i in range(len(columnas_pivote) - 1, 0, -1):
        col = columnas_pivote[i]
        for f in range(i - 1, -1, -1):
            if not M[f][col].es_cero():
                factor = -M[f][col]
                operacion = sumar_multiplo(M, f, i, factor)
                registrar(pasos, operacion, M,
                          "Se anula el elemento encima del pivote.")

    return pasos


# ---------------------------------------------------------------------------
# Rango
# ---------------------------------------------------------------------------

def rango_desde_pivotes(columnas_pivote):
    """El rango es la cantidad de pivotes encontrados."""
    return len(columnas_pivote)
