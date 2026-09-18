# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: output/reporte.py
#  Convierte el diccionario devuelto por resolutor.resolver() en un informe
#  de texto completo.
#
#  Al estar desacoplado de la interfaz, mantiene separadas la logica de
#  presentacion y la interfaz grafica.
# =============================================================================

from core.formato import (texto_matriz, texto_sistema, separador, subtitulo,
                           nombre_variable, subindice)
from solver.solucion import texto_expresion
from solver.clasificacion import DETERMINADO, INDETERMINADO, INCONSISTENTE


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
    """Todos los pasos de la reduccion a forma escalonada."""
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
    variables_basicas = ", ".join(nombre_variable(c) for c in columnas_pivote)

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
        nombres = ", ".join(nombre_variable(c) for c in libres)
        lineas.append("")
        lineas.append("  El rango es menor que el número de variables.")
        lineas.append("  Variables libres ({}): {}".format(len(libres), nombres))

    lineas.append("")
    lineas.append("  >> " + analisis["nombre"])
    return "\n".join(lineas)

# ---------------------------------------------------------------------------
# Lectura del sistema como ecuacion matricial A.x = b
# ---------------------------------------------------------------------------

def _columnas_de_A(resultado):
    """Devuelve las columnas de A como lista de vectores (listas de Fraccion)."""
    original = resultado["original"]
    n_vars = resultado["n_vars"]
    return [[fila[j] for fila in original] for j in range(n_vars)]


def _vector_b(resultado):
    """Devuelve la columna de terminos independientes como vector."""
    n_vars = resultado["n_vars"]
    return [fila[n_vars] for fila in resultado["original"]]


def _en_linea(v):
    """Escribe un vector en una sola linea: [ 1, 2, 3 ]^T."""
    return "[ " + ", ".join(str(componente) for componente in v) + " ]^T"


def seccion_ecuacion_matricial(resultado, numero):
    """
    Escribe el sistema como ecuacion matricial y como ecuacion vectorial.

    Teorema: A.x = b tiene el mismo conjunto solucion que la ecuacion
    vectorial x1.a1 + x2.a2 + ... + xn.an = b, y que el sistema cuya matriz
    aumentada es [a1 a2 ... an | b]. Las tres formas son la misma pregunta.
    """
    n_vars = resultado["n_vars"]
    columnas = _columnas_de_A(resultado)
    b = _vector_b(resultado)

    lineas = []
    lineas.append(subtitulo("{}. ECUACIÓN MATRICIAL A·x = b".format(numero)))
    lineas.append("")
    lineas.append("  Columnas de A:")
    for j in range(n_vars):
        lineas.append("     a{} = {}".format(subindice(j + 1), _en_linea(columnas[j])))
    lineas.append("     b  = {}".format(_en_linea(b)))
    lineas.append("")

    terminos = " + ".join("{}·a{}".format(nombre_variable(j), subindice(j + 1))
                          for j in range(n_vars))
    lineas.append("  Ecuación vectorial equivalente:")
    lineas.append("     {} = b".format(terminos))
    lineas.append("")
    lineas.append("  El producto A·x es la combinación lineal de las columnas de A")
    lineas.append("  usando como pesos las entradas de x, de modo que resolver A·x = b")
    lineas.append("  es exactamente resolver el sistema de matriz aumentada [A | b].")

    return "\n".join(lineas)


