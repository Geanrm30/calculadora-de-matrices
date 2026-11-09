# -*- coding: utf-8 -*-
"""
Carga anticipada de Matplotlib y SciPy en un hilo, para que su primer uso no congele la ventana.
Quien necesite esas librerías llama antes a esperar(): dos hilos no deben importar
el mismo paquete a la vez, porque Python puede bloquearse o dejarlo a medio cargar.
Unidad: Programa 7: Métodos Numéricos.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import os
import threading

_hilo = None


def _importar():
    """Importa los módulos pesados en orden; ignora los que no estén instalados."""
    os.environ.setdefault("QT_API", "pyside6")
    for modulo in ("matplotlib.figure", "matplotlib.backends.backend_qtagg",
                   "scipy.optimize"):
        try:
            __import__(modulo)
        except ImportError:
            pass


def iniciar():
    """Arranca la carga anticipada en segundo plano (una sola vez)."""
    global _hilo
    if _hilo is None:
        _hilo = threading.Thread(target=_importar, daemon=True)
        _hilo.start()


def esperar():
    """Bloquea hasta que termine la carga anticipada, si está en curso."""
    if _hilo is not None and _hilo.is_alive():
        _hilo.join()
