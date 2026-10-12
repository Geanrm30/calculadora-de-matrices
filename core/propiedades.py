# -*- coding: utf-8 -*-
"""
Verificador de propiedades algebraicas de matrices y vectores.
Implementa las propiedades de las Sesiones 9-11: suma, escalar, transpuesta,
producto, inversa y determinante. Cada propiedad calcula ambos lados por caminos
distintos y los compara con fracciones exactas. MTM0120 — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

import core.algebra as alg
import core.procedimiento as proc
from core.fraccion import Fraccion
from core.vector import como_columna, sumar_vectores

CAT_MV  = "Producto matriz-vector"
CAT_VEC = "Vectores en Rⁿ"
CAT_SUM = "Suma y escalar de matrices"
CAT_TRA = "Transpuesta"
CAT_PRO = "Producto de matrices"
CAT_INV = "Inversa"
CAT_DET = "Determinante"


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _identidad(n):
    return [[Fraccion(1) if i == j else Fraccion(0) for j in range(n)]
            for i in range(n)]


def _vector(B, j, nombre):
    """Columna j de B como vector; ValueError si B no tiene esa columna."""
    if len(B[0]) <= j:
        raise ValueError(
            "Esta propiedad necesita el vector {}.\n\n"
            "Pon al menos {} columna(s) en B: la primera es u y la segunda es v."
            .format(nombre, j + 1))
    return [fila[j] for fila in B]


def _iguales(X, Y):
    if len(X) != len(Y) or len(X[0]) != len(Y[0]):
        return False
    return all(X[i][j] == Y[i][j]
               for i in range(len(X)) for j in range(len(X[0])))


def _dim(M):
    return "{}×{}".format(len(M), len(M[0]))


def _armar(titulo, regla, nota, pasos, nom_izq, izq, nom_der, der):
    """Redacta la comprobacion y devuelve (lineas, cumple)."""
    lineas = proc._encabezado("PROPIEDAD:  " + titulo, regla, nota)

    for etiqueta, M in pasos:
        lineas.extend("  " + l for l in proc.texto_resultado(etiqueta, M))
        lineas.append("")

    lineas.extend("  " + l for l in proc.texto_resultado(
        "LADO IZQUIERDO   {} =".format(nom_izq), izq))
    lineas.append("")
    lineas.extend("  " + l for l in proc.texto_resultado(
        "LADO DERECHO   {} =".format(nom_der), der))
    lineas.append("")

    cumple = _iguales(izq, der)
    if cumple:
        lineas.append("  [CUMPLE] {} = {}: la propiedad se verifica.".format(
            nom_izq, nom_der))
    else:
        lineas.append("  [FALLA] Los dos lados no coinciden.")
        if len(izq) == len(der) and len(izq[0]) == len(der[0]):
            for i in range(len(izq)):
                for j in range(len(izq[0])):
                    if izq[i][j] != der[i][j]:
                        lineas.append("     posición ({}, {}):  {} ≠ {}".format(
                            i + 1, j + 1, izq[i][j], der[i][j]))
        else:
            lineas.append("     Tamaños distintos: {} y {}.".format(
                _dim(izq), _dim(der)))
    lineas.append("")
    return lineas, cumple


# ---------------------------------------------------------------------------
# Producto matriz-vector
# ---------------------------------------------------------------------------

def _chequear_A_u(A, u):
    if len(A[0]) != len(u):
        raise ValueError(
            "A tiene {} columnas y los vectores de B tienen {} componentes.\n\n"
            "Para calcular A·u las columnas de A deben coincidir con las "
            "filas de B.".format(len(A[0]), len(u)))


def _mv_suma(A, B, r, C=None, s=None):
    u = _vector(B, 0, "u")
    v = _vector(B, 1, "v")
    _chequear_A_u(A, u)
    lineas = proc.pasos_propiedad_suma(A, u, v)
    return lineas, any("[CUMPLE]" in l for l in lineas)


def _mv_escalar(A, B, r, C=None, s=None):
    u = _vector(B, 0, "u")
    _chequear_A_u(A, u)
    lineas = proc.pasos_propiedad_escalar(A, r, u)
    return lineas, any("[CUMPLE]" in l for l in lineas)


# ---------------------------------------------------------------------------
# Vectores en Rn
# ---------------------------------------------------------------------------

def _vec_conmutativa(A, B, r, C=None, s=None):
    u, v = _vector(B, 0, "u"), _vector(B, 1, "v")
    return _armar("u + v = v + u",
                  "La suma de vectores es conmutativa.",
                  "u = {}   v = {}".format(proc._vector_en_linea(u),
                                           proc._vector_en_linea(v)),
                  [],
                  "u + v", como_columna(sumar_vectores(u, v)),
                  "v + u", como_columna(sumar_vectores(v, u)))


def _vec_distributiva(A, B, r, C=None, s=None):
    u, v = _vector(B, 0, "u"), _vector(B, 1, "v")
    U, V = como_columna(u), como_columna(v)
    pasos = [("u + v =", alg.sumar_matrices(U, V)),
             ("r·u =", alg.multiplicar_escalar(r, U)),
             ("r·v =", alg.multiplicar_escalar(r, V))]
    return _armar("r(u + v) = r·u + r·v",
                  "El escalar distribuye sobre la suma de vectores.",
                  "r = {}".format(r), pasos,
                  "r(u + v)", alg.multiplicar_escalar(r, pasos[0][1]),
                  "r·u + r·v", alg.sumar_matrices(pasos[1][1], pasos[2][1]))


# ---------------------------------------------------------------------------
# Suma y escalar de matrices
# ---------------------------------------------------------------------------

def _sum_conmutativa(A, B, r, C=None, s=None):
    return _armar("A + B = B + A",
                  "La suma de matrices es conmutativa.", None, [],
                  "A + B", alg.sumar_matrices(A, B),
                  "B + A", alg.sumar_matrices(B, A))


def _sum_asociativa(A, B, r, C=None, s=None):
    """Necesita C del mismo tamaño que A y B."""
    if C is None:
        raise ValueError("Esta propiedad necesita la matriz C.")
    AB = alg.sumar_matrices(A, B)
    BC = alg.sumar_matrices(B, C)
    pasos = [("A + B =", AB), ("B + C =", BC)]
    return _armar("(A + B) + C = A + (B + C)",
                  "Ley asociativa: el agrupamiento no cambia el resultado.",
                  None, pasos,
                  "(A + B) + C", alg.sumar_matrices(AB, C),
                  "A + (B + C)", alg.sumar_matrices(A, BC))


def _sum_neutro(A, B, r, C=None, s=None):
    cero = [[Fraccion(0)] * len(A[0]) for _ in A]
    return _armar("A + 0 = A",
                  "La matriz cero es el elemento neutro de la suma.", None,
                  [("0 =", cero)],
                  "A + 0", alg.sumar_matrices(A, cero), "A", A)


def _sum_distributiva(A, B, r, C=None, s=None):
    pasos = [("A + B =", alg.sumar_matrices(A, B)),
             ("r·A =", alg.multiplicar_escalar(r, A)),
             ("r·B =", alg.multiplicar_escalar(r, B))]
    return _armar("r(A + B) = r·A + r·B",
                  "El escalar distribuye sobre la suma de matrices.",
                  "r = {}".format(r), pasos,
                  "r(A + B)", alg.multiplicar_escalar(r, pasos[0][1]),
                  "r·A + r·B", alg.sumar_matrices(pasos[1][1], pasos[2][1]))


def _sum_dist_escalares(A, B, r, C=None, s=None):
    """Necesita el segundo escalar s."""
    if s is None:
        raise ValueError("Esta propiedad necesita el segundo escalar s.")
    rA = alg.multiplicar_escalar(r, A)
    sA = alg.multiplicar_escalar(s, A)
    return _armar("(r + s)·A = r·A + s·A",
                  "La suma de escalares distribuye sobre la misma matriz.",
                  "r = {}   s = {}".format(r, s),
                  [("r·A =", rA), ("s·A =", sA)],
                  "(r + s)·A", alg.multiplicar_escalar(r + s, A),
                  "r·A + s·A", alg.sumar_matrices(rA, sA))


def _sum_asoc_escalares(A, B, r, C=None, s=None):
    """Necesita el segundo escalar s."""
    if s is None:
        raise ValueError("Esta propiedad necesita el segundo escalar s.")
    sA = alg.multiplicar_escalar(s, A)
    pasos = [("s·A =", sA)]
    return _armar("r·(s·A) = (r·s)·A",
                  "Dos escalares pueden combinarse antes o después de escalar.",
                  "r = {}   s = {}".format(r, s), pasos,
                  "r·(s·A)", alg.multiplicar_escalar(r, sA),
                  "(r·s)·A", alg.multiplicar_escalar(r * s, A))


def _sum_opuesto(A, B, r, C=None, s=None):
    cero = [[Fraccion(0)] * len(A[0]) for _ in A]
    opuesta = alg.multiplicar_escalar(Fraccion(-1), A)
    return _armar("A + (−A) = 0",
                  "Toda matriz sumada con su opuesta da la matriz cero.", None,
                  [("−A =", opuesta)],
                  "A + (−A)", alg.sumar_matrices(A, opuesta), "0", cero)


# ---------------------------------------------------------------------------
# Transpuesta
# ---------------------------------------------------------------------------

def _tra_doble(A, B, r, C=None, s=None):
    T = alg.transponer(A)
    return _armar("(Aᵀ)ᵀ = A",
                  "Transponer dos veces devuelve la matriz original.", None,
                  [("Aᵀ =", T)],
                  "(Aᵀ)ᵀ", alg.transponer(T), "A", A)


def _tra_suma(A, B, r, C=None, s=None):
    pasos = [("A + B =", alg.sumar_matrices(A, B)),
             ("Aᵀ =", alg.transponer(A)),
             ("Bᵀ =", alg.transponer(B))]
    return _armar("(A + B)ᵀ = Aᵀ + Bᵀ",
                  "La transpuesta de una suma es la suma de las transpuestas.",
                  None, pasos,
                  "(A + B)ᵀ", alg.transponer(pasos[0][1]),
                  "Aᵀ + Bᵀ", alg.sumar_matrices(pasos[1][1], pasos[2][1]))


def _tra_escalar(A, B, r, C=None, s=None):
    pasos = [("r·A =", alg.multiplicar_escalar(r, A)),
             ("Aᵀ =", alg.transponer(A))]
    return _armar("(r·A)ᵀ = r·Aᵀ",
                  "El escalar puede salir de la transpuesta.",
                  "r = {}".format(r), pasos,
                  "(r·A)ᵀ", alg.transponer(pasos[0][1]),
                  "r·Aᵀ", alg.multiplicar_escalar(r, pasos[1][1]))


def _tra_producto(A, B, r, C=None, s=None):
    AB = alg.multiplicar_matrices(A, B)
    Bt, At = alg.transponer(B), alg.transponer(A)
    pasos = [("A·B =", AB), ("Bᵀ =", Bt), ("Aᵀ =", At)]
    return _armar("(A·B)ᵀ = Bᵀ·Aᵀ",
                  "La transpuesta de un producto invierte el orden de los factores.",
                  None, pasos,
                  "(A·B)ᵀ", alg.transponer(AB),
                  "Bᵀ·Aᵀ", alg.multiplicar_matrices(Bt, At))


# ---------------------------------------------------------------------------
# Producto de matrices
# ---------------------------------------------------------------------------

def _pro_asociativa(A, B, r, C=None, s=None):
    """Necesita C tal que cols(B) == filas(C)."""
    if C is None:
        raise ValueError("Esta propiedad necesita la matriz C.")
    AB = alg.multiplicar_matrices(A, B)
    BC = alg.multiplicar_matrices(B, C)
    pasos = [("A·B =", AB), ("B·C =", BC)]
    return _armar("A·(B·C) = (A·B)·C",
                  "Ley asociativa del producto: el agrupamiento no cambia el resultado.",
                  None, pasos,
                  "A·(B·C)", alg.multiplicar_matrices(A, BC),
                  "(A·B)·C", alg.multiplicar_matrices(AB, C))


def _pro_dist_izq(A, B, r, C=None, s=None):
    """Necesita C del mismo tamaño que B (para la suma B+C), con cols(A) == filas(B)."""
    if C is None:
        raise ValueError("Esta propiedad necesita la matriz C.")
    BmasC = alg.sumar_matrices(B, C)
    AB = alg.multiplicar_matrices(A, B)
    AC = alg.multiplicar_matrices(A, C)
    pasos = [("B + C =", BmasC), ("A·B =", AB), ("A·C =", AC)]
    return _armar("A·(B + C) = A·B + A·C",
                  "Ley distributiva izquierda del producto sobre la suma.",
                  None, pasos,
                  "A·(B + C)", alg.multiplicar_matrices(A, BmasC),
                  "A·B + A·C", alg.sumar_matrices(AB, AC))


def _pro_dist_der(A, B, r, C=None, s=None):
    """Necesita C del mismo tamaño que B (para la suma B+C), con cols(B) == filas(A)."""
    if C is None:
        raise ValueError("Esta propiedad necesita la matriz C.")
    BmasC = alg.sumar_matrices(B, C)
    BA = alg.multiplicar_matrices(B, A)
    CA = alg.multiplicar_matrices(C, A)
    pasos = [("B + C =", BmasC), ("B·A =", BA), ("C·A =", CA)]
    return _armar("(B + C)·A = B·A + C·A",
                  "Ley distributiva derecha del producto sobre la suma.",
                  None, pasos,
                  "(B + C)·A", alg.multiplicar_matrices(BmasC, A),
                  "B·A + C·A", alg.sumar_matrices(BA, CA))


def _pro_escalar(A, B, r, C=None, s=None):
    AB = alg.multiplicar_matrices(A, B)
    rA = alg.multiplicar_escalar(r, A)
    rB = alg.multiplicar_escalar(r, B)
    pasos = [("A·B =", AB), ("r·A =", rA), ("r·B =", rB)]
    izq = alg.multiplicar_escalar(r, AB)
    der = alg.multiplicar_matrices(rA, B)
    alt = alg.multiplicar_matrices(A, rB)
    lineas, c1 = _armar("r·(A·B) = (r·A)·B = A·(r·B)",
                        "El escalar puede asociarse con cualquiera de los factores.",
                        "r = {}".format(r), pasos,
                        "r·(A·B)", izq, "(r·A)·B", der)
    # Verificación adicional del tercer miembro A(rB)
    c2 = _iguales(izq, alt)
    lineas.append("  Verificación A·(r·B): {}".format(
        "[CUMPLE] coincide con r·(A·B)." if c2 else "[FALLA] no coincide."))
    lineas.append("")
    return lineas, c1 and c2


def _pro_identidad(A, B, r, C=None, s=None):
    m, n = len(A), len(A[0])
    pasos = [("Iₘ =  (identidad {}×{})".format(m, m), _identidad(m)),
             ("Iₙ =  (identidad {}×{})".format(n, n), _identidad(n))]
    izq = alg.multiplicar_matrices(A, pasos[1][1])
    der = alg.multiplicar_matrices(pasos[0][1], A)
    lineas, c1 = _armar("A·Iₙ = A = Iₘ·A",
                        "La matriz identidad es el neutro del producto.", None,
                        pasos, "A·Iₙ", izq, "Iₘ·A", der)
    c2 = _iguales(izq, A)
    if c2:
        lineas.append("  Además ambos coinciden con A.")
    else:
        lineas.append("  [FALLA] Los productos no coinciden con A.")
    lineas.append("")
    return lineas, c1 and c2


def _pro_no_conmutativo(A, B, r, C=None, s=None):
    """
    Informativa: muestra A·B y B·A para demostrar que en general no conmutan.
    No es una igualdad que deba cumplirse, por eso devuelve cumple=None.
    """
    AB = alg.multiplicar_matrices(A, B)
    lineas = proc._encabezado(
        "AB ≠ BA  (el producto no es conmutativo en general)",
        "Comparar A·B con B·A: lo normal es que sean distintos.")
    lineas.extend("  " + l for l in proc.texto_resultado("A·B =", AB))
    lineas.append("")
    try:
        BA = alg.multiplicar_matrices(B, A)
    except ValueError:
        lineas.append("  B·A no está definido: columnas de B ({}) ≠ filas de A ({}).".format(
            len(B[0]), len(A)))
        lineas.append("  Por tanto A·B ≠ B·A.")
        lineas.append("")
        return lineas, None
    lineas.extend("  " + l for l in proc.texto_resultado("B·A =", BA))
    lineas.append("")
    if _iguales(AB, BA):
        lineas.append("  Con estos datos A·B = B·A (ocurre solo en casos particulares).")
    else:
        lineas.append("  [INFO] A·B ≠ B·A: el orden de los factores sí importa.")
    lineas.append("")
    return lineas, None


# ---------------------------------------------------------------------------
# Inversa (Sesion 10)
# ---------------------------------------------------------------------------

def _inv_doble(A, B, r, C=None, s=None):
    """(A⁻¹)⁻¹ = A. Requiere A cuadrada e invertible."""
    if len(A) != len(A[0]):
        raise ValueError("Esta propiedad requiere una matriz cuadrada.")
    from modulos.modulo_matrices import inversa_gauss_jordan
    Ainv = inversa_gauss_jordan(A)
    AinvInv = inversa_gauss_jordan(Ainv)
    return _armar("(A⁻¹)⁻¹ = A",
                  "Invertir dos veces devuelve la matriz original.",
                  None, [("A⁻¹ =", Ainv)],
                  "(A⁻¹)⁻¹", AinvInv, "A", A)


def _inv_producto(A, B, r, C=None, s=None):
    """(AB)⁻¹ = B⁻¹A⁻¹. Requiere A y B cuadradas del mismo tamaño."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError("A debe ser cuadrada para esta propiedad.")
    if len(B) != n or len(B[0]) != n:
        raise ValueError(
            "B debe ser cuadrada {}×{} (igual que A) para esta propiedad. "
            "Ajusta las dimensiones de B.".format(n, n))
    from modulos.modulo_matrices import inversa_gauss_jordan
    AB = alg.multiplicar_matrices(A, B)
    Ainv = inversa_gauss_jordan(A)
    Binv = inversa_gauss_jordan(B)
    pasos = [("A·B =", AB), ("A⁻¹ =", Ainv), ("B⁻¹ =", Binv)]
    return _armar("(A·B)⁻¹ = B⁻¹·A⁻¹",
                  "La inversa de un producto invierte el orden de los factores.",
                  None, pasos,
                  "(A·B)⁻¹", inversa_gauss_jordan(AB),
                  "B⁻¹·A⁻¹", alg.multiplicar_matrices(Binv, Ainv))


