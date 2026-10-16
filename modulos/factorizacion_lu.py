# -*- coding: utf-8 -*-
"""
Módulo de Factorización LU y resolución de sistemas Ax = b en dos etapas,
siguiendo el formato visto en clase:

  DATOS      A = L·U y el vector b (L y U se calculan automáticamente, sin
             mostrar su procedimiento).
  PASO 1     Ly = b por Gauss-Jordan:  [L | b] ~ [I | y]
  PASO 2     Ux = y por Gauss-Jordan:  [U | y] ~ [I | x]
  RESULTADO  y, x y la comprobación (L·U = A y A·x = b).

Implementado con aritmética exacta de Fraccion.
MTM0120 Álgebra Lineal — UAM. Proyecto Integrador de Álgebra Lineal.
"""

from core.fraccion import Fraccion
import core.algebra as alg
from core.formato import texto_matriz, ancho_columna, subindice


# ---------------------------------------------------------------------------
# Utilidades de escritura
# ---------------------------------------------------------------------------

def _sub(n):
    """Subíndice Unicode de un número ya en base 1: 2 -> ₂."""
    return subindice(n)


def _fila(i):
    """Nombre de la fila i (base 0) en base 1 con subíndice: 0 -> F₁."""
    return "F" + _sub(i + 1)


def _mult(coef, nombre):
    """
    Escribe 'coef·nombre' como en clase: F₁, −F₁, 2F₁ y (3/2)·F₁
    (las fracciones van entre paréntesis).
    """
    if coef.es_uno():
        return nombre
    if (-coef).es_uno():
        return "−" + nombre
    if coef.den == 1:
        return str(coef) + nombre
    return "(" + str(coef) + ")·" + nombre


def _op_reemplazo(i, j, k):
    """
    Operación de reemplazo  F_i → F_i + k·F_j  (flecha de izquierda a derecha:
    la fila de la izquierda se cambia por la expresión de la derecha).
    Si k es negativo se escribe como resta: F₃ → F₃ − 2F₁.
    """
    if k.es_negativo():
        signo = " − "
        magnitud = -k
    else:
        signo = " + "
        magnitud = k
    return "{} → {}{}{}".format(_fila(i), _fila(i), signo, _mult(magnitud, _fila(j)))


def _op_escala(i, factor):
    """Operación de escalamiento  F_i → factor·F_i."""
    return "{} → {}".format(_fila(i), _mult(factor, _fila(i)))


def _vector(v):
    """Vector en una línea como en clase: (3, 4, -6)."""
    return "(" + ", ".join(str(c) for c in v) + ")"


def _texto_matriz(M, sangria="  "):
    """
    Escribe una matriz NORMAL (sin columna de términos independientes) con las
    columnas alineadas. Se usa para A, L, U y L·U.

    OJO: core.formato.texto_matriz sirve solo para matrices AUMENTADAS [A | b]
    (lee la columna extra fila[n_vars]), por eso no se puede usar aquí.
    """
    ancho = ancho_columna(M) + 2
    lineas = []
    for fila in M:
        valores = "".join("{:>{a}}".format(str(v), a=ancho) for v in fila)
        lineas.append(sangria + "[" + valores + " ]")
    return "\n".join(lineas)


def _lado_a_lado(bloques, sangria="  "):
    """
    Dibuja varias matrices en la misma fila, cada una con su rótulo arriba:

            A            L
      [ 2  1 ]  =  [ 1  0 ]

    bloques: lista de (rótulo, matriz, separador que va a la derecha).
    """
    columnas = []
    for rotulo, M, sep in bloques:
        lineas = _texto_matriz(M, sangria="").split("\n")
        ancho = max(max(len(l) for l in lineas), len(rotulo))
        lineas = [l.ljust(ancho) for l in lineas]
        columnas.append((rotulo, lineas, ancho, sep))

    n_filas = max(len(c[1]) for c in columnas)
    fila_sep = n_filas // 2

    encabezado = ""
    cuerpo = ["" for _ in range(n_filas)]
    for rotulo, lineas, ancho, sep in columnas:
        encabezado += rotulo.center(ancho) + " " * len(sep)
        for r in range(n_filas):
            texto = lineas[r] if r < len(lineas) else " " * ancho
            cuerpo[r] += texto + (sep if r == fila_sep else " " * len(sep))

    return "\n".join([sangria + encabezado.rstrip()] +
                     [sangria + c.rstrip() for c in cuerpo])


# ---------------------------------------------------------------------------
# Cálculo (silencioso): A = L·U
# ---------------------------------------------------------------------------

