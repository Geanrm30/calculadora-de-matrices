# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/propiedades.py
#  Verificacion numerica de las propiedades algebraicas de vectores y matrices.
#
#  Cada propiedad se comprueba con los datos de las cuadriculas: se calcula el
#  lado izquierdo y el derecho por caminos distintos y se comparan entrada por
#  entrada (con fracciones exactas, sin redondeo).
#
#  Datos que usa cada propiedad:
#      A, B : matrices de las cuadriculas
#      r    : el escalar
#      u, v : la 1ª y la 2ª columna de B (vectores)
#
#  Si los datos no sirven para una propiedad (dimensiones incompatibles, falta
#  una segunda columna, etc.) se lanza ValueError con la explicacion.
# =============================================================================

import core.algebra as alg
import core.procedimiento as proc
from core.fraccion import Fraccion
from core.vector import como_columna, desde_columna, sumar_vectores

CAT_MV  = "Producto matriz-vector"
CAT_VEC = "Vectores en Rⁿ"
CAT_SUM = "Suma y escalar de matrices"
CAT_TRA = "Transpuesta"
CAT_PRO = "Producto de matrices"


# ---------------------------------------------------------------------------
# Utilidades
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
# Producto matriz-vector (reutiliza el paso a paso ya existente)
# ---------------------------------------------------------------------------

def _chequear_A_u(A, u):
    if len(A[0]) != len(u):
        raise ValueError(
            "A tiene {} columnas y los vectores de B tienen {} componentes.\n\n"
            "Para calcular A·u las columnas de A deben coincidir con las "
            "filas de B.".format(len(A[0]), len(u)))


def _mv_suma(A, B, r):
    u = _vector(B, 0, "u")
    v = _vector(B, 1, "v")
    _chequear_A_u(A, u)
    lineas = proc.pasos_propiedad_suma(A, u, v)
    return lineas, any("[CUMPLE]" in l for l in lineas)


def _mv_escalar(A, B, r):
    u = _vector(B, 0, "u")
    _chequear_A_u(A, u)
    lineas = proc.pasos_propiedad_escalar(A, r, u)
    return lineas, any("[CUMPLE]" in l for l in lineas)


# ---------------------------------------------------------------------------
# Vectores en Rn
# ---------------------------------------------------------------------------

def _vec_conmutativa(A, B, r):
    u, v = _vector(B, 0, "u"), _vector(B, 1, "v")
    return _armar("u + v = v + u",
                  "La suma de vectores es conmutativa.",
                  "u = {}   v = {}".format(proc._vector_en_linea(u),
                                           proc._vector_en_linea(v)),
                  [],
                  "u + v", como_columna(sumar_vectores(u, v)),
                  "v + u", como_columna(sumar_vectores(v, u)))


def _vec_distributiva(A, B, r):
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

def _sum_conmutativa(A, B, r):
    return _armar("A + B = B + A",
                  "La suma de matrices es conmutativa.", None, [],
                  "A + B", alg.sumar_matrices(A, B),
                  "B + A", alg.sumar_matrices(B, A))


def _sum_distributiva(A, B, r):
    pasos = [("A + B =", alg.sumar_matrices(A, B)),
             ("r·A =", alg.multiplicar_escalar(r, A)),
             ("r·B =", alg.multiplicar_escalar(r, B))]
    return _armar("r(A + B) = r·A + r·B",
                  "El escalar distribuye sobre la suma de matrices.",
                  "r = {}".format(r), pasos,
                  "r(A + B)", alg.multiplicar_escalar(r, pasos[0][1]),
                  "r·A + r·B", alg.sumar_matrices(pasos[1][1], pasos[2][1]))


def _sum_opuesto(A, B, r):
    cero = [[Fraccion(0)] * len(A[0]) for _ in A]
    opuesta = alg.multiplicar_escalar(Fraccion(-1), A)
    return _armar("A + (−A) = 0",
                  "Toda matriz sumada con su opuesta da la matriz cero.", None,
                  [("−A =", opuesta)],
                  "A + (−A)", alg.sumar_matrices(A, opuesta), "0", cero)


# ---------------------------------------------------------------------------
# Transpuesta
# ---------------------------------------------------------------------------

def _tra_doble(A, B, r):
    T = alg.transponer(A)
    return _armar("(Aᵀ)ᵀ = A",
                  "Transponer dos veces devuelve la matriz original.", None,
                  [("Aᵀ =", T)],
                  "(Aᵀ)ᵀ", alg.transponer(T), "A", A)


