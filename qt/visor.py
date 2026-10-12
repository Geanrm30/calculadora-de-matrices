# -*- coding: utf-8 -*-
"""
Ventana independiente para leer un resultado con comodidad: texto grande,
con zoom, copiar y guardar. Se pueden abrir varias a la vez.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QHBoxLayout,
                               QLabel, QPlainTextEdit, QVBoxLayout)

from qt import tema as T
from qt.componentes import BotonAnimado, aparecer, mostrar_aviso


class VisorTexto(QDialog):

    def __init__(self, padre, titulo, texto, nombre_archivo="informe.txt"):
        super().__init__(padre)
        self.setWindowTitle(titulo)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.resize(1000, 720)
        self.setMinimumSize(520, 360)
        self._texto = texto.strip()
        self._nombre = nombre_archivo
        self._tam = 13

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(16, 14, 16, 16)
        raiz.setSpacing(12)

        barra = QHBoxLayout()
        lbl = QLabel(titulo)
        lbl.setStyleSheet("font-size: 13pt; font-weight: 700;")
        barra.addWidget(lbl)
        barra.addStretch(1)
        for texto_b, cmd in (("A−", lambda: self._zoom(-1)),
                             ("A+", lambda: self._zoom(1)),
                             ("Copiar", self._copiar),
                             ("Guardar", self._guardar),
                             ("Cerrar", self.close)):
            b = BotonAnimado(texto_b, "suave", pequeno=True)
            b.clicked.connect(cmd)
            barra.addWidget(b)
        raiz.addLayout(barra)

        self.edit = QPlainTextEdit()
        self.edit.setReadOnly(True)
        self.edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.edit.setPlainText(self._texto)
        self._aplicar_fuente()
        raiz.addWidget(self.edit, 1)

        QShortcut(QKeySequence("Esc"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl++"), self, activated=lambda: self._zoom(1))
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self._zoom(1))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self._zoom(-1))

    def showEvent(self, e):
        super().showEvent(e)
        aparecer(self.edit, 300)

    def _aplicar_fuente(self):
        self.edit.setStyleSheet(
            "padding: 14px; font-family: '{}'; font-size: {}pt;".format(
                T.MONO, self._tam))

    def _zoom(self, d):
        self._tam = max(8, min(32, self._tam + d))
        self._aplicar_fuente()

    def _copiar(self):
        QApplication.clipboard().setText(self._texto)
        mostrar_aviso(self, "Copiado al portapapeles")

    def _guardar(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", self._nombre,
            "Texto (*.txt);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._texto + "\n")
            mostrar_aviso(self, "Informe guardado")
        except OSError as ex:
            mostrar_aviso(self, "No se pudo guardar: {}".format(ex), "error")


def abrir_visor(padre, titulo, texto, nombre_archivo="informe.txt"):
    if not texto or not texto.strip():
        return None
    v = VisorTexto(padre.window(), titulo, texto, nombre_archivo)
    v.show()
    return v
