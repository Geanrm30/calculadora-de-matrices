# -*- coding: utf-8 -*-
"""
Operaciones vectoriales en Rⁿ reutilizando core/algebra.py, ya que un vector
es algebraicamente una matriz n×1.
Unidad: Proyecto Integrador (Sesiones 1-11).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

import core.algebra as algebra


def como_columna(v):
    """Escribe el vector (v1, ..., vn) como matriz columna n × 1."""
    return [[componente] for componente in v]


def desde_columna(M):
    """Operacion inversa: convierte una matriz n x 1 en la lista (v1,...,vn)."""
    return [fila[0] for fila in M]


def sumar_vectores(u, v):
    """Suma componente a componente (u + v)_i = u_i + v_i.
    Exige que u y v tengan el mismo tamaño.
    """
    return desde_columna(algebra.sumar_matrices(como_columna(u), como_columna(v)))


def escalar_por_vector(r, v):
    """Producto por un escalar (r·v)_i = r·v_i, delegado en el producto escalar-matriz."""
    return desde_columna(algebra.multiplicar_escalar(r, como_columna(v)))


def matriz_de_vectores(vectores):
    """Arma la matriz A cuyas columnas son los vectores v1, ..., vk.
    Es el paso previo para estudiar si b es combinación lineal de ellos.
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


def combinacion_con_escalares(vectores, escalares):
    """Calcula c1·v1 + ... + ck·vk para comprobar una combinación ya encontrada."""
    if len(vectores) != len(escalares):
        raise ValueError("Debe haber un escalar por cada vector.")

    acumulado = escalar_por_vector(escalares[0], vectores[0])
    for k in range(1, len(vectores)):
        acumulado = sumar_vectores(acumulado, escalar_por_vector(escalares[k], vectores[k]))
    return acumulado
