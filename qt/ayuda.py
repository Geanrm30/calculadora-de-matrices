# -*- coding: utf-8 -*-
"""Ventana de ayuda: atajos de teclado y «Acerca de»."""
import platform

import PySide6
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QMessageBox, QScrollArea, QTabWidget,
                               QVBoxLayout, QWidget)

from qt import NOMBRE, VERSION
from qt import tema as T
from qt.componentes import BotonAnimado, Tarjeta
from qt.icono import dibujar

# Única fuente de verdad de los atajos: la ayuda los lista tal cual.
ATAJOS = [
    ("General", [
        ("F1", "Abrir esta ayuda"),
        ("Ctrl+1 … Ctrl+4", "Cambiar de herramienta"),
        ("Ctrl+Shift+T", "Cambiar entre tema claro y oscuro"),
        ("Ctrl++  /  Ctrl+−  /  Ctrl+0",
         "Agrandar, reducir o restablecer la letra de cuadrículas y resultados"),
        ("Ctrl+Q", "Salir (se guarda la sesión)"),
    ]),
    ("Cuadrículas de matriz", [
        ("Enter  /  ↓  /  ↑", "Moverse entre filas"),
        ("Tab", "Pasar a la celda siguiente"),
        ("Ctrl+Z  /  Ctrl+Y", "Deshacer / rehacer cambios de la matriz"),
        ("Ctrl+V", "Pegar una tabla desde Excel o texto"),
    ]),
    ("Solucionador", [
        ("Ctrl+Enter", "Resolver el sistema"),
        ("Ctrl+L", "Limpiar"),
        ("Ctrl+R", "Reproducir / pausar los pasos"),
        ("←  /  →", "Paso anterior / siguiente"),
        ("Ctrl+S", "Guardar el informe (.txt)"),
        ("Ctrl+P", "Exportar el informe a PDF"),
    ]),
    ("Operaciones con matrices", [
        ("Ctrl+D", "det(A)"),
        ("Ctrl+I", "A⁻¹ por Gauss-Jordan"),
        ("Ctrl+M", "A × B"),
        ("Ctrl+L", "Limpiar"),
        ("Ctrl+S", "Guardar el resultado (.txt)"),
        ("Ctrl+P", "Exportar el resultado a PDF"),
    ]),
]


