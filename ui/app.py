# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

from core.fraccion import desde_texto
from core.formato import subindice, nombre_variable, texto_ecuacion
from solver.clasificacion import INCONSISTENTE, DETERMINADO, INDETERMINADO
from solver.resolutor import resolver as _resolver
from output.reporte import (separador, seccion_clasificacion,
                             seccion_solucion, seccion_verificacion)

# ─────────────────────────────────────────────────────────────
# Paleta oscura (Catppuccin Mocha)
# ─────────────────────────────────────────────────────────────
FONDO   = "#1E1E2E"   # fondo principal
PANEL   = "#181825"   # barra lateral / nav
SUPERF  = "#313244"   # superficie (celdas, inputs)
BORDE   = "#45475A"   # bordes
TEXTO   = "#CDD6F4"   # texto principal
MUTED   = "#7F849C"   # texto secundario
NARANJA = "#FAB387"   # acento (botón resolver, hover, etc.)
NAR_H   = "#C9946A"   # naranja hover
VERDE   = "#A6E3A1"   # éxito / CUMPLE
ROJO    = "#F38BA8"   # error / FALLA
AZUL    = "#89B4FA"   # títulos / encabezados
PIV_BG  = "#2D2410"   # fondo columna pivote
HDR_BG  = "#1E2845"   # fondo encabezado de columna

# ─────────────────────────────────────────────────────────────
# Tipografías
# ─────────────────────────────────────────────────────────────
F_TITULO = ("Segoe UI", 15, "bold")
F_SUBTIT = ("Segoe UI",  9)
F_NORMAL = ("Segoe UI", 10)
F_BOLD   = ("Segoe UI", 10, "bold")
F_MONO   = ("Consolas", 10)
F_MONO_B = ("Consolas", 11, "bold")
F_BTN    = ("Segoe UI", 11, "bold")
F_BTN_SM = ("Segoe UI",  9)

LIMITE = 20


