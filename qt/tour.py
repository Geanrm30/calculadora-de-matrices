# -*- coding: utf-8 -*-
"""
Recorrido guiado: oscurece la ventana, ilumina un elemento a la vez y explica
para qué sirve. Se muestra la primera vez y se puede repetir desde la ayuda.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import (QEasingCurve, QEvent, QPoint, QRectF, Qt, QTimer,
                            QVariantAnimation)
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)

from qt import tema as T
from qt.componentes import BotonAnimado


@dataclass
class PasoTour:
    titulo: str
    texto: str
    objetivo: Callable[[], QWidget]      # widget que se ilumina
    pagina: Optional[str] = None         # página a mostrar antes (clave)


class Tour(QWidget):

    MARGEN = 10

    def __init__(self, ventana, pasos, al_terminar=None):
        super().__init__(ventana)
        self._ventana = ventana
        self._pasos = pasos
        self._al_terminar = al_terminar
        self._i = 0
        self._hueco = QRectF()
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(320)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._mover_hueco)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setGeometry(ventana.rect())

        # Tarjeta con la explicación
        self.card = QFrame(self)
        self.card.setObjectName("tarjeta")
        self.card.setFixedWidth(360)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(18, 16, 18, 14)
        cl.setSpacing(8)
        self.lbl_num = QLabel("")
        self.lbl_num.setObjectName("tarjetaTitulo")
        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setStyleSheet(
            "font-size: 13pt; font-weight: 700; background: transparent;")
        self.lbl_texto = QLabel("")
        self.lbl_texto.setWordWrap(True)
        self.lbl_texto.setStyleSheet("background: transparent;")
        for l in (self.lbl_num, self.lbl_titulo, self.lbl_texto):
            cl.addWidget(l)

        fila = QHBoxLayout()
        fila.setSpacing(6)
        self.b_omitir = BotonAnimado("Omitir", "fantasma", pequeno=True)
        self.b_ant = BotonAnimado("Anterior", "suave", pequeno=True)
        self.b_sig = BotonAnimado("Siguiente", "primario", pequeno=True)
        self.b_omitir.clicked.connect(self.terminar)
        self.b_ant.clicked.connect(self.anterior)
        self.b_sig.clicked.connect(self.siguiente)
        fila.addWidget(self.b_omitir)
        fila.addStretch(1)
        fila.addWidget(self.b_ant)
        fila.addWidget(self.b_sig)
        cl.addLayout(fila)

        ventana.installEventFilter(self)
        self.show()
        self.raise_()
        self.setFocus()
        self._ir(0, animar=False)

    # ── Navegación ────────────────────────────────────────────

    def _ir(self, i, animar=True):
        self._i = i
        paso = self._pasos[i]
        if paso.pagina:
            self._ventana.ir_a(paso.pagina)

        self.lbl_num.setText("PASO {} DE {}".format(i + 1, len(self._pasos)))
        self.lbl_titulo.setText(paso.titulo)
        self.lbl_texto.setText(paso.texto)
        self.b_ant.setEnabled(i > 0)
        self.b_sig.setText("Finalizar" if i == len(self._pasos) - 1 else "Siguiente")
        # Espera a que termine la transición de página y se acomode el diseño.
        QTimer.singleShot(380 if paso.pagina else 40,
                          lambda: self._ubicar_seguro(animar))

    def siguiente(self):
        if self._i >= len(self._pasos) - 1:
            self.terminar()
        else:
            self._ir(self._i + 1)

    def anterior(self):
        if self._i > 0:
            self._ir(self._i - 1)

    def terminar(self):
        self._ventana.removeEventFilter(self)
        self.hide()
        self.deleteLater()
        if self._al_terminar:
            self._al_terminar()

    # ── Colocación ────────────────────────────────────────────

    def _rect_objetivo(self):
        w = self._pasos[self._i].objetivo()
        # Si la página tiene desplazamiento, se lleva el elemento a la vista.
        padre = w.parentWidget()
        while padre is not None:
            if isinstance(padre, QScrollArea):
                padre.ensureWidgetVisible(w, 20, 20)
            padre = padre.parentWidget()
        origen = w.mapTo(self._ventana, QPoint(0, 0))
        m = self.MARGEN
        return QRectF(origen.x() - m, origen.y() - m,
                      w.width() + 2 * m, w.height() + 2 * m)

    def _ubicar_seguro(self, animar=True):
        try:
            self._ubicar(animar)
        except RuntimeError:
            pass                          # el recorrido se cerró antes

    def _ubicar(self, animar=True):
        if not self.isVisible():
            return
        destino = self._rect_objetivo()
        if animar and not self._hueco.isNull():
            self._anim.stop()
            self._anim.setStartValue(self._hueco)
            self._anim.setEndValue(destino)
            self._anim.start()
        else:
            self._hueco = destino
            self.update()
        self._colocar_tarjeta(destino)

    def _mover_hueco(self, rect):
        self._hueco = rect
        self.update()

    def _colocar_tarjeta(self, rect=None):
        rect = rect or self._hueco
        self.card.adjustSize()
        cw, ch = self.card.width(), self.card.height()
        W, H, g = self.width(), self.height(), 18

        # A la derecha del elemento, si cabe; si no a la izquierda, debajo o arriba.
        if rect.right() + g + cw <= W - 12:
            x, y = rect.right() + g, rect.top()
        elif rect.left() - g - cw >= 12:
            x, y = rect.left() - g - cw, rect.top()
        elif rect.bottom() + g + ch <= H - 12:
            x, y = rect.left(), rect.bottom() + g
        else:
            x, y = rect.left(), rect.top() - g - ch
        x = max(12, min(x, W - cw - 12))
        y = max(12, min(y, H - ch - 12))
        self.card.move(int(x), int(y))

    # ── Dibujo y eventos ──────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        todo = QPainterPath()
        todo.addRect(QRectF(self.rect()))
        hueco = QPainterPath()
        hueco.addRoundedRect(self._hueco, 12, 12)
        p.fillPath(todo.subtracted(hueco), QColor(0, 0, 0, 175))
        p.setPen(QPen(QColor(T.NARANJA), 2.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(self._hueco, 12, 12)

    def eventFilter(self, obj, e):
        if obj is self._ventana and e.type() == QEvent.Resize:
            self.setGeometry(self._ventana.rect())
            QTimer.singleShot(0, lambda: self._ubicar_seguro(False))
        return super().eventFilter(obj, e)

    def mousePressEvent(self, e):
        e.accept()                   # bloquea los clics mientras dura el recorrido

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.terminar()
        elif e.key() in (Qt.Key_Right, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.siguiente()
        elif e.key() == Qt.Key_Left:
            self.anterior()
        else:
            e.accept()
