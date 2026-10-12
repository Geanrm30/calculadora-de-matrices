# -*- coding: utf-8 -*-
"""
Guarda y recupera las preferencias y lo escrito en cada herramienta entre
sesiones (tema, tamaño y posición de la ventana, cuadrículas, opciones).
Usa QSettings, así que vive en el registro de Windows / en el perfil del usuario.
"""
import json
import os

from PySide6.QtCore import QSettings


def _ajustes():
    nombre = os.environ.get("CALCULADORA_AJUSTES", "CalculadoraAlgebraLineal")
    return QSettings("UAM", nombre)


def leer(clave, defecto=None):
    try:
        bruto = _ajustes().value(clave)
        if bruto is None:
            return defecto
        return json.loads(bruto)
    except (ValueError, TypeError):
        return defecto


def escribir(clave, valor):
    try:
        _ajustes().setValue(clave, json.dumps(valor, ensure_ascii=False))
    except (TypeError, ValueError):
        pass


def borrar_todo():
    _ajustes().clear()