def _inv_transpuesta(A, B, r, C=None, s=None):
    """(Aᵀ)⁻¹ = (A⁻¹)ᵀ. Requiere A cuadrada e invertible."""
    if len(A) != len(A[0]):
        raise ValueError("Esta propiedad requiere una matriz cuadrada.")
    from modulos.modulo_matrices import inversa_gauss_jordan
    At = alg.transponer(A)
    Ainv = inversa_gauss_jordan(A)
    pasos = [("Aᵀ =", At), ("A⁻¹ =", Ainv)]
    return _armar("(Aᵀ)⁻¹ = (A⁻¹)ᵀ",
                  "La transpuesta y la inversa conmutan.",
                  None, pasos,
                  "(Aᵀ)⁻¹", inversa_gauss_jordan(At),
                  "(A⁻¹)ᵀ", alg.transponer(Ainv))


# ---------------------------------------------------------------------------
# Determinante (Sesion 11)
# ---------------------------------------------------------------------------

def _det_transpuesta(A, B, r, C=None, s=None):
    """det(Aᵀ) = det(A). El resultado escalar se muestra como matriz 1×1."""
    if len(A) != len(A[0]):
        raise ValueError("El determinante solo está definido para matrices cuadradas.")
    from modulos.modulo_matrices import determinante
    At = alg.transponer(A)
    dA = determinante(A)
    dAt = determinante(At)
    return _armar("det(Aᵀ) = det(A)",
                  "Transponer no cambia el valor del determinante.",
                  "det(A) = {}".format(dA), [("Aᵀ =", At)],
                  "det(Aᵀ)", [[dAt]],
                  "det(A)", [[dA]])


