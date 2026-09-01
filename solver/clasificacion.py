# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: solver/clasificacion.py
#  Clasificacion del sistema a partir de la matriz escalonada.
#
#  Criterio (teorema de Rouche-Frobenius):
#      rango(A) < rango([A|b])       -> INCONSISTENTE      (sin solucion)
#      rango(A) = rango([A|b]) = n   -> CONSISTENTE DETERMINADO   (unica)
#      rango(A) = rango([A|b]) < n   -> CONSISTENTE INDETERMINADO (infinitas)
# =============================================================================

from core.matriz import fila_de_coeficientes_nulos

INCONSISTENTE = "inconsistente"
DETERMINADO = "determinado"
INDETERMINADO = "indeterminado"


def buscar_contradiccion(M, n_vars):
    """
    Busca una fila [0 0 ... 0 | k] con k distinto de cero, que equivale a la
    igualdad imposible 0 = k.
    Devuelve el numero de fila (base 1) o None si no existe.
    """
    for i in range(len(M)):
        if fila_de_coeficientes_nulos(M, i, n_vars) and not M[i][n_vars].es_cero():
            return i + 1
    return None


def variables_libres(n_vars, columnas_pivote):
    """Indices de las columnas que no tienen pivote."""
    return [c for c in range(n_vars) if c not in columnas_pivote]


def es_homogeneo(M, n_vars):
    """Un sistema es homogeneo si todos los terminos independientes son cero."""
    for fila in M:
        if not fila[n_vars].es_cero():
            return False
    return True


def clasificar(M_escalonada, n_vars, columnas_pivote, M_original):
    """
    Analiza el sistema y devuelve un diccionario con todo lo necesario para
    explicar la clasificacion. No imprime nada.
    """
    fila_contradiccion = buscar_contradiccion(M_escalonada, n_vars)
    rango_A = len(columnas_pivote)
    rango_Ab = rango_A + (1 if fila_contradiccion is not None else 0)
    libres = variables_libres(n_vars, columnas_pivote)

    if fila_contradiccion is not None:
        tipo = INCONSISTENTE
        nombre = "SISTEMA INCONSISTENTE: SIN SOLUCIÓN"
    elif rango_A == n_vars:
        tipo = DETERMINADO
        nombre = "SISTEMA CONSISTENTE DETERMINADO: SOLUCIÓN ÚNICA"
    else:
        tipo = INDETERMINADO
        nombre = "SISTEMA CONSISTENTE INDETERMINADO: INFINITAS SOLUCIONES"

    return {
        "tipo": tipo,
        "nombre": nombre,
        "rango_A": rango_A,
        "rango_Ab": rango_Ab,
        "n_vars": n_vars,
        "libres": libres,
        "fila_contradiccion": fila_contradiccion,
        "valor_contradiccion": (M_escalonada[fila_contradiccion - 1][n_vars]
                                if fila_contradiccion is not None else None),
        "homogeneo": es_homogeneo(M_original, n_vars),
    }
