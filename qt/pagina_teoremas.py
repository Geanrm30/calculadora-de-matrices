# -*- coding: utf-8 -*-
"""Catálogo de teoremas y criterios del curso, con buscador."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QLabel, QLineEdit, QScrollArea,
                               QVBoxLayout, QWidget)

from core.teoremas import TEOREMAS
from qt import tema as T
from qt.componentes import Tarjeta, aparecer
from qt.pagina_base import PaginaBase


class PaginaTeoremas(PaginaBase):

    def __init__(self, ventana):
        super().__init__(ventana, "Teoremas y criterios",
                         "Catálogo de teoremas del curso (Sesiones 1–11)")

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar por nombre, enunciado o herramienta…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setMinimumHeight(38)
        self.buscador.textChanged.connect(self._filtrar)
        self.raiz.addWidget(self.buscador)

        self.lbl_cuenta = QLabel("")
        self.lbl_cuenta.setObjectName("nota")
        self.raiz.addWidget(self.lbl_cuenta)

        cont = QWidget()
        self.lista = QVBoxLayout(cont)
        self.lista.setContentsMargins(0, 0, 8, 0)
        self.lista.setSpacing(10)

        self.tarjetas = []
        for i, (nombre, enunciado, uso) in enumerate(TEOREMAS, start=1):
            t = self._tarjeta(i, nombre, enunciado, uso)
            self.lista.addWidget(t)
            self.tarjetas.append((t, "{} {} {}".format(nombre, enunciado, uso).lower()))
        self.lista.addStretch(1)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(cont)
        self.raiz.addWidget(area, 1)
        self._filtrar("")

    @staticmethod
    def _tarjeta(n, nombre, enunciado, uso):
        t = Tarjeta()
        t.cuerpo.setSpacing(6)

        enc = QLabel("{}.  {}".format(n, nombre))
        enc.setWordWrap(True)
        enc.setStyleSheet("color: {}; font-size: 11.5pt; font-weight: 700;"
                          " background: transparent;".format(T.NARANJA))
        t.agregar(enc)

        cuerpo = QLabel(enunciado)
        cuerpo.setWordWrap(True)
        cuerpo.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cuerpo.setStyleSheet("font-size: 10.5pt; background: transparent;")
        t.agregar(cuerpo)

        u = QLabel("Se usa en: " + uso)
        u.setWordWrap(True)
        u.setStyleSheet("color: {}; font-style: italic; background: transparent;"
                        .format(T.AZUL))
        t.agregar(u)
        return t

    def _filtrar(self, texto):
        q = texto.strip().lower()
        visibles = 0
        for t, clave in self.tarjetas:
            mostrar = q in clave
            t.setVisible(mostrar)
            visibles += mostrar
        self.lbl_cuenta.setText("{} de {} teoremas".format(visibles, len(self.tarjetas)))