def _det_producto(A, B, r, C=None, s=None):
    """det(AB) = det(A)·det(B). Requiere A y B cuadradas del mismo tamaño."""
    n = len(A)
    if n != len(A[0]):
        raise ValueError("A debe ser cuadrada para esta propiedad.")
    if len(B) != n or len(B[0]) != n:
        raise ValueError(
            "B debe ser cuadrada {}×{} (igual que A) para esta propiedad. "
            "Ajusta las dimensiones de B.".format(n, n))
    from modulos.modulo_matrices import determinante
    AB = alg.multiplicar_matrices(A, B)
    dA = determinante(A)
    dB = determinante(B)
    return _armar("det(A·B) = det(A)·det(B)",
                  "El determinante es multiplicativo.",
                  "det(A) = {}   det(B) = {}".format(dA, dB), [("A·B =", AB)],
                  "det(A·B)", [[determinante(AB)]],
                  "det(A)·det(B)", [[dA * dB]])


def _det_inversa_prop(A, B, r, C=None, s=None):
    """det(A⁻¹) = 1/det(A). Requiere A cuadrada e invertible."""
    if len(A) != len(A[0]):
        raise ValueError("Esta propiedad requiere una matriz cuadrada.")
    from modulos.modulo_matrices import determinante, inversa_gauss_jordan
    dA = determinante(A)
    if dA.es_cero():
        raise ValueError("A es singular (det = 0): no existe A⁻¹.")
    Ainv = inversa_gauss_jordan(A)
    return _armar("det(A⁻¹) = 1/det(A)",
                  "La inversa multiplica al determinante por su recíproco.",
                  "det(A) = {}".format(dA), [("A⁻¹ =", Ainv)],
                  "det(A⁻¹)", [[determinante(Ainv)]],
                  "1/det(A)", [[Fraccion(1) / dA]])


