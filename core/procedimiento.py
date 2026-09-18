# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/procedimiento.py
#  Paso a paso de las operaciones con matrices y vectores.
#
#  core/algebra.py CALCULA; este modulo EXPLICA. Recorre las mismas
#  posiciones que recorren los bucles del calculo y escribe, entrada por
#  entrada, la formula general, la sustitucion de los valores y el resultado.
#  Ninguna funcion imprime: todas devuelven listas de lineas de texto.
#
#  El producto A.x se explica con los DOS procedimientos vistos en clase:
#      1) Ax como combinacion lineal de las columnas de A
#                Ax = x1.a1 + x2.a2 + ... + xn.an
#      2) Regla fila-vector: la entrada i de Ax es la suma de los productos
#         de la fila i de A por las entradas de x.
# =============================================================================

from core.formato import subindice, ancho_columna
import core.algebra as algebra


# ---------------------------------------------------------------------------
# Utilidades de escritura
# ---------------------------------------------------------------------------

def _ind(i, j):
    """
    Subindice de fila y columna en base 1: (0, 0) -> el par de digitos 11.

    Cuando algun indice tiene dos digitos se separa con coma para que no se
    confunda "fila 1 columna 12" con "fila 11 columna 2".
    """
    f = subindice(i + 1)
    c = subindice(j + 1)
    if i + 1 > 9 or j + 1 > 9:
        return f + "," + c
    return f + c


def _sub(i):
    """Subindice simple en base 1: 0 -> el digito 1 en subindice."""
    return subindice(i + 1)


def _valor(v):
    """Encierra el valor entre parentesis si es negativo, para que se lea bien."""
    texto = str(v)
    if texto.startswith("-"):
        return "(" + texto + ")"
    return texto


def _encabezado(titulo, regla, nota=None):
    """Bloque inicial comun: nombre de la operacion y regla algebraica."""
    lineas = [titulo, ""]
    lineas.append("  Regla:  " + regla)
    if nota is not None:
        lineas.append("  " + nota)
    lineas.append("")
    return lineas


def _vector_en_linea(v):
    """Escribe un vector columna en una sola linea: [ 1, 2, 3 ]^T."""
    return "[ " + ", ".join(str(componente) for componente in v) + " ]^T"


# ---------------------------------------------------------------------------
# Suma y resta de matrices
# ---------------------------------------------------------------------------

def pasos_suma(A, B, resta=False):
    """
    Explica la suma (o la resta) entrada por entrada.

    Procedimiento algebraico: la suma de matrices es una operacion ENTRADA A
    ENTRADA, definida solo si ambas tienen el mismo tamano m x n. Los dos
    bucles anidados (i sobre las filas, j sobre las columnas) visitan cada
    posicion una sola vez; no hay acumulacion como si la hay en el producto.
    """
    signo = "-" if resta else "+"
    nombre = "RESTA A - B" if resta else "SUMA A + B"

    lineas = _encabezado(
        "PASO A PASO - " + nombre,
        "cᵢⱼ = aᵢⱼ {} bᵢⱼ   para cada posicion (i, j)".format(signo),
        "Requisito: A y B deben tener el mismo tamano. Aqui ambas son {}x{}.".format(
            len(A), len(A[0])))

    for i in range(len(A)):
        lineas.append("  Fila {}:".format(i + 1))
        for j in range(len(A[0])):
            a = A[i][j]
            b = B[i][j]
            c = a - b if resta else a + b
            lineas.append("    c{ij} = a{ij} {s} b{ij} = {va} {s} {vb} = {vc}".format(
                ij=_ind(i, j), s=signo,
                va=_valor(a), vb=_valor(b), vc=str(c)))
        lineas.append("")

    return lineas


# ---------------------------------------------------------------------------
# Producto por un escalar
# ---------------------------------------------------------------------------

def pasos_escalar(r, A):
    """
    Explica el producto de un escalar por una matriz.

    Procedimiento algebraico: el escalar multiplica a TODAS las entradas. El
    tamano no cambia y no existe ninguna restriccion de dimensiones.
    """
    lineas = _encabezado(
        "PASO A PASO - PRODUCTO POR EL ESCALAR r = {}".format(r),
        "(r·A)ᵢⱼ = r · aᵢⱼ   para cada posicion (i, j)",
        "El escalar multiplica a cada entrada; el tamano {}x{} se conserva.".format(
            len(A), len(A[0])))

    for i in range(len(A)):
        lineas.append("  Fila {}:".format(i + 1))
        for j in range(len(A[0])):
            a = A[i][j]
            lineas.append("    c{ij} = r · a{ij} = {vr} · {va} = {vc}".format(
                ij=_ind(i, j), vr=_valor(r), va=_valor(a), vc=str(a * r)))
        lineas.append("")

    return lineas


