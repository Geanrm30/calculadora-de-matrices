# -*- coding: utf-8 -*-
"""
Teclado de calculadora para escribir f(x) sin teclear los nombres: funciones (sin, cos, ln...),
potencias, constantes, dígitos y operadores. Cada botón inserta su texto en el campo,
en la posición del cursor, y deja el foco en el campo.
Unidad: Programa 7: Métodos Numéricos (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QPushButton, QVBoxLayout, QWidget

from qt import tema as T
from qt.componentes import BotonAnimado

_FUNCIONES = (("sin", "sin(", "seno"), ("cos", "cos(", "coseno"), ("tan", "tan(", "tangente"),
              ("ln", "ln(", "logaritmo natural"),
              ("log₁₀", "log10(", "logaritmo en base 10 (log(x) a secas es el natural)"))
_POTENCIAS = (("√", "sqrt(", "raíz cuadrada"), ("x²", "**2", "al cuadrado"),
              ("xⁿ", "**", "potencia: escribe el exponente después"),
              ("|x|", "abs(", "valor absoluto"), ("eˣ", "exp(", "exponencial"))
_CONSTANTES = (("π", "pi", "número pi"), ("e", "e", "número de Euler"),
               ("x", "x", "la variable"), ("(", "(", ""), (")", ")", ""))
_NUMEROS = (("7", "8", "9", "÷", "⌫"), ("4", "5", "6", "×", "C"), ("1", "2", "3", "−", "+"))
_TEXTO_DE = {"÷": "/", "×": "*", "−": "-"}


class TecladoFunciones(QWidget):
    """Botón que muestra u oculta un teclado de calculadora ligado a un campo de texto."""

    def __init__(self, campo, con_punto_y_coma=False):
        """Crea el botón y el teclado; con `con_punto_y_coma` añade «;» para varias funciones."""
        super().__init__()
        self.campo = campo
        self._botones = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.boton = BotonAnimado("Mostrar teclado de funciones", "suave", pequeno=True)
        self.boton.setToolTip("Escribe funciones, potencias y números con botones, "
                              "como en una calculadora.")
        self.boton.clicked.connect(self._alternar)
        lay.addWidget(self.boton)
        self.panel = QWidget()
        self.panel.setVisible(False)
        self._llenar(QGridLayout(self.panel), con_punto_y_coma)
        lay.addWidget(self.panel)
        self.estilo()

    def _llenar(self, rejilla, con_punto_y_coma):
        """Coloca los botones del teclado en la rejilla de 5 columnas."""
        rejilla.setContentsMargins(0, 0, 0, 0)
        rejilla.setSpacing(4)
        fila = 0
        for grupo, tipo in ((_FUNCIONES, "funcion"), (_POTENCIAS, "funcion"),
                            (_CONSTANTES, "constante")):
            for columna, (rotulo, texto, ayuda) in enumerate(grupo):
                self._boton(rejilla, rotulo, texto, ayuda, tipo, fila, columna)
            fila += 1
        for fila_numeros in _NUMEROS:
            for columna, rotulo in enumerate(fila_numeros):
                tipo = "operador" if rotulo in "÷×−+⌫C" else "numero"
                self._boton(rejilla, rotulo, _TEXTO_DE.get(rotulo, rotulo), "", tipo,
                            fila, columna)
            fila += 1
        self._boton(rejilla, "0", "0", "", "numero", fila, 0, 2)
        self._boton(rejilla, ".", ".", "", "numero", fila, 2)
        if con_punto_y_coma:
            self._boton(rejilla, "; otra función", ";", "separa varias funciones en la "
                        "misma gráfica", "operador", fila, 3, 2)

    def _boton(self, rejilla, rotulo, texto, ayuda, tipo, fila, columna, ancho=1):
        """Crea un botón del teclado que inserta `texto` (o borra, si es ⌫ o C)."""
        b = QPushButton(rotulo)
        b.setProperty("tipo", tipo)
        b.setFocusPolicy(Qt.NoFocus)
        b.setCursor(Qt.PointingHandCursor)
        if ayuda:
            b.setToolTip("{} → {}".format(ayuda, texto) if texto != rotulo else ayuda)
        b.clicked.connect(lambda _=False, t=texto, r=rotulo: self._pulsar(r, t))
        rejilla.addWidget(b, fila, columna, 1, ancho)
        self._botones.append(b)

    def _pulsar(self, rotulo, texto):
        """Inserta el texto del botón en el campo, o borra un carácter (⌫) o todo (C)."""
        if rotulo == "⌫":
            self.campo.backspace()
        elif rotulo == "C":
            self.campo.clear()
        else:
            self.campo.insert(texto)
        self.campo.setFocus()

    def _alternar(self):
        """Muestra u oculta el teclado y cambia el texto del botón."""
        visible = not self.panel.isVisible()
        self.panel.setVisible(visible)
        self.boton.setText("Ocultar teclado de funciones" if visible
                           else "Mostrar teclado de funciones")

    def estilo(self):
        """Aplica al teclado los colores del tema y el tamaño de letra actuales."""
        colores = {"funcion": T.AZUL, "constante": T.VERDE, "operador": T.NARANJA,
                   "numero": T.TEXTO}
        reglas = ["QPushButton {{ background: {s}; border: 1px solid {b}; border-radius: 7px;"
                  " padding: 7px 0; font-size: {t}pt; font-weight: 600; }}"
                  "QPushButton:hover {{ background: {b}; }}"
                  "QPushButton:pressed {{ background: {c}; }}".format(
                      s=T.SUPERF, b=T.BORDE, t=T.tam(10), c=T.CRUST)]
        reglas += ['QPushButton[tipo="{}"] {{ color: {}; }}'.format(k, v)
                   for k, v in colores.items()]
        self.panel.setStyleSheet("".join(reglas))