def _det_op_fila(A, B, r, C=None, s=None):
    """Verifica el efecto de las 3 operaciones de fila sobre det(A).
    Usa r como escalar k y opera siempre sobre las dos primeras filas."""
    if len(A) != len(A[0]):
        raise ValueError("El determinante solo está definido para matrices cuadradas.")
    if len(A) < 2:
        raise ValueError("Se necesitan al menos 2 filas para aplicar operaciones de fila.")
    from modulos.modulo_matrices import determinante
    n = len(A)
    dA = determinante(A)

    lineas = proc._encabezado(
        "PROPIEDAD 5: Operaciones de fila y el determinante",
        "Intercambio → -det(A), reemplazo → det(A), escalar k → k·det(A).",
        "det(A) = {}   k = r = {}   (se opera sobre F1 y F2)".format(dA, r))

    # Operación 1: intercambio F1 ↔ F2
    A_swap = [fila[:] for fila in A]
    A_swap[0], A_swap[1] = A_swap[1], A_swap[0]
    d_swap = determinante(A_swap)
    c1 = d_swap == -dA
    lineas += ["  Operación 1: F1 ↔ F2  (intercambio de filas)",
               "    det esperado: -det(A) = {}".format(-dA),
               "    det obtenido:          {}".format(d_swap),
               "    [{}]".format("CUMPLE" if c1 else "FALLA"), ""]

    # Operación 2: reemplazo F2 → F2 + r·F1 (el reemplazo no cambia el det)
    A_repl = [fila[:] for fila in A]
    A_repl[1] = [A_repl[1][j] + r * A_repl[0][j] for j in range(n)]
    d_repl = determinante(A_repl)
    c2 = d_repl == dA
    lineas += ["  Operación 2: F2 → F2 + {}·F1  (reemplazo)".format(r),
               "    det esperado: det(A)   = {}".format(dA),
               "    det obtenido:           {}".format(d_repl),
               "    [{}]".format("CUMPLE" if c2 else "FALLA"), ""]

    # Operación 3: escalar F1 → r·F1 (multiplica el det por r)
    A_esc = [fila[:] for fila in A]
    A_esc[0] = [r * A_esc[0][j] for j in range(n)]
    d_esc = determinante(A_esc)
    esperado_esc = r * dA
    c3 = d_esc == esperado_esc
    lineas += ["  Operación 3: F1 → {}·F1  (escalar)".format(r),
               "    det esperado: {}·det(A) = {}".format(r, esperado_esc),
               "    det obtenido:             {}".format(d_esc),
               "    [{}]".format("CUMPLE" if c3 else "FALLA"), ""]

    cumple = c1 and c2 and c3
    lineas.append("  [{}] Las tres operaciones de fila verificadas.".format(
        "CUMPLE" if cumple else "FALLA"))
    lineas.append("")
    return lineas, cumple


