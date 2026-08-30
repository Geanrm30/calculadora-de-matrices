# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: gui.py
#  Interfaz grafica y punto de entrada de la aplicacion:
#
#      python gui.py
#
#  Responsabilidades: capturar el sistema, validar los datos ingresados,
#  delegar el calculo en resolutor.py y presentar el informe generado por
#  reporte.py. No contiene logica de calculo.
#
#  Construida sobre tkinter, incluido en la biblioteca estandar de Python.
#  Se limita a la presentacion: no interviene en el procedimiento numerico.
# =============================================================================

import tkinter as tk
from tkinter import messagebox

from fraccion import desde_texto
from clasificacion import INCONSISTENTE
from resolutor import resolver
from reporte import generar


# ---------------------------------------------------------------------------
# Paleta y tipografías
# ---------------------------------------------------------------------------

NARANJA = "#E8722C"
GRIS_FONDO = "#F4F4F2"
GRIS_TEXTO = "#2B2B2B"
BLANCO = "#FFFFFF"
VERDE = "#1E7A4C"
ROJO = "#B3261E"
AZUL = "#1F4E79"

FUENTE_TITULO = ("Segoe UI", 15, "bold")
FUENTE_NORMAL = ("Segoe UI", 10)
FUENTE_ETIQUETA = ("Segoe UI", 10, "bold")
FUENTE_MONO = ("Consolas", 10)

LIMITE = 8  # tamaño máximo del sistema