def seccion_combinacion(resultado, numero):
    """
    Responde si b es combinacion lineal de las columnas de A, y en caso
    afirmativo escribe la combinacion con sus escalares.
    """
    tipo = resultado["analisis"]["tipo"]
    n_vars = resultado["n_vars"]
    columnas = _columnas_de_A(resultado)
    b = _vector_b(resultado)

    lineas = []
    lineas.append(subtitulo("{}. ¿ES b COMBINACIÓN LINEAL DE LAS COLUMNAS DE A?".format(numero)))
    lineas.append("")
    lineas.append("  Pregunta: ¿existen escalares x₁, ..., x{} tales que".format(
        subindice(n_vars)))
    lineas.append("            x₁·a₁ + ... + x{}·a{} = b?".format(
        subindice(n_vars), subindice(n_vars)))
    lineas.append("")

    if tipo == INCONSISTENTE:
        lineas.append("  [FALLA] NO es combinación lineal.")
        lineas.append("")
        lineas.append("  El sistema resultó inconsistente: no existe ningún juego de")
        lineas.append("  escalares que genere a b. El vector b queda fuera del conjunto")
        lineas.append("  generado por las columnas de A.")
        return "\n".join(lineas)

    lineas.append("  [CUMPLE] SÍ es combinación lineal.")
    lineas.append("")

    x = resultado["solucion"]
    escalares = " + ".join("({})·a{}".format(x[j], subindice(j + 1))
                           for j in range(n_vars))
    lineas.append("  Escalares encontrados:")
    for j in range(n_vars):
        lineas.append("     {} = {}".format(nombre_variable(j), x[j]))
    lineas.append("")
    lineas.append("  Combinación:")
    lineas.append("     b = " + escalares)
    lineas.append("")

    # Comprobacion componente a componente: se rehace la combinacion.
    lineas.append("  Comprobación (se rehace la combinación):")
    for i in range(len(b)):
        productos = [columnas[j][i] * x[j] for j in range(n_vars)]
        total = productos[0]
        for j in range(1, n_vars):
            total = total + productos[j]
        sumandos = " + ".join(
            "({})·({})".format(x[j], columnas[j][i]) for j in range(n_vars))
        marca = "OK" if total == b[i] else "ERROR"
        lineas.append("     componente {}: {} = {}   [{}] b{} = {}".format(
            i + 1, sumandos, total, marca, subindice(i + 1), b[i]))
    lineas.append("")

    if tipo == DETERMINADO:
        lineas.append("  La combinación es ÚNICA: sólo existe ese juego de escalares.")
    else:
        lineas.append("  Existen INFINITAS combinaciones que generan a b (hay variables")
        lineas.append("  libres). Arriba se muestra una de ellas.")

    return "\n".join(lineas)


def seccion_independencia(resultado, numero):
    """
    Decide si las columnas de A son linealmente independientes y, cuando son
    dependientes, escribe una relacion de dependencia concreta.

    El analisis se hace SIEMPRE sobre el sistema homogeneo A.x = 0 propio de
    esas columnas (lo resuelve solver/independencia.py), porque la
    independencia lineal depende unicamente de los vectores: el termino
    independiente b del sistema que se este resolviendo no interviene.
    """
    from solver.independencia import analizar, texto_relacion, comprobar_relacion

    n_vars = resultado["n_vars"]
    columnas = _columnas_de_A(resultado)
    analisis = analizar(columnas)

    def nombre_columna(indice):
        return "a" + subindice(indice + 1)

    lineas = []
    lineas.append(subtitulo("{}. INDEPENDENCIA LINEAL DE LAS COLUMNAS DE A".format(numero)))
    lineas.append("")
    lineas.append("  Definición: el conjunto es linealmente DEPENDIENTE si existen")
    lineas.append("  escalares no todos cero tales que x₁·a₁ + ... + x{}·a{} = 0.".format(
        subindice(n_vars), subindice(n_vars)))
    lineas.append("  Si la única solución es la trivial, es INDEPENDIENTE.")
    lineas.append("")

    lineas.append("  Vectores analizados (columnas de A):")
    for j in range(n_vars):
        lineas.append("     {} = {}".format(nombre_columna(j), _en_linea(columnas[j])))
    lineas.append("")

    # Criterios que deciden sin necesidad de eliminar
    if analisis["criterios"]:
        lineas.append("  Por inspección:")
        for hallazgo in analisis["criterios"]:
            lineas.append("     · " + hallazgo["texto"])
        lineas.append("")

    lineas.append("  Por eliminación (sistema homogéneo A·x = 0):")
    lineas.append("")

    if analisis["independiente"]:
        lineas.append("     [CUMPLE] Las columnas son LINEALMENTE INDEPENDIENTES.")
        lineas.append("     No hay variables libres, así que A·x = 0 sólo admite la")
        lineas.append("     solución trivial x₁ = ... = x{} = 0.".format(subindice(n_vars)))
        return "\n".join(lineas)

    libres = analisis["libres"]
    nombres = ", ".join(nombre_variable(c) for c in libres)
    lineas.append("     [FALLA] Las columnas son LINEALMENTE DEPENDIENTES.")
    lineas.append("     Hay {} variable(s) libre(s) ({}), de modo que existen".format(
        len(libres), nombres))
    lineas.append("     soluciones no triviales.")
    lineas.append("")

    relacion = analisis["relacion"]
    if relacion is not None:
        escalares, indice_libre, valor = relacion
        lineas.append("  Relación de dependencia (tomando {} = {}):".format(
            nombre_variable(indice_libre), valor))
        lineas.append("")
        lineas.append("     " + texto_relacion(escalares, nombre_columna))
        lineas.append("")

        cero = comprobar_relacion(columnas, escalares)
        lineas.append("  Comprobación: la combinación da {}".format(_en_linea(cero)))
        lineas.append("")
        lineas.append("  Es una entre infinitas relaciones posibles: cualquier otro valor")
        lineas.append("  de la variable libre da otra relación válida.")

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
                lineas.append("  {} = {}".format(nombre_variable(j), valor))
            else:
                lineas.append("  {} = {}   (≈ {:.6f})".format(
                    nombre_variable(j), valor, valor.a_decimal()))
        return "\n".join(lineas)

    expresiones = resultado["expresiones"]
    libres = resultado["libres"]

    lineas.append("\n  Solución general parametrizada:")
    lineas.append("")
    for j in range(n_vars):
        if j in libres:
            lineas.append("  {} = {}   (parámetro libre)".format(
                nombre_variable(j), nombre_variable(j)))
        else:
            lineas.append("  {} = {}".format(
                nombre_variable(j), texto_expresion(expresiones[j], libres)))

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
        vector_str += "\n      + {} * [".format(nombre_variable(k)) + ", ".join(vec_params[k]) + "]^T"
    lineas.append(vector_str)

    lineas.append("\n  Solución particular tomando todas las variables libres = 0:")
    lineas.append("")
    x = resultado["solucion"]
    valores = ", ".join("{} = {}".format(nombre_variable(j), x[j]) for j in range(n_vars))
    lineas.append("  " + valores)
    return "\n".join(lineas)