def _det_triangular_prop(A, B, r, C=None, s=None):
    """Compara det por expansión de cofactores con det por reducción triangular.
    Ambos métodos deben coincidir; la reducción es más eficiente para n grande."""
    if len(A) != len(A[0]):
        raise ValueError("El determinante solo está definido para matrices cuadradas.")
    from modulos.modulo_matrices import determinante, determinante_triangular
    d_cofactores = determinante(A)
    d_triangular = determinante_triangular(A)
    cumple = d_cofactores == d_triangular

    lineas = proc._encabezado(
        "PROPIEDAD 6: Cofactores vs. reducción triangular",
        "La expansión por cofactores y la reducción a triangular deben dar el mismo det.",
        "n = {}   (cofactores ≈ n! multiplicaciones; triangular ≈ n³)".format(len(A)))
    lineas += [
        "  Expansión por cofactores:  det(A) = {}".format(d_cofactores),
        "  Reducción triangular:      det(A) = {}".format(d_triangular),
        ""]
    if cumple:
        lineas.append("  [CUMPLE] Ambos métodos coinciden.")
    else:
        lineas.append("  [FALLA] {} ≠ {}: hay un error en la implementación.".format(
            d_cofactores, d_triangular))
    lineas.append("")
    return lineas, cumple


# ---------------------------------------------------------------------------
# Catalogo: (clave, nombre que ve el usuario, categoria, funcion)
# ---------------------------------------------------------------------------

