# -*- coding: utf-8 -*-
"""
Instalación automática del componente gráfico (PySide6) la primera vez que se
abre la calculadora. Muestra una ventana de espera con una barra de progreso;
si no se puede mostrar una ventana, informa por consola.

Este módulo solo usa la biblioteca estándar: se ejecuta ANTES de que exista
PySide6, así que no puede depender de él.
MTM0120 Álgebra Lineal — Universidad Americana.
"""

import importlib
import importlib.util
import queue
import subprocess
import sys
import threading

PAQUETE = "PySide6-Essentials>=6.6"   # lo que se instala con pip (versión ligera)
MODULO = "PySide6"                    # lo que se importa

# Colores de la ventana de espera (los mismos del tema oscuro del programa).
FONDO, PANEL, TEXTO, MUTED = "#1E1E2E", "#181825", "#CDD6F4", "#7F849C"
NARANJA, ROJO, SUPERF = "#FAB387", "#F38BA8", "#313244"


def hay_modulo(nombre):
    importlib.invalidate_caches()
    return importlib.util.find_spec(nombre) is not None


# ─────────────────────────────────────────────────────────────
# Instalación (sin interfaz): llama a pip y avisa de cada línea
# ─────────────────────────────────────────────────────────────

class Instalacion:
    """Ejecuta pip paso a paso; `al_linea(texto)` recibe lo que va ocurriendo."""

    def __init__(self, modulo, paquete, al_linea):
        self.modulo = modulo
        self.paquete = paquete
        self.al_linea = al_linea
        self.cancelada = False
        self._proceso = None

    def cancelar(self):
        self.cancelada = True
        try:
            if self._proceso is not None:
                self._proceso.terminate()
        except OSError:
            pass

    def _pip(self, argumentos):
        """Corre `python -m <argumentos>` mostrando su salida. True si terminó bien."""
        banderas = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # sin consola extra
        try:
            self._proceso = subprocess.Popen(
                [sys.executable, "-m"] + argumentos,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                errors="replace", creationflags=banderas)
        except OSError as ex:
            self.al_linea("No se pudo ejecutar pip: {}".format(ex))
            return False
        for linea in self._proceso.stdout:
            if self.cancelada:
                break
            linea = linea.strip()
            if linea:
                self.al_linea(linea)
        self._proceso.wait()
        return self._proceso.returncode == 0 and not self.cancelada

    def ejecutar(self):
        """Devuelve True si al terminar el módulo ya se puede importar."""
        if hay_modulo(self.modulo):
            return True
        # Algunas instalaciones de Python no traen pip.
        if not hay_modulo("pip"):
            self.al_linea("Preparando el instalador de paquetes (pip)...")
            self._pip(["ensurepip", "--upgrade"])
        base = ["pip", "install", "--disable-pip-version-check", self.paquete]
        # Primero la instalación normal; si no hay permisos, solo para el usuario.
        for extra in ([], ["--user"]):
            if self.cancelada:
                return False
            if self._pip(base + extra) and hay_modulo(self.modulo):
                return True
        return False


def _amigable(linea):
    """
    Traduce las líneas de pip a algo que entienda cualquier persona. Devuelve
    None para las líneas técnicas que no vale la pena mostrar.
    """
    bajo = linea.lower()
    if bajo.startswith("collecting"):
        return "Buscando los componentes necesarios..."
    if bajo.startswith(("downloading", "using cached")):
        partes = linea.split()
        nombre = partes[1].split("-")[0] if len(partes) > 1 else ""
        return "Descargando {}...".format(nombre) if nombre else "Descargando..."
    if bajo.startswith("defaulting to user installation"):
        return "Instalando solo para tu usuario..."
    if bajo.startswith("installing"):
        return "Instalando (esto puede tardar un poco)..."
    if bajo.startswith("successfully"):
        return "¡Listo!"
    if bajo.startswith("preparando"):
        return linea
    return None


# ─────────────────────────────────────────────────────────────
# Ventana de espera
# ─────────────────────────────────────────────────────────────

