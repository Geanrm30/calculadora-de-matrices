# -*- coding: utf-8 -*-
"""
Módulo de Factorización LU y resolución de sistemas Ax = b en dos etapas
(Sustitución hacia adelante Ly = b y sustitución hacia atrás Ux = y).
Implementado con aritmética exacta de Fraccion. MTM0120 Álgebra Lineal — UAM.
Elaborado para el Proyecto Integrador de Álgebra Lineal.
"""

from core.fraccion import Fraccion
import core.algebra as alg
from core.formato import texto_matriz, ancho_columna, subindice


def _sub(n):
    """Subíndice Unicode de un número ya en base 1: 2 -> ₂ (se usa en y₂, x₂, b₂, f₂)."""
    return subindice(n)


def _ind(fila, col):
    """
    Subíndice doble en base 1: (2, 1) -> ₂₁ (se usa en L₂₁).
    Si algún índice tiene dos dígitos se separa con coma (L₁₀,₁), igual que
    core/procedimiento, para no confundir "fila 1 columna 12" con "fila 11 columna 2".
    """
    f = subindice(fila)
    c = subindice(col)
    if fila > 9 or col > 9:
        return f + "," + c
    return f + c


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


def factorizacion_lu_pasos(A):
    """
    Obtiene la Factorización LU de una matriz A (A = L·U) mediante operaciones
    elementales de reemplazo de filas.
    Registra los multiplicadores en L y la forma escalonada en U.
    Devuelve un diccionario con las matrices L, U, los pasos detallados y la comprobación.
    """
    m = len(A)
    n = len(A[0])

    if m != n:
        raise ValueError(
            "La factorización LU estándar requiere una matriz cuadrada "
            "(A es {}×{}).".format(m, n))

    # Copias de trabajo
    U = [[A[i][j] for j in range(n)] for i in range(m)]
    L = [[Fraccion(1) if i == j else Fraccion(0) for j in range(m)] for i in range(m)]

    lineas_proceso = []
    lineas_proceso.append("=== 1. PROCESO DE FACTORIZACIÓN A = L·U ===")
    lineas_proceso.append(f"Matriz inicial A ({m}×{n}):")
    lineas_proceso.append(_texto_matriz(A, sangria="  "))
    lineas_proceso.append("")

    paso_num = 1
    for col in range(n - 1):
        pivote = U[col][col]
        if pivote.es_cero():
            raise ValueError(
                f"El pivote en la posición ({col+1}, {col+1}) es cero. "
                "La factorización LU sin intercambios de filas no es posible "
                "para esta matriz.")

        lineas_proceso.append(f"--- Columna pivote {col+1} (pivote = {pivote}) ---")

        for fila in range(col + 1, m):
            factor = U[fila][col] / pivote
            L[fila][col] = factor

            # Operación elemental: f_fila -> f_fila - factor * f_col
            for c in range(col, n):
                U[fila][c] = U[fila][c] - factor * U[col][c]

            lineas_proceso.append(
                f"  Paso {paso_num}: f{_sub(fila+1)} ← f{_sub(fila+1)} - ({factor})·f{_sub(col+1)}  "
                f"(multiplicador L{_ind(fila+1, col+1)} = {factor})"
            )
            paso_num += 1

        lineas_proceso.append("")
        lineas_proceso.append("  Matriz U parcial:")
        lineas_proceso.append(_texto_matriz(U, sangria="    "))
        lineas_proceso.append("")

    lineas_proceso.append("Matrices finales de la descomposición:")
    lineas_proceso.append("Matriz L (Triangular inferior unitaria):")
    lineas_proceso.append(_texto_matriz(L, sangria="  "))
    lineas_proceso.append("")
    lineas_proceso.append("Matriz U (Forma escalonada):")
    lineas_proceso.append(_texto_matriz(U, sangria="  "))
    lineas_proceso.append("")

    # Comprobación L * U = A
    LU = alg.multiplicar_matrices(L, U)
    comprobacion_ok = all(
        LU[i][j] == A[i][j] for i in range(m) for j in range(n)
    )

    lineas_proceso.append("Comprobación L·U = A:")
    lineas_proceso.append(_texto_matriz(LU, sangria="  "))
    if comprobacion_ok:
        lineas_proceso.append("  [CUMPLE] El producto L·U coincide exactamente con A.")
    else:
        lineas_proceso.append("  [FALLA] El producto L·U no coincide con A.")
    lineas_proceso.append("")

    return {
        "L": L,
        "U": U,
        "pasos": lineas_proceso,
        "comprobacion_lu": comprobacion_ok
    }


