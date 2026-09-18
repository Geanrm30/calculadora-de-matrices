# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/algebra.py
#  Operaciones basicas del algebra de matrices.
#
#  Una matriz es una lista de listas de objetos Fraccion: cada sublista es una
#  fila. A[i][j] es la entrada de la fila i, columna j (contando desde 0).
#
#  Todas las operaciones se implementan con bucles y listas de Python
#  estandar, sin NumPy ni funciones de algebra lineal de otras bibliotecas.
#  Las que tienen restriccion de tamano la validan y lanzan ValueError con el
#  motivo, que la interfaz muestra al usuario.
#
#  El desarrollo paso a paso de cada una de estas operaciones esta en
#  core/procedimiento.py: aqui solo se calcula.
# =============================================================================

from core.fraccion import Fraccion


def sumar_matrices(A, B):
    """
    Suma de matrices:  (A + B)ᵢⱼ = aᵢⱼ + bᵢⱼ

    Procedimiento algebraico: la suma se hace ENTRADA A ENTRADA, sumando las
    que ocupan la misma posicion. Por eso solo esta definida cuando ambas
    matrices tienen el mismo tamano m x n; el resultado tambien es m x n.

    Los dos bucles (uno por filas, otro por columnas) visitan cada posicion
    exactamente una vez.
    """
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(
            "No se pueden sumar: A es {}x{} y B es {}x{}. "
            "La suma exige el mismo tamano.".format(
                len(A), len(A[0]), len(B), len(B[0])))

    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def restar_matrices(A, B):
    """
    Resta de matrices:  (A - B)ᵢⱼ = aᵢⱼ - bᵢⱼ

    Procedimiento algebraico: identico a la suma, entrada por entrada, y con
    la misma restriccion de tamano. Equivale a calcular A + (-1)·B.
    """
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError(
            "No se pueden restar: A es {}x{} y B es {}x{}. "
            "La resta exige el mismo tamano.".format(
                len(A), len(A[0]), len(B), len(B[0])))

    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def multiplicar_escalar(k, A):
    """
    Producto de un escalar por una matriz:  (k·A)ᵢⱼ = k · aᵢⱼ

    Procedimiento algebraico: el escalar multiplica a TODAS las entradas. No
    hay restriccion de tamano y el resultado conserva las dimensiones de A.
    """
    return [[A[i][j] * k for j in range(len(A[0]))] for i in range(len(A))]


def multiplicar_matrices(A, B):
    """
    Producto de matrices:  A(m x n) · B(n x p) = C(m x p)

    Procedimiento algebraico: cada entrada del resultado es el producto punto
    entre una FILA de A y una COLUMNA de B,

        cᵢⱼ = aᵢ₁·b₁ⱼ + aᵢ₂·b₂ⱼ + ... + aᵢₙ·bₙⱼ

    De esa formula salen los TRES BUCLES ANIDADOS:

        i (filas de A)     elige la fila del resultado
        j (columnas de B)  elige la columna del resultado
        k (1..n)           recorre y acumula los n productos de esa entrada

    El bucle interno k es el que obliga a que el numero de columnas de A sea
    igual al numero de filas de B: es el indice que ambas comparten. Si no
    coinciden, no hay con que emparejar los factores y el producto no existe.

    Caso particular: si B tiene una sola columna, el producto es A·x, que es
    la combinacion lineal de las columnas de A usando como pesos las entradas
    de x (ver core/procedimiento.py).
    """
    if len(A[0]) != len(B):
        raise ValueError(
            "No se pueden multiplicar: A es {}x{} y B es {}x{}. "
            "Las columnas de A ({}) deben ser iguales a las filas de B ({}).".format(
                len(A), len(A[0]), len(B), len(B[0]), len(A[0]), len(B)))

    # El resultado arranca en ceros: cada entrada se va acumulando en el
    # bucle interno, tal como se suman los n productos de la formula.
    C = [[Fraccion(0) for _ in range(len(B[0]))] for _ in range(len(A))]

    for i in range(len(A)):                 # fila del resultado
        for j in range(len(B[0])):          # columna del resultado
            for k in range(len(B)):         # acumulacion del producto punto
                C[i][j] = C[i][j] + (A[i][k] * B[k][j])

    return C


def transponer(A):
    """
    Transpuesta:  (Aᵀ)ⱼᵢ = aᵢⱼ

    Procedimiento algebraico: se intercambian filas por columnas, de modo que
    la fila i de A se convierte en la columna i de Aᵀ. Una matriz m x n
    produce una n x m.
    """
    filas = len(A)
    cols = len(A[0])
    return [[A[i][j] for i in range(filas)] for j in range(cols)]
