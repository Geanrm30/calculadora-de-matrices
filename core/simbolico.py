# -*- coding: utf-8 -*-
"""
Derivada simbólica de f(x) con SymPy (Programa 9 y propagación del error).

La expresión escrita por el usuario se valida PRIMERO con el evaluador seguro
(`core.evaluador`, lista blanca de nodos AST) y solo entonces se entrega a SymPy ya
normalizada, así que nunca se ejecuta texto arbitrario. SymPy se importa la primera
vez que se necesita (tarda un poco en cargar) y solo para derivar y para leer
polinomios; los valores numéricos de f y f′ se calculan con funciones de Python.
Unidad: Programa 9: Método abierto de Newton-Raphson.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import math
import re

from core.evaluador import FueraDeDominio, compilar

_sp = None
_ESPACIO = None
_SUPERINDICES = {}
_FUNCIONES_PERMITIDAS = {"sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh",
                         "exp", "log", "Abs", "sign", "sqrt"}


class ErrorDerivada(ValueError):
    """SymPy no pudo interpretar o derivar la expresión."""


def sympy():
    """Importa SymPy la primera vez (falla con un mensaje claro si no está instalado)."""
    global _sp
    if _sp is None:
        from core import calentamiento
        calentamiento.esperar()
        try:
            import sympy as modulo
        except ImportError:
            raise ErrorDerivada("Falta la librería SymPy (pip install sympy).") from None
        _sp = modulo
    return _sp


def _espacio():
    """Nombres con los que se interpreta la expresión normalizada (todos conocidos y seguros)."""
    global _ESPACIO
    if _ESPACIO is None:
        sp = sympy()
        x = sp.Symbol("x", real=True)
        local = {"x": x, "pi": sp.pi, "e": sp.E, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                 "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "sinh": sp.sinh,
                 "cosh": sp.cosh, "tanh": sp.tanh, "exp": sp.exp, "log": sp.log,
                 "ln": sp.log, "sqrt": sp.sqrt, "abs": sp.Abs, "cbrt": sp.cbrt,
                 "log10": lambda u: sp.log(u, 10), "log2": lambda u: sp.log(u, 2),
                 "floor": sp.floor, "ceil": sp.ceiling}
        glob = {"Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational,
                "Symbol": sp.Symbol, "Mod": sp.Mod}
        _ESPACIO = (x, local, glob)
    return _ESPACIO


def _signo(v):
    """Función signo para la derivada de |x|."""
    return (v > 0) - (v < 0)


def texto_bonito(expr):
    """Expresión de SymPy como texto legible que el propio evaluador sabe volver a leer."""
    sp = sympy()
    t = sp.sstr(expr)
    t = t.replace("**", "^").replace("*", "·").replace("Abs(", "abs(")
    t = re.sub(r"\blog\(", "ln(", t)
    t = t.replace(" - ", " − ").replace("(-", "(−")
    return re.sub(r"^-", "−", t.strip())


class FuncionDerivable:
    """f(x), su derivada simbólica f′(x) y evaluadores numéricos de ambas."""

    def __init__(self, texto):
        """Valida el texto con el evaluador seguro y lo deriva con SymPy; lanza ErrorFuncion o ErrorDerivada."""
        self.f = compilar(texto)
        self.texto = self.f.texto
        sp = sympy()
        x, local, glob = _espacio()
        try:
            self.expr = sp.parse_expr(self.f.normalizado, local_dict=local, global_dict=dict(glob),
                                      transformations=sp.parsing.sympy_parser.standard_transformations)
        except Exception:
            raise ErrorDerivada("SymPy no pudo interpretar la expresión «{}».".format(texto)) from None
        if not self.expr.has(x):
            # f constante: la derivada es 0 y Newton no puede avanzar (se avisa más adelante).
            pass
        try:
            self.derivada = sp.diff(self.expr, x)
        except Exception:
            raise ErrorDerivada("SymPy no pudo derivar la expresión.") from None
        nombres = {type(a).__name__ for a in self.derivada.atoms(sp.Function)}
        nombres |= {a.func.__name__ for a in self.derivada.atoms(sp.Function)
                    if hasattr(a, "func")}
        if (self.derivada.has(sp.Derivative, sp.Subs, sp.DiracDelta, sp.Heaviside)
                or not nombres <= _FUNCIONES_PERMITIDAS):
            raise ErrorDerivada("f(x) no se puede derivar de forma simbólica con las funciones "
                                "escritas (por ejemplo floor, ceil o %). Usa la derivada "
                                "numérica.")
        self._df = sp.lambdify(x, self.derivada, modules=[{"Abs": abs, "sign": _signo}, "math"])
        self.derivada_simplificada = self._simplificar(sp, x)
        self.texto_derivada = texto_bonito(self.derivada_simplificada)
        self.texto_sympy = texto_bonito(self.expr)

    def _simplificar(self, sp, x):
        """Versión simplificada de f′ (solo si no es enorme); la numérica sigue usando la original."""
        if sp.count_ops(self.derivada) > 60:
            return self.derivada
        try:
            return sp.simplify(self.derivada)
        except Exception:
            return self.derivada

    def valor(self, x):
        """f(x) como float; lanza FueraDeDominio fuera del dominio."""
        return self.f(x)

    def derivada_en(self, x):
        """f′(x) como float; lanza FueraDeDominio si no existe, no es real o no es finita."""
        try:
            v = self._df(float(x))
        except ZeroDivisionError:
            raise FueraDeDominio("división entre cero al evaluar f′") from None
        except OverflowError:
            raise FueraDeDominio("desbordamiento al evaluar f′") from None
        except (ValueError, TypeError):
            raise FueraDeDominio("f′ no está definida (o no es real) en ese punto") from None
        if isinstance(v, complex) or not math.isfinite(v):
            raise FueraDeDominio("f′ no es real o no es finita en ese punto")
        return float(v)