def _con_ventana(modulo, paquete):
    """
    Muestra la ventana de espera. Devuelve True/False según el resultado, o
    None si no se pudo abrir ninguna ventana (entonces se usa la consola).
    """
    try:
        import tkinter as tk
        from tkinter import ttk
        raiz = tk.Tk()
    except Exception:                       # sin tkinter o sin pantalla
        return None

    raiz.title("Calculadora de Álgebra Lineal")
    raiz.configure(bg=FONDO)
    raiz.resizable(False, False)
    ancho, alto = 520, 270
    raiz.geometry("{}x{}+{}+{}".format(
        ancho, alto, (raiz.winfo_screenwidth() - ancho) // 2,
        (raiz.winfo_screenheight() - alto) // 2))
    raiz.attributes("-topmost", True)

    tk.Label(raiz, text="Calculadora de Álgebra Lineal", bg=FONDO, fg=TEXTO,
             font=("Segoe UI", 15, "bold")).pack(pady=(26, 2))
    titulo = tk.Label(raiz, text="Preparando todo para la primera vez",
                      bg=FONDO, fg=NARANJA, font=("Segoe UI", 10, "bold"))
    titulo.pack()
    detalle = tk.Label(
        raiz, bg=FONDO, fg=MUTED, font=("Segoe UI", 10), justify="center",
        wraplength=460,
        text="Se está descargando un componente necesario.\n"
             "Hace falta internet y puede tardar un par de minutos.\n"
             "Solo ocurre esta vez; no cierres esta ventana.")
    detalle.pack(pady=(12, 14))

    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure("Calc.Horizontal.TProgressbar", troughcolor=SUPERF,
                     background=NARANJA, bordercolor=FONDO, lightcolor=NARANJA,
                     darkcolor=NARANJA, thickness=10)
    barra = ttk.Progressbar(raiz, mode="indeterminate", length=420,
                            style="Calc.Horizontal.TProgressbar")
    barra.pack()
    barra.start(14)

    estado = tk.Label(raiz, text="Conectando...", bg=FONDO, fg=TEXTO,
                      font=("Segoe UI", 9), wraplength=460)
    estado.pack(pady=(12, 0))
    boton = tk.Button(raiz, text="Cerrar", bg=SUPERF, fg=TEXTO, relief="flat",
                      font=("Segoe UI", 10), padx=20, pady=5,
                      activebackground="#45475A", activeforeground=TEXTO,
                      command=raiz.destroy)

    cola = queue.Queue()
    trabajo = Instalacion(modulo, paquete, cola.put)
    resultado = {"ok": False}

    def hilo():
        resultado["ok"] = trabajo.ejecutar()
        cola.put(None)                      # señal de fin

    def fallo():
        barra.stop()
        barra.pack_forget()
        titulo.config(text="No se pudo instalar el componente", fg=ROJO)
        detalle.config(
            text="Revisa tu conexión a internet y vuelve a abrir el programa.\n"
                 "También puedes instalarlo a mano escribiendo en una consola:\n"
                 "pip install {}".format(paquete.split(">")[0]))
        estado.config(text="")
        boton.pack(pady=(16, 0))
        raiz.protocol("WM_DELETE_WINDOW", raiz.destroy)

    def revisar():
        try:
            while True:
                linea = cola.get_nowait()
                if linea is None:
                    if resultado["ok"]:
                        barra.stop()
                        raiz.destroy()
                    else:
                        fallo()
                    return
                texto = _amigable(linea)
                if texto:
                    estado.config(text=texto)
        except queue.Empty:
            pass
        raiz.after(100, revisar)

    def al_cerrar():
        trabajo.cancelar()
        raiz.destroy()

    raiz.protocol("WM_DELETE_WINDOW", al_cerrar)
    threading.Thread(target=hilo, daemon=True).start()
    raiz.after(100, revisar)
    raiz.mainloop()
    return resultado["ok"]


# ─────────────────────────────────────────────────────────────
# Alternativa por consola
# ─────────────────────────────────────────────────────────────

def _decir(texto=""):
    """print que no falla si el programa se abrió sin consola (pythonw)."""
    if sys.stdout is not None:
        try:
            print(texto, flush=True)
        except (OSError, UnicodeEncodeError):
            pass


def _esperar_tecla():
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            input("\nPulsa Enter para cerrar esta ventana...")
    except (EOFError, OSError):
        pass


def _con_consola(modulo, paquete):
    _decir("=" * 62)
    _decir("  Calculadora de Álgebra Lineal")
    _decir("=" * 62)
    _decir("Primera ejecución: falta un componente de la interfaz ({}).".format(modulo))
    _decir("Se va a descargar e instalar ahora (necesita internet).")
    _decir("Puede tardar un par de minutos, no cierres esta ventana.\n")
    ok = Instalacion(modulo, paquete, _decir).ejecutar()
    if ok:
        _decir("\nInstalación terminada. Abriendo la calculadora...\n")
        return True
    _decir("\nNo se pudo instalar automáticamente {}.".format(modulo))
    _decir("Revisa tu conexión a internet y vuelve a abrir el programa, o")
    _decir("instálalo a mano escribiendo en una consola:")
    _decir("    pip install {}".format(paquete.split(">")[0]))
    _esperar_tecla()
    return False


# ─────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────

def asegurar_dependencias(modulo=MODULO, paquete=PAQUETE):
    """
    Comprueba que la librería gráfica esté disponible y, si no, la instala
    (con ventana de espera si es posible). Devuelve True si se puede continuar.
    """
    if hay_modulo(modulo):
        return True
    resultado = _con_ventana(modulo, paquete)
    if resultado is None:                   # no se pudo abrir una ventana
        return _con_consola(modulo, paquete)
    return bool(resultado) and hay_modulo(modulo)