def resolver_sistema_lu_pasos(L, U, b, A=None):
    """
    Resuelve Ax = b en dos etapas sustitutivas utilizando L y U:
    1. Sustitución hacia adelante: Ly = b
    2. Sustitución hacia atrás: Ux = y
    Si se entrega A, la comprobación final usa la matriz original (A·x = b);
    si no, se usa L·U.
    Devuelve un diccionario con el vector y, el vector x y todo el procedimiento explicado.
    """
    m = len(L)
    n = len(U[0])

    # b puede llegar como lista plana o como columna [[b1], [b2], ...]
    b_plano = [val[0] if isinstance(val, list) else val for val in b]

    if len(b_plano) != m:
        raise ValueError(
            "b debe tener {} componentes (una por fila de A), tiene {}.".format(
                m, len(b_plano)))

    # Un cero en la diagonal de U significa que A es singular: no hay solución única
    for i in range(min(m, n)):
        if U[i][i].es_cero():
            raise ValueError(
                "La matriz A es singular: U tiene un cero en la diagonal "
                "(posición ({0}, {0})). El sistema no tiene solución única, "
                "así que no se puede resolver con L y U.".format(i + 1))

    lineas = []
    lineas.append("=== 2. RESOLUCIÓN DE Ax = b MEDIANTE DESCOMPOSICIÓN LU ===")
    lineas.append(f"Vector de términos independientes b = [ {', '.join(str(v) for v in b_plano)} ]^T")
    lineas.append("")

    # ETAPA 1: Resolver Ly = b (Sustitución hacia adelante)
    lineas.append("--- Etapa 1: Sustitución hacia adelante (Ly = b) ---")
    lineas.append("Se resuelve el sistema triangular inferior ampliando [L | b]:")

    aug_L = [list(L[i]) + [b_plano[i]] for i in range(m)]
    lineas.append(texto_matriz(aug_L, m, sangria="  "))
    lineas.append("")

    y = [Fraccion(0) for _ in range(m)]
    for i in range(m):
        acum = aug_L[i][m]
        for j in range(i):
            acum = acum - aug_L[i][j] * y[j]
        y[i] = acum / aug_L[i][i]
        lineas.append(f"  y{_sub(i+1)} = {acum} / {aug_L[i][i]} = {y[i]}")

    lineas.append("")
    lineas.append(f"Vector intermedio y = [ {', '.join(str(val) for val in y)} ]^T")
    lineas.append("")

    # ETAPA 2: Resolver Ux = y (Sustitución hacia atrás)
    lineas.append("--- Etapa 2: Sustitución hacia atrás (Ux = y) ---")
    lineas.append("Se resuelve el sistema triangular superior ampliando [U | y]:")

    aug_U = [list(U[i]) + [y[i]] for i in range(m)]
    lineas.append(texto_matriz(aug_U, n, sangria="  "))
    lineas.append("")

    x = [Fraccion(0) for _ in range(n)]
    for i in range(n - 1, -1, -1):
        acum = aug_U[i][n]
        for c in range(i + 1, n):
            acum = acum - U[i][c] * x[c]
        x[i] = acum / U[i][i]
        lineas.append(f"  x{_sub(i+1)} = {acum} / {U[i][i]} = {x[i]}")

    lineas.append("")
    lineas.append(f"Solución final x = [ {', '.join(str(val) for val in x)} ]^T")
    lineas.append("")

    # Comprobación final A * x = b
    lineas.append("--- Comprobación final del sistema (A·x = b) ---")

    A_ref = A if A is not None else alg.multiplicar_matrices(L, U)
    x_mat = [[val] for val in x]
    Ax = alg.multiplicar_matrices(A_ref, x_mat)

    comprobacion_ax = all(Ax[i][0] == b_plano[i] for i in range(m))

    for i in range(m):
        lineas.append(f"  Ecuación {i+1}: obtenida = {Ax[i][0]} | esperada (b{_sub(i+1)}) = {b_plano[i]}")

    if comprobacion_ax:
        lineas.append("  [CUMPLE] La solución x satisface exactamente A·x = b.")
    else:
        lineas.append("  [FALLA] La solución no satisface el sistema.")
    lineas.append("")

    return {
        "y": y,
        "x": x,
        "pasos": lineas,
        "comprobacion_ax": comprobacion_ax
    }


def ejecutar_modulo_lu(A, b=None):
    """
    Ejecuta el flujo completo de factorización LU y, si se entrega b, la
    resolución del sistema Ax = b, concatenando los informes paso a paso.
    Sin b solo factoriza (y, x quedan en None).
    """
    res_lu = factorizacion_lu_pasos(A)

    if b is None:
        return {
            "L": res_lu["L"],
            "U": res_lu["U"],
            "y": None,
            "x": None,
            "informe": "\n".join(res_lu["pasos"]),
            "valido": res_lu["comprobacion_lu"]
        }

    res_res = resolver_sistema_lu_pasos(res_lu["L"], res_lu["U"], b, A)

    informe_completo = "\n".join(res_lu["pasos"] + res_res["pasos"])
    return {
        "L": res_lu["L"],
        "U": res_lu["U"],
        "y": res_res["y"],
        "x": res_res["x"],
        "informe": informe_completo,
        "valido": res_lu["comprobacion_lu"] and res_res["comprobacion_ax"]
    }