class Aplicacion:

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Solucionador de sistemas de ecuaciones lineales")
        self.raiz.geometry("1320x840")
        self.raiz.minsize(1020, 660)
        self.raiz.configure(bg=FONDO)

        s = ttk.Style()
        s.theme_use("clam")
        self._estilos(s)

        self.casillas     = []
        self.n_ecuaciones = tk.IntVar(value=3)
        self.n_variables  = tk.IntVar(value=3)
        self.usar_jordan  = tk.BooleanVar(value=True)
        self.resultado_actual  = None
        self._informe_completo = ""

        # estado paso a paso (combinado: eliminacion + jordan)
        self._todos_pasos = []   # lista de dicts con tipo/operacion/comentario/matriz
        self._idx_paso    = 0
        self._r_proceso   = None

        self._construir_encabezado()
        self._construir_cuerpo()
        self.generar_casillas()
        self.raiz.bind("<Control-Return>", lambda e: self.resolver())

    # ──────────────────────────────────────────────────────────
    # Estilos ttk
    # ──────────────────────────────────────────────────────────

    def _estilos(self, s):
        s.configure("TNotebook", background=FONDO, tabmargins=[2, 6, 0, 0])
        s.configure("TNotebook.Tab",
                    background=PANEL, foreground=MUTED,
                    padding=[16, 8], font=F_BTN_SM)
        s.map("TNotebook.Tab",
              background=[("selected", SUPERF), ("active", FONDO)],
              foreground=[("selected", NARANJA), ("active", TEXTO)],
              font=[("selected", F_BOLD)])

        s.configure("TPanedwindow", background=FONDO)

        s.configure("TSeparator", background=BORDE)

        s.configure("TScrollbar", background=PANEL,
                    troughcolor=FONDO, arrowcolor=MUTED, borderwidth=0)
        s.map("TScrollbar", background=[("active", BORDE)])

        s.configure("Treeview",
                    background=SUPERF, foreground=TEXTO,
                    rowheight=30, fieldbackground=SUPERF, font=F_MONO,
                    borderwidth=0)
        s.configure("Treeview.Heading",
                    background=HDR_BG, foreground=AZUL,
                    font=F_BOLD, relief="flat", padding=[8, 5])
        s.map("Treeview",
              background=[("selected", "#2D3B5A")],
              foreground=[("selected", AZUL)])

    # ──────────────────────────────────────────────────────────
    # Construcción de la ventana
    # ──────────────────────────────────────────────────────────

    def _construir_encabezado(self):
        barra = tk.Frame(self.raiz, bg=PANEL, height=68)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        cnt = tk.Frame(barra, bg=PANEL)
        cnt.pack(side="left", padx=20, fill="y")
        tk.Label(cnt, text="Sistemas de ecuaciones lineales",
                 bg=PANEL, fg=TEXTO, font=F_TITULO).pack(anchor="sw", pady=(14, 0))
        tk.Label(cnt, text="Método matricial  ·  operaciones elementales por filas",
                 bg=PANEL, fg=MUTED, font=F_SUBTIT).pack(anchor="nw", pady=(0, 10))

    def _construir_cuerpo(self):
        self.paned = ttk.PanedWindow(self.raiz, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        izq = tk.Frame(self.paned, bg=FONDO)
        self.paned.add(izq, weight=1)
        self._construir_izquierda(izq)

        der = tk.Frame(self.paned, bg=FONDO)
        self.paned.add(der, weight=3)
        self._construir_derecha(der)

    def _construir_izquierda(self, p):
        self._panel_tamano(p)
        self._panel_acciones(p)
        self._panel_entrada(p)

    def _construir_derecha(self, p):
        # barra de estado + copiar
        barra = tk.Frame(p, bg=PANEL, padx=14, pady=8)
        barra.pack(fill="x")

        self.lbl_estado = tk.Label(barra,
            text="Ingrese el sistema y presione RESOLVER.",
            bg=PANEL, fg=MUTED, font=F_BOLD, anchor="w")
        self.lbl_estado.pack(side="left", fill="x", expand=True)

        btn_g = tk.Button(barra, text="Guardar informe",
            font=F_BTN_SM, bg=SUPERF, fg=TEXTO,
            activebackground=BORDE, activeforeground=TEXTO,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self.guardar_informe)
        btn_g.pack(side="right", padx=(4, 0))
        self._hover(btn_g, BORDE, SUPERF)

        btn_c = tk.Button(barra, text="Copiar informe",
            font=F_BTN_SM, bg=SUPERF, fg=TEXTO,
            activebackground=BORDE, activeforeground=TEXTO,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self.copiar_informe)
        btn_c.pack(side="right")
        self._hover(btn_c, BORDE, SUPERF)

        ttk.Separator(p, orient="horizontal").pack(fill="x")

        self.notebook = ttk.Notebook(p)
        self.notebook.pack(fill="both", expand=True)

        self._crear_tab_proceso()
        self._crear_tab_solucion()

    # ──────────────────────────────────────────────────────────
    # Panel izquierdo
    # ──────────────────────────────────────────────────────────

    def _panel_tamano(self, p):
        m = tk.LabelFrame(p, text=" Tamaño del sistema ",
                          bg=FONDO, fg=MUTED, font=F_BOLD,
                          padx=10, pady=10)
        m.pack(fill="x", pady=(0, 8))

        for r, txt, var in [(0, "Ecuaciones (m):", self.n_ecuaciones),
                             (1, "Variables (n):",  self.n_variables)]:
            tk.Label(m, text=txt, bg=FONDO, fg=TEXTO,
                     font=F_NORMAL).grid(row=r, column=0, sticky="w", pady=3)
            tk.Spinbox(m, from_=1, to=LIMITE, width=5, font=F_MONO,
                       textvariable=var,
                       bg=SUPERF, fg=TEXTO, buttonbackground=PANEL,
                       insertbackground=NARANJA, relief="flat",
                       command=self.generar_casillas
                       ).grid(row=r, column=1, padx=8)

        b = tk.Button(m, text="Generar cuadrícula", font=F_NORMAL,
                      relief="flat", bg=SUPERF, fg=TEXTO,
                      activebackground=BORDE, activeforeground=TEXTO,
                      command=self.generar_casillas)
        b.grid(row=2, column=0, columnspan=2, pady=(8, 0), sticky="we")
        self._hover(b, BORDE, SUPERF)

    def _panel_entrada(self, p):
        m = tk.LabelFrame(p, text=" Matriz aumentada [A | b] ",
                          bg=FONDO, fg=MUTED, font=F_BOLD, padx=8, pady=8)
        m.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(m, text="Enteros (-7), fracciones (3/4), decimales (2.5), raíces (√4).",
                 bg=FONDO, fg=MUTED, font=("Segoe UI", 8),
                 wraplength=320, justify="left"
                 ).pack(side="bottom", anchor="w", pady=(6, 0))

        mc = tk.Frame(m, bg=FONDO)
        mc.pack(fill="both", expand=True)
        mc.grid_rowconfigure(0, weight=1)
        mc.grid_columnconfigure(0, weight=1)

        self._cv_ent = tk.Canvas(mc, bg=FONDO, highlightthickness=0)
        sy = ttk.Scrollbar(mc, orient="vertical",   command=self._cv_ent.yview)
        sx = ttk.Scrollbar(mc, orient="horizontal", command=self._cv_ent.xview)
        self._cv_ent.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self._cv_ent.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")

        self._contenedor = tk.Frame(self._cv_ent, bg=FONDO)
        self._cv_ent.create_window((0, 0), window=self._contenedor, anchor="nw")
        self._contenedor.bind("<Configure>", lambda e: self._cv_ent.configure(
            scrollregion=self._cv_ent.bbox("all")))

    def _panel_acciones(self, p):
        m = tk.Frame(p, bg=FONDO)
        m.pack(fill="x", side="bottom", pady=(0, 8))

        tk.Checkbutton(m, text="Incluir forma escalonada reducida (Gauss-Jordan)",
                       variable=self.usar_jordan,
                       bg=FONDO, fg=TEXTO, selectcolor=SUPERF,
                       activebackground=FONDO, activeforeground=TEXTO,
                       font=("Segoe UI", 9)).pack(anchor="w")

        br = tk.Button(m, text="RESOLVER", font=F_BTN,
                       bg=NARANJA, fg=PANEL,
                       activebackground=NAR_H, activeforeground=PANEL,
                       relief="flat", pady=9, cursor="hand2",
                       command=self.resolver)
        br.pack(fill="x", pady=(8, 2))
        self._hover(br, NAR_H, NARANJA)

        tk.Label(m, text="Ctrl+Enter para resolver rápidamente",
                 bg=FONDO, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="e")

        bl = tk.Button(m, text="Limpiar", font=F_BTN_SM,
                       bg=SUPERF, fg=TEXTO,
                       activebackground=BORDE, activeforeground=TEXTO,
                       relief="flat", pady=5, cursor="hand2",
                       command=self.limpiar)
        bl.pack(fill="x", pady=(4, 0))
        self._hover(bl, BORDE, SUPERF)

    # ──────────────────────────────────────────────────────────
    # Creación de pestañas
    # ──────────────────────────────────────────────────────────

    def _crear_tab_proceso(self):
        tab = tk.Frame(self.notebook, bg=FONDO)
        self.notebook.add(tab, text="  Sistema y eliminación  ")
        self.tab_proceso = tab

        # — Área de info (fija arriba) —
        info = tk.Frame(tab, bg=FONDO, padx=16, pady=12)
        info.pack(fill="x")

        self._lbl_ptitulo = tk.Label(info,
            text="Presione RESOLVER para comenzar.",
            bg=FONDO, fg=MUTED, font=F_BOLD)
        self._lbl_ptitulo.pack(anchor="w")

        self._lbl_poper = tk.Label(info, text="",
            bg=FONDO, fg=TEXTO, font=F_MONO_B)
        self._lbl_poper.pack(anchor="w", pady=(3, 0))

        self._lbl_pcom = tk.Label(info, text="",
            bg=FONDO, fg=MUTED, font=("Segoe UI", 9, "italic"))
        self._lbl_pcom.pack(anchor="w")

        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=16)

        # — Área de matriz (expandible) —
        area = tk.Frame(tab, bg=FONDO)
        area.pack(fill="both", expand=True, padx=16, pady=12)

        cv = tk.Canvas(area, bg=FONDO, highlightthickness=0)
        vsb = ttk.Scrollbar(area, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        cv.pack(fill="both", expand=True)

        self._cv_proc = cv
        self._fm_proc = tk.Frame(cv, bg=FONDO)
        cv.create_window((0, 0), window=self._fm_proc, anchor="nw")

        # — Barra de navegación (fija abajo) —
        nav = tk.Frame(tab, bg=PANEL, pady=10, padx=16)
        nav.pack(fill="x", side="bottom")

        self._p_ini  = self._btn_nav(nav, "⏮ Inicio",    lambda: self._ir(0))
        self._p_prev = self._btn_nav(nav, "◀ Anterior",  self._prev)
        self._lbl_nav = tk.Label(nav, text="", bg=PANEL,
                                  fg=MUTED, font=F_NORMAL, width=14)
        self._lbl_nav.pack(side="left", padx=12)
        self._p_next = self._btn_nav(nav, "Siguiente ▶", self._next)
        self._p_fin  = self._btn_nav(nav, "Final ⏭",    lambda: self._ir(-1))

    def _crear_tab_solucion(self):
        tab = tk.Frame(self.notebook, bg=FONDO)
        self.notebook.add(tab, text="  Solución y verificación  ")
        self.tab_solucion = tab

        # widget de texto (informe estilo antiguo)
        marco = tk.Frame(tab, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=2, pady=2)

        vsb = ttk.Scrollbar(marco, orient="vertical")
        hsb = ttk.Scrollbar(tab,   orient="horizontal")

        self._txt_sol = tk.Text(marco, wrap="none", font=F_MONO,
                                 bg=PANEL, fg=TEXTO,
                                 insertbackground=NARANJA,
                                 selectbackground="#2D3B5A",
                                 selectforeground=AZUL,
                                 relief="flat", borderwidth=0,
                                 padx=16, pady=14,
                                 yscrollcommand=vsb.set,
                                 xscrollcommand=hsb.set,
                                 state="disabled")
        vsb.config(command=self._txt_sol.yview)
        hsb.config(command=self._txt_sol.xview)

        vsb.pack(side="right", fill="y")
        self._txt_sol.pack(fill="both", expand=True)
        hsb.pack(fill="x")

        # tags de color
        self._txt_sol.tag_configure("titulo",
            foreground=AZUL,  font=("Consolas", 10, "bold"))
        self._txt_sol.tag_configure("exito",
            foreground=VERDE, font=("Consolas", 10, "bold"))
        self._txt_sol.tag_configure("error",
            foreground=ROJO,  font=("Consolas", 10, "bold"))

    # ──────────────────────────────────────────────────────────
    # Helpers de UI
    # ──────────────────────────────────────────────────────────

    def _hover(self, w, c1, c0):
        w.bind("<Enter>", lambda e: w.config(bg=c1))
        w.bind("<Leave>", lambda e: w.config(bg=c0))

    def _btn_nav(self, padre, texto, cmd):
        b = tk.Button(padre, text=texto, font=F_BTN_SM,
                      bg=PANEL, fg=TEXTO, relief="flat",
                      cursor="hand2", padx=8, pady=4,
                      activebackground=BORDE, activeforeground=TEXTO,
                      state="disabled", command=cmd)
        b.pack(side="left", padx=4)
        self._hover(b, BORDE, PANEL)
        return b

    def _dibujar_matriz(self, padre, M, n_vars, pivotes=None):
        for w in padre.winfo_children():
            w.destroy()
        if not M:
            return

        CW = 8

        for j in range(n_vars):
            bg = PIV_BG if pivotes and j in pivotes else HDR_BG
            fg = NARANJA if pivotes and j in pivotes else AZUL
            tk.Label(padre, text="x" + subindice(j + 1),
                     bg=bg, fg=fg, font=F_BOLD,
                     width=CW, anchor="center",
                     relief="flat", borderwidth=0,
                     highlightthickness=1, highlightbackground=BORDE
                     ).grid(row=0, column=j, padx=1, pady=1, sticky="nsew")

        tk.Label(padre, text=" | ", bg=FONDO, fg=BORDE,
                 font=F_BOLD).grid(row=0, column=n_vars, padx=4)

        tk.Label(padre, text="b",
                 bg=HDR_BG, fg=AZUL, font=F_BOLD,
                 width=CW, anchor="center",
                 relief="flat", highlightthickness=1, highlightbackground=BORDE
                 ).grid(row=0, column=n_vars + 1, padx=1, pady=1, sticky="nsew")

        for i, fila in enumerate(M):
            for j in range(n_vars):
                bg = PIV_BG if pivotes and j in pivotes else SUPERF
                fg = NARANJA if pivotes and j in pivotes else TEXTO
                tk.Label(padre, text=str(fila[j]),
                         bg=bg, fg=fg, font=F_MONO,
                         width=CW, anchor="center",
                         relief="flat", highlightthickness=1, highlightbackground=BORDE
                         ).grid(row=i + 1, column=j, padx=1, pady=1, sticky="nsew")

            tk.Label(padre, text=" | ", bg=FONDO, fg=BORDE,
                     font=F_BOLD).grid(row=i + 1, column=n_vars, padx=4)

            tk.Label(padre, text=str(fila[n_vars]),
                     bg=SUPERF, fg=TEXTO, font=F_MONO,
                     width=CW, anchor="center",
                     relief="flat", highlightthickness=1, highlightbackground=BORDE
                     ).grid(row=i + 1, column=n_vars + 1, padx=1, pady=1, sticky="nsew")

    def _escribir_txt(self, widget, contenido):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", contenido)
        # aplicar tags línea a línea
        lineas = contenido.split("\n")
        for num, linea in enumerate(lineas):
            ini = "{}.0".format(num + 1)
            fin = "{}.end".format(num + 1)
            if linea.startswith("---") or linea.startswith("==="):
                widget.tag_add("titulo", ini, fin)
            elif ">>" in linea:
                if "INCONSISTENTE" in linea:
                    widget.tag_add("error", ini, fin)
                else:
                    widget.tag_add("exito", ini, fin)
            elif "FALLA" in linea:
                widget.tag_add("error", ini, fin)
            elif "CUMPLE" in linea or "superada" in linea:
                widget.tag_add("exito", ini, fin)
        widget.config(state="disabled")

    # ──────────────────────────────────────────────────────────
    # Cuadrícula de entrada
    # ──────────────────────────────────────────────────────────

    def generar_casillas(self):
        anteriores = self.leer_texto_casillas()
        for h in self._contenedor.winfo_children():
            h.destroy()

        m = self.n_ecuaciones.get()
        n = self.n_variables.get()
        self.casillas = []

        for j in range(n):
            tk.Label(self._contenedor, text="x" + subindice(j + 1),
                     bg=FONDO, fg=AZUL, font=F_BOLD,
                     width=6).grid(row=0, column=j, pady=(0, 4))
        tk.Label(self._contenedor, text="|", bg=FONDO,
                 fg=MUTED, font=F_BOLD).grid(row=0, column=n, padx=4)
        tk.Label(self._contenedor, text="b", bg=FONDO, fg=AZUL,
                 font=F_BOLD, width=6).grid(row=0, column=n + 1, pady=(0, 4))

        for i in range(m):
            fila = []
            for j in range(n + 1):
                col = j if j < n else j + 1
                e = tk.Entry(self._contenedor, width=6, justify="center",
                             font=F_MONO, relief="flat", borderwidth=0,
                             bg=SUPERF, fg=TEXTO,
                             insertbackground=NARANJA,
                             highlightthickness=1,
                             highlightbackground=BORDE,
                             highlightcolor=NARANJA)
                e.grid(row=i + 1, column=col, padx=2, pady=2)
                if i < len(anteriores) and j < len(anteriores[i]):
                    e.insert(0, anteriores[i][j])
                else:
                    e.insert(0, "0")
                fila.append(e)
            tk.Label(self._contenedor, text="|", bg=FONDO,
                     fg=MUTED, font=F_BOLD).grid(row=i + 1, column=n, padx=4)
            self.casillas.append(fila)

    def leer_texto_casillas(self):
        return [[c.get() for c in fila] for fila in self.casillas]

    # ──────────────────────────────────────────────────────────
    # Acciones
    # ──────────────────────────────────────────────────────────

    def construir_matriz(self):
        matriz = []
        for i, fila_c in enumerate(self.casillas):
            fila = []
            n = len(fila_c) - 1
            for j, c in enumerate(fila_c):
                try:
                    fila.append(desde_texto(c.get()))
                except (ValueError, ZeroDivisionError):
                    etiq = ("b{}".format(i + 1) if j == n
                            else "x{} ec.{}".format(subindice(j + 1), i + 1))
                    messagebox.showerror("Dato inválido",
                        "El valor «{}» en {} no es válido.\n\n"
                        "Use entero (-7), fracción (3/4) o decimal (2.5).".format(
                            c.get(), etiq))
                    c.config(highlightbackground=ROJO)
                    self.raiz.after(2500, lambda w=c: w.config(highlightbackground=BORDE))
                    c.focus_set()
                    return None
            matriz.append(fila)
        return matriz

    def resolver(self):
        matriz = self.construir_matriz()
        if matriz is None:
            return

        n_vars = self.n_variables.get()
        jordan = self.usar_jordan.get()

        try:
            resultado = _resolver(matriz, n_vars, aplicar_jordan=jordan)
        except Exception as ex:
            messagebox.showerror("Error al resolver",
                                 "Ocurrió un problema: {}".format(ex))
            return

        self.resultado_actual = resultado

        # Informe completo (para Copiar)
        from output.reporte import generar
        self._informe_completo = generar(resultado, incluir_jordan=jordan)

        tipo   = resultado["analisis"]["tipo"]
        nombre = resultado["analisis"]["nombre"]
        color  = ROJO if tipo == INCONSISTENTE else VERDE
        self.lbl_estado.config(text=nombre, fg=color)

        self._poblar_proceso(resultado)
        self._poblar_solucion(resultado, jordan)
        self.notebook.select(0)

    def limpiar(self):
        for fila in self.casillas:
            for c in fila:
                c.delete(0, tk.END)
                c.insert(0, "0")
        self.resultado_actual  = None
        self._informe_completo = ""
        self.lbl_estado.config(
            text="Ingrese el sistema y presione RESOLVER.", fg=MUTED)

        self._lbl_ptitulo.config(text="Presione RESOLVER para comenzar.")
        self._lbl_poper.config(text="")
        self._lbl_pcom.config(text="")
        self._lbl_nav.config(text="")
        for w in self._fm_proc.winfo_children():
            w.destroy()
        for b in (self._p_ini, self._p_prev, self._p_next, self._p_fin):
            b.config(state="disabled")

        self._escribir_txt(self._txt_sol, "")

    def copiar_informe(self):
        if not self._informe_completo:
            return
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append(self._informe_completo)
        pt = self.lbl_estado.cget("text")
        pc = self.lbl_estado.cget("fg")
        self.lbl_estado.config(text="Informe copiado al portapapeles.", fg=VERDE)
        self.raiz.after(2500, lambda: self.lbl_estado.config(text=pt, fg=pc))

    def guardar_informe(self):
        if not self._informe_completo:
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar informe",
            initialfile="informe.txt")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._informe_completo)
            pt = self.lbl_estado.cget("text")
            pc = self.lbl_estado.cget("fg")
            self.lbl_estado.config(text="Informe guardado.", fg=VERDE)
            self.raiz.after(2500, lambda: self.lbl_estado.config(text=pt, fg=pc))
        except OSError as ex:
            messagebox.showerror("Error al guardar", str(ex))

    # ──────────────────────────────────────────────────────────
    # Tab 1 — Proceso (Sistema + Eliminación + Jordan)
    # ──────────────────────────────────────────────────────────

    def _poblar_proceso(self, r):
        self._r_proceso = r
        n_vars  = r["n_vars"]
        pivotes = r["columnas_pivote"]

        # Construir lista unificada de pasos
        # Paso 0 = sistema original
        # Pasos 1..N_elim = eliminación
        # Pasos N_elim+1.. = jordan
        self._todos_pasos = []

        for p in r["pasos"]:
            self._todos_pasos.append({
                "tipo": "Eliminación",
                "operacion": p["operacion"],
                "comentario": p["comentario"],
                "matriz": p["matriz"],
            })

        jordan = r.get("pasos_jordan")
        if jordan is not None:
            for p in jordan:
                self._todos_pasos.append({
                    "tipo": "Gauss-Jordan",
                    "operacion": p["operacion"],
                    "comentario": p["comentario"],
                    "matriz": p["matriz"],
                })

        self._idx_paso = 0
        self._actualizar_proceso()

    def _actualizar_proceso(self):
        r       = self._r_proceso
        pasos   = self._todos_pasos
        idx     = self._idx_paso
        n_vars  = r["n_vars"]
        pivotes = r["columnas_pivote"]
        total   = len(pasos)

        n_elim   = len(r["pasos"])
        jordan   = r.get("pasos_jordan")
        n_jordan = len(jordan) if jordan else 0

        if idx == 0:
            # Mostrar sistema original
            # Cuántos pasos hay de cada tipo
            partes = []
            if n_elim > 0:
                partes.append("{} paso{} de eliminación".format(
                    n_elim, "s" if n_elim != 1 else ""))
            if n_jordan > 0:
                partes.append("{} paso{} de Gauss-Jordan".format(
                    n_jordan, "s" if n_jordan != 1 else ""))
            resumen = " · ".join(partes) if partes else "matriz ya escalonada"

            self._lbl_ptitulo.config(
                text="Sistema original — {} × {}   ({})".format(
                    r["n_ecuaciones"], n_vars, resumen),
                fg=AZUL)
            self._lbl_poper.config(text="")
            self._lbl_pcom.config(text="")

            # Dibujar: ecuaciones + matriz inicial
            self._dibujar_sistema_completo(r["original"], n_vars, pivotes)

        elif idx <= total:
            p = pasos[idx - 1]
            tipo = p["tipo"]

            if tipo == "Eliminación":
                num_local   = idx
                total_local = n_elim
            else:
                num_local   = idx - n_elim
                total_local = n_jordan

            self._lbl_ptitulo.config(
                text="{} — Paso {} / {}".format(tipo, num_local, total_local),
                fg=NARANJA if tipo == "Eliminación" else AZUL)
            self._lbl_poper.config(text=p["operacion"])
            self._lbl_pcom.config(text=p["comentario"])
            self._dibujar_matriz(self._fm_proc, p["matriz"], n_vars, pivotes)

        else:
            # Vista resumen: todos los pasos apilados
            self._lbl_ptitulo.config(
                text="Proceso completo — todos los pasos",
                fg=VERDE)
            self._lbl_poper.config(text="")
            self._lbl_pcom.config(text="")
            self._dibujar_todos_los_pasos()

        # Fijar scrollregion y rueda tras completar el dibujo
        self._fm_proc.update_idletasks()
        h = self._fm_proc.winfo_reqheight()
        w = self._fm_proc.winfo_reqwidth()
        self._cv_proc.configure(scrollregion=(0, 0, w, h))
        self._cv_proc.yview_moveto(0)
        self._ligar_rueda(self._fm_proc)

        nav_text = "Completo" if idx > total else "{} / {}".format(idx, total)
        self._lbl_nav.config(text=nav_text)
        self._p_ini.config( state="normal" if idx > 0         else "disabled")
        self._p_prev.config(state="normal" if idx > 0         else "disabled")
        self._p_next.config(state="normal" if idx <= total     else "disabled")
        self._p_fin.config( state="normal" if idx <= total     else "disabled")

    def _ligar_rueda(self, widget):
        widget.bind("<MouseWheel>",
            lambda e: self._cv_proc.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        for child in widget.winfo_children():
            self._ligar_rueda(child)

    def _dibujar_sistema_completo(self, M, n_vars, pivotes):
        """En el paso 0 muestra las ecuaciones y luego la matriz."""
        for w in self._fm_proc.winfo_children():
            w.destroy()

        r = self._r_proceso

        # Ecuaciones
        tk.Label(self._fm_proc, text="Sistema ingresado:",
                 bg=FONDO, fg=MUTED, font=F_BTN_SM,
                 anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 4))

        for i, fila in enumerate(M):
            tk.Label(self._fm_proc, text="  " + texto_ecuacion(fila, n_vars),
                     bg=FONDO, fg=TEXTO, font=F_MONO,
                     anchor="w").grid(row=i + 1, column=0, sticky="w")

        # Separador visual
        tk.Label(self._fm_proc, text="", bg=FONDO
                 ).grid(row=len(M) + 1, column=0, pady=4)

        # Subtítulo
        tk.Label(self._fm_proc, text="Matriz aumentada [A | b]:",
                 bg=FONDO, fg=MUTED, font=F_BTN_SM,
                 anchor="w").grid(row=len(M) + 2, column=0, sticky="w", pady=(0, 4))

        # Matriz
        mat_frame = tk.Frame(self._fm_proc, bg=FONDO)
        mat_frame.grid(row=len(M) + 3, column=0, sticky="w")
        self._dibujar_matriz(mat_frame, M, n_vars, pivotes)

        # Nota homogéneo
        if r["analisis"]["homogeneo"]:
            tk.Label(self._fm_proc,
                     text="\nSistema homogéneo — siempre consistente "
                          "(admite al menos la solución trivial).",
                     bg=FONDO, fg=MUTED, font=("Segoe UI", 9),
                     anchor="w").grid(row=len(M) + 4, column=0, sticky="w", pady=(4, 0))

    def _dibujar_todos_los_pasos(self):
        for w in self._fm_proc.winfo_children():
            w.destroy()

        r       = self._r_proceso
        n_vars  = r["n_vars"]
        pivotes = r["columnas_pivote"]
        pasos   = self._todos_pasos
        n_elim  = len(r["pasos"])

        row = 0

        # ── Sistema original ──────────────────────────────────
        tk.Label(self._fm_proc, text="Sistema ingresado:",
                 bg=FONDO, fg=MUTED, font=F_BTN_SM,
                 anchor="w").grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1

        for fila in r["original"]:
            tk.Label(self._fm_proc,
                     text="  " + texto_ecuacion(fila, n_vars),
                     bg=FONDO, fg=TEXTO, font=F_MONO,
                     anchor="w").grid(row=row, column=0, sticky="w")
            row += 1

        tk.Label(self._fm_proc, text="", bg=FONDO
                 ).grid(row=row, column=0, pady=4)
        row += 1

        tk.Label(self._fm_proc, text="Matriz aumentada [A | b]:",
                 bg=FONDO, fg=MUTED, font=F_BTN_SM,
                 anchor="w").grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1

        mf0 = tk.Frame(self._fm_proc, bg=FONDO)
        mf0.grid(row=row, column=0, sticky="w")
        self._dibujar_matriz(mf0, r["original"], n_vars, pivotes)
        row += 1

        # ── Cada paso ─────────────────────────────────────────
        for i, p in enumerate(pasos):
            tk.Label(self._fm_proc, text="─" * 60,
                     bg=FONDO, fg=BORDE, font=F_MONO,
                     anchor="w").grid(row=row, column=0, sticky="w", pady=(10, 4))
            row += 1

            tipo = p["tipo"]
            if tipo == "Eliminación":
                num_local   = i + 1
                total_local = n_elim
                color_tipo  = NARANJA
            else:
                num_local   = i - n_elim + 1
                j_pasos     = r.get("pasos_jordan") or []
                total_local = len(j_pasos)
                color_tipo  = AZUL

            tk.Label(self._fm_proc,
                     text="{} — Paso {} / {}".format(tipo, num_local, total_local),
                     bg=FONDO, fg=color_tipo, font=F_BOLD,
                     anchor="w").grid(row=row, column=0, sticky="w")
            row += 1

            tk.Label(self._fm_proc, text=p["operacion"],
                     bg=FONDO, fg=TEXTO, font=F_MONO_B,
                     anchor="w").grid(row=row, column=0, sticky="w", pady=(2, 0))
            row += 1

            if p.get("comentario"):
                tk.Label(self._fm_proc, text=p["comentario"],
                         bg=FONDO, fg=MUTED,
                         font=("Segoe UI", 9, "italic"),
                         anchor="w").grid(row=row, column=0, sticky="w")
                row += 1

            tk.Label(self._fm_proc, text="", bg=FONDO
                     ).grid(row=row, column=0, pady=3)
            row += 1

            mf = tk.Frame(self._fm_proc, bg=FONDO)
            mf.grid(row=row, column=0, sticky="w")
            self._dibujar_matriz(mf, p["matriz"], n_vars, pivotes)
            row += 1

    def _ir(self, idx):
        total = len(self._todos_pasos)
        self._idx_paso = (total + 1) if idx == -1 else max(0, min(idx, total + 1))
        self._actualizar_proceso()

    def _prev(self):
        if self._idx_paso > 0:
            self._idx_paso -= 1
            self._actualizar_proceso()

    def _next(self):
        total = len(self._todos_pasos)
        if self._idx_paso <= total:
            self._idx_paso += 1
            self._actualizar_proceso()

    # ──────────────────────────────────────────────────────────
    # Tab 2 — Solución y Verificación (informe texto)
    # ──────────────────────────────────────────────────────────

    def _poblar_solucion(self, r, jordan):
        numero = 3
        if jordan and r.get("pasos_jordan") is not None:
            numero = 4

        bloques = [
            separador("="),
            "  CLASIFICACIÓN · SOLUCIÓN · VERIFICACIÓN",
            separador("="),
            seccion_clasificacion(r, numero),
            seccion_solucion(r, numero + 1),
            seccion_verificacion(r, numero + 2),
            "\n" + separador("="),
        ]
        texto = "\n".join(bloques)
        self._escribir_txt(self._txt_sol, texto)


def main():
    raiz = tk.Tk()
    Aplicacion(raiz)
    raiz.mainloop()