class DialogoAyuda(QDialog):
    """
    Pestañas «Atajos» y «Acerca de». Las señales `repetir_tour` y `borrar_datos`
    se emiten desde sus botones (esta última, solo si el usuario lo confirma).
    """

    repetir_tour = Signal()
    borrar_datos = Signal()

    def __init__(self, padre, pestana=0):
        super().__init__(padre)
        self.setWindowTitle("Ayuda")
        self.resize(760, 640)
        self.setMinimumSize(560, 460)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 18, 20, 16)
        raiz.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._pestana_atajos(), "Atajos de teclado")
        self.tabs.addTab(self._pestana_acerca(), "Acerca de")
        self.tabs.setCurrentIndex(pestana)
        raiz.addWidget(self.tabs, 1)

        pie = QHBoxLayout()
        b_tour = BotonAnimado("Repetir el recorrido guiado", "azul", pequeno=True)
        b_tour.clicked.connect(self._pedir_tour)
        pie.addWidget(b_tour)
        pie.addStretch(1)
        b_cerrar = BotonAnimado("Cerrar", "suave", pequeno=True)
        b_cerrar.clicked.connect(self.accept)
        pie.addWidget(b_cerrar)
        raiz.addLayout(pie)

    def _pedir_tour(self):
        self.accept()
        self.repetir_tour.emit()

    def _confirmar_borrado(self):
        """Pregunta si de verdad se quiere borrar todo; True solo si se confirma."""
        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Warning)
        caja.setWindowTitle("Borrar todos los datos")
        caja.setText("¿Seguro que quieres borrar todos los datos?")
        caja.setInformativeText(
            "Se borrarán las matrices y los resultados, el historial, la sesión "
            "guardada, el tema y el tamaño de letra, y la calculadora volverá a sus "
            "valores por defecto. Esta acción no se puede deshacer.")
        borrar = caja.addButton("Sí, borrar todo", QMessageBox.DestructiveRole)
        cancelar = caja.addButton("Cancelar", QMessageBox.RejectRole)
        caja.setDefaultButton(cancelar)
        caja.setEscapeButton(cancelar)
        caja.exec()
        return caja.clickedButton() is borrar

    def _pedir_borrado(self):
        if self._confirmar_borrado():
            self.accept()
            self.borrar_datos.emit()

    # ── Atajos ────────────────────────────────────────────────

    def _pestana_atajos(self):
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(0, 10, 8, 10)
        lay.setSpacing(12)

        for grupo, filas in ATAJOS:
            t = Tarjeta(grupo, T.AZUL)
            grid = QGridLayout()
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(8)
            for i, (tecla, texto) in enumerate(filas):
                chip = QLabel(tecla)
                chip.setStyleSheet(
                    "background-color: {}; color: {}; border: 1px solid {};"
                    " border-radius: 6px; padding: 3px 9px;"
                    " font-family: '{}'; font-weight: 700;".format(
                        T.SUPERF, T.NARANJA, T.BORDE, T.MONO))
                desc = QLabel(texto)
                desc.setWordWrap(True)
                desc.setStyleSheet("background: transparent;")
                grid.addWidget(chip, i, 0, Qt.AlignLeft | Qt.AlignVCenter)
                grid.addWidget(desc, i, 1)
            grid.setColumnStretch(1, 1)
            t.agregar_layout(grid)
            lay.addWidget(t)
        lay.addStretch(1)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(cont)
        return area

    # ── Acerca de ─────────────────────────────────────────────

    def _pestana_acerca(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 24, 10, 10)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignHCenter)

        logo = QLabel()
        logo.setPixmap(dibujar(112))
        logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo)

        nombre = QLabel(NOMBRE)
        nombre.setAlignment(Qt.AlignCenter)
        nombre.setStyleSheet("font-size: 20pt; font-weight: 800;")
        lay.addWidget(nombre)

        ver = QLabel("Versión {}".format(VERSION))
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: {}; font-weight: 600;".format(T.NARANJA))
        lay.addWidget(ver)

        curso = QLabel("MTM0120 Álgebra Lineal  ·  Universidad Americana")
        curso.setAlignment(Qt.AlignCenter)
        curso.setStyleSheet("color: {};".format(T.MUTED))
        lay.addWidget(curso)

        lay.addSpacing(12)
        desc = QLabel("Resuelve sistemas de ecuaciones lineales, opera con matrices "
                      "y vectores y consulta los teoremas del curso. Todo con "
                      "fracciones exactas y el procedimiento paso a paso.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setFixedWidth(500)          # ancho fijo: así la altura se calcula bien
        lay.addWidget(desc, 0, Qt.AlignHCenter)

        lay.addSpacing(12)
        autores = QLabel("<b>Elaborado por</b><br>Anthony Sying González Chow<br>"
                         "Jose Maria Moncada Maya<br>"
                         "Geanfranco Alexander Rodriguez Mendieta")
        autores.setAlignment(Qt.AlignCenter)
        lay.addWidget(autores)

        lay.addStretch(1)
        borrar = BotonAnimado("Borrar todos los datos", "peligro", pequeno=True)
        borrar.setToolTip("Vuelve la calculadora a sus valores por defecto")
        borrar.clicked.connect(self._pedir_borrado)
        lay.addWidget(borrar, 0, Qt.AlignHCenter)
        nota = QLabel("Devuelve la calculadora a sus valores por defecto.")
        nota.setObjectName("nota")
        nota.setAlignment(Qt.AlignCenter)
        lay.addWidget(nota)
        lay.addSpacing(8)
        tec = QLabel("Python {}  ·  PySide6 {}".format(
            platform.python_version(), PySide6.__version__))
        tec.setObjectName("nota")
        tec.setAlignment(Qt.AlignCenter)
        lay.addWidget(tec)
        return w
