# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk

from core.fraccion import desde_texto, Fraccion
import core.algebra as alg
from core.formato import texto_matriz

# ─────────────────────────────────────────────────────────────
# Paleta oscura y Tipografías
# ─────────────────────────────────────────────────────────────
FONDO   = "#1E1E2E"
PANEL   = "#181825"
SUPERF  = "#313244"
BORDE   = "#45475A"
TEXTO   = "#CDD6F4"
MUTED   = "#7F849C"
NARANJA = "#FAB387"
NAR_H   = "#C9946A"
AZUL    = "#89B4FA"
VERDE   = "#A6E3A1"
ROJO    = "#F38BA8"

F_TITULO = ("Segoe UI", 15, "bold")
F_SUBTIT = ("Segoe UI",  9)
F_NORMAL = ("Segoe UI", 10)
F_BOLD   = ("Segoe UI", 10, "bold")
F_MONO   = ("Consolas", 10)
F_BTN    = ("Segoe UI", 11, "bold")

LIMITE = 10

class AppMatrices:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Operaciones con Matrices")
        self.raiz.geometry("1200x800")
        self.raiz.minsize(900, 600)
        self.raiz.configure(bg=FONDO)

        self.casillas_A = []
        self.casillas_B = []
        
        self.filas_A = tk.IntVar(value=2)
        self.cols_A  = tk.IntVar(value=2)
        self.filas_B = tk.IntVar(value=2)
        self.cols_B  = tk.IntVar(value=2)
        
        self.escalar = tk.StringVar(value="2") # Para rA

        self._construir_encabezado()
        self._construir_cuerpo()
        self.generar_cuadriculas()

    def _construir_encabezado(self):
        barra = tk.Frame(self.raiz, bg=PANEL, height=68)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        cnt = tk.Frame(barra, bg=PANEL)
        cnt.pack(side="left", padx=20, fill="y")
        tk.Label(cnt, text="Álgebra de Matrices", bg=PANEL, fg=TEXTO, font=F_TITULO).pack(anchor="sw", pady=(14, 0))
        tk.Label(cnt, text="Suma, Resta, Multiplicación y Transposición", bg=PANEL, fg=MUTED, font=F_SUBTIT).pack(anchor="nw", pady=(0, 10))

        btn_volver = tk.Button(barra, text="Volver al Menú", font=F_BTN,
                               bg=BORDE, fg=TEXTO,
                               activebackground=MUTED, activeforeground=PANEL,
                               relief="flat", padx=15, pady=4, cursor="hand2",
                               command=self.volver_menu)
        btn_volver.pack(side="right", padx=20)
        
        btn_volver.bind("<Enter>", lambda e: btn_volver.config(bg=MUTED, fg=PANEL))
        btn_volver.bind("<Leave>", lambda e: btn_volver.config(bg=BORDE, fg=TEXTO))

    def _construir_cuerpo(self):
        paned = ttk.PanedWindow(self.raiz, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        izq = tk.Frame(paned, bg=FONDO, width=250)
        centro = tk.Frame(paned, bg=FONDO)
        der = tk.Frame(paned, bg=FONDO, width=350)
        
        paned.add(izq, weight=0)
        paned.add(centro, weight=2)
        paned.add(der, weight=1)

        self._panel_dimensiones(izq)
        self._panel_matrices(centro)
        self._panel_operaciones(der)

    def _panel_dimensiones(self, p):
        # Dimensiones Matriz A
        ma = tk.LabelFrame(p, text=" Matriz A ", bg=FONDO, fg=MUTED, font=F_BOLD, padx=10, pady=10)
        ma.pack(fill="x", pady=(0, 10))
        tk.Label(ma, text="Filas (m):", bg=FONDO, fg=TEXTO, font=F_NORMAL).grid(row=0, column=0, sticky="w")
        tk.Spinbox(ma, from_=1, to=LIMITE, width=5, textvariable=self.filas_A, bg=SUPERF, fg=TEXTO, buttonbackground=PANEL, relief="flat", command=self.generar_cuadriculas).grid(row=0, column=1, padx=5, pady=2)
        tk.Label(ma, text="Cols (n):", bg=FONDO, fg=TEXTO, font=F_NORMAL).grid(row=1, column=0, sticky="w")
        tk.Spinbox(ma, from_=1, to=LIMITE, width=5, textvariable=self.cols_A, bg=SUPERF, fg=TEXTO, buttonbackground=PANEL, relief="flat", command=self.generar_cuadriculas).grid(row=1, column=1, padx=5, pady=2)

        # Dimensiones Matriz B
        mb = tk.LabelFrame(p, text=" Matriz B ", bg=FONDO, fg=MUTED, font=F_BOLD, padx=10, pady=10)
        mb.pack(fill="x", pady=(0, 10))
        tk.Label(mb, text="Filas (n):", bg=FONDO, fg=TEXTO, font=F_NORMAL).grid(row=0, column=0, sticky="w")
        tk.Spinbox(mb, from_=1, to=LIMITE, width=5, textvariable=self.filas_B, bg=SUPERF, fg=TEXTO, buttonbackground=PANEL, relief="flat", command=self.generar_cuadriculas).grid(row=0, column=1, padx=5, pady=2)
        tk.Label(mb, text="Cols (p):", bg=FONDO, fg=TEXTO, font=F_NORMAL).grid(row=1, column=0, sticky="w")
        tk.Spinbox(mb, from_=1, to=LIMITE, width=5, textvariable=self.cols_B, bg=SUPERF, fg=TEXTO, buttonbackground=PANEL, relief="flat", command=self.generar_cuadriculas).grid(row=1, column=1, padx=5, pady=2)
        
        btn = tk.Button(p, text="Generar cuadrículas", font=F_NORMAL, bg=SUPERF, fg=TEXTO, relief="flat", command=self.generar_cuadriculas)
        btn.pack(fill="x", pady=5)
        
        btn_limpiar = tk.Button(p, text="Limpiar", font=F_NORMAL, bg=SUPERF, fg=TEXTO, relief="flat", command=self.limpiar)
        btn_limpiar.pack(fill="x", pady=5)

    def _panel_matrices(self, p):
        # Matriz A (Arriba)
        self.frame_A = tk.LabelFrame(p, text=" Entradas Matriz A ", bg=FONDO, fg=AZUL, font=F_BOLD, padx=8, pady=8)
        self.frame_A.pack(fill="both", expand=True, pady=(0, 5))
        self.contenedor_A = tk.Frame(self.frame_A, bg=FONDO)
        self.contenedor_A.pack(anchor="nw")

        # Matriz B (Abajo)
        self.frame_B = tk.LabelFrame(p, text=" Entradas Matriz B ", bg=FONDO, fg=AZUL, font=F_BOLD, padx=8, pady=8)
        self.frame_B.pack(fill="both", expand=True, pady=(5, 0))
        self.contenedor_B = tk.Frame(self.frame_B, bg=FONDO)
        self.contenedor_B.pack(anchor="nw")

    def _panel_operaciones(self, p):
        op_frame = tk.LabelFrame(p, text=" Operaciones ", bg=FONDO, fg=MUTED, font=F_BOLD, padx=10, pady=10)
        op_frame.pack(fill="x", pady=(0, 10))

        tk.Button(op_frame, text="A + B", font=F_BTN, bg=NARANJA, fg=PANEL, relief="flat", command=lambda: self.ejecutar_operacion("suma")).pack(fill="x", pady=3)
        tk.Button(op_frame, text="A - B", font=F_BTN, bg=NARANJA, fg=PANEL, relief="flat", command=lambda: self.ejecutar_operacion("resta")).pack(fill="x", pady=3)
        tk.Button(op_frame, text="A × B", font=F_BTN, bg=NARANJA, fg=PANEL, relief="flat", command=lambda: self.ejecutar_operacion("multiplicacion")).pack(fill="x", pady=3)
        
        # Sub-frame para escalar
        f_esc = tk.Frame(op_frame, bg=FONDO)
        f_esc.pack(fill="x", pady=3)
        tk.Button(f_esc, text="rA (Escalar)", font=F_BTN, bg=NARANJA, fg=PANEL, relief="flat", command=lambda: self.ejecutar_operacion("escalar")).pack(side="left", expand=True, fill="x", padx=(0, 5))
        tk.Entry(f_esc, textvariable=self.escalar, width=5, font=F_MONO, justify="center", bg=SUPERF, fg=TEXTO, relief="flat").pack(side="right")

        tk.Button(op_frame, text="A^T (Transpuesta A)", font=F_BTN, bg=NARANJA, fg=PANEL, relief="flat", command=lambda: self.ejecutar_operacion("transpuesta")).pack(fill="x", pady=3)

        self.txt_resultado = tk.Text(p, wrap="none", font=F_MONO, bg=FONDO, fg=TEXTO, relief="flat", borderwidth=0, state="disabled", padx=16, pady=14)
        self.txt_resultado.pack(fill="both", expand=True)

    def _crear_celdas(self, contenedor, filas, cols, anteriores):
        casillas = []
        for w in contenedor.winfo_children():
            w.destroy()
            
        for i in range(filas):
            fila = []
            for j in range(cols):
                e = tk.Entry(contenedor, width=6, justify="center", font=F_MONO, relief="flat", bg=SUPERF, fg=TEXTO, highlightthickness=1, highlightbackground=BORDE, highlightcolor=NARANJA)
                e.grid(row=i, column=j, padx=2, pady=2)
                
                if i < len(anteriores) and j < len(anteriores[i]):
                    e.insert(0, anteriores[i][j])
                else:
                    e.insert(0, "0")
                    
                fila.append(e)
            casillas.append(fila)
        return casillas

    def generar_cuadriculas(self):
        ant_A = [[c.get() for c in fila] for fila in self.casillas_A] if self.casillas_A else []
        ant_B = [[c.get() for c in fila] for fila in self.casillas_B] if self.casillas_B else []

        self.casillas_A = self._crear_celdas(self.contenedor_A, self.filas_A.get(), self.cols_A.get(), ant_A)
        self.casillas_B = self._crear_celdas(self.contenedor_B, self.filas_B.get(), self.cols_B.get(), ant_B)

    def limpiar(self):
        for fila in self.casillas_A:
            for c in fila:
                c.delete(0, tk.END)
                c.insert(0, "0")
        for fila in self.casillas_B:
            for c in fila:
                c.delete(0, tk.END)
                c.insert(0, "0")
        self.mostrar_resultado("")

    def _leer_matriz(self, casillas, nombre=""):
        matriz = []
        for i, fila_c in enumerate(casillas):
            fila = []
            for j, c in enumerate(fila_c):
                try:
                    fila.append(desde_texto(c.get()))
                except ValueError:
                    messagebox.showerror("Dato inválido", f"Valor incorrecto en la Matriz {nombre} (Fila {i+1}, Col {j+1}).")
                    return None
            matriz.append(fila)
        return matriz

    def ejecutar_operacion(self, operacion):
        A = self._leer_matriz(self.casillas_A, "A")
        if A is None: return
        
        B = self._leer_matriz(self.casillas_B, "B")
        if B is None: return

        resultado = None
        titulo = ""

        try:
            if operacion == "suma":
                resultado = alg.sumar_matrices(A, B)
                titulo = "A + B ="
            elif operacion == "resta":
                resultado = alg.restar_matrices(A, B)
                titulo = "A - B ="
            elif operacion == "multiplicacion":
                resultado = alg.multiplicar_matrices(A, B)
                titulo = "A × B ="
            elif operacion == "escalar":
                try:
                    r = desde_texto(self.escalar.get())
                    resultado = alg.multiplicar_escalar(r, A)
                    titulo = f"{r} × A ="
                except ValueError:
                    messagebox.showerror("Error", "Escalar inválido.")
                    return
            elif operacion == "transpuesta":
                resultado = alg.transponer(A)
                titulo = "A^T ="
                
            # Formatear y mostrar
            if resultado:
                from core.formato import ancho_columna
                ancho = ancho_columna(resultado)
                
                lineas = [titulo]
                for fila in resultado:
                    # Alinea los valores a la derecha y los encierra en corchetes
                    valores = "   ".join("{:>{a}}".format(str(v), a=ancho) for v in fila)
                    lineas.append("  [ " + valores + " ]")
                
                self.mostrar_resultado("\n".join(lineas))

        except ValueError as e:
            messagebox.showerror("Error matemático", str(e))

    def mostrar_resultado(self, texto):
        self.txt_resultado.config(state="normal")
        self.txt_resultado.delete("1.0", tk.END)
        self.txt_resultado.insert(tk.END, "\n" + texto + "\n")
        self.txt_resultado.config(state="disabled")

    def volver_menu(self):
        self.raiz.destroy()
        import main
        main.iniciar_menu()