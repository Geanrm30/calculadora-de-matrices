# -*- coding: utf-8 -*-
"""
Aritmética exacta con números racionales implementada sobre enteros de Python.
Permite comparaciones exactas (sin tolerancia de punto flotante) necesarias para
la eliminación gaussiana.
Unidad: Proyecto Integrador (Sesiones 1-11).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""


def mcd(a, b):
    """Máximo común divisor por Euclides: mcd(a, b) = mcd(b, a mod b).
    Recibe dos enteros y devuelve un entero no negativo.
    """
    a = abs(a)
    b = abs(b)
    while b != 0:
        a, b = b, a % b
    return a


class Fraccion:
    """
    Numero racional guardado siempre en su forma mas simple y con el
    signo en el numerador (el denominador nunca es negativo).
    """

    def __init__(self, numerador, denominador=1, simbolo=None):
        """Crea la fracción num/den en forma irreducible; el denominador no puede ser cero."""
        if denominador == 0:
            raise ZeroDivisionError("El denominador no puede ser cero.")

        if denominador < 0:
            numerador = -numerador
            denominador = -denominador

        divisor = mcd(numerador, denominador)
        if divisor > 1:
            numerador = numerador // divisor
            denominador = denominador // divisor

        self.num = numerador
        self.den = denominador
        self.simbolo = simbolo

    def _convertir(self, otro):
        """Permite operar una Fraccion con un entero directamente."""
        if isinstance(otro, Fraccion):
            return otro
        if isinstance(otro, int):
            return Fraccion(otro, 1)
        raise TypeError("No se puede operar una Fraccion con {}".format(type(otro)))

    def __add__(self, otro):
        """Suma exacta: a/b + c/d = (ad + cb)/(bd)."""
        otro = self._convertir(otro)
        return Fraccion(self.num * otro.den + otro.num * self.den,
                        self.den * otro.den)

    def __sub__(self, otro):
        """Resta exacta: a/b − c/d = (ad − cb)/(bd)."""
        otro = self._convertir(otro)
        return Fraccion(self.num * otro.den - otro.num * self.den,
                        self.den * otro.den)

    def __mul__(self, otro):
        """Producto exacto: (a/b)(c/d) = (ac)/(bd)."""
        otro = self._convertir(otro)
        return Fraccion(self.num * otro.num, self.den * otro.den)

    def __truediv__(self, otro):
        """División exacta multiplicando por el inverso; el divisor no puede ser cero."""
        otro = self._convertir(otro)
        if otro.num == 0:
            raise ZeroDivisionError("Division entre cero.")
        return Fraccion(self.num * otro.den, self.den * otro.num)

    def __neg__(self):
        """Devuelve la fracción opuesta."""
        return Fraccion(-self.num, self.den)

    def inverso(self):
        """Devuelve 1/self. Se usa para normalizar el pivote a 1."""
        if self.num == 0:
            raise ZeroDivisionError("El cero no tiene inverso multiplicativo.")
        return Fraccion(self.den, self.num)

    def __eq__(self, otro):
        """Dos fracciones irreducibles son iguales si coinciden numerador y denominador."""
        otro = self._convertir(otro)
        return self.num == otro.num and self.den == otro.den

    def es_cero(self):
        """Pregunta exacta: no hace falta ninguna tolerancia."""
        return self.num == 0

    def es_uno(self):
        """Indica si la fracción vale exactamente 1."""
        return self.num == 1 and self.den == 1

    def es_negativo(self):
        """Indica si la fracción es menor que cero."""
        return self.num < 0

    def a_decimal(self):
        """Valor aproximado, solo para mostrarlo junto al valor exacto."""
        return self.num / self.den

    def __str__(self):
        """Texto de la fracción: entero si el denominador es 1, 'a/b' en otro caso."""
        if hasattr(self, 'simbolo') and self.simbolo is not None:
            return self.simbolo
        if self.den == 1:
            return str(self.num)
        if self.den > 9999:
            return "{:.4f}".format(self.num / self.den)
        return "{}/{}".format(self.num, self.den)


import unicodedata

_EQUIVALENCIAS = {
    **{ord(c): "-" for c in "\u2212\u2013\u2014\u2012\u2010\u2011\ufe63\uff0d"},
    **{ord(c): "/" for c in "\u2215\u2044\uff0f"},
    **{ord(c): None for c in "\u200b\u200c\u200d\ufeff"},
}


def normalizar_texto_numerico(texto):
    """
    Convierte a símbolos de teclado el texto copiado de Excel, Word o un PDF
    (menos tipográfico, rayas, barra de fracción) y quita todo espacio.
    """
    texto = unicodedata.normalize("NFKC", texto)
    return "".join(texto.translate(_EQUIVALENCIAS).split())


def desde_texto(texto):
    """Convierte el texto escrito por el usuario en una Fraccion exacta.
    Acepta enteros, fracciones a/b, decimales, raíces √ y los símbolos de Excel y Word.
    """
    texto = normalizar_texto_numerico(texto)
    if texto == "":
        raise ValueError("Valor vacio.")

    texto = texto.replace(",", ".")

    if texto.startswith("√") or (texto.startswith("sqrt(") and texto.endswith(")")):
        if texto.startswith("√"):
            adentro = texto[1:]
        else:
            adentro = texto.split("(")[1][:-1]

        try:
            valor_interno = float(adentro)
            if valor_interno < 0:
                raise ValueError("Raiz negativa")
            raiz_calculada = valor_interno ** 0.5

            if raiz_calculada.is_integer():
                return Fraccion(int(raiz_calculada), 1)
            else:
                decimales = "{:.6f}".format(raiz_calculada).split(".")
                numerador = int(decimales[0] + decimales[1])
                denominador = 10 ** 6
                return Fraccion(numerador, denominador, simbolo="√" + adentro)
        except ValueError:
            raise ValueError("Valor invalido dentro de la raiz.")

    if "/" in texto:
        partes = texto.split("/")
        if len(partes) != 2:
            raise ValueError("Fraccion mal escrita: {}".format(texto))
        numerador = int(partes[0])
        denominador = int(partes[1])
        if denominador == 0:
            raise ValueError("El denominador no puede ser cero.")
        return Fraccion(numerador, denominador)

    if "." in texto:
        partes = texto.split(".")
        if len(partes) != 2:
            raise ValueError("Numero mal escrito: {}".format(texto))
        entero = partes[0]
        decimales = partes[1]

        negativo = entero.startswith("-")
        if negativo:
            entero = entero[1:]
        if entero == "":
            entero = "0"

        numerador = int(entero + decimales)
        denominador = 10 ** len(decimales)
        if negativo:
            numerador = -numerador
        return Fraccion(numerador, denominador)

    return Fraccion(int(texto), 1)

