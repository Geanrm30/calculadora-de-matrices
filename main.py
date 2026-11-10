# -*- coding: utf-8 -*-
"""
Punto de entrada de la Calculadora de Álgebra Lineal (Proyecto Integrador).
Interfaz gráfica en PySide6: una sola ventana con menú lateral que da acceso
al solucionador, las operaciones con matrices, la factorización LU, los métodos
numéricos y el catálogo de teoremas. Si falta un componente, se instala solo.
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instalador import asegurar_dependencias


def iniciar():
    """Crea la aplicación Qt, aplica el tema guardado y abre la ventana principal."""
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from qt import NOMBRE, persistencia, tema
    from qt.icono import crear_icono
    from qt.ventana_principal import VentanaPrincipal

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "UAM.CalculadoraAlgebraLineal")
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    from core import calentamiento
    calentamiento.iniciar()
    app.setApplicationName(NOMBRE)
    app.setWindowIcon(crear_icono())
    app.setFont(QFont(tema.FUENTE, 10))
    tema.aplicar(persistencia.leer("tema", "oscuro"))
    tema.poner_escala(persistencia.leer("escala", 1.0))
    app.setStyleSheet(tema.hoja_de_estilos())

    ventana = VentanaPrincipal()
    ventana.restaurar_sesion()
    from qt.componentes import fundido_de_ventana
    ventana.setWindowOpacity(0.0)
    ventana.show()
    fundido_de_ventana(ventana, 520)
    ventana.mostrar_tour_si_corresponde()
    ventana.precargar_paginas()
    app._ventana_principal = ventana
    return app.exec()


if __name__ == "__main__":
    if not asegurar_dependencias():
        sys.exit(1)
    sys.exit(iniciar())