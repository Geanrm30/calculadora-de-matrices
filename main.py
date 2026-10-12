# -*- coding: utf-8 -*-
"""
Punto de entrada del Proyecto Integrador: Calculadora de Álgebra Lineal.
Interfaz gráfica en PySide6: una sola ventana con menú lateral que da acceso
al solucionador, a las operaciones con matrices y al catálogo de teoremas.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

import sys
import os

# Garantiza que el directorio raiz del proyecto este en sys.path para que
# los paquetes core/, solver/, output/ y qt/ sean importables sin importar
# desde que directorio se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def iniciar():
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from qt import persistencia, tema
    from qt.ventana_principal import VentanaPrincipal

    app = QApplication(sys.argv)
    app.setApplicationName("Calculadora de Álgebra Lineal")
    app.setFont(QFont(tema.FUENTE, 10))
    tema.aplicar(persistencia.leer("tema", "oscuro"))
    app.setStyleSheet(tema.hoja_de_estilos())

    ventana = VentanaPrincipal()
    ventana.restaurar_sesion()
    ventana.show()
    app._ventana_principal = ventana
    return app.exec()


# Nombre conservado por compatibilidad con versiones anteriores del programa.
def iniciar_menu():
    """Alias de iniciar()."""
    return iniciar()


if __name__ == "__main__":
    sys.exit(iniciar())
