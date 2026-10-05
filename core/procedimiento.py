# -*- coding: utf-8 -*-
"""
Paso a paso de las operaciones con matrices y vectores para el Proyecto Integrador.
core/algebra.py CALCULA; este módulo EXPLICA. Recorre las mismas posiciones que
los bucles del cálculo y escribe fórmula, sustitución y resultado por cada entrada.
Ninguna función imprime: todas devuelven listas de líneas de texto.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

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
# Determinante por expansión de cofactores
# ---------------------------------------------------------------------------

def pasos_determinante_cofactores(A):
    """Expansión de la primera fila: muestra cada submatriz, cofactor y contribución."""
    from modulos.modulo_matrices import submatriz, determinante
    from core.fraccion import Fraccion
    n = len(A)

    lineas = _encabezado(
        "PASO A PASO - det(A) POR EXPANSIÓN DE COFACTORES (primera fila)",
        "det(A) = a₁₁C₁₁ + a₁₂C₁₂ + ... + a₁ₙC₁ₙ   donde  Cᵢⱼ = (-1)^(i+j) · Mᵢⱼ",
        "Se expande por la primera fila (i = 1). A es {}×{}.".format(n, n))

    if n == 1:
        lineas.append("  Para 1×1: det([a]) = a = {}".format(str(A[0][0])))
        lineas.append("")
        return lineas

    terms = []
    for j in range(n):
        signo_f = Fraccion(1) if j % 2 == 0 else Fraccion(-1)
        sig_str = "+" if j % 2 == 0 else "-"
        a1j = A[0][j]
        Sub = submatriz(A, 0, j)
        det_sub = determinante(Sub)
        contrib = signo_f * a1j * det_sub
        terms.append(contrib)

        lineas.append("  ── Cofactor C₁{} (j = {}):".format(j + 1, j + 1))
        lineas.append("     signo  = (-1)^(1+{}) = {}1".format(j + 1, sig_str))
        lineas.append("     a₁{}  = {}".format(j + 1, str(a1j)))
        lineas.append("     Submatriz M₁{} (sin fila 1, sin columna {}):".format(
            j + 1, j + 1))
        for fila_s in Sub:
            lineas.append("       [ {} ]".format("   ".join(str(v) for v in fila_s)))
        lineas.append("     det(M₁{}) = {}".format(j + 1, str(det_sub)))
        cof_ij = signo_f * det_sub
        lineas.append("     C₁{} = {} · {} = {}".format(
            j + 1, sig_str, _valor(det_sub), str(cof_ij)))
        lineas.append("     Contribución: a₁{} · C₁{} = {} · {} = {}".format(
            j + 1, j + 1, _valor(a1j), _valor(cof_ij), str(contrib)))
        lineas.append("")

    total = terms[0]
    for k in range(1, n):
        total = total + terms[k]
    lineas.append("  det(A) = {}".format(" + ".join(_valor(t) for t in terms)))
    lineas.append("       = {}".format(str(total)))
    lineas.append("")
    return lineas


# ---------------------------------------------------------------------------
# Determinante por Sarrus (solo 3×3)
# ---------------------------------------------------------------------------

def pasos_determinante_sarrus(A):
    """Regla de Sarrus: 3 diagonales positivas y 3 negativas para matrices 3×3."""
    lineas = _encabezado(
        "PASO A PASO - det(A) POR LA REGLA DE SARRUS (3×3)",
        "det = (a11a22a33 + a12a23a31 + a13a21a32)"
        " - (a31a22a13 + a32a23a11 + a33a21a12)",
        "Solo válida para matrices 3×3.")

    lineas.append("  Matriz A:")
    for fila in A:
        lineas.append("  [ {} ]".format("   ".join(str(v) for v in fila)))
    lineas.append("")

    p1 = A[0][0] * A[1][1] * A[2][2]
    p2 = A[0][1] * A[1][2] * A[2][0]
    p3 = A[0][2] * A[1][0] * A[2][1]
    n1 = A[2][0] * A[1][1] * A[0][2]
    n2 = A[2][1] * A[1][2] * A[0][0]
    n3 = A[2][2] * A[1][0] * A[0][1]

    lineas.append("  Diagonales positivas (↘):")
    lineas.append("    d₊₁ = a₁₁·a₂₂·a₃₃ = {}·{}·{} = {}".format(
        _valor(A[0][0]), _valor(A[1][1]), _valor(A[2][2]), str(p1)))
    lineas.append("    d₊₂ = a₁₂·a₂₃·a₃₁ = {}·{}·{} = {}".format(
        _valor(A[0][1]), _valor(A[1][2]), _valor(A[2][0]), str(p2)))
    lineas.append("    d₊₃ = a₁₃·a₂₁·a₃₂ = {}·{}·{} = {}".format(
        _valor(A[0][2]), _valor(A[1][0]), _valor(A[2][1]), str(p3)))
    lineas.append("")
    lineas.append("  Diagonales negativas (↗):")
    lineas.append("    d₋₁ = a₃₁·a₂₂·a₁₃ = {}·{}·{} = {}".format(
        _valor(A[2][0]), _valor(A[1][1]), _valor(A[0][2]), str(n1)))
    lineas.append("    d₋₂ = a₃₂·a₂₃·a₁₁ = {}·{}·{} = {}".format(
        _valor(A[2][1]), _valor(A[1][2]), _valor(A[0][0]), str(n2)))
    lineas.append("    d₋₃ = a₃₃·a₂₁·a₁₂ = {}·{}·{} = {}".format(
        _valor(A[2][2]), _valor(A[1][0]), _valor(A[0][1]), str(n3)))
    lineas.append("")

    pos = p1 + p2 + p3
    neg = n1 + n2 + n3
    resultado = pos - neg
    lineas.append("  Suma positiva:  {} + {} + {} = {}".format(
        _valor(p1), _valor(p2), _valor(p3), str(pos)))
    lineas.append("  Suma negativa:  {} + {} + {} = {}".format(
        _valor(n1), _valor(n2), _valor(n3), str(neg)))
    lineas.append("  det(A) = {} - {} = {}".format(
        _valor(pos), _valor(neg), str(resultado)))
    lineas.append("")
    return lineas


# ---------------------------------------------------------------------------
# Determinante por reducción triangular
# ---------------------------------------------------------------------------

def pasos_determinante_triangular(A):
    """Reducción a triangular superior: muestra cada intercambio y eliminación de fila."""
    from core.fraccion import Fraccion
    n = len(A)

    lineas = _encabezado(
        "PASO A PASO - det(A) POR REDUCCIÓN TRIANGULAR",
        "Se reduce A a triangular superior. det = signo · a₁₁·a₂₂·····aₙₙ",
        "Cada intercambio invierte el signo; las eliminaciones no cambian det.")

    if n == 1:
        lineas.append("  Para 1×1: det = {}".format(str(A[0][0])))
        lineas.append("")
        return lineas

    M = [[A[i][j] for j in range(n)] for i in range(n)]
    signo = Fraccion(1)
    paso = [0]

    def mostrar(lineas, M):
        for fila in M:
            lineas.append("  [ {} ]".format("   ".join(str(v) for v in fila)))
        lineas.append("")

    lineas.append("  Matriz inicial:")
    mostrar(lineas, M)

    for col in range(n):
        pivote_fila = next(
            (f for f in range(col, n) if not M[f][col].es_cero()), None)

        if pivote_fila is None:
            lineas.append("  Columna {}: todos los valores son cero → det(A) = 0".format(
                col + 1))
            lineas.append("")
            return lineas

        if pivote_fila != col:
            paso[0] += 1
            lineas.append("  Paso {}: Intercambio F{} ↔ F{}  (el signo se invierte)".format(
                paso[0], col + 1, pivote_fila + 1))
            M[col], M[pivote_fila] = M[pivote_fila], M[col]
            signo = signo * Fraccion(-1)
            mostrar(lineas, M)

        for fila in range(col + 1, n):
            if not M[fila][col].es_cero():
                factor = M[fila][col] / M[col][col]
                paso[0] += 1
                lineas.append("  Paso {}: F{} ← F{} − ({}) · F{}".format(
                    paso[0], fila + 1, fila + 1, str(factor), col + 1))
                for k in range(col, n):
                    M[fila][k] = M[fila][k] - factor * M[col][k]
                mostrar(lineas, M)

    diag = [M[i][i] for i in range(n)]
    lineas.append("  Matriz triangular superior final:")
    mostrar(lineas, M)
    lineas.append("  Diagonal: {}".format(
        " · ".join(str(d) for d in diag)))

    producto = diag[0]
    for k in range(1, n):
        producto = producto * diag[k]

    sig_str = "+1" if not str(signo).startswith("-") else "−1"
    resultado = signo * producto
    lineas.append("  det(A) = signo * prod. diagonal = {} * {} = {}".format(
        sig_str, str(producto), str(resultado)))
    lineas.append("")
    return lineas


# ---------------------------------------------------------------------------
# Inversa por Gauss-Jordan
# ---------------------------------------------------------------------------

def pasos_inversa_gauss_jordan(A):
    """[A|I] → [I|A⁻¹] con Gauss-Jordan: muestra cada operación elemental de fila."""
    from core.fraccion import Fraccion
    from core.formato import ancho_columna
    n = len(A)

    lineas = _encabezado(
        "PASO A PASO - A⁻¹ POR GAUSS-JORDAN",
        "Se construye [A | I] y se aplica Gauss-Jordan hasta obtener [I | A⁻¹].",
        "Cada op. elemental aplicada a la derecha transforma I en A⁻¹.")

    cer = Fraccion(0)
    uno = Fraccion(1)
    M = [
        [A[i][j] for j in range(n)] + [uno if i == k else cer for k in range(n)]
        for i in range(n)
    ]

    def mostrar_aug(lineas, M):
        ancho = max(len(str(M[i][j])) for i in range(n) for j in range(2 * n))
        ancho = max(ancho, 1)
        for i in range(n):
            izq = "   ".join("{:>{a}}".format(str(M[i][j]), a=ancho) for j in range(n))
            der = "   ".join("{:>{a}}".format(str(M[i][n+j]), a=ancho) for j in range(n))
            lineas.append("  [ {} | {} ]".format(izq, der))
        lineas.append("")

    lineas.append("  Matriz aumentada inicial  [A | I]:")
    mostrar_aug(lineas, M)

    paso = 0
    for col in range(n):
        pivote = next(
            (f for f in range(col, n) if not M[f][col].es_cero()), None)

        if pivote is None:
            lineas.append("  Sin pivote en columna {} → A es singular.".format(col + 1))
            return lineas

        if pivote != col:
            paso += 1
            lineas.append("  Paso {}: F{} ↔ F{}".format(
                paso, col + 1, pivote + 1))
            M[col], M[pivote] = M[pivote], M[col]
            mostrar_aug(lineas, M)

        p = M[col][col]
        if not p.es_uno():
            paso += 1
            lineas.append("  Paso {}: F{} ← F{} / {}   (pivote → 1)".format(
                paso, col + 1, col + 1, str(p)))
            M[col] = [v / p for v in M[col]]
            mostrar_aug(lineas, M)

        for fila in range(n):
            if fila != col and not M[fila][col].es_cero():
                factor = M[fila][col]
                paso += 1
                lineas.append("  Paso {}: F{} ← F{} − {} · F{}".format(
                    paso, fila + 1, fila + 1, str(factor), col + 1))
                M[fila] = [M[fila][k] - factor * M[col][k]
                           for k in range(2 * n)]
                mostrar_aug(lineas, M)

    A_inv = [[M[i][n + j] for j in range(n)] for i in range(n)]
    lineas.append("  Resultado final  [I | A⁻¹]:")
    mostrar_aug(lineas, M)
    return lineas


# ---------------------------------------------------------------------------
# Inversa por la fórmula de la adjunta
# ---------------------------------------------------------------------------

def pasos_inversa_adjunta(A):
    """A⁻¹ = (1/det(A))·adj(A): muestra cada cofactor, la adjunta y la fórmula final."""
    from modulos.modulo_matrices import submatriz, determinante
    from core.fraccion import Fraccion
    import core.algebra as alg_local
    n = len(A)

    lineas = _encabezado(
        "PASO A PASO - A⁻¹ POR LA FÓRMULA DE LA ADJUNTA",
        "A⁻¹ = (1/det(A)) · adj(A)   donde   adj(A) = (matriz de cofactores)ᵀ",
        "Cᵢⱼ = (-1)^(i+j) · det(Mᵢⱼ)   con Mᵢⱼ = submatriz sin fila i y columna j.")

    if n == 1:
        lineas.append("  Para 1×1: A⁻¹ = [[1/{}]] = [[{}]]".format(
            str(A[0][0]), str(Fraccion(1) / A[0][0])))
        lineas.append("")
        return lineas

    det = determinante(A)
    lineas.append("  det(A) = {}".format(str(det)))
    lineas.append("")

    C = []
    lineas.append("  ── Matriz de cofactores C (entrada a entrada):")
    lineas.append("")
    for i in range(n):
        fila_c = []
        for j in range(n):
            signo_f = Fraccion(1) if (i + j) % 2 == 0 else Fraccion(-1)
            sig_str = "+" if (i + j) % 2 == 0 else "-"
            Sub = submatriz(A, i, j)
            det_sub = determinante(Sub)
            c_ij = signo_f * det_sub
            fila_c.append(c_ij)
            lineas.append("    C{} = (-1)^({}+{}) · det(M{}) = {} · {} = {}".format(
                _ind(i, j), i + 1, j + 1, _ind(i, j),
                sig_str, _valor(det_sub), str(c_ij)))
            lineas.append("    Submatriz M{}:".format(_ind(i, j)))
            for fila_s in Sub:
                lineas.append("      [ {} ]".format("   ".join(str(v) for v in fila_s)))
            lineas.append("")
        C.append(fila_c)

    lineas.extend(texto_resultado("  Matriz de cofactores  C =", C))
    lineas.append("")

    adj = alg_local.transponer(C)
    lineas.extend(texto_resultado("  adj(A) = Cᵀ =", adj))
    lineas.append("")

    inv = alg_local.multiplicar_escalar(Fraccion(1) / det, adj)
    lineas.append("  A⁻¹ = (1/{}) · adj(A)".format(str(det)))
    lineas.extend(texto_resultado("     =", inv))
    lineas.append("")
    return lineas


# ---------------------------------------------------------------------------
# Regla de Cramer
# ---------------------------------------------------------------------------

def pasos_cramer(A, b):
    """Cramer: muestra det(A), cada Aᵢ con su det y la fórmula xᵢ = det(Aᵢ)/det(A)."""
    from modulos.modulo_matrices import determinante
    from core.fraccion import Fraccion
    n = len(A)

    lineas = _encabezado(
        "PASO A PASO - REGLA DE CRAMER",
        "xᵢ = det(Aᵢ) / det(A)   donde Aᵢ = A con columna i reemplazada por b.",
        "A es {}×{}; b tiene {} componentes.".format(n, n, n))

    det_A = determinante(A)
    lineas.append("  det(A) = {}".format(str(det_A)))
    lineas.append("")

    sol = []
    for i in range(n):
        Ai = [[A[fila][col] if col != i else b[fila]
               for col in range(n)]
              for fila in range(n)]
        det_Ai = determinante(Ai)
        xi = det_Ai / det_A
        sol.append(xi)

        lineas.append("  ── Variable x{}:".format(i + 1))
        lineas.append("     A{} (columna {} reemplazada por b):".format(
            i + 1, i + 1))
        for fila in Ai:
            lineas.append("     [ {} ]".format("   ".join(str(v) for v in fila)))
        lineas.append("     det(A{}) = {}".format(i + 1, str(det_Ai)))
        lineas.append("     x{} = det(A{}) / det(A) = {} / {} = {}".format(
            i + 1, i + 1, _valor(det_Ai), _valor(det_A), str(xi)))
        lineas.append("")

    sol_mat = [[v] for v in sol]
    lineas.extend(texto_resultado("  Solución  x =", sol_mat))
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