class Aplicacion:
    """Ventana principal del solucionador."""

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Solucionador de sistemas de ecuaciones lineales")
        self.raiz.geometry("1120x740")
        self.raiz.minsize(900, 600)
        self.raiz.configure(bg=GRIS_FONDO)

        # Estado
        self.casillas = []          # matriz de widgets Entry
        self.n_ecuaciones = tk.IntVar(value=3)
        self.n_variables = tk.IntVar(value=3)
        self.usar_jordan = tk.BooleanVar(value=True)
        self.resultado_actual = None

        self._construir_encabezado()
        self._construir_cuerpo()
        self.generar_casillas()

    # -----------------------------------------------------------------
    # Construcción de la ventana
    # -----------------------------------------------------------------

    def _construir_encabezado(self):
        """Barra superior con el título."""
        barra = tk.Frame(self.raiz, bg=NARANJA, height=64)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text="Sistemas de ecuaciones lineales",
                 bg=NARANJA, fg=BLANCO, font=FUENTE_TITULO).pack(
                     side="left", padx=20, pady=(12, 0), anchor="w")

        tk.Label(barra, text="Método matricial · operaciones elementales por filas",
                 bg=NARANJA, fg=BLANCO, font=FUENTE_NORMAL).pack(
                     side="left", padx=0, pady=(16, 0))

    def _construir_cuerpo(self):
        """Divide la ventana en panel izquierdo (datos) y derecho (resultado)."""
        cuerpo = tk.Frame(self.raiz, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=12)

        izquierda = tk.Frame(cuerpo, bg=GRIS_FONDO, width=360)
        izquierda.pack(side="left", fill="y")
        izquierda.pack_propagate(False)

        derecha = tk.Frame(cuerpo, bg=GRIS_FONDO)
        derecha.pack(side="left", fill="both", expand=True, padx=(14, 0))

        # El orden de empaquetado es significativo: los paneles anclados al
        # extremo inferior se registran primero, de modo que la cuadricula
        # ocupe el espacio restante y los controles permanezcan visibles
        # ante cualquier redimensionamiento.
        self._panel_tamano(izquierda)
        self._panel_acciones(izquierda)
        self._panel_matriz(izquierda)
        self._panel_resultado(derecha)

    def _panel_tamano(self, padre):
        """Selección del número de ecuaciones y variables."""
        marco = tk.LabelFrame(padre, text=" Tamaño del sistema ", bg=GRIS_FONDO,
                              fg=GRIS_TEXTO, font=FUENTE_ETIQUETA, padx=10, pady=10)
        marco.pack(fill="x")

        tk.Label(marco, text="Ecuaciones (m):", bg=GRIS_FONDO,
                 font=FUENTE_NORMAL).grid(row=0, column=0, sticky="w", pady=3)
        tk.Spinbox(marco, from_=1, to=LIMITE, width=5, font=FUENTE_NORMAL,
                   textvariable=self.n_ecuaciones,
                   command=self.generar_casillas).grid(row=0, column=1, padx=8)

        tk.Label(marco, text="Variables (n):", bg=GRIS_FONDO,
                 font=FUENTE_NORMAL).grid(row=1, column=0, sticky="w", pady=3)
        tk.Spinbox(marco, from_=1, to=LIMITE, width=5, font=FUENTE_NORMAL,
                   textvariable=self.n_variables,
                   command=self.generar_casillas).grid(row=1, column=1, padx=8)

        tk.Button(marco, text="Generar cuadrícula", font=FUENTE_NORMAL,
                  command=self.generar_casillas).grid(
                      row=2, column=0, columnspan=2, pady=(8, 0), sticky="we")

    def _panel_matriz(self, padre):
        """Cuadrícula con barras de scroll fijas mediante grid."""
        marco = tk.LabelFrame(padre, text=" Matriz aumentada [A | b] ", bg=GRIS_FONDO,
                              fg=GRIS_TEXTO, font=FUENTE_ETIQUETA, padx=8, pady=8)
        marco.pack(fill="both", expand=True, pady=(10, 8))

        tk.Label(marco, text="Se aceptan enteros (-7), fracciones (3/4), decimales (2.5) y raíces (√4).",
                 bg=GRIS_FONDO, fg="#555555", font=("Segoe UI", 8),
                 justify="left", wraplength=320).pack(side="bottom", anchor="w", pady=(6, 0))

        # Estructura de Scroll
        self.marco_canvas = tk.Frame(marco, bg=GRIS_FONDO)
        self.marco_canvas.pack(fill="both", expand=True, anchor="nw")
        
        self.marco_canvas.grid_rowconfigure(0, weight=1)
        self.marco_canvas.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.marco_canvas, bg=GRIS_FONDO, highlightthickness=0)
        self.scroll_y = tk.Scrollbar(self.marco_canvas, orient="vertical", command=self.canvas.yview)
        self.scroll_x = tk.Scrollbar(self.marco_canvas, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        self.contenedor = tk.Frame(self.canvas, bg=GRIS_FONDO)
        self.ventana_canvas = self.canvas.create_window((0, 0), window=self.contenedor, anchor="nw")
        self.contenedor.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _panel_acciones(self, padre):
        """Botones y opciones, anclados al fondo del panel izquierdo."""
        marco = tk.Frame(padre, bg=GRIS_FONDO)
        marco.pack(fill="x", side="bottom", pady=(8, 0))

        tk.Checkbutton(marco, text="Incluir forma escalonada reducida (Gauss-Jordan)",
                       variable=self.usar_jordan, bg=GRIS_FONDO,
                       font=("Segoe UI", 9)).pack(anchor="w")

        tk.Button(marco, text="RESOLVER", font=("Segoe UI", 11, "bold"),
                  bg=NARANJA, fg=BLANCO, activebackground="#C75F1E",
                  activeforeground=BLANCO, relief="flat", pady=8,
                  command=self.resolver).pack(fill="x", pady=(6, 4))

        tk.Button(marco, text="Limpiar", font=FUENTE_NORMAL,
                  command=self.limpiar).pack(fill="x")

    def _panel_resultado(self, padre):
        """Cuadro de texto donde se muestra el informe."""
        self.etiqueta_estado = tk.Label(padre, text="Ingrese el sistema y presione RESOLVER.",
                                        bg=GRIS_FONDO, fg=GRIS_TEXTO,
                                        font=("Segoe UI", 11, "bold"), anchor="w")
        self.etiqueta_estado.pack(fill="x", pady=(0, 6))

        marco = tk.Frame(padre, bg=GRIS_FONDO)
        marco.pack(fill="both", expand=True)

        barra = tk.Scrollbar(marco, orient="vertical")
        self.texto = tk.Text(marco, wrap="none", font=FUENTE_MONO, bg=BLANCO,
                             fg=GRIS_TEXTO, relief="solid", borderwidth=1,
                             yscrollcommand=barra.set, padx=10, pady=10)
        barra.config(command=self.texto.yview)

        barra_h = tk.Scrollbar(padre, orient="horizontal", command=self.texto.xview)
        self.texto.configure(xscrollcommand=barra_h.set)

        barra.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)
        barra_h.pack(fill="x")

        # Etiquetas de color para resaltar partes del informe
        self.texto.tag_configure("titulo", foreground=AZUL,
                                 font=("Consolas", 10, "bold"))
        self.texto.tag_configure("exito", foreground=VERDE,
                                 font=("Consolas", 10, "bold"))
        self.texto.tag_configure("error", foreground=ROJO,
                                 font=("Consolas", 10, "bold"))

    # -----------------------------------------------------------------
    # Cuadrícula de coeficientes
    # -----------------------------------------------------------------

    def generar_casillas(self):
        """Rehace la cuadrícula conservando los valores que ya estaban escritos."""
        anteriores = self.leer_texto_casillas()

        for hijo in self.contenedor.winfo_children():
            hijo.destroy()

        m = self.n_ecuaciones.get()
        n = self.n_variables.get()
        self.casillas = []

        # Encabezados de columna
        for j in range(n):
            tk.Label(self.contenedor, text="x{}".format(j + 1), bg=GRIS_FONDO,
                     font=FUENTE_ETIQUETA, width=6).grid(row=0, column=j, pady=(0, 4))
        tk.Label(self.contenedor, text="|", bg=GRIS_FONDO,
                 font=FUENTE_ETIQUETA).grid(row=0, column=n, padx=4)
        tk.Label(self.contenedor, text="b", bg=GRIS_FONDO,
                 font=FUENTE_ETIQUETA, width=6).grid(row=0, column=n + 1, pady=(0, 4))

        # Casillas
        for i in range(m):
            fila = []
            for j in range(n + 1):
                columna = j if j < n else j + 1  # deja hueco para la barra
                casilla = tk.Entry(self.contenedor, width=6, justify="center",
                                   font=FUENTE_MONO, relief="solid", borderwidth=1)
                casilla.grid(row=i + 1, column=columna, padx=2, pady=2)

                # Recuperar el valor previo si existía
                if i < len(anteriores) and j < len(anteriores[i]):
                    casilla.insert(0, anteriores[i][j])
                else:
                    casilla.insert(0, "0")

                fila.append(casilla)

            tk.Label(self.contenedor, text="|", bg=GRIS_FONDO,
                     font=FUENTE_ETIQUETA).grid(row=i + 1, column=n, padx=4)
            self.casillas.append(fila)

    def leer_texto_casillas(self):
        """Devuelve el contenido actual de las casillas como texto."""
        datos = []
        for fila in self.casillas:
            datos.append([casilla.get() for casilla in fila])
        return datos

    # -----------------------------------------------------------------
    # Acciones
    # -----------------------------------------------------------------

    def limpiar(self):
        """Pone todas las casillas en cero y vacía el informe."""
        for fila in self.casillas:
            for casilla in fila:
                casilla.delete(0, tk.END)
                casilla.insert(0, "0")
        self.texto.delete("1.0", tk.END)
        self.resultado_actual = None
        self.etiqueta_estado.config(text="Ingrese el sistema y presione RESOLVER.",
                                    fg=GRIS_TEXTO)

    def construir_matriz(self):
        """
        Lee las casillas y las convierte en una matriz de Fracciones.
        Devuelve None si alguna casilla tiene un valor inválido.
        """
        matriz = []
        for i in range(len(self.casillas)):
            fila = []
            for j in range(len(self.casillas[i])):
                texto = self.casillas[i][j].get()
                try:
                    fila.append(desde_texto(texto))
                except (ValueError, ZeroDivisionError):
                    etiqueta = "b{}".format(i + 1) if j == len(self.casillas[i]) - 1 \
                        else "x{} de la ecuación {}".format(j + 1, i + 1)
                    messagebox.showerror(
                        "Dato inválido",
                        "El valor «{}» del coeficiente {} no es válido.\n\n"
                        "Escriba un entero (-7), una fracción (3/4) "
                        "o un decimal (2.5).".format(texto, etiqueta))
                    self.casillas[i][j].focus_set()
                    return None
            matriz.append(fila)
        return matriz

    def resolver(self):
        """Resuelve el sistema y muestra el informe."""
        matriz = self.construir_matriz()
        if matriz is None:
            return

        n_vars = self.n_variables.get()
        jordan = self.usar_jordan.get()

        try:
            resultado = resolver(matriz, n_vars, aplicar_jordan=jordan)
            informe = generar(resultado, incluir_jordan=jordan)
        except Exception as error:
            messagebox.showerror("Error al resolver",
                                 "Ocurrió un problema: {}".format(error))
            return

        self.resultado_actual = resultado
        self.mostrar_informe(informe)

        # Estado con el color según la clasificación
        tipo = resultado["analisis"]["tipo"]
        nombre = resultado["analisis"]["nombre"]
        color = ROJO if tipo == INCONSISTENTE else VERDE
        self.etiqueta_estado.config(text=nombre, fg=color)

    def mostrar_informe(self, informe):
        """Vuelca el informe en el cuadro de texto y resalta algunas líneas."""
        self.texto.delete("1.0", tk.END)
        self.texto.insert("1.0", informe)

        # Resaltado por líneas: títulos de sección y veredictos
        lineas = informe.split("\n")
        for numero in range(len(lineas)):
            linea = lineas[numero]
            inicio = "{}.0".format(numero + 1)
            fin = "{}.end".format(numero + 1)

            if linea.startswith("---") or linea.startswith("==="):
                self.texto.tag_add("titulo", inicio, fin)
            elif ">>" in linea:
                if "INCONSISTENTE" in linea:
                    self.texto.tag_add("error", inicio, fin)
                else:
                    self.texto.tag_add("exito", inicio, fin)
            elif "FALLA" in linea:
                self.texto.tag_add("error", inicio, fin)
            elif "CUMPLE" in linea or "Verificación superada" in linea:
                self.texto.tag_add("exito", inicio, fin)

def main():
    raiz = tk.Tk()
    Aplicacion(raiz)
    raiz.mainloop()


# Punto de entrada de la interfaz gráfica
if __name__ == "__main__":
    main()
