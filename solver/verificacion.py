# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: solver/verificacion.py
#  Comprobacion automatica de la solucion obtenida.
#
#  La sustitucion se hace SIEMPRE en el sistema original (la copia guardada
#  antes de escalonar). Verificar contra la matriz ya reducida no probaria
#  nada: es el resultado del mismo proceso que se quiere comprobar.
#
#  Como la aritmetica es exacta, la comparacion es una igualdad real y no
#  una comparacion con tolerancia.
# =============================================================================

from core.fraccion import Fraccion


def verificar_valores(matriz_original, n_vars, x):
    """
    Sustituye los valores en cada ecuacion original y compara A*x con b.
    Devuelve (lista_de_resultados, todo_correcto).
    """
    resultados = []
    todo_correcto = True

    for i in range(len(matriz_original)):
        fila = matriz_original[i]

        obtenido = Fraccion(0)
        cadena_operacion = []

        for j in range(n_vars):
            obtenido = obtenido + fila[j] * x[j]
            if not fila[j].es_cero():
                cadena_operacion.append("({})({})".format(fila[j], x[j]))

        esperado = fila[n_vars]
        correcto = (obtenido == esperado)
        if not correcto:
            todo_correcto = False

        texto_op = " + ".join(cadena_operacion) if cadena_operacion else "0"
        texto_op = texto_op.replace("+ (-", "- (")

        resultados.append({
            "ecuacion": i + 1,
            "operacion": texto_op,
            "obtenido": obtenido,
            "esperado": esperado,
            "correcto": correcto,
        })

    return resultados, todo_correcto


def verificar_expresiones(matriz_original, n_vars, expresiones, libres):
    """
    Comprueba la solucion general SIN dar valores a los parametros.

    Sustituye en cada ecuacion las expresiones simbolicas y verifica que:
      - el termino independiente resultante sea igual a b, y
      - el coeficiente de cada parametro se cancele (quede en cero).
    """
    ancho = 1 + len(libres)
    resultados = []
    todo_correcto = True

    for i in range(len(matriz_original)):
        fila = matriz_original[i]

        acumulado = [Fraccion(0) for _ in range(ancho)]
        for j in range(n_vars):
            if not fila[j].es_cero():
                for k in range(ancho):
                    acumulado[k] = acumulado[k] + fila[j] * expresiones[j][k]

        constante_ok = (acumulado[0] == fila[n_vars])

        parametros_ok = True
        for k in range(1, ancho):
            if not acumulado[k].es_cero():
                parametros_ok = False
                break

        correcto = constante_ok and parametros_ok
        if not correcto:
            todo_correcto = False

        resultados.append({
            "ecuacion": i + 1,
            "constante": acumulado[0],
            "esperado": fila[n_vars],
            "coeficientes_parametros": acumulado[1:],
            "correcto": correcto,
        })

    return resultados, todo_correcto
