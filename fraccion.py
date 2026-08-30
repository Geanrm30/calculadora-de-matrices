# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: fraccion.py
#  Aritmetica exacta con numeros racionales.
#
#  Motivo: la eliminacion gaussiana requiere determinar si un elemento es
#  exactamente cero para seleccionar pivotes y detectar inconsistencias. La
#  representacion en punto flotante introduce error de redondeo, de modo que
#  un valor teoricamente nulo puede quedar en el orden de 1e-17 y obligar a
#  comparar contra una tolerancia arbitraria. Con aritmetica racional la
#  comparacion es exacta y el resultado se expresa en fracciones irreducibles.
#
#  Implementado sobre enteros de Python. No se emplea el modulo fractions,
#  math.gcd ni ninguna libreria externa.
# =============================================================================


def mcd(a, b):
    """
    Maximo comun divisor por el algoritmo de Euclides.

    Se apoya en que mcd(a, b) = mcd(b, a mod b), iterando hasta que el
    resto es cero. Complejidad logaritmica respecto del menor operando.
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

    # -----------------------------------------------------------------
    # Construccion
    # -----------------------------------------------------------------
    def __init__(self, numerador, denominador=1, simbolo=None):
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

    # -----------------------------------------------------------------
    # Conversion de otros tipos a Fraccion
    # -----------------------------------------------------------------
    def _convertir(self, otro):
        """Permite operar una Fraccion con un entero directamente."""
        if isinstance(otro, Fraccion):
            return otro
        if isinstance(otro, int):
            return Fraccion(otro, 1)
        raise TypeError("No se puede operar una Fraccion con {}".format(type(otro)))

    # -----------------------------------------------------------------
    # Operaciones aritmeticas
    # -----------------------------------------------------------------
    def __add__(self, otro):
        otro = self._convertir(otro)
        return Fraccion(self.num * otro.den + otro.num * self.den,
                        self.den * otro.den)

    def __sub__(self, otro):
        otro = self._convertir(otro)
        return Fraccion(self.num * otro.den - otro.num * self.den,
                        self.den * otro.den)

    def __mul__(self, otro):
        otro = self._convertir(otro)
        return Fraccion(self.num * otro.num, self.den * otro.den)

    def __truediv__(self, otro):
        otro = self._convertir(otro)
        if otro.num == 0:
            raise ZeroDivisionError("Division entre cero.")
        return Fraccion(self.num * otro.den, self.den * otro.num)

    def __neg__(self):
        return Fraccion(-self.num, self.den)

    def inverso(self):
        """Devuelve 1/self. Se usa para normalizar el pivote a 1."""
        if self.num == 0:
            raise ZeroDivisionError("El cero no tiene inverso multiplicativo.")
        return Fraccion(self.den, self.num)

    # -----------------------------------------------------------------
    # Comparaciones y consultas
    # -----------------------------------------------------------------
    def __eq__(self, otro):
        otro = self._convertir(otro)
        # Al estar siempre simplificadas, basta comparar numerador y denominador
        return self.num == otro.num and self.den == otro.den

    def es_cero(self):
        """Pregunta exacta: no hace falta ninguna tolerancia."""
        return self.num == 0

    def es_uno(self):
        return self.num == 1 and self.den == 1

    def es_negativo(self):
        return self.num < 0

    def a_decimal(self):
        """Valor aproximado, solo para mostrarlo junto al valor exacto."""
        return self.num / self.den

    # -----------------------------------------------------------------
    # Representacion en texto
    # -----------------------------------------------------------------
    def __str__(self):
        # Si conserva el símbolo intacto (no ha sido operada)
        if hasattr(self, 'simbolo') and self.simbolo is not None:
            return self.simbolo
            
        # Si es un número entero
        if self.den == 1:
            return str(self.num)
            
        # Si la fracción es gigante (producto de operar con raíces), 
        # se muestra como decimal corto a 4 cifras para no deformar la matriz visualmente.
        if self.den > 9999:
            return "{:.4f}".format(self.num / self.den)
            
        # Fracción normal pequeña
        return "{}/{}".format(self.num, self.den)


# ---------------------------------------------------------------------------
# Lectura de fracciones escritas por el usuario
# ---------------------------------------------------------------------------

def desde_texto(texto):
    """
    Convierte lo que escribe el usuario en una Fraccion exacta.
    Formatos aceptados:
        entero      ->  -7
        fraccion    ->  3/4   -5/2
        decimal     ->  2.5   -0.25   (se convierte a fraccion exacta)
    Lanza ValueError si el texto no es valido.
    """

    texto = texto.strip().replace(" ", "")
    if texto == "":
        raise ValueError("Valor vacio.")

    # Se acepta la coma como separador decimal
    texto = texto.replace(",", ".")

    # Caso especial: Raíz cuadrada con símbolo √ (Alt+251)
    if texto.startswith("√") or (texto.startswith("sqrt(") and texto.endswith(")")):
        if texto.startswith("√"):
            adentro = texto[1:]
        else:
            adentro = texto.split("(")[1][:-1]
            
        try:
            valor_interno = float(adentro)
            if valor_interno < 0:
                raise ValueError("Raíz negativa")
            raiz_calculada = valor_interno ** 0.5
            
            if raiz_calculada.is_integer():
                return Fraccion(int(raiz_calculada), 1)
            else:
                decimales = "{:.6f}".format(raiz_calculada).split(".")
                numerador = int(decimales[0] + decimales[1])
                denominador = 10 ** 6
                # Se guarda como fracción exacta pero conserva el símbolo visual
                return Fraccion(numerador, denominador, simbolo="√" + adentro)
        except ValueError:
            raise ValueError("Valor inválido dentro de la raíz.")

    # Caso 1: fraccion escrita como a/b
    if "/" in texto:
        partes = texto.split("/")
        if len(partes) != 2:
            raise ValueError("Fraccion mal escrita: {}".format(texto))
        numerador = int(partes[0])
        denominador = int(partes[1])
        if denominador == 0:
            raise ValueError("El denominador no puede ser cero.")
        return Fraccion(numerador, denominador)

    # Caso 2: decimal -> se pasa a fraccion exacta (2.5 = 25/10 = 5/2)
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

    # Caso 3: entero
    return Fraccion(int(texto), 1)


# Constantes de uso frecuente
CERO = Fraccion(0)
UNO = Fraccion(1)
