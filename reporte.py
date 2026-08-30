# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: reporte.py
#  Convierte el diccionario devuelto por resolutor.resolver() en un informe
#  de texto completo.
#
#  Al estar desacoplado de la interfaz, mantiene separadas la logica de
#  presentacion y la interfaz grafica.
# =============================================================================

from formato import texto_matriz, texto_sistema, separador, subtitulo
from solucion import texto_expresion
from clasificacion import DETERMINADO, INDETERMINADO, INCONSISTENTE


# ---------------------------------------------------------------------------
# Secciones del informe
# ---------------------------------------------------------------------------

def seccion_datos(resultado):
    """Sistema ingresado y matriz aumentada inicial."""
    original = resultado["original"]
    n_vars = resultado["n_vars"]

    lineas = []
    lineas.append(subtitulo("1. DATOS DEL SISTEMA"))
    lineas.append("\n  Tamaño: {} ecuaciones x {} variables".format(
        resultado["n_ecuaciones"], n_vars))
    lineas.append("")
    lineas.append(texto_sistema(original, n_vars, "  Sistema ingresado:"))
    lineas.append("")
    lineas.append(texto_matriz(original, n_vars, "  Matriz aumentada [A | b]:"))

    if resultado["analisis"]["homogeneo"]:
        lineas.append("\n  Observación: el sistema es homogéneo (todos los términos")
        lineas.append("  independientes son cero), por lo que siempre es consistente:")
        lineas.append("  como mínimo admite la solución trivial.")

    return "\n".join(lineas)


def seccion_eliminacion(resultado):
    """Todos los pasos de la reducción a forma escalonada."""
    n_vars = resultado["n_vars"]
    pasos = resultado["pasos"]

    lineas = []
    lineas.append(subtitulo("2. ELIMINACIÓN POR FILAS (forma escalonada)"))

    if len(pasos) == 0:
        lineas.append("\n  La matriz ya se encontraba en forma escalonada.")
    else:
        for i in range(len(pasos)):
            paso = pasos[i]
            lineas.append("\n  Paso {}:  {}".format(i + 1, paso["operacion"]))
            if paso["comentario"]:
                lineas.append("           {}".format(paso["comentario"]))
            lineas.append(texto_matriz(paso["matriz"], n_vars, sangria="  "))

    lineas.append("")
    lineas.append(texto_matriz(resultado["escalonada"], n_vars,
                               "  Matriz escalonada final:"))
    lineas.append("")
    lineas.append(texto_sistema(resultado["escalonada"], n_vars,
                                "  Sistema equivalente:"))
    return "\n".join(lineas)


def seccion_jordan(resultado):
    """Pasos adicionales hasta la forma escalonada reducida."""
    if resultado["pasos_jordan"] is None:
        return ""

    n_vars = resultado["n_vars"]
    pasos = resultado["pasos_jordan"]

    lineas = []
    lineas.append(subtitulo("3. FORMA ESCALONADA REDUCIDA (Gauss-Jordan)"))

    if len(pasos) == 0:
        lineas.append("\n  La matriz escalonada ya estaba reducida.")
    else:
        for i in range(len(pasos)):
            paso = pasos[i]
            lineas.append("\n  Paso {}:  {}".format(i + 1, paso["operacion"]))
            lineas.append(texto_matriz(paso["matriz"], n_vars, sangria="  "))

    lineas.append("")
    lineas.append(texto_matriz(resultado["reducida"], n_vars,
                               "  Matriz escalonada reducida:"))
    return "\n".join(lineas)


def seccion_clasificacion(resultado, numero):
    """Rangos y tipo de sistema."""
    analisis = resultado["analisis"]
    columnas_pivote = resultado["columnas_pivote"]
    numeros_pivote = ", ".join(str(c + 1) for c in columnas_pivote)
    variables_basicas = ", ".join("x{}".format(c + 1) for c in columnas_pivote)

    lineas = []
    lineas.append(subtitulo("{}. CLASIFICACIÓN DEL SISTEMA".format(numero)))
    lineas.append("")
    lineas.append("  Rango de A          : {}".format(analisis["rango_A"]))
    lineas.append("  Rango de [A | b]    : {}".format(analisis["rango_Ab"]))
    lineas.append("  Número de variables : {}".format(analisis["n_vars"]))
    lineas.append("  Columnas pivote     : {}".format(numeros_pivote))
    lineas.append("  Variables básicas   : {}".format(variables_basicas))

    if analisis["tipo"] == INCONSISTENTE:
        lineas.append("")
        lineas.append("  La fila {} quedó de la forma  0 = {} , lo cual es imposible.".format(
            analisis["fila_contradiccion"], analisis["valor_contradiccion"]))
        lineas.append("  Por lo tanto rango(A) < rango([A | b]).")

    elif analisis["tipo"] == DETERMINADO:
        lineas.append("")
        lineas.append("  Hay un pivote por cada variable, así que ninguna queda libre.")

    else:
        libres = analisis["libres"]
        nombres = ", ".join("x{}".format(c + 1) for c in libres)
        lineas.append("")
        lineas.append("  El rango es menor que el número de variables.")
        lineas.append("  Variables libres ({}): {}".format(len(libres), nombres))

    lineas.append("")
    lineas.append("  >> " + analisis["nombre"])
    return "\n".join(lineas)


