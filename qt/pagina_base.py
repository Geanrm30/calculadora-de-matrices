# -*- coding: utf-8 -*-
"""Base común de las páginas: título, subtítulo, aviso de error y contenido."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from qt.componentes import aparecer, mostrar_aviso


class BannerError(QLabel):
    """Franja roja bajo el título con el motivo del error. Clic para cerrarla."""

    def __init__(self):
        super().__init__()
        self.setObjectName("errorBanner")
        self.setWordWrap(True)
        self.setTextFormat(Qt.PlainText)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Clic para cerrar")
        self.hide()

    def mousePressEvent(self, e):
        self.hide()


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

        self.banner = BannerError()
        self.raiz.addWidget(self.banner)

    def atajo(self, secuencia, funcion):
        """Atajo de teclado activo solo mientras esta página está visible."""
        QShortcut(QKeySequence(secuencia), self, activated=funcion,
                  context=Qt.WindowShortcut)

    @staticmethod
    def respetar_minimos(splitter):
        """
        Evita que un panel del divisor se aplaste por debajo de lo que su
        contenido necesita (los títulos se cortaban y los botones se montaban).
        Si la ventana es más estrecha, la página se desplaza en horizontal.
        """
        for i in range(splitter.count()):
            w = splitter.widget(i)
            w.setMinimumWidth(max(w.minimumWidth(), w.minimumSizeHint().width()))

    # ── Errores e información ─────────────────────────────────
    # Los errores se muestran en una franja dentro de la página (sin ventana
    # emergente que interrumpa); la celda culpable queda en rojo.

    def error(self, titulo, texto):
        detalle = " ".join(texto.split())
        self.banner.setText("⚠  {}: {}".format(titulo, detalle))
        self.banner.show()
        aparecer(self.banner, 220)

    def ocultar_error(self, *_):
        if not self.banner.isHidden():
            self.banner.hide()

    def info(self, titulo, texto):
        mostrar_aviso(self, texto, "info")
