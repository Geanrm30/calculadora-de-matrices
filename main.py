# -*- coding: utf-8 -*-
# =============================================================================
#  Punto de entrada principal.
#
#  python main.py
#
#  Muestra el menu y abre la herramienta elegida. Cada herramienta vive en su
#  propia ventana; al cerrarse, este modulo lee en core/estado.py cual es la
#  siguiente y la abre. De esa manera se navega sin anidar ventanas y los
#  datos escritos en cada herramienta se conservan (los guarda core/estado.py).
# =============================================================================

import sys
import os
import tkinter as tk

# Garantiza que el directorio raiz del proyecto este en sys.path para que
# los paquetes core/, solver/, output/ y ui/ sean importables sin importar
# desde que directorio se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core.estado as estado
from ui.app import Aplicacion
from ui.app_matrices import AppMatrices

# Paleta (la misma de las dos herramientas)
FONDO   = "#1E1E2E"
PANEL   = "#181825"
TEXTO   = "#CDD6F4"
MUTED   = "#7F849C"
NARANJA = "#FAB387"
AZUL    = "#89B4FA"
ROJO    = "#F38BA8"


def _boton(padre, texto, detalle, color, comando):
    """Boton del menu con una linea de titulo y una de descripcion."""
    marco = tk.Frame(padre, bg=FONDO)
    marco.pack(fill="x", padx=40, pady=6)

    b = tk.Button(marco, text=texto, bg=color, fg=PANEL,
                  font=("Segoe UI", 11, "bold"), relief="flat",
                  cursor="hand2", pady=8, command=comando)
    b.pack(fill="x")

    tk.Label(marco, text=detalle, bg=FONDO, fg=MUTED,
             font=("Segoe UI", 8), justify="left").pack(anchor="w", pady=(2, 0))
    return b


def mostrar_menu():
    """Ventana de seleccion de herramienta."""
    menu = tk.Tk()
    menu.title("Algebra Lineal - Menu Principal")
    menu.geometry("470x400")
    menu.configure(bg=FONDO)

    tk.Label(menu, text="Calculadora de Algebra Lineal",
             fg=TEXTO, bg=FONDO,
             font=("Segoe UI", 15, "bold")).pack(pady=(26, 2))
    tk.Label(menu, text="Unidad I  ·  Ecuaciones lineales en algebra lineal",
             fg=MUTED, bg=FONDO, font=("Segoe UI", 9)).pack(pady=(0, 20))

    def abrir(destino):
        estado.ir_a(destino)
        menu.destroy()

    _boton(menu, "1.  Solucionador  (Gauss / Gauss-Jordan)",
           "Ecuacion matricial A·x = b, combinacion lineal e independencia.",
           NARANJA, lambda: abrir("gauss"))

    _boton(menu, "2.  Operaciones con matrices y vectores",
           "Suma, resta, escalar, producto y transpuesta, con paso a paso.",
           AZUL, lambda: abrir("matrices"))

    _boton(menu, "Cerrar programa", "", ROJO, menu.destroy)

    menu.mainloop()


def _abrir_ventana(constructor):
    """Crea una ventana Tk nueva, monta la herramienta y espera a que cierre."""
    raiz = tk.Tk()
    constructor(raiz)
    raiz.mainloop()


def iniciar():
    """
    Bucle de navegacion.

    Se repite mientras alguna herramienta pida abrir otra. Cuando una ventana
    se cierra sin dejar destino (boton Cerrar o la X), el bucle termina y el
    programa finaliza.
    """
    estado.ir_a("menu")

    while True:
        destino = estado.tomar_destino()

        if destino is None:
            break
        elif destino == "menu":
            mostrar_menu()
        elif destino == "gauss":
            _abrir_ventana(Aplicacion)
        elif destino == "matrices":
            _abrir_ventana(AppMatrices)
        else:
            break


# Nombre conservado por compatibilidad con versiones anteriores del programa.
def iniciar_menu():
    """Alias de iniciar(): arranca el programa desde el menu."""
    iniciar()


if __name__ == "__main__":
    iniciar()
