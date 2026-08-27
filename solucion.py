# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: solucion.py
#  Obtencion de los valores de las variables a partir de la matriz escalonada.
#
#  Contiene dos sustituciones regresivas:
#    - numerica  : devuelve un valor concreto por variable.
#    - simbolica : devuelve cada variable pivote escrita en funcion de las
#                  variables libres.
#
#  Justificacion de la variante simbolica: en forma escalonada, no reducida,
#  una fila puede contener a la derecha del pivote otras variables pivote
#  ademas de las libres. Omitir esos terminos al despejar produce una
#  expresion general incorrecta, aun cuando la solucion particular obtenida
#  por sustitucion numerica sea valida.
# =============================================================================

from fraccion import Fraccion
from clasificacion import variables_libres
from formato import texto_coeficiente


# ---------------------------------------------------------------------------
# Sustitucion regresiva numerica
# ---------------------------------------------------------------------------

def sustitucion_regresiva(M, n_vars, columnas_pivote, valores_libres=None):
    """
    Calcula el valor de cada variable recorriendo las filas con pivote de
    abajo hacia arriba. A las variables libres se les asigna el valor
    indicado en valores_libres (diccionario indice -> Fraccion); por defecto
    valen cero, lo que produce una solucion particular.
    """
    x = [Fraccion(0) for _ in range(n_vars)]

    if valores_libres is not None:
        for indice in valores_libres:
            x[indice] = valores_libres[indice]

    for i in range(len(columnas_pivote) - 1, -1, -1):
        col = columnas_pivote[i]
        acumulado = M[i][n_vars]
        # Se pasan al otro lado todas las variables a la derecha del pivote
        for c in range(col + 1, n_vars):
            if not M[i][c].es_cero():
                acumulado = acumulado - M[i][c] * x[c]
        x[col] = acumulado / M[i][col]

    return x


# ---------------------------------------------------------------------------
# Sustitucion regresiva simbolica
# ---------------------------------------------------------------------------

def calcular_expresiones(M, n_vars, columnas_pivote):
    """
    Cada variable se representa como una lista de coeficientes:

        [termino_independiente, coef_libre_1, coef_libre_2, ...]

    Con una unica variable libre x2, la expresion x1 = 3 - 2*x2 se almacena
    como [3, -2], y la propia variable libre como [0, 1].

    Devuelve (expresiones, libres).
    """
    libres = variables_libres(n_vars, columnas_pivote)
    ancho = 1 + len(libres)  # constante + un lugar por variable libre

    expresiones = [[Fraccion(0) for _ in range(ancho)] for _ in range(n_vars)]

    # Cada variable libre es su propio parametro
    for k in range(len(libres)):
        expresiones[libres[k]][k + 1] = Fraccion(1)

    # De la ultima fila con pivote hacia la primera
    for i in range(len(columnas_pivote) - 1, -1, -1):
        col = columnas_pivote[i]
        pivote = M[i][col]

        acumulado = [Fraccion(0) for _ in range(ancho)]
        acumulado[0] = M[i][n_vars]

        # Se restan las expresiones de todas las variables a la derecha
        for c in range(col + 1, n_vars):
            if not M[i][c].es_cero():
                for k in range(ancho):
                    acumulado[k] = acumulado[k] - M[i][c] * expresiones[c][k]

        # Se divide entre el pivote para despejar
        for k in range(ancho):
            expresiones[col][k] = acumulado[k] / pivote

    return expresiones, libres


def texto_expresion(expresion, libres):
    """
    Convierte una expresion simbolica en texto legible:
        [3, -2]  con libres = [1]   ->   "3 - 2*x2"
    """
    texto = ""
    constante = expresion[0]

    # Termino independiente: se omite si es cero y hay parametros
    hay_parametros = False
    for k in range(len(libres)):
        if not expresion[k + 1].es_cero():
            hay_parametros = True
            break

    if not constante.es_cero() or not hay_parametros:
        texto = str(constante)

    # Terminos con parametros
    for k in range(len(libres)):
        coeficiente = expresion[k + 1]
        if coeficiente.es_cero():
            continue

        magnitud = -coeficiente if coeficiente.es_negativo() else coeficiente

        if texto == "":
            signo = "-" if coeficiente.es_negativo() else ""
        else:
            signo = " - " if coeficiente.es_negativo() else " + "

        cuerpo = "{}x{}".format(texto_coeficiente(magnitud), libres[k] + 1)

        texto += signo + cuerpo

    if texto == "":
        texto = "0"

    return texto