def seccion_solucion(resultado, numero):
    """Valores de las variables."""
    tipo = resultado["analisis"]["tipo"]
    n_vars = resultado["n_vars"]

    lineas = []
    lineas.append(subtitulo("{}. SOLUCIÓN".format(numero)))

    if tipo == INCONSISTENTE:
        lineas.append("")
        lineas.append("  El sistema no tiene solución: no existe ninguna asignación")
        lineas.append("  de valores que satisfaga todas las ecuaciones a la vez.")
        return "\n".join(lineas)

    if tipo == DETERMINADO:
        x = resultado["solucion"]
        lineas.append("")
        for j in range(n_vars):
            valor = x[j]
            if valor.den == 1:
                lineas.append("  x{} = {}".format(j + 1, valor))
            else:
                lineas.append("  x{} = {}   (≈ {:.6f})".format(
                    j + 1, valor, valor.a_decimal()))
        return "\n".join(lineas)

    # Caso indeterminado
    expresiones = resultado["expresiones"]
    libres = resultado["libres"]

    lineas.append("\n  Solución general parametrizada:")
    lineas.append("")
    for j in range(n_vars):
        if j in libres:
            lineas.append("  x{} = x{}   (parámetro libre)".format(j + 1, j + 1))
        else:
            lineas.append("  x{} = {}".format(
                j + 1, texto_expresion(expresiones[j], libres)))

    # Forma Vectorial
    lineas.append("\n  Solución en forma vectorial:")
    vec_const = []
    vec_params = {k: [] for k in libres}

    for j in range(n_vars):
        if j in libres:
            vec_const.append("0")
            for k in libres:
                vec_params[k].append("1" if k == j else "0")
        else:
            expr = expresiones[j]
            vec_const.append(str(expr[0]))
            for idx, k in enumerate(libres):
                vec_params[k].append(str(expr[idx + 1]))

    vector_str = "  x = [" + ", ".join(vec_const) + "]^T"
    for k in libres:
        vector_str += "\n      + x{} * [".format(k + 1) + ", ".join(vec_params[k]) + "]^T"
    lineas.append(vector_str)

    lineas.append("\n  Solución particular tomando todas las variables libres = 0:")
    lineas.append("")
    x = resultado["solucion"]
    valores = ", ".join("x{} = {}".format(j + 1, x[j]) for j in range(n_vars))
    lineas.append("  " + valores)
    return "\n".join(lineas)


def seccion_verificacion(resultado, numero):
    """Sustitución en el sistema original."""
    tipo = resultado["analisis"]["tipo"]

    lineas = []
    lineas.append(subtitulo("{}. VERIFICACIÓN".format(numero)))

    if tipo == INCONSISTENTE:
        lineas.append("")
        lineas.append("  No se realiza verificación porque no hay solución que sustituir.")
        return "\n".join(lineas)

    # Verificacion simbolica (solo en el caso indeterminado)
    if resultado["verificacion_general"] is not None:
        lineas.append("\n  a) Solución general sustituida en el sistema original.")
        lineas.append("     Se comprueba que los parámetros se cancelan, es decir que")
        lineas.append("     la igualdad se cumple para cualquier valor que tomen.")
        lineas.append("")
        for r in resultado["verificacion_general"]:
            coeficientes = ", ".join(str(c) for c in r["coeficientes_parametros"])
            estado = "CUMPLE" if r["correcto"] else "FALLA"
            lineas.append("     Ecuación {}: término independiente = {} (esperado {}) | "
                          "coeficientes de los parámetros = [{}]  [{}]".format(
                              r["ecuacion"], r["constante"], r["esperado"],
                              coeficientes, estado))
        lineas.append("\n  b) Solución particular sustituida en el sistema original.")
    else:
        lineas.append("\n  Solución sustituida en el sistema original.")

    lineas.append("")
    for r in resultado["verificacion"]:
        estado = "CUMPLE" if r["correcto"] else "FALLA"
        lineas.append("     Ecuación {}: {} = {} | esperado = {}  [{}]".format(
            r["ecuacion"], r["operacion"], r["obtenido"], r["esperado"], estado))

    lineas.append("")
    if resultado["todo_correcto"]:
        lineas.append("  Verificación superada: la igualdad se cumple de forma exacta")
        lineas.append("  en todas las ecuaciones (aritmética con fracciones, sin redondeo).")
    else:
        lineas.append("  Atención: alguna ecuación no se cumple.")

    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Informe completo
# ---------------------------------------------------------------------------

def generar(resultado, incluir_jordan=True):
    """Arma el informe completo como una sola cadena de texto."""
    bloques = []
    bloques.append(separador("="))
    bloques.append("  RESOLUCIÓN DE UN SISTEMA DE ECUACIONES LINEALES")
    bloques.append("  Método matricial con operaciones elementales por filas")
    bloques.append(separador("="))

    bloques.append(seccion_datos(resultado))
    bloques.append(seccion_eliminacion(resultado))

    numero = 3
    if incluir_jordan and resultado["pasos_jordan"] is not None:
        bloques.append(seccion_jordan(resultado))
        numero = 4

    bloques.append(seccion_clasificacion(resultado, numero))
    bloques.append(seccion_solucion(resultado, numero + 1))
    bloques.append(seccion_verificacion(resultado, numero + 2))
    bloques.append("\n" + separador("="))

    return "\n".join(bloques)
