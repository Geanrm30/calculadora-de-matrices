# -*- coding: utf-8 -*-
"""
Guarda y recupera las preferencias y lo escrito en cada herramienta entre
sesiones (tema, tamaño y posición de la ventana, cuadrículas, opciones).
Usa QSettings, así que vive en el registro de Windows / en el perfil del usuario.
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import json

from PySide6.QtCore import QSettings


def _ajustes():
    """Devuelve los ajustes persistentes de la aplicación (QSettings)."""
    return QSettings("UAM", "CalculadoraAlgebraLineal")


def leer(clave, defecto=None):
    """Lee el valor guardado bajo 'clave' (JSON); devuelve 'defecto' si no existe o está dañado."""
    try:
        bruto = _ajustes().value(clave)
        if bruto is None:
            return defecto
        return json.loads(bruto)
    except (ValueError, TypeError):
        return defecto


def escribir(clave, valor):
    """Guarda 'valor' bajo 'clave' como JSON; ignora los errores de escritura."""
    try:
        _ajustes().setValue(clave, json.dumps(valor, ensure_ascii=False))
    except (TypeError, ValueError):
        pass


def borrar_todo():
    """Borra todos los ajustes guardados."""
    _ajustes().clear()
