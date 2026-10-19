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

import textwrap

from core.fraccion import Fraccion
import core.algebra as alg
from core.formato import texto_matriz, ancho_columna, subindice

MENSAJE_SIN_PERMUTACION = ("La matriz no admite Factorización LU sin permutación "
                           "(requiere pivoteo parcial PA = LU)")
MENSAJE_FACTORIZACION_CORRECTA = "La factorización es correcta (L · U == A)"
MENSAJE_FACTORIZACION_INCORRECTA = "La factorización es incorrecta (L · U != A)"
MENSAJE_COMPROBACION_CORRECTA = "Comprobación exitosa: A · x == b"
MENSAJE_COMPROBACION_INCORRECTA = "La comprobación falló: A · x != b"
MENSAJE_SINGULAR = ("U tiene un cero en la diagonal: A es singular y el sistema no "
                    "tiene solución única, así que no se resuelve con L y U.")


# ---------------------------------------------------------------------------
# Utilidades de escritura
# ---------------------------------------------------------------------------

def _sub(n):
    """Subíndice Unicode de un número ya en base 1: 2 -> ₂."""
    return subindice(n)


def _fila(i):
    """Nombre de la fila i (base 0) en base 1, como en la presentación: 0 -> F1."""
    return "F" + str(i + 1)


def _mult(coef, nombre):
    """
    Escribe 'coef·nombre' como en clase: F1, −F1, 2F1 y (−3/2)·F1
    (las fracciones van entre paréntesis y el signo menos es el tipográfico).
    """
    if coef.es_uno():
        return nombre
    if (-coef).es_uno():
        return "−" + nombre
    if coef.den == 1:
        return str(coef).replace("-", "−") + nombre
    return "(" + str(coef).replace("-", "−") + ")·" + nombre


def _op_reemplazo(i, j, k):
    """
    Operación de reemplazo  F_i ← F_i + k·F_j  (la fila de la izquierda pasa a
    valer la expresión de la derecha). Si k es negativo se escribe como resta:
    F3 ← F3 − 2F1.
    """
    if k.es_negativo():
        signo = " − "
        magnitud = -k
    else:
        signo = " + "
        magnitud = k
    return "{} ← {}{}{}".format(_fila(i), _fila(i), signo, _mult(magnitud, _fila(j)))


def _op_escala(i, factor):
    """Operación de escalamiento  F_i ← factor·F_i."""
    return "{} ← {}".format(_fila(i), _mult(factor, _fila(i)))


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

def factorizar_lu(A, registro=None):
    """
    Obtiene A = L·U para una matriz de tamaño m×n (cuadrada o no) usando solo
    operaciones de reemplazo de filas, como en clase:
      - U (m×n) es una forma escalonada de A.
      - L (m×m) es triangular inferior con unos en la diagonal. La columna k de
        L son las entradas de la k-ésima columna pivote (de arriba hacia abajo)
        divididas entre el pivote.
    Si una columna no tiene pivote (todo lo que queda de ella es cero) se pasa a
    la siguiente columna; las columnas de L que no se usan quedan como las de la
    identidad. No escribe ningún procedimiento: si se pasa un diccionario vacío en
    `registro` se llena con lo ocurrido (pivotes, operaciones y matrices U) para
    que _procedimiento_factorizacion lo escriba.
    """
    m = len(A)
    n = len(A[0])

    U = [[A[i][j] for j in range(n)] for i in range(m)]
    L = [[Fraccion(1) if i == j else Fraccion(0) for j in range(m)] for i in range(m)]
    if registro is not None:
        registro["pivotes"] = []
        registro["sin_pivote"] = []

    fila = 0   # fila donde debería ir el siguiente pivote (= columna de L que se llena)
    for col in range(n):
        if fila >= m:
            break

        pivote = U[fila][col]
        if pivote.es_cero():
            # Sin pivote en esta columna si todo lo de abajo también es cero;
            # si no, haría falta intercambiar filas (y eso ya no es A = L·U).
            if any(not U[i][col].es_cero() for i in range(fila + 1, m)):
                raise ValueError(MENSAJE_SIN_PERMUTACION)
            if registro is not None:
                registro["sin_pivote"].append((col, fila))
            continue

        entradas = [U[i][col] for i in range(fila, m)]
        ops = []
        for i in range(fila + 1, m):
            if U[i][col].es_cero():
                continue
            factor = U[i][col] / pivote
            L[i][fila] = factor
            for c in range(col, n):
                U[i][c] = U[i][c] - factor * U[fila][c]
            ops.append((i, fila, factor))

        if registro is not None:
            registro["pivotes"].append({
                "col": col, "fila": fila, "pivote": pivote, "entradas": entradas,
                "ops": ops, "U": [list(f) for f in U]})

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


def _envolver(lineas, ancho=78):
    """
    Parte las líneas de texto corrido (viñetas y párrafos) para que quepan en la
    ventana; las matrices y las operaciones (que empiezan con corchete, espacios
    o paréntesis) quedan intactas. Las continuaciones se sangran bajo el texto.
    """
    salida = []
    for linea in lineas:
        resto = linea.lstrip("• ")
        if len(linea) <= ancho or not resto[:1].isalpha() or "[" in linea or "←" in linea:
            salida.append(linea)
            continue
        sangria = "  " if linea.startswith("•") else ""
        partes = textwrap.wrap(linea, width=ancho, subsequent_indent=sangria)
        salida += partes
    return salida