def seccion_verificacion(resultado, numero):
    """Sustitucion en el sistema original."""
    tipo = resultado["analisis"]["tipo"]

    lineas = []
    lineas.append(subtitulo("{}. VERIFICACIÓN".format(numero)))

    if tipo == INCONSISTENTE:
        lineas.append("")
        lineas.append("  No se realiza verificación porque no hay solución que sustituir.")
        return "\n".join(lineas)

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
# Que secciones de analisis corresponden
# ---------------------------------------------------------------------------

def secciones_en_rn(resultado, incluir_vectores, contexto=None):
    """
    Devuelve, en orden, las secciones de analisis en Rn que corresponden a
    este sistema, sin repetir ninguna.

    La casilla de analisis en Rn pide las dos preguntas (combinacion lineal e
    independencia); el contexto pide la del enunciado con el que llego el
    sistema. Cuando coinciden, la seccion se escribe una sola vez.

    Dos salvedades:
      - La ecuacion matricial no se escribe si el sistema vino planteado como
        independencia lineal, porque alli el termino independiente es cero.
      - La combinacion lineal se omite en un sistema homogeneo: b = 0 siempre
        es combinacion de cualquier conjunto (con todos los escalares cero),
        asi que la pregunta interesante es la independencia.
    """
    homogeneo = resultado["analisis"]["homogeneo"]

    secciones = []

    if contexto in ("matricial", "combinacion"):
        secciones.append(seccion_ecuacion_matricial)

    pide_combinacion = (contexto == "combinacion" or incluir_vectores)
    if pide_combinacion and contexto != "independencia" and not homogeneo:
        secciones.append(seccion_combinacion)

    if contexto == "independencia" or incluir_vectores:
        secciones.append(seccion_independencia)

    return secciones


# ---------------------------------------------------------------------------
# Informe completo
# ---------------------------------------------------------------------------

def generar(resultado, incluir_jordan=True, incluir_vectores=False,
            contexto=None):
    """
    Arma el informe completo como una sola cadena de texto.

    'contexto' indica con que enunciado se planteo el sistema para agregar la
    seccion que corresponda: ecuacion matricial, combinacion lineal o
    independencia lineal.
    """
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
    numero += 1

    # Secciones de analisis en Rn. Cada una aparece como maximo una vez, se
    # haya pedido por el enunciado con el que llego el sistema (contexto) o
    # por la casilla de analisis en Rn.
    for seccion in secciones_en_rn(resultado, incluir_vectores, contexto):
        bloques.append(seccion(resultado, numero))
        numero += 1

    bloques.append(seccion_solucion(resultado, numero))
    bloques.append(seccion_verificacion(resultado, numero + 1))
    bloques.append("\n" + separador("="))

    return "\n".join(bloques)