# ---------------------------------------------------------------------------
# Producto de matrices
# ---------------------------------------------------------------------------

def pasos_multiplicacion(A, B):
    """
    Explica el producto A(m x n) . B(n x p) termino por termino.

    Procedimiento algebraico: cada entrada del resultado es el producto punto
    entre una FILA de A y una COLUMNA de B. De ahi salen los tres bucles
    anidados:

        i  (1..m)  elige la fila de A      -> fila del resultado
        j  (1..p)  elige la columna de B   -> columna del resultado
        k  (1..n)  recorre los n productos que se acumulan en esa entrada

    El bucle k es el que obliga a que las columnas de A (n) coincidan con las
    filas de B (n): es el indice que comparten ambas matrices.

    Cuando B tiene una sola columna el producto es A.x, y se anaden las dos
    lecturas vistas en clase: combinacion lineal de las columnas de A y regla
    fila-vector.
    """
    m = len(A)
    n = len(A[0])
    p = len(B[0])

    lineas = _encabezado(
        "PASO A PASO - PRODUCTO A × B",
        "cᵢⱼ = aᵢ₁·b₁ⱼ + aᵢ₂·b₂ⱼ + ... + aᵢₙ·bₙⱼ   "
        "(fila i de A por columna j de B)",
        "A es {}x{} y B es {}x{}: las {} columnas de A coinciden con las {} "
        "filas de B, asi que el resultado es {}x{}.".format(m, n, n, p, n, n, m, p))

    lineas.append("  Los bucles anidados recorren i = 1..{} (filas de A) y "
                  "j = 1..{} (columnas de B);".format(m, p))
    lineas.append("  para cada par (i, j) el bucle k = 1..{} acumula los {} "
                  "productos.".format(n, n))
    lineas.append("")

    for i in range(m):
        for j in range(p):
            lineas.append("  c{}  <-  fila {} de A · columna {} de B".format(
                _ind(i, j), i + 1, j + 1))

            # Formula general, con los nombres de las entradas
            nombres = ["a{}·b{}".format(_ind(i, k), _ind(k, j)) for k in range(n)]
            lineas.append("     = " + " + ".join(nombres))

            # Sustitucion de los valores
            valores = ["{}·{}".format(_valor(A[i][k]), _valor(B[k][j]))
                       for k in range(n)]
            lineas.append("     = " + " + ".join(valores))

            # Cada producto ya resuelto y, por ultimo, la suma acumulada
            productos = [A[i][k] * B[k][j] for k in range(n)]
            if n > 1:
                lineas.append("     = " + " + ".join(_valor(v) for v in productos))

            total = productos[0]
            for k in range(1, n):
                total = total + productos[k]
            lineas.append("     = " + str(total))
            lineas.append("")

    # Si B es un vector columna, el producto es A.x: se anaden las dos
    # lecturas que se usan en clase para ese caso particular.
    if p == 1:
        x = [B[k][0] for k in range(n)]
        lineas.append("")
        lineas.extend(pasos_columnas(A, x))
        lineas.append("")
        lineas.extend(pasos_fila_vector(A, x))

    return lineas


def pasos_columnas(A, x):
    """
    Explica A.x como COMBINACION LINEAL DE LAS COLUMNAS de A:

        A.x = x1.a1 + x2.a2 + ... + xn.an

    Esta es la definicion de la ecuacion matricial: el producto A.x pesa cada
    columna de A con la entrada correspondiente de x. Es la lectura que
    convierte el sistema en una pregunta sobre combinaciones lineales.
    """
    m = len(A)
    n = len(A[0])

    lineas = _encabezado(
        "A·x COMO COMBINACION LINEAL DE LAS COLUMNAS DE A",
        "A·x = x₁·a₁ + x₂·a₂ + ... + xₙ·aₙ",
        "Cada columna aₖ de A se multiplica por la entrada xₖ y se suman los "
        "n vectores resultantes.")

    # Las columnas de A, una por una
    for k in range(n):
        columna = [A[i][k] for i in range(m)]
        lineas.append("    a{} = {}    (columna {} de A)".format(
            _sub(k), _vector_en_linea(columna), k + 1))
    lineas.append("")

    # La combinacion escrita con los pesos
    terminos = ["{}·a{}".format(_valor(x[k]), _sub(k)) for k in range(n)]
    lineas.append("    A·x = " + " + ".join(terminos))
    lineas.append("")

    # Cada vector ya multiplicado por su peso
    escalados = []
    for k in range(n):
        columna = [A[i][k] for i in range(m)]
        escalado = [componente * x[k] for componente in columna]
        escalados.append(escalado)
        lineas.append("    {}·a{} = {}".format(
            _valor(x[k]), _sub(k), _vector_en_linea(escalado)))
    lineas.append("")

    # La suma componente a componente
    for i in range(m):
        sumandos = " + ".join(_valor(escalados[k][i]) for k in range(n))
        total = escalados[0][i]
        for k in range(1, n):
            total = total + escalados[k][i]
        lineas.append("    componente {}:  {} = {}".format(i + 1, sumandos, total))
    lineas.append("")

    resultado = []
    for i in range(m):
        total = escalados[0][i]
        for k in range(1, n):
            total = total + escalados[k][i]
        resultado.append(total)
    lineas.append("    A·x = " + _vector_en_linea(resultado))
    lineas.append("")

    return lineas