def _lista_y(items):
    """['1', '2', '4'] -> '1, 2 y 4'."""
    items = [str(t) for t in items]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


def _bloque_ops_matriz(ops, M):
    """Operaciones de una columna y la matriz (normal, sin barra) que resulta."""
    lineas = ["  Operaciones:"]
    for i, j, factor in ops:
        lineas.append("    " + _op_reemplazo(i, j, -factor))
    lineas.append(_texto_matriz(M, sangria="    "))
    lineas.append("")
    return lineas


def _columna_de_l(entradas, pivote, cocientes):
    """Una columna de L como en clase:  [2, -4, 2, -6] ÷ 2 → [1, -2, 1, -3]."""
    if len(entradas) == 1:
        return ["    {} ÷ {} → {}".format(entradas[0], pivote, cocientes[0])]
    texto = _lado_a_lado([("", [[v] for v in entradas], "  ÷ {}  →  ".format(pivote)),
                          ("", [[v] for v in cocientes], "")], sangria="    ")
    return texto.split("\n")[1:]    # se quita el renglón de rótulos vacío


def _procedimiento_factorizacion(A, L, U, registro):
    """
    Procedimiento de A = L·U en el orden de la presentación (Ejemplo 3):
      Paso 1  reducir A a U con reemplazos de fila,
      Paso 2  construir L dividiendo entre el pivote,
      Paso 3  las mismas operaciones reducen L a I.
    """
    m = len(A)
    pivotes = registro["pivotes"]
    con_ops = [r for r in pivotes if r["ops"]]
    lineas = []

    # ---- Paso 1: reducir A a U -------------------------------------------
    lineas.append("=== FACTORIZACIÓN, paso 1: reducir A a U ===")
    lineas.append("  Matriz A:")
    lineas.append(_texto_matriz(A, sangria="    "))
    lineas.append("")
    for r in con_ops:
        lineas += _bloque_ops_matriz(r["ops"], r["U"])
    if not con_ops:
        lineas.append("  No hay nada que anular: A ya es escalonada, así que U = A.")
        lineas.append("")
    if pivotes:
        lineas.append("• Columnas pivote de A: {} (pivotes {}).".format(
            _lista_y([r["col"] + 1 for r in pivotes]),
            _lista_y([r["pivote"] for r in pivotes])))
    else:
        lineas.append("• A no tiene columnas pivote (todas sus entradas son cero).")
    for col, fila in registro["sin_pivote"]:
        lineas.append("• La columna {} no tiene pivote: de la fila {} hacia abajo solo hay ceros."
                      .format(col + 1, fila + 1))
    lineas.append("• Solo hay reemplazos de fila hacia abajo, sin intercambios; "
                  "por eso existe A = L·U.")
    lineas.append("")

    # ---- Paso 2: construir L ----------------------------------------------
    lineas.append("=== FACTORIZACIÓN, paso 2: construir L ===")
    lineas.append("En cada columna pivote se dividen entre el pivote las entradas de esa "
                  "columna de U (del pivote hacia abajo, antes de anularlas); los cocientes "
                  "forman la columna de L.")
    lineas.append("")
    for r in pivotes:
        cocientes = [e / r["pivote"] for e in r["entradas"]]
        lineas.append("  Columna {} de L: pivote {} (col. {} de A)".format(
            r["fila"] + 1, r["pivote"], r["col"] + 1))
        lineas += _columna_de_l(r["entradas"], r["pivote"], cocientes)
        lineas.append("")
    rango = len(pivotes)
    if rango < m:
        if rango == m - 1:
            lineas.append("• La columna {} de L no tiene pivote: queda como la de la identidad."
                          .format(m))
        else:
            lineas.append("• Las columnas {} a {} de L no tienen pivote: quedan como las de la "
                          "identidad.".format(rango + 1, m))
        lineas.append("")
    lineas.append("  L ({0} × {0}):".format(m))
    lineas.append(_texto_matriz(L, sangria="    "))
    lineas.append("")
    lineas.append("• Sobre la diagonal van ceros y la diagonal son unos: L es triangular "
                  "inferior unitaria.")
    lineas.append("")

    # ---- Paso 3: las mismas operaciones reducen L a I ----------------------
    lineas.append("=== FACTORIZACIÓN, paso 3: las mismas operaciones reducen L a I ===")
    lineas.append("  Se parte de L:")
    lineas.append(_texto_matriz(L, sangria="    "))
    lineas.append("")
    M = [list(f) for f in L]
    for r in con_ops:
        for i, j, factor in r["ops"]:
            M[i] = [M[i][c] - factor * M[j][c] for c in range(m)]
        lineas += _bloque_ops_matriz(r["ops"], M)
    if not con_ops:
        lineas.append("  No hubo operaciones: L ya es la identidad I.")
        lineas.append("")
    lineas.append("• Aplicamos a L exactamente las mismas operaciones que redujeron A a U; "
                  "el resultado es la identidad I.")
    lineas.append("")
    return _envolver(lineas)


