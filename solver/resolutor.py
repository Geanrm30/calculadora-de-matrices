# -*- coding: utf-8 -*-
"""
Coordina el proceso completo de resolución y devuelve un diccionario con todos
los resultados intermedios; sin entrada ni salida directa.
Unidad: Proyecto Integrador (Sesiones 1-11).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

from core.fraccion import Fraccion
from core.matriz import copiar
from solver.eliminacion import escalonar, reducir_jordan
from solver.clasificacion import clasificar, DETERMINADO, INCONSISTENTE
from solver.solucion import sustitucion_regresiva, calcular_expresiones
from solver.verificacion import verificar_valores, verificar_expresiones


def resolver(matriz, n_vars, aplicar_jordan=True):
    """Resuelve el sistema de la matriz aumentada [A|b] con n_vars variables.
    Si aplicar_jordan es True calcula además la forma escalonada reducida.
    Devuelve un dict con los pasos, la clasificación y las expresiones de la solución.
    """
    original = copiar(matriz)

    trabajo = copiar(matriz)
    pasos, columnas_pivote = escalonar(trabajo, n_vars)
    escalonada = copiar(trabajo)

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

    if aplicar_jordan and len(columnas_pivote) > 1:
        matriz_jordan = copiar(escalonada)
        pasos_jordan = reducir_jordan(matriz_jordan, n_vars, columnas_pivote)
        resultado["pasos_jordan"] = pasos_jordan
        resultado["reducida"] = matriz_jordan

    tipo = analisis["tipo"]

    if tipo == INCONSISTENTE:
        return resultado

    if tipo == DETERMINADO:
        x = sustitucion_regresiva(escalonada, n_vars, columnas_pivote)
        verificacion, correcto = verificar_valores(original, n_vars, x)
        resultado["solucion"] = x
        resultado["verificacion"] = verificacion
        resultado["todo_correcto"] = correcto
        return resultado

    expresiones, libres = calcular_expresiones(escalonada, n_vars, columnas_pivote)
    resultado["expresiones"] = expresiones
    resultado["libres"] = libres

    verificacion_general, correcto_general = verificar_expresiones(
        original, n_vars, expresiones, libres)
    resultado["verificacion_general"] = verificacion_general

    valores_libres = {}
    for c in libres:
        valores_libres[c] = Fraccion(0)
    x = sustitucion_regresiva(escalonada, n_vars, columnas_pivote, valores_libres)

    verificacion, correcto = verificar_valores(original, n_vars, x)
    resultado["solucion"] = x
    resultado["verificacion"] = verificacion
    resultado["todo_correcto"] = correcto and correcto_general

    return resultado
