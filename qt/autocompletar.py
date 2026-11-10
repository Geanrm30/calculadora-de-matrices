# -*- coding: utf-8 -*-
"""
Autocompletado de nombres de función (sin, sqrt, log...) en los campos donde se escribe f(x).
Sugiere a partir de la segunda letra y completa la palabra que está escribiéndose,
sin tocar el resto de la expresión.
Unidad: Programa 7: Métodos Numéricos (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import re

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtWidgets import QCompleter

from core import evaluador

_PALABRA_FINAL = re.compile(r"[A-Za-z_]*$")
_MIN_LETRAS = 2


class _CompletadorConTab(QCompleter):
    """Completador que acepta la sugerencia resaltada también con Tab (sin mover el foco)."""

    def eventFilter(self, objeto, evento):
        """Con Tab y el popup abierto elige la sugerencia y consume la tecla."""
        if (evento.type() == QEvent.KeyPress and evento.key() == Qt.Key_Tab
                and objeto is self.popup() and self.popup().isVisible()):
            indice = self.popup().currentIndex()
            if not indice.isValid():
                indice = self.completionModel().index(0, 0)
            self.popup().hide()
            self.activated[str].emit(self.completionModel().data(indice))
            return True
        return super().eventFilter(objeto, evento)


def instalar(campo):
    """Activa en el campo las sugerencias de funciones y constantes y devuelve el completador."""
    nombres = sorted(evaluador.nombres_de_funciones() | evaluador.nombres_de_constantes())
    funciones = evaluador.nombres_de_funciones()
    completador = _CompletadorConTab(nombres, campo)
    completador.setWidget(campo)
    completador.setCaseSensitivity(Qt.CaseInsensitive)
    completador.setCompletionMode(QCompleter.PopupCompletion)
    completador.setMaxVisibleItems(8)

    def palabra_actual():
        """Letras escritas justo antes del cursor y la posición donde empiezan."""
        antes = campo.text()[:campo.cursorPosition()]
        m = _PALABRA_FINAL.search(antes)
        return m.group(), m.start()

    def sugerir(_texto):
        """Muestra las sugerencias para la palabra que se está escribiendo."""
        palabra, _ = palabra_actual()
        completador.popup().hide()
        if len(palabra) < _MIN_LETRAS:
            return
        completador.setCompletionPrefix(palabra)
        if completador.completionCount() == 0 or (
                completador.currentCompletion().lower() == palabra.lower()):
            return
        completador.popup().setCurrentIndex(completador.completionModel().index(0, 0))
        zona = campo.cursorRect()
        zona.setWidth(completador.popup().sizeHintForColumn(0) + 28)
        completador.complete(zona)

    def insertar(sugerencia):
        """Reemplaza la palabra escrita por la sugerencia (con «(» si es una función)."""
        _, inicio = palabra_actual()
        fin = campo.cursorPosition()
        cierre = "(" if sugerencia in funciones else ""
        texto = campo.text()
        campo.setText(texto[:inicio] + sugerencia + cierre + texto[fin:])
        campo.setCursorPosition(inicio + len(sugerencia) + len(cierre))
        campo.setProperty("recien_autocompletado", True)
        QTimer.singleShot(0, lambda: campo.setProperty("recien_autocompletado", False))

    completador.activated[str].connect(insertar)
    campo.textEdited.connect(sugerir)
    return completador


def al_pulsar_enter(campo, accion):
    """Ejecuta `accion` al pulsar Enter, salvo que ese Enter haya elegido una sugerencia."""
    def decidir():
        """Se ejecuta después de que Qt avise de la sugerencia aceptada, si la hubo."""
        if not campo.property("recien_autocompletado"):
            accion()

    campo.returnPressed.connect(lambda: QTimer.singleShot(0, decidir))