PROPIEDADES = [
    # Producto matriz-vector
    ("mv_suma",      "A(u + v) = A·u + A·v",    CAT_MV,  _mv_suma),
    ("mv_escalar",   "A(r·u) = r(A·u)",         CAT_MV,  _mv_escalar),

    # Vectores en Rn
    ("vec_conm",     "u + v = v + u",           CAT_VEC, _vec_conmutativa),
    ("vec_dist",     "r(u + v) = r·u + r·v",    CAT_VEC, _vec_distributiva),

    # Suma y escalar de matrices (6 propiedades del teorema, Sesion 9)
    ("sum_conm",     "A + B = B + A",           CAT_SUM, _sum_conmutativa),
    ("sum_asoc",     "(A+B)+C = A+(B+C)",       CAT_SUM, _sum_asociativa),
    ("sum_neutro",   "A + 0 = A",               CAT_SUM, _sum_neutro),
    ("sum_dist",     "r(A + B) = r·A + r·B",    CAT_SUM, _sum_distributiva),
    ("sum_dist_rs",  "(r+s)A = r·A + s·A",      CAT_SUM, _sum_dist_escalares),
    ("sum_asoc_rs",  "r(sA) = (rs)A",           CAT_SUM, _sum_asoc_escalares),
    ("sum_opuesto",  "A + (−A) = 0",            CAT_SUM, _sum_opuesto),

    # Transpuesta (4 propiedades del teorema, Sesion 9)
    ("tra_doble",    "(Aᵀ)ᵀ = A",               CAT_TRA, _tra_doble),
    ("tra_suma",     "(A + B)ᵀ = Aᵀ + Bᵀ",      CAT_TRA, _tra_suma),
    ("tra_escalar",  "(r·A)ᵀ = r·Aᵀ",           CAT_TRA, _tra_escalar),
    ("tra_prod",     "(A·B)ᵀ = Bᵀ·Aᵀ",          CAT_TRA, _tra_producto),

    # Producto de matrices (5 propiedades del teorema, Sesion 9)
    ("pro_asoc",     "A(BC) = (AB)C",           CAT_PRO, _pro_asociativa),
    ("pro_dist_izq", "A(B+C) = AB+AC",          CAT_PRO, _pro_dist_izq),
    ("pro_dist_der", "(B+C)A = BA+CA",          CAT_PRO, _pro_dist_der),
    ("pro_escalar",  "r(AB) = (rA)B = A(rB)",   CAT_PRO, _pro_escalar),
    ("pro_ident",    "A·I = A = I·A",           CAT_PRO, _pro_identidad),
    ("pro_noconm",   "A·B ≠ B·A  (en general)", CAT_PRO, _pro_no_conmutativo),

    # Inversa (3 propiedades del teorema, Sesion 10)
    ("inv_doble",    "(A⁻¹)⁻¹ = A",              CAT_INV, _inv_doble),
    ("inv_prod",     "(AB)⁻¹ = B⁻¹·A⁻¹",         CAT_INV, _inv_producto),
    ("inv_trans",    "(Aᵀ)⁻¹ = (A⁻¹)ᵀ",          CAT_INV, _inv_transpuesta),

    # Determinante (Sesion 11)
    ("det_trans",    "det(Aᵀ) = det(A)",                  CAT_DET, _det_transpuesta),
    ("det_prod",     "det(AB) = det(A)·det(B)",           CAT_DET, _det_producto),
    ("det_inv",      "det(A⁻¹) = 1/det(A)",               CAT_DET, _det_inversa_prop),
    ("det_op_fila",  "operaciones de fila y det",  CAT_DET, _det_op_fila),
    ("det_tri",      "triangular vs cofactores",   CAT_DET, _det_triangular_prop),
]

