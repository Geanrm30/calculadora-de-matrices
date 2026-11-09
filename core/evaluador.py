# -*- coding: utf-8 -*-
"""
Evaluador seguro de funciones f(x) escritas por el usuario.

Nunca se usa eval() sobre el texto: la expresión se convierte a un árbol AST y
solo se recorren los nodos de una LISTA BLANCA (números, x, constantes,
+ - * / **, y funciones autorizadas). Cualquier otra cosa se rechaza.
Unidad: Programa 7: Métodos Numéricos.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import ast
import math
import re


class ErrorFuncion(ValueError):
    """La expresión está mal escrita o no se permite."""


class FueraDeDominio(ArithmeticError):
    """f(x) no está definida (o no es real / no es finita) en ese punto."""


_FUNCIONES = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "exp": math.exp, "log": math.log, "ln": math.log, "log10": math.log10,
    "log2": math.log2, "sqrt": math.sqrt, "abs": abs,
    "cbrt": lambda v: math.copysign(abs(v) ** (1.0 / 3.0), v),
    "floor": math.floor, "ceil": math.ceil,
}
_ALIAS = {"sen": "sin", "arcsin": "asin", "arccos": "acos", "arctan": "atan",
          "raiz": "sqrt", "valor_absoluto": "abs", "senh": "sinh"}
_CONSTANTES = {"pi": math.pi, "e": math.e}
_MAX_LARGO = 300
_MAX_NODOS = 400

_TOKEN = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)"
                    r"|([A-Za-z_][A-Za-z_0-9]*)|(\*\*|.))")


def nombres_de_funciones():
    """Conjunto con los nombres de función aceptados (con sus alias)."""
    return set(_FUNCIONES) | set(_ALIAS)


def nombres_de_constantes():
    """Conjunto con los nombres de constante aceptados."""
    return set(_CONSTANTES)


def usa_circunflejo(texto):
    """Indica si la expresión escribe la potencia con ^ (en Python es **)."""
    return "^" in (texto or "")


def _tokenizar(texto):
    """Divide el texto en fichas (números, nombres, operadores) y valida los caracteres."""
    pos, fichas = 0, []
    texto = texto.rstrip()
    while pos < len(texto):
        m = _TOKEN.match(texto, pos)
        if not m or m.end() == pos:
            raise ErrorFuncion("Carácter no válido en la función.")
        num, nom, op = m.groups()
        if num is not None:
            fichas.append(("num", num))
        elif nom is not None:
            fichas.append(("nom", nom))
        else:
            fichas.append(("op", op))
        pos = m.end()
    return fichas


def _normalizar(texto):
    """
    Pasa del texto escrito a una expresión de Python: `^` es potencia, el
    producto implícito se completa (2x → 2*x, 3(x+1) → 3*(x+1)) y los
    símbolos matemáticos habituales se traducen.
    """
    t = (texto or "").strip()
    for a, b in (("−", "-"), ("–", "-"), ("×", "*"), ("·", "*"), ("÷", "/"),
                 ("π", "pi"), ("√", "sqrt"), ("²", "**2"), ("³", "**3"),
                 ("^", "**"), (",", ".")):
        t = t.replace(a, b)
    if "=" in t:
        t = t.split("=", 1)[1]
    if not t.strip():
        raise ErrorFuncion("Escribe una función, por ejemplo x**3 - 2*x - 5.")
    if len(t) > _MAX_LARGO:
        raise ErrorFuncion("La función es demasiado larga.")
    fichas = _tokenizar(t)
    salida = []
    for i, (tipo, val) in enumerate(fichas):
        if tipo == "nom":
            val = _ALIAS.get(val.lower(), val.lower() if val.lower() in _FUNCIONES
                             or val.lower() in _CONSTANTES or val.lower() == "x"
                             else val)
            fichas[i] = (tipo, val)
        if salida:
            pt, pv = salida[-1]
            es_valor_previo = (pt == "num" or pv == ")" or
                               (pt == "nom" and pv not in _FUNCIONES))
            if es_valor_previo and (
                    tipo == "nom" or val == "(" or (tipo == "num" and pv == ")")):
                salida.append(("op", "*"))
        salida.append((tipo, fichas[i][1]))
    return " ".join(v for _, v in salida)


class Funcion:
    """f(x) lista para evaluar. `f(x)` devuelve un float o lanza FueraDeDominio."""

    def __init__(self, texto):
        """Normaliza y valida el texto de f(x); lanza ErrorFuncion si no es admisible."""
        self.texto = (texto or "").strip()
        self.normalizado = _normalizar(self.texto)
        try:
            arbol = ast.parse(self.normalizado, mode="eval")
        except SyntaxError:
            raise ErrorFuncion("La función está mal escrita (revisa paréntesis "
                               "y operadores).") from None
        if sum(1 for _ in ast.walk(arbol)) > _MAX_NODOS:
            raise ErrorFuncion("La función es demasiado compleja.")
        self._validar(arbol.body)
        self._arbol = arbol.body
        try:
            self(1.0)
        except FueraDeDominio:
            pass

    def _validar(self, n):
        """Recorre el árbol y rechaza todo nodo, nombre o función fuera de la lista permitida."""
        if isinstance(n, ast.Constant):
            if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
                raise ErrorFuncion("Solo se permiten números.")
        elif isinstance(n, ast.Name):
            if n.id != "x" and n.id not in _CONSTANTES:
                raise ErrorFuncion("Símbolo no permitido: «{}». Usa x, pi, e o "
                                   "una función autorizada.".format(n.id))
        elif isinstance(n, ast.BinOp):
            if not isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div,
                                     ast.Pow, ast.Mod)):
                raise ErrorFuncion("Operador no permitido.")
            self._validar(n.left)
            self._validar(n.right)
        elif isinstance(n, ast.UnaryOp):
            if not isinstance(n.op, (ast.UAdd, ast.USub)):
                raise ErrorFuncion("Operador no permitido.")
            self._validar(n.operand)
        elif isinstance(n, ast.Call):
            if (not isinstance(n.func, ast.Name) or n.keywords
                    or n.func.id not in _FUNCIONES):
                nombre = getattr(n.func, "id", "?")
                raise ErrorFuncion("Función no permitida: «{}». Autorizadas: {}."
                                   .format(nombre, ", ".join(sorted(_FUNCIONES))))
            if len(n.args) != 1 and not (n.func.id in ("log",) and len(n.args) == 2):
                raise ErrorFuncion("«{}» recibe un argumento.".format(n.func.id))
            for a in n.args:
                self._validar(a)
        else:
            raise ErrorFuncion("Expresión no permitida.")

    def _ev(self, n, x):
        """Evalúa el árbol en x con aritmética de float; lanza FueraDeDominio si no existe el valor."""
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.Name):
            return x if n.id == "x" else _CONSTANTES[n.id]
        if isinstance(n, ast.UnaryOp):
            v = self._ev(n.operand, x)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            a, b = self._ev(n.left, x), self._ev(n.right, x)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                if b == 0:
                    raise FueraDeDominio("división entre cero")
                return a / b
            if isinstance(n.op, ast.Mod):
                if b == 0:
                    raise FueraDeDominio("división entre cero")
                return a % b
            if a == 0 and b < 0:
                raise FueraDeDominio("división entre cero (0 elevado a una "
                                     "potencia negativa)")
            if a < 0 and b != math.floor(b):
                raise FueraDeDominio("resultado no real (base negativa con "
                                     "exponente fraccionario)")
            return a ** b
        if isinstance(n, ast.Call):
            args = [self._ev(a, x) for a in n.args]
            nombre = n.func.id
            if nombre == "log" and len(args) == 2:
                return math.log(args[0], args[1])
            return _FUNCIONES[nombre](*args)
        raise ErrorFuncion("Expresión no permitida.")

    def __call__(self, x):
        """Devuelve f(x) como float; propaga FueraDeDominio si x no está en el dominio."""
        try:
            v = self._ev(self._arbol, float(x))
        except FueraDeDominio:
            raise
        except ZeroDivisionError:
            raise FueraDeDominio("división entre cero") from None
        except OverflowError:
            raise FueraDeDominio("desbordamiento (valor demasiado grande)") from None
        except ValueError:
            raise FueraDeDominio("fuera del dominio de la función") from None
        if isinstance(v, complex) or not math.isfinite(v):
            raise FueraDeDominio("el valor no es real o no es finito")
        return float(v)


def compilar(texto):
    """Devuelve una `Funcion` o lanza `ErrorFuncion` con un mensaje claro."""
    return Funcion(texto)
