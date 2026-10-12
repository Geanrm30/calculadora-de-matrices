# -*- coding: utf-8 -*-
"""Base común de las páginas: título, subtítulo y área de contenido."""
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget


class PaginaBase(QWidget):

    def __init__(self, ventana, titulo, subtitulo):
        super().__init__()
        self.ventana = ventana

        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(26, 22, 26, 20)
        self.raiz.setSpacing(14)

        cab = QVBoxLayout()
        cab.setSpacing(2)
        lbl = QLabel(titulo)
        lbl.setObjectName("titulo")
        sub = QLabel(subtitulo)
        sub.setObjectName("subtitulo")
        cab.addWidget(lbl)
        cab.addWidget(sub)
        self.raiz.addLayout(cab)

    # Mensajes de error / información con el aspecto del tema
    def error(self, titulo, texto):
        QMessageBox.warning(self, titulo, texto)

    def info(self, titulo, texto):
        QMessageBox.information(self, titulo, texto)
