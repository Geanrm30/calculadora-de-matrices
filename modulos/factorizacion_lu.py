"""
Módulo de Factorización LU (A = LU) y resolución de sistemas Ax = b
mediante sustitución hacia adelante (Ly = b) y hacia atrás (Ux = y).
MTM0120 Álgebra Lineal — Universidad Americana.
"""

from core.fraccion import Fraccion
import core.algebra as alg
from core.matriz import copiar

def factorizacion_lu(A):
    """
    Obtiene la Factorización LU de una matriz cuadrada A (A = L * U)
    mediante operaciones elementales de reemplazo de filas (sin intercambios).
    Retorna (L, U).
    """
    m = len(A)
    n = len(A[0])
    if m != n:
        raise ValueError("La matriz A debe ser cuadrada para la factorización LU.")

    U = copiar(A)
    # L es una matriz m x m triangular inferior unitaria (unos en la diagonal)
    L = [[Fraccion(1) if i == j else Fraccion(0) for j in range(m)] for i in range(m)]

    for col in range(n):
        if U[col][col].es_cero():
            raise ValueError(
                f"El pivote en la posición ({col+1}, {col+1}) es cero. "
                "La factorización LU estándar requiere pivotes no nulos sin intercambios de filas."
            )
        
        for fila in range(col + 1, m):
            if not U[fila][col].es_cero():
                factor = U[fila][col] / U[col][col]
                L[fila][col] = factor
                # F_fila <- F_fila - factor * F_col
                for k in range(col, n):
                    U[fila][k] = U[fila][k] - factor * U[col][k]

    return L, U

def verificar_lu(A, L, U):
    """Verifica si L * U == A de forma exacta con aritmética racional."""
    producto = alg.multiplicar_matrices(L, U)
    if len(producto) != len(A) or len(producto[0]) != len(A[0]):
        return False
    for i in range(len(A)):
        for j in range(len(A[0])):
            if producto[i][j] != A[i][j]:
                return False
    return True

def sustitucion_hacia_adelante(L, b):
    """
    Etapa 1: Sustitución hacia adelante
    Resuelve el sistema triangular inferior L y = b para hallar el vector intermedio y.
    """
    m = len(L)
    y = [Fraccion(0) for _ in range(m)]
    for i in range(m):
        suma = Fraccion(0)
        for j in range(i):
            suma = suma + L[i][j] * y[j]
        y[i] = b[i] - suma
    return y
def sustitucion_hacia_atras(U, y):
    """
    Etapa 2: Sustitución hacia atrás
    Resuelve el sistema triangular superior U x = y para determinar la solución final x.
    """
    m = len(U)
    n = len(U[0])
    x = [Fraccion(0) for _ in range(n)]
    
    for i in range(m - 1, -1, -1):
        col_pivote = -1
        for j in range(n):
            if not U[i][j].es_cero():
                col_pivote = j
                break
        if col_pivote == -1:
            continue
        
        suma = Fraccion(0)
        for j in range(col_pivote + 1, n):
            suma = suma + U[i][j] * x[j]
            
        x[col_pivote] = (y[i] - suma) / U[i][col_pivote]
    return x

def resolver_sistema_lu(A, b_vec):
    """
    Coordina la descomposición LU y la resolución de Ax = b en dos etapas:
    1. Ly = b (sustitución hacia adelante).
    2. Ux = y (sustitución hacia atrás)
    Retorna (y, x, L, U, verificado).
    """
    L, U = factorizacion_lu(A)
    verificado = verificar_lu(A, L, U)
    y = sustitucion_hacia_adelante(L, b_vec)
    x = sustitucion_hacia_atras(U, y)
    return y, x, L, U, verificado