def factorizar_lu(A):
    """
    Obtiene A = L·U para una matriz de tamaño m×n (cuadrada o no) usando solo
    operaciones de reemplazo de filas, como en clase:
      - U (m×n) es una forma escalonada de A.
      - L (m×m) es triangular inferior con unos en la diagonal. La columna k de
        L son las entradas de la k-ésima columna pivote (de arriba hacia abajo)
        divididas entre el pivote.
    Si una columna no tiene pivote (todo lo que queda de ella es cero) se pasa a
    la siguiente columna; las columnas de L que no se usan quedan como las de la
    identidad. No escribe ningún procedimiento.
    """
    m = len(A)
    n = len(A[0])

    U = [[A[i][j] for j in range(n)] for i in range(m)]
    L = [[Fraccion(1) if i == j else Fraccion(0) for j in range(m)] for i in range(m)]

    fila = 0   # fila donde debería ir el siguiente pivote (= columna de L que se llena)
    for col in range(n):
        if fila >= m:
            break

        pivote = U[fila][col]
        if pivote.es_cero():
            # Sin pivote en esta columna si todo lo de abajo también es cero;
            # si no, haría falta intercambiar filas (y eso ya no es A = L·U).
            if any(not U[i][col].es_cero() for i in range(fila + 1, m)):
                raise ValueError(
                    "El pivote en la posición ({}, {}) es cero y hay entradas no "
                    "nulas debajo de él. La factorización LU sin intercambios de "
                    "filas no es posible para esta matriz.".format(fila + 1, col + 1))
            continue

        for i in range(fila + 1, m):
            if U[i][col].es_cero():
                continue
            factor = U[i][col] / pivote
            L[i][fila] = factor
            for c in range(col, n):
                U[i][c] = U[i][c] - factor * U[fila][c]

        fila += 1

    return L, U


# ---------------------------------------------------------------------------
# Gauss-Jordan de cada etapa (con procedimiento)
# ---------------------------------------------------------------------------

def _bloque_operaciones(ops, M, n):
    """Operaciones de una columna y la matriz que resulta de aplicarlas."""
    lineas = ["  Operaciones:"]
    for op in ops:
        lineas.append("    " + op)
    lineas.append(texto_matriz(M, n, sangria="    "))
    lineas.append("")
    return lineas


def _gauss_jordan_inferior(L, b, nombre_izq, nombre_der):
    """
    [L | b] ~ [I | y]. Como L es triangular inferior con unos en la diagonal,
    solo hay que anular lo que está debajo de cada pivote (columna por columna).
    Devuelve (vector y, líneas del procedimiento).
    """
    n = len(L)
    M = [list(L[i]) + [b[i]] for i in range(n)]

    lineas = ["  Matriz inicial [{} | {}]:".format(nombre_izq, nombre_der),
              texto_matriz(M, n, sangria="    "), ""]

    for col in range(n):
        ops = []
        for i in range(col + 1, n):
            c = M[i][col]
            if c.es_cero():
                continue
            M[i] = [M[i][k] - c * M[col][k] for k in range(n + 1)]
            ops.append(_op_reemplazo(i, col, -c))
        if ops:
            lineas += _bloque_operaciones(ops, M, n)

    return [M[i][n] for i in range(n)], lineas


def _gauss_jordan_superior(U, y, nombre_izq, nombre_der):
    """
    [U | y] ~ [I | x]. Se trabaja de la última columna a la primera: primero
    el pivote se lleva a 1 y luego se anula lo que está encima de él.
    Devuelve (vector x, líneas del procedimiento).
    """
    n = len(U)
    M = [list(U[i]) + [y[i]] for i in range(n)]

    lineas = ["  Matriz inicial [{} | {}]:".format(nombre_izq, nombre_der),
              texto_matriz(M, n, sangria="    "), ""]

    for col in range(n - 1, -1, -1):
        ops = []
        p = M[col][col]
        if not p.es_uno():
            f = Fraccion(1) / p
            M[col] = [v * f for v in M[col]]
            ops.append(_op_escala(col, f))
        for i in range(col):
            c = M[i][col]
            if c.es_cero():
                continue
            M[i] = [M[i][k] - c * M[col][k] for k in range(n + 1)]
            ops.append(_op_reemplazo(i, col, -c))
        if ops:
            lineas += _bloque_operaciones(ops, M, n)

    return [M[i][n] for i in range(n)], lineas


# ---------------------------------------------------------------------------
# Flujo completo
# ---------------------------------------------------------------------------