_POR_CLAVE = {clave: (nombre, cat, f) for clave, nombre, cat, f in PROPIEDADES}


def nombre_de(clave):
    return _POR_CLAVE[clave][0]


def etiqueta(clave):
    """Texto del selector: categoria · propiedad."""
    nombre, cat, _ = _POR_CLAVE[clave]
    return "{}  ·  {}".format(cat, nombre)


def clave_de_etiqueta(texto):
    for clave, _n, _c, _f in PROPIEDADES:
        if etiqueta(clave) == texto:
            return clave
    return None


def verificar(clave, A, B, r, C=None, s=None):
    """Devuelve (lineas, cumple). cumple: True / False / None (solo informativa)."""
    return _POR_CLAVE[clave][2](A, B, r, C, s)


def verificar_todas(A, B, r, C=None, s=None):
    """
    Comprueba todas las propiedades con los datos actuales. Las que no se
    pueden aplicar (dimensiones incompatibles, falta C, falta s) se listan
    aparte como OMITIDA sin detener las demas.
    """
    cuerpo, resumen = [], []
    for clave, nombre, cat, f in PROPIEDADES:
        try:
            lineas, cumple = f(A, B, r, C, s)
        except (ValueError, ZeroDivisionError) as ex:
            motivo = str(ex).split("\n")[0]
            resumen.append("  [OMITIDA] {}  ({})".format(nombre, motivo))
            continue
        cuerpo.extend(lineas)
        cuerpo.append("  " + "-" * 60)
        cuerpo.append("")
        marca = {True: "[CUMPLE]", False: "[FALLA] ", None: "[INFO]  "}[cumple]
        resumen.append("  {} {}".format(marca, nombre))

    encabezado = ["RESUMEN DE PROPIEDADES", ""] + resumen + ["", "=" * 62, ""]
    return encabezado + cuerpo
