# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: solver/eliminacion.py
#  Reduccion de la matriz aumentada mediante operaciones elementales por filas.
#
#  Dos niveles:
#    1. escalonar()       -> forma escalonada (ceros DEBAJO de cada pivote).
#    2. reducir_jordan()  -> forma escalonada reducida (ceros ENCIMA tambien).
# =============================================================================

from core.fraccion import Fraccion
from core.matriz import copiar, intercambiar_filas, escalar_fila, sumar_multiplo
from core.formato import subindice


def registrar(pasos, operacion, M, comentario=""):
    """Registra el estado de la matriz despues de una operacion elemental."""
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
    fila_actual = 0

    for col in range(n_vars):
        if fila_actual >= n_filas:
            break

        fila_pivote = -1
        for f in range(fila_actual, n_filas):
            if not M[f][col].es_cero():
                fila_pivote = f
                break

        if fila_pivote == -1:
            continue

        if fila_pivote != fila_actual:
            operacion = intercambiar_filas(M, fila_actual, fila_pivote)
            registrar(pasos, operacion, M,
                      "El pivote de la columna x{} era cero.".format(subindice(col + 1)))

        pivote = M[fila_actual][col]
        if not pivote.es_uno():
            operacion = escalar_fila(M, fila_actual, pivote.inverso())
            registrar(pasos, operacion, M,
                      "Se normaliza el pivote de la columna x{} a 1.".format(subindice(col + 1)))

        for f in range(fila_actual + 1, n_filas):
            if not M[f][col].es_cero():
                factor = -M[f][col]
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