def pasos_fila_vector(A, x):
    """
    Explica A.x con la REGLA FILA-VECTOR.

    Si el producto A.x esta definido, la entrada i de A.x es la suma de los
    productos de las entradas de la fila i de A por las entradas de x. Da el
    mismo resultado que la combinacion lineal de columnas, pero se calcula
    fila por fila en lugar de columna por columna.
    """
    m = len(A)
    n = len(A[0])

    lineas = _encabezado(
        "A·x CON LA REGLA FILA-VECTOR",
        "(A·x)ᵢ = aᵢ₁·x₁ + aᵢ₂·x₂ + ... + aᵢₙ·xₙ",
        "La entrada i del resultado usa unicamente la fila i de A.")

    for i in range(m):
        fila = [A[i][k] for k in range(n)]
        lineas.append("    fila {} de A = [ {} ]".format(
            i + 1, ", ".join(str(v) for v in fila)))

        nombres = ["a{}·x{}".format(_ind(i, k), _sub(k)) for k in range(n)]
        lineas.append("      (A·x){} = {}".format(_sub(i), " + ".join(nombres)))

        valores = ["{}·{}".format(_valor(A[i][k]), _valor(x[k])) for k in range(n)]
        lineas.append("            = " + " + ".join(valores))

        productos = [A[i][k] * x[k] for k in range(n)]
        total = productos[0]
        for k in range(1, n):
            total = total + productos[k]
        if n > 1:
            lineas.append("            = " + " + ".join(_valor(v) for v in productos))
        lineas.append("            = " + str(total))
        lineas.append("")

    return lineas


# ---------------------------------------------------------------------------
# Transpuesta
# ---------------------------------------------------------------------------

def pasos_transpuesta(A):
    """
    Explica la transposicion.

    Procedimiento algebraico: la entrada que estaba en la fila i, columna j
    pasa a la fila j, columna i. En la practica cada FILA de A se escribe como
    COLUMNA de A^T, de modo que una matriz m x n se convierte en una n x m.
    """
    m = len(A)
    n = len(A[0])

    lineas = _encabezado(
        "PASO A PASO - TRANSPUESTA A^T",
        "(A^T)ⱼᵢ = aᵢⱼ   (se intercambian los indices)",
        "A es {}x{}, por lo tanto A^T es {}x{}.".format(m, n, n, m))

    for i in range(m):
        fila = ", ".join(str(v) for v in A[i])
        lineas.append("    fila {} de A = [ {} ]  ->  columna {} de A^T".format(
            i + 1, fila, i + 1))
    lineas.append("")

    for i in range(m):
        for j in range(n):
            lineas.append("      (A^T){} = a{} = {}".format(
                _ind(j, i), _ind(i, j), str(A[i][j])))
    lineas.append("")

    return lineas


# ---------------------------------------------------------------------------
# Propiedades del producto matriz-vector
# ---------------------------------------------------------------------------

