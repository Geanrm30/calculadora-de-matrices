# -*- coding: utf-8 -*-
"""
Visor de teoremas del curso (tkinter): muestra el catálogo de core/teoremas.py
en una ventana desplazable organizada por sesión y tema.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import tkinter as tk
from tkinter import ttk

import core.estado as estado
from core.teoremas import TEOREMAS

FONDO   = "#1E1E2E"
PANEL   = "#181825"
SUPERF  = "#313244"
BORDE   = "#45475A"
TEXTO   = "#CDD6F4"
MUTED   = "#7F849C"
NARANJA = "#FAB387"
AZUL    = "#89B4FA"


class AppTeoremas:
    """Ventana con todos los teoremas usados por el programa."""

    def __init__(self, raiz):
        self.raiz = raiz
        raiz.title("Teoremas")
        raiz.geometry("860x700")
        raiz.minsize(640, 480)
        raiz.configure(bg=FONDO)
        raiz.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        barra = tk.Frame(raiz, bg=PANEL, height=68)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text="Teoremas y criterios", bg=PANEL, fg=TEXTO,
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=20)
        b = tk.Button(barra, text="Volver al Menú", font=("Segoe UI", 9),
                      bg=BORDE, fg=TEXTO, activebackground=MUTED,
                      activeforeground=PANEL, relief="flat", padx=15, pady=4,
                      cursor="hand2", command=self.volver_menu)
        b.pack(side="right", padx=20)

        cuerpo = tk.Frame(raiz, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=10, pady=10)

        self.lienzo = tk.Canvas(cuerpo, bg=FONDO, highlightthickness=0)
        sb = ttk.Scrollbar(cuerpo, orient="vertical", command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.lienzo.pack(side="left", fill="both", expand=True)

        self.interior = tk.Frame(self.lienzo, bg=FONDO)
        self._ventana = self.lienzo.create_window((0, 0), window=self.interior,
                                                  anchor="nw")
        self.interior.bind("<Configure>", lambda e: self.lienzo.configure(
            scrollregion=self.lienzo.bbox("all")))
        self.lienzo.bind("<Configure>", self._ajustar_ancho)
        raiz.bind("<MouseWheel>", lambda e: self.lienzo.yview_scroll(
            int(-e.delta / 120), "units"))

        for i, (nombre, enunciado, uso) in enumerate(TEOREMAS, start=1):
            self._tarjeta(i, nombre, enunciado, uso)

    def _ajustar_ancho(self, evento):
        self.lienzo.itemconfigure(self._ventana, width=evento.width)
        for w in self.interior.winfo_children():
            for lbl in w.winfo_children():
                lbl.configure(wraplength=max(evento.width - 60, 200))

    def _tarjeta(self, n, nombre, enunciado, uso):
        t = tk.Frame(self.interior, bg=SUPERF, padx=14, pady=10)
        t.pack(fill="x", pady=5)
        tk.Label(t, text="{}.  {}".format(n, nombre), bg=SUPERF, fg=NARANJA,
                 font=("Segoe UI", 11, "bold"), anchor="w",
                 justify="left", wraplength=780).pack(fill="x")
        tk.Label(t, text=enunciado, bg=SUPERF, fg=TEXTO,
                 font=("Segoe UI", 10), anchor="w", justify="left",
                 wraplength=780).pack(fill="x", pady=(4, 4))
        tk.Label(t, text="Se usa en: " + uso, bg=SUPERF, fg=AZUL,
                 font=("Segoe UI", 9, "italic"), anchor="w",
                 justify="left", wraplength=780).pack(fill="x")

    def _al_cerrar(self):
        estado.ir_a(None)
        self.raiz.destroy()

    def volver_menu(self):
        estado.ir_a("menu")
        self.raiz.destroy()
