# -*- coding: utf-8 -*-
# =============================================================================
#  Punto de entrada principal.
#
#  python main.py
#
#  Lanza la interfaz grafica del solucionador de sistemas de ecuaciones
#  lineales.
# =============================================================================

import sys
import os
import tkinter as tk

# Garantiza que el directorio raiz del proyecto este en sys.path para que
# los paquetes core/, solver/, output/ y ui/ sean importables sin importar
# desde que directorio se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import Aplicacion
from ui.app_matrices import AppMatrices

def abrir_gauss(raiz_menu):
    raiz_menu.destroy()
    nueva_raiz = tk.Tk()
    Aplicacion(nueva_raiz)
    nueva_raiz.mainloop()

def abrir_matrices(raiz_menu):
    raiz_menu.destroy()
    nueva_raiz = tk.Tk()
    AppMatrices(nueva_raiz)
    nueva_raiz.mainloop()

def iniciar_menu():
    menu = tk.Tk()
    menu.title("Álgebra Lineal - Menú Principal")
    menu.geometry("400x300")
    menu.configure(bg="#1E1E2E")

    tk.Label(menu, text="Seleccione una herramienta", fg="#CDD6F4", bg="#1E1E2E", font=("Segoe UI", 14, "bold")).pack(pady=30)

    tk.Button(menu, text="1. Solucionador (Gauss-Jordan)", bg="#FAB387", fg="#181825", font=("Segoe UI", 11, "bold"), command=lambda: abrir_gauss(menu)).pack(fill="x", padx=50, pady=10)
    tk.Button(menu, text="2. Operaciones con Matrices", bg="#89B4FA", fg="#181825", font=("Segoe UI", 11, "bold"), command=lambda: abrir_matrices(menu)).pack(fill="x", padx=50, pady=10)

    tk.Button(menu, text="Cerrar programa", bg="#F38BA8", fg="#181825", font=("Segoe UI", 11, "bold"), command=menu.destroy).pack(fill="x", padx=50, pady=(20, 10))

    menu.mainloop()

if __name__ == "__main__":
    iniciar_menu()