def pasos_propiedad_suma(A, u, v):
    """
    Comprueba la propiedad  A(u + v) = A.u + A.v  con los datos dados.

    Procedimiento: se calculan los dos lados por separado y se comparan
    componente a componente. El lado izquierdo suma primero los vectores y
    multiplica una sola vez; el derecho multiplica dos veces y suma despues.
    """
    from core.vector import como_columna, desde_columna, sumar_vectores

    lineas = _encabezado(
        "PROPIEDAD:  A(u + v) = A·u + A·v",
        "El producto matriz-vector distribuye sobre la suma de vectores.",
        "u = {}   v = {}".format(_vector_en_linea(u), _vector_en_linea(v)))

    # Lado izquierdo: primero se suma, despues se multiplica
    suma = sumar_vectores(u, v)
    lineas.append("  LADO IZQUIERDO   A(u + v)")
    lineas.append("")
    lineas.append("    u + v = {}".format(_vector_en_linea(suma)))
    izquierdo = desde_columna(algebra.multiplicar_matrices(A, como_columna(suma)))
    lineas.extend("  " + linea for linea in pasos_fila_vector(A, suma))
    lineas.append("    A(u + v) = {}".format(_vector_en_linea(izquierdo)))
    lineas.append("")

    # Lado derecho: primero se multiplica cada uno, despues se suman
    Au = desde_columna(algebra.multiplicar_matrices(A, como_columna(u)))
    Av = desde_columna(algebra.multiplicar_matrices(A, como_columna(v)))
    derecho = sumar_vectores(Au, Av)

    lineas.append("  LADO DERECHO   A·u + A·v")
    lineas.append("")
    lineas.append("    A·u = {}".format(_vector_en_linea(Au)))
    lineas.append("    A·v = {}".format(_vector_en_linea(Av)))
    lineas.append("")
    for i in range(len(Au)):
        lineas.append("    componente {}:  {} + {} = {}".format(
            i + 1, _valor(Au[i]), _valor(Av[i]), derecho[i]))
    lineas.append("")
    lineas.append("    A·u + A·v = {}".format(_vector_en_linea(derecho)))
    lineas.append("")

    lineas.extend(_comparar(izquierdo, derecho,
                            "A(u + v)", "A·u + A·v"))
    return lineas


def pasos_propiedad_escalar(A, c, u):
    """
    Comprueba la propiedad  A(c.u) = c(A.u)  con los datos dados.

    Procedimiento: da lo mismo escalar el vector antes de multiplicar por A
    que multiplicar primero y escalar el resultado.
    """
    from core.vector import como_columna, desde_columna, escalar_por_vector

    lineas = _encabezado(
        "PROPIEDAD:  A(c·u) = c(A·u)",
        "El escalar puede aplicarse antes o despues de multiplicar por A.",
        "c = {}   u = {}".format(c, _vector_en_linea(u)))

    # Lado izquierdo: primero se escala el vector
    cu = escalar_por_vector(c, u)
    lineas.append("  LADO IZQUIERDO   A(c·u)")
    lineas.append("")
    lineas.append("    c·u = {}".format(_vector_en_linea(cu)))
    izquierdo = desde_columna(algebra.multiplicar_matrices(A, como_columna(cu)))
    lineas.append("    A(c·u) = {}".format(_vector_en_linea(izquierdo)))
    lineas.append("")

    # Lado derecho: primero se multiplica por A
    Au = desde_columna(algebra.multiplicar_matrices(A, como_columna(u)))
    derecho = escalar_por_vector(c, Au)
    lineas.append("  LADO DERECHO   c(A·u)")
    lineas.append("")
    lineas.append("    A·u = {}".format(_vector_en_linea(Au)))
    for i in range(len(Au)):
        lineas.append("    componente {}:  {} · {} = {}".format(
            i + 1, _valor(c), _valor(Au[i]), derecho[i]))
    lineas.append("    c(A·u) = {}".format(_vector_en_linea(derecho)))
    lineas.append("")

    lineas.extend(_comparar(izquierdo, derecho, "A(c·u)", "c(A·u)"))
    return lineas


def _comparar(izquierdo, derecho, nombre_izq, nombre_der):
    """Compara los dos lados componente a componente y concluye."""
    lineas = ["  COMPARACION", ""]
    iguales = True
    for i in range(len(izquierdo)):
        coincide = izquierdo[i] == derecho[i]
        if not coincide:
            iguales = False
        lineas.append("    componente {}:  {}  {}  {}".format(
            i + 1, izquierdo[i], "=" if coincide else "≠", derecho[i]))
    lineas.append("")
    if iguales:
        lineas.append("    [CUMPLE] {} = {}: la propiedad se verifica.".format(
            nombre_izq, nombre_der))
    else:
        lineas.append("    [FALLA] Los dos lados no coinciden.")
    lineas.append("")
    return lineas


# ---------------------------------------------------------------------------
# Resultado final
# ---------------------------------------------------------------------------

def texto_resultado(titulo, M):
    """Escribe la matriz resultado con las columnas alineadas."""
    ancho = ancho_columna(M)
    lineas = [titulo]
    for fila in M:
        valores = "   ".join("{:>{a}}".format(str(v), a=ancho) for v in fila)
        lineas.append("  [ " + valores + " ]")
    return lineas