def _ejemplos_de_entradas(L, U):
    """
    Algunas entradas de L·U (fila de L por columna de U, sin los términos nulos),
    como en la comprobación de la presentación.
    """
    m = len(L)
    n = len(U[0])
    candidatas = [(m - 1, n - 1), (m - 2, 1), (1, n - 1)]
    elegidas = []
    for i, j in candidatas:
        if 1 <= i < m and 0 <= j < n and (i, j) not in elegidas:
            elegidas.append((i, j))
    if not elegidas:
        return []
    lineas = ["Ejemplos de entradas de L·U (fila de L por columna de U, sin los términos nulos):"]
    for i, j in elegidas:
        terminos = []
        total = Fraccion(0)
        for k in range(m):
            if L[i][k].es_cero() or U[k][j].es_cero():
                continue
            terminos.append("({})·({})".format(L[i][k], U[k][j]))
            total = total + L[i][k] * U[k][j]
        lineas.append("  Fila {}, col. {}: {} = {}".format(
            i + 1, j + 1, " + ".join(terminos) if terminos else "0", total))
    lineas.append("")
    return lineas


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

    Devuelve un diccionario: L, U, y, x, informe (texto), factorizacion_correcta,
    comprobacion_correcta (None si no hubo b) y valido (bool).
    """
    m = len(A)
    n = len(A[0])
    registro = {} if con_pasos else None
    L, U = factorizar_lu(A, registro)
    singular = False
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
        # Un cero en la diagonal de U significa que A es singular: se muestran
        # L y U, pero no se resuelve el sistema.
        if any(U[i][i].es_cero() for i in range(n)):
            singular = True
            b_plano = None

    lineas = []

    # ---- DATOS ----------------------------------------------------------
    lineas.append("=== DATOS: A = L·U" + (" y vector b" if b_plano is not None else "") + " ===")
    if singular:
        lineas.append(MENSAJE_SINGULAR)
    if not con_pasos:
        lineas.append("L y U se calculan automáticamente a partir de A.")
    if not cuadrada:
        lineas.append("A es {0}×{1}: L es {0}×{0} (triangular inferior con unos en la diagonal) "
                      "y U es {0}×{1} (forma escalonada).".format(m, n))
        lineas.append("Como A no es cuadrada solo se calcula la factorización A = L·U.")
    lineas.append("")
    if con_pasos:
        # El procedimiento llega hasta A = L·U: aquí solo se muestran los datos
        bloques = [("A", A, "  ,  " if b_plano is not None else "")]
    else:
        bloques = [("A", A, " = "), ("L", L, " · "),
                   ("U", U, "  ,  " if b_plano is not None else "")]
    if b_plano is not None:
        bloques.append(("b", [[v] for v in b_plano], ""))
    lineas.append(_lado_a_lado(bloques))
    lineas.append("")

    if con_pasos:
        lineas.append("• A tiene m = {} filas y n = {} columnas.".format(m, n))
        lineas.append("• L será cuadrada, de {0} × {0}: triangular inferior con unos en la "
                      "diagonal.".format(m))
        lineas.append("• U será de {} × {}: una forma escalonada de A.".format(m, n))
        lineas += _envolver(["• Solo se usan reemplazos de fila (sumar un múltiplo de una fila a "
                             "otra de abajo), sin intercambios."])
        lineas.append("")
        lineas.append("Plan de factorización:")
        lineas.append("  1) Reducir A a U con reemplazos de fila.")
        lineas.append("  2) Construir L: en cada columna pivote, dividir entre el pivote.")
        lineas.append("  3) Comprobar que L·U = A.")
        lineas.append("")
        lineas += _procedimiento_factorizacion(A, L, U, registro)
        lineas.append("  Resultado de la factorización:")
        lineas.append(_lado_a_lado([("A", A, " = "), ("L", L, " · "), ("U", U, "")],
                                   sangria="    "))
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
    lineas.append("  " + (MENSAJE_FACTORIZACION_CORRECTA if lu_ok
                          else MENSAJE_FACTORIZACION_INCORRECTA))
    lineas.append("")
    if con_pasos:
        lineas += _envolver(_ejemplos_de_entradas(L, U))
        if b_plano is None:
            lineas += _envolver(["• Aquí no hay vector b (o A no es cuadrada), por lo que no se "
                                 "calculan y ni x. Con un b dado se resuelven Ly = b y Ux = y "
                                 "con Gauss-Jordan."])
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
        lineas.append("  " + (MENSAJE_COMPROBACION_CORRECTA if ax_ok
                              else MENSAJE_COMPROBACION_INCORRECTA))
        lineas.append("")

    return {
        "L": L,
        "U": U,
        "y": y,
        "x": x,
        "informe": "\n".join(lineas),
        "factorizacion_correcta": lu_ok,
        "comprobacion_correcta": (ax_ok if b_plano is not None else None),
        "valido": lu_ok and ax_ok
    }