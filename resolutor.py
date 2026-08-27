# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: resolutor.py
#  Coordina el procedimiento completo y devuelve un unico diccionario con
#  todos los resultados intermedios y finales.
#
#  El modulo no realiza entrada ni salida: recibe una matriz y devuelve
#  datos. Esta separacion permite que la interfaz, el informe y cualquier
#  consumidor futuro operen sobre el mismo resultado, sin duplicar la
#  logica de calculo ni arriesgar divergencias entre ellos.
# =============================================================================

from fraccion import Fraccion
from matriz import copiar
from eliminacion import escalonar, reducir_jordan
from clasificacion import clasificar, DETERMINADO, INDETERMINADO, INCONSISTENTE
from solucion import sustitucion_regresiva, calcular_expresiones
from verificacion import verificar_valores, verificar_expresiones


def resolver(matriz, n_vars, aplicar_jordan=True):
    """
    Resuelve el sistema representado por la matriz aumentada.

    Parametros:
        matriz        : lista de listas de Fraccion, la matriz aumentada [A|b]
        n_vars        : numero de variables
        aplicar_jordan: si True, ademas de la forma escalonada se calcula la
                        forma escalonada reducida (Gauss-Jordan)

    Devuelve un diccionario con: la matriz original, los pasos, la matriz
    escalonada, la clasificacion, la solucion y la verificacion.
    """
    # Copia intacta del sistema original para la verificacion final
    original = copiar(matriz)

    # --- Fase 1: eliminacion hasta forma escalonada ---
    trabajo = copiar(matriz)
    pasos, columnas_pivote = escalonar(trabajo, n_vars)
    escalonada = copiar(trabajo)

    # --- Fase 2: clasificacion ---
    analisis = clasificar(escalonada, n_vars, columnas_pivote, original)

    resultado = {
        "original": original,
        "n_vars": n_vars,
        "n_ecuaciones": len(original),
        "pasos": pasos,
        "escalonada": escalonada,
        "columnas_pivote": columnas_pivote,
        "analisis": analisis,
        "solucion": None,
        "expresiones": None,
        "libres": analisis["libres"],
        "verificacion": None,
        "verificacion_general": None,
        "todo_correcto": None,
        "pasos_jordan": None,
        "reducida": None,
    }

    # --- Fase 3: Gauss-Jordan (opcional, solo si hay algo que reducir) ---
    if aplicar_jordan and len(columnas_pivote) > 1:
        matriz_jordan = copiar(escalonada)
        pasos_jordan = reducir_jordan(matriz_jordan, n_vars, columnas_pivote)
        resultado["pasos_jordan"] = pasos_jordan
        resultado["reducida"] = matriz_jordan

    # --- Fase 4: solucion segun el tipo de sistema ---
    tipo = analisis["tipo"]

    if tipo == INCONSISTENTE:
        # No hay nada que calcular ni que verificar
        return resultado

    if tipo == DETERMINADO:
        x = sustitucion_regresiva(escalonada, n_vars, columnas_pivote)
        verificacion, correcto = verificar_valores(original, n_vars, x)
        resultado["solucion"] = x
        resultado["verificacion"] = verificacion
        resultado["todo_correcto"] = correcto
        return resultado

    # Caso indeterminado: solucion general mas una solucion particular
    expresiones, libres = calcular_expresiones(escalonada, n_vars, columnas_pivote)
    resultado["expresiones"] = expresiones
    resultado["libres"] = libres

    # Verificacion simbolica: vale para cualquier valor de los parametros
    verificacion_general, correcto_general = verificar_expresiones(
        original, n_vars, expresiones, libres)
    resultado["verificacion_general"] = verificacion_general

    # Solucion particular tomando todas las variables libres iguales a cero
    valores_libres = {}
    for c in libres:
        valores_libres[c] = Fraccion(0)
    x = sustitucion_regresiva(escalonada, n_vars, columnas_pivote, valores_libres)

    verificacion, correcto = verificar_valores(original, n_vars, x)
    resultado["solucion"] = x
    resultado["verificacion"] = verificacion
    resultado["todo_correcto"] = correcto and correcto_general

    return resultado
