# -*- coding: utf-8 -*-
"""
Punto de entrada del Proyecto Integrador: Calculadora de Álgebra Lineal.
Interfaz gráfica en PySide6: una sola ventana con menú lateral que da acceso
al solucionador, a las operaciones con matrices y al catálogo de teoremas.
Si PySide6 no está instalado, se descarga e instala solo la primera vez.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

import os
import sys

# Garantiza que el directorio raiz del proyecto este en sys.path para que
# los paquetes core/, solver/, output/ y qt/ sean importables sin importar
# desde que directorio se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instalador import asegurar_dependencias


def iniciar():
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from qt import NOMBRE, persistencia, tema
    from qt.icono import crear_icono
    from qt.ventana_principal import VentanaPrincipal

    # En Windows, sin esto la barra de tareas agrupa la ventana bajo el icono
    # de python.exe en lugar del icono propio.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "UAM.CalculadoraAlgebraLineal")
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE)
    app.setApplicationDisplayName(NOMBRE)
    app.setWindowIcon(crear_icono())
    app.setFont(QFont(tema.FUENTE, 10))
    tema.aplicar(persistencia.leer("tema", "oscuro"))
    tema.poner_escala(persistencia.leer("escala", 1.0))
    app.setStyleSheet(tema.hoja_de_estilos())

    ventana = VentanaPrincipal()
    ventana.restaurar_sesion()
    ventana.show()
    ventana.mostrar_tour_si_corresponde()
    app._ventana_principal = ventana
    return app.exec()


# Nombre conservado por compatibilidad con versiones anteriores del programa.
def iniciar_menu():
    """Alias de iniciar()."""
    return iniciar()


if __name__ == "__main__":
    if not asegurar_dependencias():
        sys.exit(1)
    sys.exit(iniciar())
