# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/formato.py
#  Construccion de las cadenas de texto que se muestran al usuario.
#
#  Ninguna funcion de este modulo imprime: todas DEVUELVEN cadenas. El
#  destino final del texto (pantalla, archivo u otro) queda a cargo del
#  modulo que lo consuma.
# =============================================================================

_SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def subindice(n):
    """Convierte un numero a digitos subindice Unicode: 1 -> ₁, 12 -> ₁₂."""
    return str(n).translate(_SUBSCRIPTS)


# ---------------------------------------------------------------------------
# Matriz aumentada
# ---------------------------------------------------------------------------

def ancho_columna(M):
    """Calcula el ancho necesario para que todas las entradas queden alineadas."""
    ancho = 1
    for fila in M:
        for valor in fila:
            largo = len(str(valor))
            if largo > ancho:
                ancho = largo
    return ancho


def texto_matriz(M, n_vars, titulo=None, sangria="  "):
    """
    Devuelve la matriz aumentada [A | b] con la barra vertical que separa
    los coeficientes del termino independiente.
    """
    ancho = ancho_columna(M) + 2
    lineas = []

    if titulo is not None:
        lineas.append(titulo)

    for fila in M:
        coeficientes = ""
        for c in range(n_vars):
            coeficientes += "{:>{a}}".format(str(fila[c]), a=ancho)
        independiente = "{:>{a}}".format(str(fila[n_vars]), a=ancho)
        lineas.append(sangria + "[" + coeficientes + "   |" + independiente + " ]")

    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Sistema en forma de ecuaciones
# ---------------------------------------------------------------------------

def texto_coeficiente(magnitud):
    """
    Escribe el coeficiente que acompana a una variable.
    El 1 se omite (x₂, no 1x₂) y las fracciones van entre parentesis
    para que (3/2)x₂ no se confunda con 3/(2x₂).
    """
    if magnitud.es_uno():
        return ""
    if magnitud.den != 1:
        return "({})".format(magnitud)
    return str(magnitud)


def nombre_variable(indice, nombres=None):
    """
    Nombre de la variable numero 'indice'. Por defecto x₁, x₂, x₃...
    Usa digitos subindice Unicode para notacion matematica correcta.
    El parametro 'nombres' permite otra numeracion, util al mostrar un
    subconjunto de variables en la solucion parametrizada.
    """
    if nombres is not None and indice < len(nombres):
        return nombres[indice]
    return "x" + subindice(indice + 1)


def texto_termino(coeficiente, indice_variable, es_primero, nombres=None):
    """
    Escribe un termino del tipo '+ 3x₂' cuidando el signo y omitiendo
    los coeficientes 1 y -1 (se escribe x₂, no 1x₂).
    """
    if coeficiente.es_cero():
        return ""

    if es_primero:
        signo = "-" if coeficiente.es_negativo() else ""
    else:
        signo = " - " if coeficiente.es_negativo() else " + "

    magnitud = -coeficiente if coeficiente.es_negativo() else coeficiente
    cuerpo = "{}{}".format(texto_coeficiente(magnitud),
                           nombre_variable(indice_variable, nombres))

    return signo + cuerpo


def texto_ecuacion(fila, n_vars, nombres=None):
    """Convierte una fila de la matriz aumentada en una ecuacion legible."""
    partes = ""
    primero = True

    for c in range(n_vars):
        pedazo = texto_termino(fila[c], c, primero, nombres)
        if pedazo != "":
            partes += pedazo
            primero = False

    if partes == "":
        partes = "0"

    return "{} = {}".format(partes, fila[n_vars])


def texto_sistema(M, n_vars, titulo=None, sangria="  "):
    """Devuelve el sistema completo escrito como ecuaciones."""
    lineas = []
    if titulo is not None:
        lineas.append(titulo)
    for fila in M:
        lineas.append(sangria + texto_ecuacion(fila, n_vars))
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Elementos decorativos
# ---------------------------------------------------------------------------

def separador(caracter="=", largo=66):
    return caracter * largo


def encabezado(texto, caracter="="):
    """Titulo de seccion enmarcado."""
    return "{}\n  {}\n{}".format(separador(caracter), texto, separador(caracter))


def subtitulo(texto):
    return "\n--- {} ---".format(texto)