def ejecutar_modulo_lu(A, b=None, con_pasos=True):
    """
    Flujo completo en el orden de clase:
      1) DATOS: A = L·U (calculados automáticamente) y el vector b.
      2) PASO 1: Ly = b por Gauss-Jordan  ->  y   (solo si con_pasos)
      3) PASO 2: Ux = y por Gauss-Jordan  ->  x   (solo si con_pasos)
      4) RESULTADO Y COMPROBACIÓN: y, x, L·U = A y A·x = b.
    Sin b solo se factoriza A (y, x quedan en None).
    A puede ser m×n: si no es cuadrada solo se factoriza (resolver Ax = b con
    L y U en dos etapas requiere A cuadrada), aunque se entregue b.

    Devuelve un diccionario: L, U, y, x, informe (texto) y valido (bool).
    """
    m = len(A)
    n = len(A[0])
    L, U = factorizar_lu(A)
    cuadrada = (m == n)
    if not cuadrada:
        b = None

    # b puede llegar como lista plana o como columna [[b1], [b2], ...]
    b_plano = None
    if b is not None:
        b_plano = [val[0] if isinstance(val, list) else val for val in b]
        if len(b_plano) != m:
            raise ValueError(
                "b debe tener {} componentes (una por fila de A), tiene {}.".format(
                    m, len(b_plano)))
        # Un cero en la diagonal de U significa que A es singular
        for i in range(n):
            if U[i][i].es_cero():
                raise ValueError(
                    "La matriz A es singular: U tiene un cero en la diagonal "
                    "(posición ({0}, {0})). El sistema no tiene solución única, "
                    "así que no se puede resolver con L y U.".format(i + 1))

    lineas = []

    # ---- DATOS ----------------------------------------------------------
    lineas.append("=== DATOS: A = L·U" + (" y vector b" if b_plano is not None else "") + " ===")
    lineas.append("L y U se calculan automáticamente a partir de A.")
    if not cuadrada:
        lineas.append("A es {0}×{1}: L es {0}×{0} (triangular inferior con unos en la diagonal) "
                      "y U es {0}×{1} (forma escalonada).".format(m, n))
        lineas.append("Como A no es cuadrada solo se calcula la factorización A = L·U.")
    lineas.append("")
    bloques = [("A", A, " = "), ("L", L, " · "),
               ("U", U, "  ,  " if b_plano is not None else "")]
    if b_plano is not None:
        bloques.append(("b", [[v] for v in b_plano], ""))
    lineas.append(_lado_a_lado(bloques))
    lineas.append("")

    if b_plano is not None and con_pasos:
        lineas.append("Plan de solución:")
        lineas.append("  1) Resolver Ly = b con Gauss-Jordan:  [L | b] ~ [I | y]")
        lineas.append("  2) Resolver Ux = y con Gauss-Jordan:  [U | y] ~ [I | x]")
        lineas.append("  Comprobación: L·U = A (entrada por entrada) y A·x = b.")
        lineas.append("")

    y = None
    x = None
    if b_plano is not None:
        # ---- PASO 1: Ly = b -------------------------------------------
        y, l1 = _gauss_jordan_inferior(L, b_plano, "L", "b")
        if con_pasos:
            lineas.append("=== PASO 1: Ly = b, de [L | b] a [I | y] ===")
            lineas += l1
            lineas.append("  y = " + _vector(y))
            lineas.append("")

        # ---- PASO 2: Ux = y -------------------------------------------
        x, l2 = _gauss_jordan_superior(U, y, "U", "y")
        if con_pasos:
            lineas.append("=== PASO 2: Ux = y, de [U | y] a [I | x] ===")
            lineas += l2
            lineas.append("  x = " + _vector(x))
            lineas.append("")

    # ---- RESULTADO Y COMPROBACIÓN --------------------------------------
    lineas.append("=== RESULTADO Y COMPROBACIÓN ===")
    lineas.append("")

    if b_plano is not None:
        lineas.append(_lado_a_lado([("y", [[v] for v in y], "    "),
                                    ("x", [[v] for v in x], "")]))
        lineas.append("")

    LU = alg.multiplicar_matrices(L, U)
    lu_ok = all(LU[i][j] == A[i][j] for i in range(m) for j in range(n))

    lineas.append("Comprobación de L·U = A:")
    lineas.append(_lado_a_lado([("L·U", LU, "  =  "), ("A", A, "")]))
    lineas.append("  " + ("✓ L·U coincide con A entrada por entrada."
                          if lu_ok else "✗ L·U NO coincide con A."))
    lineas.append("")

    ax_ok = True
    if b_plano is not None:
        lineas.append("Comprobación de Ax = b:")
        for i in range(m):
            terminos = " + ".join("({})·({})".format(A[i][j], x[j]) for j in range(n))
            obtenido = Fraccion(0)
            for j in range(n):
                obtenido = obtenido + A[i][j] * x[j]
            ok = (obtenido == b_plano[i])
            ax_ok = ax_ok and ok
            if ok:
                lineas.append("  {} = {} ✓".format(terminos, obtenido))
            else:
                lineas.append("  {} = {} ✗ (se esperaba {})".format(
                    terminos, obtenido, b_plano[i]))
        lineas.append("")
        lineas.append("  " + ("✓ La solución x satisface exactamente A·x = b."
                              if ax_ok else "✗ La solución NO satisface A·x = b."))
        lineas.append("")

    return {
        "L": L,
        "U": U,
        "y": y,
        "x": x,
        "informe": "\n".join(lineas),
        "valido": lu_ok and ax_ok
    }