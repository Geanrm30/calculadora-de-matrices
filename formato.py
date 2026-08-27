# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: formato.py
#  Construccion de las cadenas de texto que se muestran al usuario.
#
#  Ninguna funcion de este modulo imprime: todas DEVUELVEN cadenas. El
#  destino final del texto (pantalla, archivo u otro) queda a cargo del
#  modulo que lo consuma.
# =============================================================================


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
    Escribe el coeficiente que acompaña a una variable.
    El 1 se omite (x2, no 1x2) y las fracciones van entre paréntesis
    para que (3/2)x2 no se confunda con 3/(2x2).
    """
    if magnitud.es_uno():
        return ""
    if magnitud.den != 1:
        return "({})".format(magnitud)
    return str(magnitud)


def nombre_variable(indice, nombres=None):
    """
    Nombre de la variable numero 'indice'. Por defecto x1, x2, x3...
    El parametro 'nombres' permite otra numeracion, que hace falta cuando
    se dibuja un corte y las dos variables que quedan no son x1 y x2.
    """
    if nombres is not None and indice < len(nombres):
        return nombres[indice]
    return "x{}".format(indice + 1)


def texto_termino(coeficiente, indice_variable, es_primero, nombres=None):
    """
    Escribe un termino del tipo '+ 3x2' cuidando el signo y omitiendo
    los coeficientes 1 y -1 (se escribe x2, no 1x2).
    """
    if coeficiente.es_cero():
        return ""

    # Signo
    if es_primero:
        signo = "-" if coeficiente.es_negativo() else ""
    else:
        signo = " - " if coeficiente.es_negativo() else " + "

    # Valor absoluto del coeficiente
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
        partes = "0"  # todos los coeficientes eran cero

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
