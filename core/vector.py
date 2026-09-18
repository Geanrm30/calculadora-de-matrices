# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/vector.py
#  Operaciones vectoriales en R^n.
#
#  Un vector de R^n es, algebraicamente, una matriz de una sola columna
#  (n x 1). Por eso este modulo NO reimplementa la aritmetica: reutiliza las
#  funciones de core/algebra.py cambiando el tamano de la matriz. Cada
#  funcion documenta la equivalencia:
#
#      u + v            <->   suma de dos matrices n x 1
#      u - v            <->   resta de dos matrices n x 1
#      r * v            <->   producto de un escalar por una matriz n x 1
#      c1.v1+...+ck.vk  <->   producto A.c, con los vk como columnas de A
# =============================================================================

import core.algebra as algebra


# ---------------------------------------------------------------------------
# Conversion entre lista plana y matriz columna
# ---------------------------------------------------------------------------

def como_columna(v):
    """
    Escribe el vector v = (v1, ..., vn) como matriz columna n x 1.

        v = [1, 2, 3]   ->   [[1],
                              [2],
                              [3]]
    """
    return [[componente] for componente in v]


def desde_columna(M):
    """Operacion inversa: convierte una matriz n x 1 en la lista (v1,...,vn)."""
    return [fila[0] for fila in M]


def es_vector(M):
    """Indica si la matriz M tiene una sola columna, es decir, si es un vector."""
    return len(M) > 0 and len(M[0]) == 1


# ---------------------------------------------------------------------------
# Operaciones basicas en R^n
# ---------------------------------------------------------------------------

def sumar_vectores(u, v):
    """
    Suma componente a componente: (u + v)_i = u_i + v_i.

    Procedimiento: se escriben ambos vectores como matrices n x 1 y se aplica
    la suma de matrices, que exige el mismo tamano; esa validacion es la que
    obliga a que u y v pertenezcan al mismo espacio R^n.
    """
    return desde_columna(algebra.sumar_matrices(como_columna(u), como_columna(v)))


def restar_vectores(u, v):
    """
    Resta componente a componente: (u - v)_i = u_i - v_i.

    Equivale a u + (-1)v; se resuelve como resta de matrices n x 1.
    """
    return desde_columna(algebra.restar_matrices(como_columna(u), como_columna(v)))


def escalar_por_vector(r, v):
    """
    Producto por un escalar: (r.v)_i = r * v_i.

    El escalar multiplica a cada componente, igual que multiplica a cada
    entrada de una matriz; se delega en el producto escalar-matriz.
    """
    return desde_columna(algebra.multiplicar_escalar(r, como_columna(v)))


# ---------------------------------------------------------------------------
# Combinacion lineal
# ---------------------------------------------------------------------------

def matriz_de_vectores(vectores):
    """
    Arma la matriz A cuyas COLUMNAS son los vectores v1, ..., vk recibidos.

    Es el paso previo para estudiar una combinacion lineal: la pregunta
    "?es b combinacion lineal de v1,...,vk?" equivale al sistema A.c = b,
    donde la incognita c reune los escalares c1,...,ck.

    Recibe una lista de vectores (cada uno como lista de componentes) y
    valida que todos tengan la misma cantidad de componentes.
    """
    if not vectores:
        raise ValueError("Se necesita al menos un vector.")

    n = len(vectores[0])
    for indice, v in enumerate(vectores):
        if len(v) != n:
            raise ValueError(
                "El vector v{} tiene {} componentes y se esperaban {}: "
                "todos deben pertenecer al mismo R^n.".format(indice + 1, len(v), n))

    # Fila i de A = i-esima componente de cada vector.
    return [[vectores[j][i] for j in range(len(vectores))] for i in range(n)]


def sistema_combinacion_lineal(vectores, b):
    """
    Devuelve la matriz aumentada [A | b] del sistema A.c = b asociado a la
    pregunta "?es b combinacion lineal de v1,...,vk?".

    Resolver ese sistema responde las tres cosas a la vez:
        sin solucion        -> b NO es combinacion lineal del conjunto
        solucion unica      -> lo es, y de una sola manera
        infinitas soluciones-> lo es, y de infinitas maneras
    Los valores de c1,...,ck son exactamente los escalares de la combinacion.
    """
    A = matriz_de_vectores(vectores)

    if len(b) != len(A):
        raise ValueError(
            "El vector b tiene {} componentes y los vectores del conjunto "
            "tienen {}.".format(len(b), len(A)))

    return [A[i] + [b[i]] for i in range(len(A))]


def combinacion_con_escalares(vectores, escalares):
    """
    Calcula c1.v1 + c2.v2 + ... + ck.vk.

    Sirve para comprobar una combinacion ya encontrada: se multiplica cada
    vector por su escalar y se acumulan las sumas componente a componente.
    Equivale al producto matricial A.c con los vk como columnas de A.
    """
    if len(vectores) != len(escalares):
        raise ValueError("Debe haber un escalar por cada vector.")

    acumulado = escalar_por_vector(escalares[0], vectores[0])
    for k in range(1, len(vectores)):
        acumulado = sumar_vectores(acumulado, escalar_por_vector(escalares[k], vectores[k]))
    return acumulado
