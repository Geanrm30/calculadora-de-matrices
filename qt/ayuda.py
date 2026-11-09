# -*- coding: utf-8 -*-
"""
Ventana de ayuda: atajos de teclado y «Acerca de».
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import platform

import PySide6
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QMessageBox, QScrollArea, QVBoxLayout, QWidget)

from qt import NOMBRE, VERSION
from qt import tema as T
from qt.componentes import (BotonAnimado, CajaAnimada, DialogoAnimado,
                            PestanasAnimadas, Tarjeta)
from qt.icono import dibujar

ATAJOS = [
    ("General", [
        ("F1", "Abrir esta ayuda"),
        ("Ctrl+1 … Ctrl+6", "Cambiar de herramienta"),
        ("Ctrl+Shift+T", "Cambiar entre tema claro y oscuro"),
        ("Ctrl++  /  Ctrl+−  /  Ctrl+0",
         "Agrandar, reducir o restablecer la letra de cuadrículas y resultados"),
        ("F11  /  Esc", "Modo exposición (letra grande, sin barra lateral) / salir"),
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
    ("Factorización LU", [
        ("Ctrl+Enter", "Factorizar A = L·U"),
        ("Ctrl+L", "Limpiar"),
        ("Ctrl+S", "Guardar el informe (.txt)"),
        ("Ctrl+P", "Exportar el informe a PDF"),
    ]),
    ("Métodos Numéricos", [
        ("Enter", "Calcular desde cualquier campo de la pestaña"),
        ("Ctrl+Enter", "Calcular (bisección, gráfica, descomposición o errores)"),
        ("Ctrl+G", "Graficar la raíz de la bisección"),
        ("Ctrl+L", "Limpiar la pestaña actual"),
        ("Ctrl+Shift+Z", "Deshacer la última limpieza"),
        ("Ctrl+S", "Guardar el informe (.txt)"),
        ("Ctrl+P", "Exportar el informe a PDF"),
    ]),
]


class DialogoAyuda(DialogoAnimado):
    """
    Pestañas «Atajos» y «Acerca de». Las señales `repetir_tour` y `borrar_datos`
    se emiten desde sus botones (esta última, solo si el usuario lo confirma).
    """

    repetir_tour = Signal()
    borrar_datos = Signal()

    def __init__(self, padre, pestana=0):
        """Crea el diálogo de ayuda con pestañas de guía, atajos y acerca de."""
        super().__init__(padre)
        self.setWindowTitle("Ayuda")
        self.resize(760, 640)
        self.setMinimumSize(560, 460)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 18, 20, 16)
        raiz.setSpacing(12)

        self.tabs = PestanasAnimadas(T.FONDO)
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
        """Cierra la ayuda y, ya cerrada, pide repetir el recorrido guiado."""
        self._al_cerrar = self.repetir_tour.emit
        self.accept()

    def _confirmar_borrado(self):
        """Pregunta si de verdad se quiere borrar todo; True solo si se confirma."""
        caja = CajaAnimada(self)
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
        """Pide confirmación y, si se acepta, cierra la ayuda y pide borrar los datos guardados."""
        if self._confirmar_borrado():
            self._al_cerrar = self.borrar_datos.emit
            self.accept()


    def _pestana_atajos(self):
        """Construye la pestaña con la lista de atajos de teclado."""
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


    def _pestana_acerca(self):
        """Construye la pestaña con la información del programa y sus autores."""
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
        desc.setFixedWidth(500)
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