def _tra_suma(A, B, r):
    pasos = [("A + B =", alg.sumar_matrices(A, B)),
             ("Aᵀ =", alg.transponer(A)),
             ("Bᵀ =", alg.transponer(B))]
    return _armar("(A + B)ᵀ = Aᵀ + Bᵀ",
                  "La transpuesta de una suma es la suma de las transpuestas.",
                  None, pasos,
                  "(A + B)ᵀ", alg.transponer(pasos[0][1]),
                  "Aᵀ + Bᵀ", alg.sumar_matrices(pasos[1][1], pasos[2][1]))


def _tra_escalar(A, B, r):
    pasos = [("r·A =", alg.multiplicar_escalar(r, A)),
             ("Aᵀ =", alg.transponer(A))]
    return _armar("(r·A)ᵀ = r·Aᵀ",
                  "El escalar puede salir de la transpuesta.",
                  "r = {}".format(r), pasos,
                  "(r·A)ᵀ", alg.transponer(pasos[0][1]),
                  "r·Aᵀ", alg.multiplicar_escalar(r, pasos[1][1]))


def _tra_producto(A, B, r):
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

def _pro_identidad(A, B, r):
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


def _pro_no_conmutativo(A, B, r):
    """
    Informativa: el producto NO es conmutativo en general. No es una
    propiedad que deba cumplirse, asi que no da CUMPLE/FALLA.
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
        lineas.append("  B·A no está definido: las columnas de B ({}) no coinciden".format(
            len(B[0])))
        lineas.append("  con las filas de A ({}). Por tanto A·B ≠ B·A.".format(len(A)))
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
# Catalogo: (clave, nombre que ve el usuario, categoria, funcion)
# ---------------------------------------------------------------------------

PROPIEDADES = [
    ("mv_suma",     "A(u + v) = A·u + A·v",   CAT_MV,  _mv_suma),
    ("mv_escalar",  "A(r·u) = r(A·u)",        CAT_MV,  _mv_escalar),

    ("vec_conm",    "u + v = v + u",          CAT_VEC, _vec_conmutativa),
    ("vec_dist",    "r(u + v) = r·u + r·v",   CAT_VEC, _vec_distributiva),

    ("sum_conm",    "A + B = B + A",          CAT_SUM, _sum_conmutativa),
    ("sum_dist",    "r(A + B) = r·A + r·B",   CAT_SUM, _sum_distributiva),
    ("sum_opuesto", "A + (−A) = 0",           CAT_SUM, _sum_opuesto),

    ("tra_doble",   "(Aᵀ)ᵀ = A",              CAT_TRA, _tra_doble),
    ("tra_suma",    "(A + B)ᵀ = Aᵀ + Bᵀ",     CAT_TRA, _tra_suma),
    ("tra_escalar", "(r·A)ᵀ = r·Aᵀ",          CAT_TRA, _tra_escalar),
    ("tra_prod",    "(A·B)ᵀ = Bᵀ·Aᵀ",         CAT_TRA, _tra_producto),

    ("pro_ident",   "A·I = A = I·A",          CAT_PRO, _pro_identidad),
    ("pro_noconm",  "A·B ≠ B·A  (en general)", CAT_PRO, _pro_no_conmutativo),
]

_POR_CLAVE = {clave: (nombre, cat, f) for clave, nombre, cat, f in PROPIEDADES}


def nombre_de(clave):
    return _POR_CLAVE[clave][0]


def etiqueta(clave):
    """Texto del selector: categoria y propiedad."""
    nombre, cat, _ = _POR_CLAVE[clave]
    return "{}  ·  {}".format(cat, nombre)


def clave_de_etiqueta(texto):
    for clave, _n, _c, _f in PROPIEDADES:
        if etiqueta(clave) == texto:
            return clave
    return None


def verificar(clave, A, B, r):
    """Devuelve (lineas, cumple). cumple: True / False / None (informativa)."""
    return _POR_CLAVE[clave][2](A, B, r)


def verificar_todas(A, B, r):
    """
    Comprueba todas las propiedades posibles con los datos actuales. Las que
    no se pueden aplicar (dimensiones, falta una columna) se listan aparte
    con el motivo, sin detener a las demas.
    """
    cuerpo, resumen = [], []
    for clave, nombre, cat, f in PROPIEDADES:
        try:
            lineas, cumple = f(A, B, r)
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
