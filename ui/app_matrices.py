# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: ui/app_matrices.py
#  Herramienta de operaciones con matrices y vectores.
#
#  Un vector de R^n es una matriz de una sola columna, asi que las mismas
#  cuadriculas sirven para vectores: basta poner 1 en el numero de columnas.
#  Cuando eso ocurre la herramienta lo detecta y habla de vectores.
#
#  Todo lo escrito aqui se guarda en core/estado.py, de modo que al ir al
#  solucionador y volver, las matrices siguen en su sitio.
# =============================================================================

import tkinter as tk
from tkinter import messagebox, ttk

from core.fraccion import desde_texto, Fraccion
import core.algebra as alg
import core.procedimiento as proc
import core.estado as estado

# ─────────────────────────────────────────────────────────────
# Paleta oscura y tipografías
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
F_BTN_SM = ("Segoe UI",  9)

LIMITE = 10


class AppMatrices:

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Operaciones con matrices y vectores")
        self.raiz.geometry("1280x820")
        self.raiz.minsize(980, 640)
        self.raiz.configure(bg=FONDO)

        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TPanedwindow", background=FONDO)
        s.configure("TScrollbar", background=PANEL, troughcolor=FONDO,
                    arrowcolor=MUTED, borderwidth=0)

        self.casillas_A = []
        self.casillas_B = []
        self.resultado_actual = None     # ultima matriz calculada (Fraccion)

        # ── Recuperacion de lo que se dejo escrito antes de cambiar de
        #    herramienta. Si es la primera vez, se parte de 2x2 en ceros.
        guardado = estado.leer_matrices()
        self._texto_A = guardado["A"]
        self._texto_B = guardado["B"]

        filas_A = len(self._texto_A) if self._texto_A else 2
        cols_A  = len(self._texto_A[0]) if self._texto_A else 2
        filas_B = len(self._texto_B) if self._texto_B else 2
        cols_B  = len(self._texto_B[0]) if self._texto_B else 2

        self.filas_A = tk.IntVar(value=filas_A)
        self.cols_A  = tk.IntVar(value=cols_A)
        self.filas_B = tk.IntVar(value=filas_B)
        self.cols_B  = tk.IntVar(value=cols_B)
        self.escalar = tk.StringVar(value=guardado["escalar"])
        self.ver_pasos = tk.BooleanVar(value=guardado["paso_a_paso"])

        self._construir_encabezado()
        self._construir_cuerpo()
        self.generar_cuadriculas()

        if guardado["salida"]:
            self.mostrar_resultado(guardado["salida"])

        # Cerrar con la X equivale a terminar el programa, pero guardando.
        self.raiz.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ──────────────────────────────────────────────────────────
    # Estado compartido
    # ──────────────────────────────────────────────────────────

    def _guardar_estado(self):
        """Deja las cuadriculas y el ultimo resultado en core/estado.py."""
        estado.guardar_matrices(
            [[c.get() for c in fila] for fila in self.casillas_A],
            [[c.get() for c in fila] for fila in self.casillas_B],
            self.escalar.get(),
            self.txt_resultado.get("1.0", tk.END).rstrip(),
            self.ver_pasos.get())

    def _al_cerrar(self):
        """Cierre con la X: se guarda todo y no se pide otra ventana."""
        self._guardar_estado()
        estado.ir_a(None)
        self.raiz.destroy()

    def _navegar(self, destino):
        """Guarda y pide a main.py que abra otra herramienta."""
        self._guardar_estado()
        estado.ir_a(destino)
        self.raiz.destroy()

    def volver_menu(self):
        self._navegar("menu")

    # ──────────────────────────────────────────────────────────
    # Construcción de la ventana
    # ──────────────────────────────────────────────────────────

    def _construir_encabezado(self):
        barra = tk.Frame(self.raiz, bg=PANEL, height=68)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        cnt = tk.Frame(barra, bg=PANEL)
        cnt.pack(side="left", padx=20, fill="y")
        tk.Label(cnt, text="Operaciones con matrices y vectores",
                 bg=PANEL, fg=TEXTO, font=F_TITULO).pack(anchor="sw", pady=(14, 0))
        tk.Label(cnt, text="Suma · resta · escalar · producto · transpuesta   "
                           "(un vector es una matriz de 1 columna)",
                 bg=PANEL, fg=MUTED, font=F_SUBTIT).pack(anchor="nw", pady=(0, 10))

        btn = tk.Button(barra, text="Volver al Menú", font=F_BTN_SM,
                        bg=BORDE, fg=TEXTO, relief="flat",
                        padx=15, pady=4, cursor="hand2",
                        command=self.volver_menu)
        btn.pack(side="right", padx=20)
        self._hover(btn, MUTED, BORDE)

    def _construir_cuerpo(self):
        paned = ttk.PanedWindow(self.raiz, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        izq    = tk.Frame(paned, bg=FONDO, width=250)
        centro = tk.Frame(paned, bg=FONDO)
        der    = tk.Frame(paned, bg=FONDO, width=420)

        paned.add(izq,    weight=0)
        paned.add(centro, weight=2)
        paned.add(der,    weight=3)

        self._panel_dimensiones(izq)
        self._panel_matrices(centro)
        self._panel_derecho(der)

    # ── Panel izquierdo: dimensiones ──────────────────────────

    def _panel_dimensiones(self, p):
        ma = tk.LabelFrame(p, text=" Tamaño de A ", bg=FONDO, fg=MUTED,
                           font=F_BOLD, padx=10, pady=10)
        ma.pack(fill="x", pady=(0, 10))
        self._spin(ma, 0, "Filas (m):", self.filas_A)
        self._spin(ma, 1, "Cols (n):",  self.cols_A)

        mb = tk.LabelFrame(p, text=" Tamaño de B ", bg=FONDO, fg=MUTED,
                           font=F_BOLD, padx=10, pady=10)
        mb.pack(fill="x", pady=(0, 10))
        self._spin(mb, 0, "Filas (n):", self.filas_B)
        self._spin(mb, 1, "Cols (p):",  self.cols_B)

        tk.Label(p, text="Poné 1 columna para trabajar con vectores de Rⁿ.",
                 bg=FONDO, fg=MUTED, font=("Segoe UI", 8),
                 wraplength=210, justify="left").pack(anchor="w", pady=(0, 8))

        b1 = tk.Button(p, text="Generar cuadrículas", font=F_NORMAL,
                       bg=SUPERF, fg=TEXTO, relief="flat",
                       command=self.generar_cuadriculas)
        b1.pack(fill="x", pady=3)
        self._hover(b1, BORDE, SUPERF)

        b2 = tk.Button(p, text="Intercambiar A ↔ B", font=F_NORMAL,
                       bg=SUPERF, fg=TEXTO, relief="flat",
                       command=self.intercambiar)
        b2.pack(fill="x", pady=3)
        self._hover(b2, BORDE, SUPERF)

        b3 = tk.Button(p, text="Limpiar", font=F_NORMAL,
                       bg=SUPERF, fg=TEXTO, relief="flat",
                       command=self.limpiar)
        b3.pack(fill="x", pady=3)
        self._hover(b3, BORDE, SUPERF)

        tk.Label(p, text="Enteros (-7), fracciones (3/4),\ndecimales (2.5), raíces (√4).",
                 bg=FONDO, fg=MUTED, font=("Segoe UI", 8),
                 justify="left").pack(anchor="w", pady=(10, 0))

    def _spin(self, padre, fila, etiqueta, variable):
        tk.Label(padre, text=etiqueta, bg=FONDO, fg=TEXTO,
                 font=F_NORMAL).grid(row=fila, column=0, sticky="w", pady=2)
        tk.Spinbox(padre, from_=1, to=LIMITE, width=5, textvariable=variable,
                   font=F_MONO, bg=SUPERF, fg=TEXTO, buttonbackground=PANEL,
                   insertbackground=NARANJA, relief="flat",
                   command=self.generar_cuadriculas
                   ).grid(row=fila, column=1, padx=5, pady=2)

    # ── Panel central: las dos cuadrículas ────────────────────

    def _panel_matrices(self, p):
        self.frame_A = tk.LabelFrame(p, text=" Matriz A ", bg=FONDO, fg=AZUL,
                                     font=F_BOLD, padx=8, pady=8)
        self.frame_A.pack(fill="both", expand=True, pady=(0, 5))
        self.contenedor_A = tk.Frame(self.frame_A, bg=FONDO)
        self.contenedor_A.pack(anchor="nw")

        self.frame_B = tk.LabelFrame(p, text=" Matriz B ", bg=FONDO, fg=AZUL,
                                     font=F_BOLD, padx=8, pady=8)
        self.frame_B.pack(fill="both", expand=True, pady=(5, 0))
        self.contenedor_B = tk.Frame(self.frame_B, bg=FONDO)
        self.contenedor_B.pack(anchor="nw")

    # ── Panel derecho: operaciones, envíos y resultado ────────

    def _panel_derecho(self, p):
        ops = tk.LabelFrame(p, text=" Operaciones ", bg=FONDO, fg=MUTED,
                            font=F_BOLD, padx=10, pady=8)
        ops.pack(fill="x")

        rejilla = tk.Frame(ops, bg=FONDO)
        rejilla.pack(fill="x")
        rejilla.grid_columnconfigure(0, weight=1)
        rejilla.grid_columnconfigure(1, weight=1)

        self._op(rejilla, 0, 0, "A + B",  "suma")
        self._op(rejilla, 0, 1, "A − B",  "resta")
        self._op(rejilla, 1, 0, "A × B",  "multiplicacion")
        self._op(rejilla, 1, 1, "Aᵀ",     "transpuesta")

        f_esc = tk.Frame(ops, bg=FONDO)
        f_esc.pack(fill="x", pady=(6, 0))
        be = tk.Button(f_esc, text="r · A   (escalar)", font=F_BTN,
                       bg=NARANJA, fg=PANEL, relief="flat", cursor="hand2",
                       command=lambda: self.ejecutar_operacion("escalar"))
        be.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self._hover(be, NAR_H, NARANJA)
        tk.Entry(f_esc, textvariable=self.escalar, width=6, font=F_MONO,
                 justify="center", bg=SUPERF, fg=TEXTO,
                 insertbackground=NARANJA, relief="flat").pack(side="right")

        tk.Checkbutton(ops, text="Mostrar el paso a paso del cálculo",
                       variable=self.ver_pasos, bg=FONDO, fg=TEXTO,
                       selectcolor=SUPERF, activebackground=FONDO,
                       activeforeground=TEXTO,
                       font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))

        # — Propiedades del producto matriz-vector (teorema visto en clase) —
        props = tk.LabelFrame(p, text=" Propiedades de A·x ", bg=FONDO, fg=MUTED,
                              font=F_BOLD, padx=10, pady=8)
        props.pack(fill="x", pady=(8, 0))

        tk.Label(props, text="u y v son la 1ª y la 2ª columna de B.",
                 bg=FONDO, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        b_suma = tk.Button(props, text="A(u + v) = A·u + A·v", font=F_BTN_SM,
                           bg=SUPERF, fg=TEXTO, relief="flat", cursor="hand2",
                           command=lambda: self.ejecutar_operacion("prop_suma"))
        b_suma.pack(fill="x", pady=2)
        self._hover(b_suma, BORDE, SUPERF)

        b_esc = tk.Button(props, text="A(r · u) = r (A·u)", font=F_BTN_SM,
                          bg=SUPERF, fg=TEXTO, relief="flat", cursor="hand2",
                          command=lambda: self.ejecutar_operacion("prop_escalar"))
        b_esc.pack(fill="x", pady=2)
        self._hover(b_esc, BORDE, SUPERF)

        # — Envío al solucionador —
        env = tk.LabelFrame(p, text=" Enviar al solucionador ", bg=FONDO,
                            fg=MUTED, font=F_BOLD, padx=10, pady=8)
        env.pack(fill="x", pady=(8, 0))

        tk.Label(env, text="B debe tener una sola columna: es el vector b.",
                 bg=FONDO, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        self._envio(env, "Resolver la ecuación  A · x = b", "matricial")
        self._envio(env, "¿Es b combinación lineal de las columnas de A?", "combinacion")
        self._envio(env, "¿Son las columnas de A linealmente independientes?", "independencia")

        # — Resultado —
        res = tk.LabelFrame(p, text=" Resultado ", bg=FONDO, fg=MUTED,
                            font=F_BOLD, padx=6, pady=6)
        res.pack(fill="both", expand=True, pady=(8, 0))

        acciones = tk.Frame(res, bg=FONDO)
        acciones.pack(fill="x", pady=(0, 4))

        self.btn_res_A = tk.Button(acciones, text="Resultado → A", font=F_BTN_SM,
                                   bg=SUPERF, fg=TEXTO, relief="flat",
                                   state="disabled", cursor="hand2",
                                   command=lambda: self.usar_resultado("A"))
        self.btn_res_A.pack(side="left", padx=(0, 4))
        self._hover(self.btn_res_A, BORDE, SUPERF)

        self.btn_res_B = tk.Button(acciones, text="Resultado → B", font=F_BTN_SM,
                                   bg=SUPERF, fg=TEXTO, relief="flat",
                                   state="disabled", cursor="hand2",
                                   command=lambda: self.usar_resultado("B"))
        self.btn_res_B.pack(side="left", padx=(0, 4))
        self._hover(self.btn_res_B, BORDE, SUPERF)

        b_copiar = tk.Button(acciones, text="Copiar", font=F_BTN_SM,
                             bg=SUPERF, fg=TEXTO, relief="flat", cursor="hand2",
                             command=self.copiar_resultado)
        b_copiar.pack(side="right")
        self._hover(b_copiar, BORDE, SUPERF)

        marco = tk.Frame(res, bg=FONDO)
        marco.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(marco, orient="vertical")
        hsb = ttk.Scrollbar(res,   orient="horizontal")

        self.txt_resultado = tk.Text(marco, wrap="none", font=F_MONO,
                                     bg=FONDO, fg=TEXTO, relief="flat",
                                     borderwidth=0, padx=12, pady=10,
                                     yscrollcommand=vsb.set,
                                     xscrollcommand=hsb.set,
                                     state="disabled")
        vsb.config(command=self.txt_resultado.yview)
        hsb.config(command=self.txt_resultado.xview)

        vsb.pack(side="right", fill="y")
        self.txt_resultado.pack(fill="both", expand=True)
        hsb.pack(fill="x")

        self.txt_resultado.tag_configure("titulo", foreground=AZUL,
                                         font=("Consolas", 10, "bold"))
        self.txt_resultado.tag_configure("exito", foreground=VERDE,
                                         font=("Consolas", 10, "bold"))

    def _op(self, padre, fila, columna, texto, operacion):
        b = tk.Button(padre, text=texto, font=F_BTN, bg=NARANJA, fg=PANEL,
                      relief="flat", cursor="hand2", pady=4,
                      command=lambda: self.ejecutar_operacion(operacion))
        b.grid(row=fila, column=columna, sticky="we", padx=2, pady=2)
        self._hover(b, NAR_H, NARANJA)
        return b

    def _envio(self, padre, texto, modo):
        b = tk.Button(padre, text=texto, font=F_BTN_SM, bg=AZUL, fg=PANEL,
                      relief="flat", cursor="hand2", pady=3, anchor="w",
                      command=lambda: self.enviar_al_solucionador(modo))
        b.pack(fill="x", pady=2)
        self._hover(b, "#6C93D9", AZUL)
        return b

    def _hover(self, w, c1, c0):
        w.bind("<Enter>", lambda e: w.config(bg=c1))
        w.bind("<Leave>", lambda e: w.config(bg=c0))

    # ──────────────────────────────────────────────────────────
    # Cuadrículas
    # ──────────────────────────────────────────────────────────

    def _crear_celdas(self, contenedor, filas, cols, anteriores):
        """
        Dibuja una cuadricula de 'filas x cols' conservando lo que ya
        estuviera escrito en las posiciones que siguen existiendo.
        """
        for w in contenedor.winfo_children():
            w.destroy()

        casillas = []
        for i in range(filas):
            fila = []
            for j in range(cols):
                e = tk.Entry(contenedor, width=6, justify="center", font=F_MONO,
                             relief="flat", bg=SUPERF, fg=TEXTO,
                             insertbackground=NARANJA, highlightthickness=1,
                             highlightbackground=BORDE, highlightcolor=NARANJA)
                e.grid(row=i, column=j, padx=2, pady=2)

                if anteriores and i < len(anteriores) and j < len(anteriores[i]):
                    e.insert(0, anteriores[i][j])
                else:
                    e.insert(0, "0")

                fila.append(e)
            casillas.append(fila)
        return casillas

    def generar_cuadriculas(self):
        """Rehace las dos cuadriculas con el tamano indicado en los spinbox."""
        if self.casillas_A:
            ant_A = [[c.get() for c in fila] for fila in self.casillas_A]
        else:
            ant_A = self._texto_A          # lo recuperado del estado compartido

        if self.casillas_B:
            ant_B = [[c.get() for c in fila] for fila in self.casillas_B]
        else:
            ant_B = self._texto_B

        self.casillas_A = self._crear_celdas(
            self.contenedor_A, self.filas_A.get(), self.cols_A.get(), ant_A)
        self.casillas_B = self._crear_celdas(
            self.contenedor_B, self.filas_B.get(), self.cols_B.get(), ant_B)

        self._actualizar_titulos()

    def _actualizar_titulos(self):
        """Llama 'vector' a la cuadricula cuando tiene una sola columna."""
        etiqueta_A = " Vector A ({}×1) " if self.cols_A.get() == 1 else " Matriz A ({}×{}) "
        etiqueta_B = " Vector B ({}×1) " if self.cols_B.get() == 1 else " Matriz B ({}×{}) "

        if self.cols_A.get() == 1:
            self.frame_A.config(text=etiqueta_A.format(self.filas_A.get()))
        else:
            self.frame_A.config(text=etiqueta_A.format(self.filas_A.get(), self.cols_A.get()))

        if self.cols_B.get() == 1:
            self.frame_B.config(text=etiqueta_B.format(self.filas_B.get()))
        else:
            self.frame_B.config(text=etiqueta_B.format(self.filas_B.get(), self.cols_B.get()))

    def limpiar(self):
        for casillas in (self.casillas_A, self.casillas_B):
            for fila in casillas:
                for c in fila:
                    c.delete(0, tk.END)
                    c.insert(0, "0")
        self.resultado_actual = None
        self.btn_res_A.config(state="disabled")
        self.btn_res_B.config(state="disabled")
        self.mostrar_resultado("")

    def intercambiar(self):
        """Pone A en B y B en A, util para invertir el orden de un producto."""
        texto_A = [[c.get() for c in fila] for fila in self.casillas_A]
        texto_B = [[c.get() for c in fila] for fila in self.casillas_B]

        self._texto_A, self._texto_B = texto_B, texto_A
        self.casillas_A, self.casillas_B = [], []

        self.filas_A.set(len(texto_B))
        self.cols_A.set(len(texto_B[0]))
        self.filas_B.set(len(texto_A))
        self.cols_B.set(len(texto_A[0]))

        self.generar_cuadriculas()

    # ──────────────────────────────────────────────────────────
    # Lectura de las casillas
    # ──────────────────────────────────────────────────────────

    def _leer_matriz(self, casillas, nombre):
        """
        Convierte las casillas en una matriz de Fraccion. Si alguna entrada no
        es valida, marca la casilla, avisa y devuelve None.
        """
        matriz = []
        for i, fila_c in enumerate(casillas):
            fila = []
            for j, c in enumerate(fila_c):
                try:
                    fila.append(desde_texto(c.get()))
                except (ValueError, ZeroDivisionError):
                    messagebox.showerror(
                        "Dato inválido",
                        "El valor «{}» de {} (fila {}, columna {}) no es válido.\n\n"
                        "Use entero (-7), fracción (3/4), decimal (2.5) o raíz (√4).".format(
                            c.get(), nombre, i + 1, j + 1))
                    c.config(highlightbackground=ROJO)
                    self.raiz.after(2500, lambda w=c: w.config(highlightbackground=BORDE))
                    c.focus_set()
                    return None
            matriz.append(fila)
        return matriz

    def _leer_escalar(self):
        """Lee el escalar r; devuelve None si no es valido."""
        try:
            return desde_texto(self.escalar.get())
        except (ValueError, ZeroDivisionError):
            messagebox.showerror("Escalar inválido",
                                 "El escalar «{}» no es un número válido.".format(
                                     self.escalar.get()))
            return None

    # ──────────────────────────────────────────────────────────
    # Operaciones
    # ──────────────────────────────────────────────────────────

    def ejecutar_operacion(self, operacion):
        """
        Ejecuta la operacion pedida: primero valida las dimensiones, luego
        calcula con core/algebra.py y, si esta activada la casilla, agrega el
        desarrollo paso a paso de core/procedimiento.py.
        """
        # B solo se lee cuando la operacion la necesita; asi un error en B no
        # impide calcular Aᵀ ni r·A.
        necesita_B = operacion in ("suma", "resta", "multiplicacion",
                                   "prop_suma", "prop_escalar")

        A = self._leer_matriz(self.casillas_A, "A")
        if A is None:
            return

        B = None
        if necesita_B:
            B = self._leer_matriz(self.casillas_B, "B")
            if B is None:
                return

        try:
            if operacion in ("prop_suma", "prop_escalar"):
                self._ejecutar_propiedad(operacion, A, B)
                return

            resultado, titulo, pasos = self._calcular(operacion, A, B)
        except ValueError as ex:
            messagebox.showerror("Dimensiones incompatibles", str(ex))
            return

        if resultado is None:
            return

        lineas = []
        if self.ver_pasos.get() and pasos:
            lineas.extend(pasos)
            lineas.append("")

        lineas.extend(proc.texto_resultado(titulo, resultado))

        self.resultado_actual = resultado
        self.btn_res_A.config(state="normal")
        self.btn_res_B.config(state="normal")
        self.mostrar_resultado("\n".join(lineas))

    def _calcular(self, operacion, A, B):
        """Devuelve (matriz resultado, titulo, lineas del paso a paso)."""
        if operacion == "suma":
            return (alg.sumar_matrices(A, B), "A + B =",
                    proc.pasos_suma(A, B))

        if operacion == "resta":
            return (alg.restar_matrices(A, B), "A − B =",
                    proc.pasos_suma(A, B, resta=True))

        if operacion == "multiplicacion":
            # La validacion vive en algebra.multiplicar_matrices: si las
            # columnas de A no coinciden con las filas de B, lanza ValueError.
            resultado = alg.multiplicar_matrices(A, B)
            titulo = "A × x =" if len(B[0]) == 1 else "A × B ="
            return resultado, titulo, proc.pasos_multiplicacion(A, B)

        if operacion == "escalar":
            r = self._leer_escalar()
            if r is None:
                return None, "", []
            return (alg.multiplicar_escalar(r, A), "{} · A =".format(r),
                    proc.pasos_escalar(r, A))

        if operacion == "transpuesta":
            return alg.transponer(A), "Aᵀ =", proc.pasos_transpuesta(A)

        return None, "", []

    def _ejecutar_propiedad(self, operacion, A, B):
        """
        Comprueba las propiedades del producto matriz-vector tomando u y v de
        las columnas de B: u es la primera columna y v la segunda.
        """
        if len(A[0]) != len(B):
            messagebox.showerror(
                "Dimensiones incompatibles",
                "A tiene {} columnas y los vectores de B tienen {} componentes.\n\n"
                "Para calcular A·u las columnas de A deben coincidir con las "
                "filas de B.".format(len(A[0]), len(B)))
            return

        u = [fila[0] for fila in B]

        if operacion == "prop_escalar":
            r = self._leer_escalar()
            if r is None:
                return
            lineas = proc.pasos_propiedad_escalar(A, r, u)
        else:
            if len(B[0]) < 2:
                messagebox.showerror(
                    "Faltan datos",
                    "Esta propiedad necesita dos vectores.\n\n"
                    "Poné 2 columnas en B: la primera es u y la segunda es v.")
                return
            v = [fila[1] for fila in B]
            lineas = proc.pasos_propiedad_suma(A, u, v)

        self.resultado_actual = None
        self.btn_res_A.config(state="disabled")
        self.btn_res_B.config(state="disabled")
        self.mostrar_resultado("\n".join(lineas))

    def usar_resultado(self, destino):
        """
        Copia la ultima matriz calculada dentro de la cuadricula A o B, para
        encadenar operaciones sin volver a escribir los numeros.
        """
        if self.resultado_actual is None:
            return

        texto = [[str(v) for v in fila] for fila in self.resultado_actual]

        if destino == "A":
            self._texto_A = texto
            self.casillas_A = []
            self.filas_A.set(len(texto))
            self.cols_A.set(len(texto[0]))
        else:
            self._texto_B = texto
            self.casillas_B = []
            self.filas_B.set(len(texto))
            self.cols_B.set(len(texto[0]))

        self.generar_cuadriculas()

    def copiar_resultado(self):
        texto = self.txt_resultado.get("1.0", tk.END).strip()
        if not texto:
            return
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append(texto)

    # ──────────────────────────────────────────────────────────
    # Envío al solucionador
    # ──────────────────────────────────────────────────────────

    def enviar_al_solucionador(self, modo):
        """
        Arma la matriz aumentada y la manda al solucionador, que se abre con
        el sistema cargado y lo resuelve de inmediato.

            "matricial"    ->  [A | b], el sistema A·x = b
            "combinacion"  ->  [A | b], leido como "?es b combinacion lineal
                               de las columnas de A?"
            "independencia"->  [A | 0], el sistema homogeneo que decide si las
                               columnas de A son linealmente independientes
        """
        A = self._leer_matriz(self.casillas_A, "A")
        if A is None:
            return

        filas = len(A)
        columnas = len(A[0])

        if modo == "independencia":
            # El termino independiente es el vector cero.
            celdas = [[c.get() for c in fila] + ["0"] for fila in self.casillas_A]
        else:
            B = self._leer_matriz(self.casillas_B, "B")
            if B is None:
                return

            if len(B[0]) != 1:
                messagebox.showerror(
                    "B no es un vector",
                    "B tiene {} columnas. Para enviar el sistema, B debe ser el "
                    "vector b: poné 1 en «Cols (p)».".format(len(B[0])))
                return

            if len(B) != filas:
                messagebox.showerror(
                    "Dimensiones incompatibles",
                    "A tiene {} filas y b tiene {} componentes.\n\n"
                    "El vector b debe tener una componente por cada fila de A.".format(
                        filas, len(B)))
                return

            celdas = [[c.get() for c in self.casillas_A[i]] +
                      [self.casillas_B[i][0].get()] for i in range(filas)]

        self._guardar_estado()
        # No se fuerza la casilla de analisis en Rn: el propio contexto ya
        # trae la seccion que corresponde a la pregunta enviada.
        estado.enviar_sistema(celdas, filas, columnas, contexto=modo)
        estado.ir_a("gauss")
        self.raiz.destroy()

    # ──────────────────────────────────────────────────────────
    # Salida
    # ──────────────────────────────────────────────────────────

    def mostrar_resultado(self, texto):
        self.txt_resultado.config(state="normal")
        self.txt_resultado.delete("1.0", tk.END)
        if texto:
            self.txt_resultado.insert(tk.END, "\n" + texto + "\n")
        self.txt_resultado.config(state="disabled")
