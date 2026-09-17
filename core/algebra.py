from core.fraccion import Fraccion

def sumar_matrices(A, B):
    """Suma dos matrices A y B del mismo tamaño."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError("Las matrices deben tener el mismo tamaño para sumarse.")
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def transponer(A):
    """Devuelve la matriz transpuesta A^T."""
    filas = len(A)
    cols = len(A[0])
    return [[A[i][j] for i in range(filas)] for j in range(cols)]

def multiplicar_matrices(A, B):
    """Multiplica A (m x n) por B (n x p)."""
    if len(A[0]) != len(B):
        raise ValueError("El número de columnas de A debe coincidir con las filas de B.")

    C = [[Fraccion(0) for _ in range(len(B[0]))] for _ in range(len(A))]
    for i in range(len(A)):
        for j in range(len(B[0])):
            for k in range(len(B)):
                C[i][j] = C[i][j] + (A[i][k] * B[k][j])
    return C

def restar_matrices(A, B):
    """Resta dos matrices A y B del mismo tamaño."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError("Las matrices deben tener el mismo tamaño para restarse.")
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def multiplicar_escalar(k, A):
    """Multiplica un escalar k (objeto Fraccion) por la matriz A."""
    return [[A[i][j] * k for j in range(len(A[0]))] for i in range(len(A))]