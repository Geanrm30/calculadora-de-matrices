# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/estado.py
#  Memoria compartida entre las herramientas del programa.
#
#  Cada herramienta (menu, solucionador, operaciones con matrices) vive en su
#  propia ventana Tk: al cambiar de herramienta la ventana anterior se
#  destruye y con ella se pierden sus casillas de entrada. Este modulo guarda
#  esos datos en variables de modulo, que sobreviven mientras el programa este
#  en ejecucion, de manera que al volver a una herramienta se reconstruye la
#  cuadricula tal como se dejo.
#
#  Se guarda el TEXTO escrito por el usuario, no la Fraccion ya convertida,
#  para que "3/4" siga viendose como "3/4" y no como "0.75".
# =============================================================================


# ---------------------------------------------------------------------------
# Almacen de datos
# ---------------------------------------------------------------------------

_matrices = {
    "A": None,          # lista de listas de texto
    "B": None,
    "escalar": "2",
    "salida": "",       # ultimo resultado mostrado (texto ya formateado)
    "paso_a_paso": True,
}

_sistema = {
    "celdas": None,     # lista de listas de texto, matriz aumentada [A|b]
    "n_ecuaciones": 3,
    "n_variables": 3,
    "usar_jordan": True,
    "incluir_vectores": False,
    "contexto": None,           # None | "combinacion" | "matricial"
    "resolver_al_abrir": False,
}

# Herramienta que debe abrirse a continuacion: "menu", "gauss", "matrices"
# o None para terminar el programa.
_destino = None


# ---------------------------------------------------------------------------
# Navegacion entre ventanas
# ---------------------------------------------------------------------------

def ir_a(destino):
    """
    Anota cual es la siguiente herramienta que debe abrirse. El bucle de
    main.py lee este valor cuando termina el mainloop de la ventana actual.
    """
    global _destino
    _destino = destino


def tomar_destino():
    """Devuelve el destino pendiente y lo consume (queda en None)."""
    global _destino
    destino = _destino
    _destino = None
    return destino


# ---------------------------------------------------------------------------
# Operaciones con matrices
# ---------------------------------------------------------------------------

def guardar_matrices(texto_A, texto_B, escalar, salida="", paso_a_paso=True):
    """
    Conserva las cuadriculas A y B, el escalar y el ultimo resultado mostrado,
    todo tal como se escribio o se calculo.
    """
    _matrices["A"] = texto_A
    _matrices["B"] = texto_B
    _matrices["escalar"] = escalar
    _matrices["salida"] = salida
    _matrices["paso_a_paso"] = paso_a_paso


def leer_matrices():
    """Devuelve una copia del estado de la herramienta de operaciones."""
    return dict(_matrices)


def enviar_matrices(texto_A, texto_B):
    """
    Carga A y B desde otra herramienta (por ejemplo, el solucionador manda su
    matriz de coeficientes y su vector de terminos independientes).
    """
    _matrices["A"] = texto_A
    _matrices["B"] = texto_B
    # El resultado anterior correspondia a otras matrices: se descarta.
    _matrices["salida"] = ""


# ---------------------------------------------------------------------------
# Solucionador de sistemas
# ---------------------------------------------------------------------------

def guardar_sistema(celdas, n_ecuaciones, n_variables,
                    usar_jordan, incluir_vectores):
    """Conserva la matriz aumentada y las opciones del solucionador."""
    _sistema["celdas"] = celdas
    _sistema["n_ecuaciones"] = n_ecuaciones
    _sistema["n_variables"] = n_variables
    _sistema["usar_jordan"] = usar_jordan
    _sistema["incluir_vectores"] = incluir_vectores


def leer_sistema():
    """Devuelve una copia del estado del solucionador."""
    return dict(_sistema)


def enviar_sistema(celdas, n_ecuaciones, n_variables,
                   contexto=None, incluir_vectores=False):
    """
    Carga un sistema [A|b] construido en otra herramienta y pide que el
    solucionador lo resuelva apenas se abra.

    'contexto' identifica de donde viene el sistema para que el solucionador
    explique el resultado en los terminos correctos:
        "matricial"   -> se planteo como la ecuacion matricial A.x = b
        "combinacion" -> las columnas de A son los vectores v1..vk y se
                         pregunta si b es combinacion lineal de ellos
    """
    _sistema["celdas"] = celdas
    _sistema["n_ecuaciones"] = n_ecuaciones
    _sistema["n_variables"] = n_variables
    _sistema["contexto"] = contexto
    _sistema["resolver_al_abrir"] = True
    if incluir_vectores:
        _sistema["incluir_vectores"] = True


def tomar_orden_de_resolver():
    """Devuelve True una sola vez si el sistema llego listo para resolverse."""
    pendiente = _sistema["resolver_al_abrir"]
    _sistema["resolver_al_abrir"] = False
    return pendiente


def limpiar_contexto():
    """Olvida el origen del sistema (se llama al editarlo manualmente)."""
    _sistema["contexto"] = None
