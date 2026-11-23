# -*- coding: utf-8 -*-
"""
Formas escalonadas: verifica si una matriz m×n cualquiera está en forma escalonada (REF)
o escalonada reducida (RREF) diciendo qué condición falla, y la reduce a REF o RREF con el paso
a paso, sin necesidad de una columna b. Todo con fracciones exactas.
Unidad: Proyecto Integrador (Forma escalonada).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
from core.matriz import copiar
from solver.eliminacion import escalonar, reducir_jordan


def _texto(M, sangria="  "):
    """Matriz m×n entre corchetes, columnas alineadas."""
    ancho = max(len(str(v)) for fila in M for v in fila) + 2
    return "\n".join(sangria + "[" + "".join("{:>{a}}".format(str(v), a=ancho) for v in fila)
                     + " ]" for fila in M)


def _lider(fila):
    """Índice de la primera entrada no nula de la fila, o None si es toda ceros."""
    for j, v in enumerate(fila):
        if not v.es_cero():
            return j
    return None


def verificar(M):
    """
    Comprueba las condiciones de REF y RREF. Devuelve un dict con `ref`, `rref`, la lista de
    pivotes (fila, columna) y, por cada condición, si se cumple y en qué fila falla.
    """
    m, n = len(M), len(M[0])
    lideres = [_lider(f) for f in M]
    cond = []

    # REF 1: las filas nulas van al final.
    fallo = None
    for i in range(m - 1):
        if lideres[i] is None and lideres[i + 1] is not None:
            fallo = "la fila {} es nula y debajo hay la fila {} no nula".format(i + 1, i + 2)
            break
    cond.append(("REF 1", "Las filas de ceros están al final.", fallo))

    # REF 2: cada pivote queda estrictamente a la derecha del anterior.
    fallo = None
    previo, fprev = -1, None
    for i, c in enumerate(lideres):
        if c is None:
            continue
        if c <= previo:
            fallo = ("el pivote de la fila {} (columna {}) no queda a la derecha del de la "
                     "fila {} (columna {})".format(i + 1, c + 1, fprev + 1, previo + 1))
            break
        previo, fprev = c, i
    cond.append(("REF 2", "El pivote de cada fila está estrictamente a la derecha del de la fila "
                          "de arriba.", fallo))

    # REF 3: debajo de cada pivote solo hay ceros.
    fallo = None
    for i, c in enumerate(lideres):
        if c is None:
            continue
        for k in range(i + 1, m):
            if not M[k][c].es_cero():
                fallo = ("debajo del pivote de la fila {} (columna {}) la fila {} tiene {}"
                         .format(i + 1, c + 1, k + 1, M[k][c]))
                break
        if fallo:
            break
    cond.append(("REF 3", "Debajo de cada pivote todas las entradas son cero.", fallo))
    ref = all(c[2] is None for c in cond)

    # RREF 4: todos los pivotes valen 1.
    fallo = None
    for i, c in enumerate(lideres):
        if c is not None and not M[i][c].es_uno():
            fallo = "el pivote de la fila {} (columna {}) vale {} y debe valer 1".format(
                i + 1, c + 1, M[i][c])
            break
    cond.append(("RREF 4", "Cada pivote es un 1 (1 principal).", fallo))

    # RREF 5: encima de cada pivote solo hay ceros.
    fallo = None
    for i, c in enumerate(lideres):
        if c is None:
            continue
        for k in range(i):
            if not M[k][c].es_cero():
                fallo = ("encima del pivote de la fila {} (columna {}) la fila {} tiene {}"
                         .format(i + 1, c + 1, k + 1, M[k][c]))
                break
        if fallo:
            break
    cond.append(("RREF 5", "Encima de cada pivote todas las entradas son cero.", fallo))
    rref = ref and all(c[2] is None for c in cond)
    pivotes = [(i, c) for i, c in enumerate(lideres) if c is not None]
    return {"ref": ref, "rref": rref, "condiciones": cond, "pivotes": pivotes,
            "filas": m, "columnas": n}


def informe_verificacion(M):
    """Informe de la verificación: cada condición con [Se cumple] / [No se cumple] y el veredicto."""
    v = verificar(M)
    lineas = ["=== ¿Está en forma escalonada? ===", "",
              "Matriz A ({}×{}):".format(v["filas"], v["columnas"]), _texto(M), "",
              "--- Condiciones de la forma escalonada (REF) ---"]
    for nombre, texto, fallo in v["condiciones"][:3]:
        lineas.append("  {}: {}".format(nombre, texto))
        lineas.append("    " + ("[Se cumple]" if fallo is None
                                else "[No se cumple] " + fallo + "."))
    lineas += ["", "--- Condiciones adicionales de la escalonada reducida (RREF) ---"]
    for nombre, texto, fallo in v["condiciones"][3:]:
        lineas.append("  {}: {}".format(nombre, texto))
        if not v["ref"]:
            lineas.append("    (se revisa solo cuando ya es escalonada)")
        else:
            lineas.append("    " + ("[Se cumple]" if fallo is None
                                    else "[No se cumple] " + fallo + "."))
    lineas += ["", "--- Conclusión ---"]
    if v["rref"]:
        lineas.append("  La matriz está en forma escalonada REDUCIDA (RREF). "
                      "La RREF de una matriz es única.")
    elif v["ref"]:
        lineas.append("  La matriz está en forma escalonada (REF) pero NO es reducida.")
    else:
        lineas.append("  La matriz NO está en forma escalonada.")
    if v["ref"]:
        cols = ", ".join(str(c + 1) for _, c in v["pivotes"]) or "ninguna"
        lineas.append("  Posiciones pivote (fila, columna): " + (
            ", ".join("({}, {})".format(i + 1, c + 1) for i, c in v["pivotes"]) or "ninguna"))
        lineas.append("  Columnas pivote: {}      Rango (nº de filas no nulas) = {}".format(
            cols, len(v["pivotes"])))
    else:
        lineas.append("  Usa «Reducir a REF» o «Reducir a RREF» para llevarla a esa forma.")
    return "\n".join(lineas), v


def reducir(M, reducida):
    """
    Reduce M (m×n, sin columna b) a REF o a RREF con operaciones elementales. Devuelve
    (informe, matriz_resultado, columnas_pivote). El algoritmo normaliza cada pivote a 1,
    así que la REF obtenida tiene 1 principales (sigue siendo una forma escalonada válida).
    """
    A = copiar(M)
    n = len(A[0])
    lineas = ["=== Reducción a forma escalonada{} ===".format(" reducida (RREF)" if reducida else
                                                              " (REF)"), "",
              "Matriz inicial ({}×{}):".format(len(A), n), _texto(A), "",
              "--- Fase 1: eliminación hacia adelante (Gauss) ---"]
    pasos, cols = escalonar(A, n)
    k = 0
    for p in pasos:
        k += 1
        lineas += ["", "Paso {}: {}".format(k, p["operacion"])]
        if p["comentario"]:
            lineas.append("  " + p["comentario"])
        lineas.append(_texto(p["matriz"]))
    if not pasos:
        lineas.append("  No hizo falta ninguna operación.")
    lineas += ["", "Matriz escalonada (REF):", _texto(A)]
    if reducida:
        lineas += ["", "--- Fase 2: eliminación hacia atrás (Gauss-Jordan) ---"]
        pasos2 = reducir_jordan(A, n, cols)
        for p in pasos2:
            k += 1
            lineas += ["", "Paso {}: {}".format(k, p["operacion"])]
            if p["comentario"]:
                lineas.append("  " + p["comentario"])
            lineas.append(_texto(p["matriz"]))
        if not pasos2:
            lineas.append("  No hizo falta ninguna operación.")
        lineas += ["", "Matriz escalonada reducida (RREF):", _texto(A)]
    lineas += ["", "--- Resultado ---",
               "  Columnas pivote: {}".format(", ".join(str(c + 1) for c in cols) or "ninguna"),
               "  Rango de la matriz = {}".format(len(cols)),
               "  Columnas libres: {}".format(
                   ", ".join(str(c + 1) for c in range(n) if c not in cols) or "ninguna")]
    lineas.append("  Resultado [Se cumple]: la matriz final está en {}.".format(
        "RREF" if reducida else "forma escalonada") if verificar(A)["rref" if reducida else "ref"]
        else "  [No se cumple] comprobación final: revisar.")
    return "\n".join(lineas), A, cols
