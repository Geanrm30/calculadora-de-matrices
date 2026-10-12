# -*- coding: utf-8 -*-
"""Pantalla de inicio: bienvenida y accesos a cada herramienta."""
from PySide6.QtCore import Qt, QEasingCurve, QRectF, QSize, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from qt import tema as T
from qt.componentes import aparecer, mezclar


class TarjetaAcceso(QWidget):
    """Tarjeta grande clicable con resplandor de color al pasar el cursor."""

    def __init__(self, icono, titulo, detalle, color, atajo, al_pulsar):
        super().__init__()
        self._color = QColor(color)
        self._icono, self._titulo, self._detalle, self._atajo = (
            icono, titulo, detalle, atajo)
        self._al_pulsar = al_pulsar
        self._t = 0.0
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(250, 210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._paso)

    def _paso(self, v):
        self._t = v
        self.update()

    def _ir(self, destino):
        self._anim.stop()
        self._anim.setStartValue(self._t)
        self._anim.setEndValue(destino)
        self._anim.start()

    def enterEvent(self, e):
        self._ir(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._ir(0.0)
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self._al_pulsar()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        elev = 5 * self._t                       # la tarjeta "sube" al hover
        r = QRectF(2, 8 - elev, self.width() - 4, self.height() - 12)

        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, mezclar(T.PANEL, T.SUPERF, 0.35 + 0.5 * self._t))
        grad.setColorAt(1, mezclar(T.PANEL, T.PANEL, 0))
        p.setPen(QPen(mezclar(T.SUPERF, self._color, self._t), 1.5))
        p.setBrush(grad)
        p.drawRoundedRect(r, 16, 16)

        # Insignia del icono
        ins = QRectF(r.left() + 22, r.top() + 22, 52, 52)
        fondo = QColor(self._color)
        fondo.setAlpha(int(40 + 50 * self._t))
        p.setPen(Qt.NoPen)
        p.setBrush(fondo)
        p.drawRoundedRect(ins, 14, 14)
        p.setPen(self._color)
        p.setFont(QFont(T.FUENTE, 20, QFont.Bold))
        p.drawText(ins, Qt.AlignCenter, self._icono)

        # Atajo
        p.setPen(QColor(T.MUTED))
        p.setFont(QFont(T.FUENTE, 8))
        p.drawText(QRectF(r.right() - 90, r.top() + 22, 70, 20),
                   Qt.AlignRight | Qt.AlignVCenter, self._atajo)

        # Texto
        p.setPen(QColor(T.TEXTO))
        p.setFont(QFont(T.FUENTE, 13, QFont.Bold))
        p.drawText(QRectF(r.left() + 22, r.top() + 90, r.width() - 44, 28),
                   Qt.AlignLeft | Qt.AlignVCenter, self._titulo)
        p.setPen(QColor(T.MUTED))
        p.setFont(QFont(T.FUENTE, 9))
        p.drawText(QRectF(r.left() + 22, r.top() + 122, r.width() - 44, 60),
                   Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self._detalle)

        # Flecha que aparece al hover
        p.setPen(mezclar(T.FONDO, self._color, self._t))
        p.setFont(QFont(T.FUENTE, 14, QFont.Bold))
        p.drawText(QRectF(r.right() - 50, r.bottom() - 40, 30, 28),
                   Qt.AlignCenter, "→")


class PaginaInicio(QWidget):

    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 34, 40, 30)
        lay.setSpacing(0)

        sup = QLabel("MTM0120  ·  UNIVERSIDAD AMERICANA")
        sup.setStyleSheet("color: {}; font-size: 9pt; font-weight: 700;"
                          " letter-spacing: 3px;".format(T.NARANJA))
        lay.addWidget(sup)

        tit = QLabel("Calculadora de Álgebra Lineal")
        tit.setStyleSheet("font-size: 30pt; font-weight: 800; padding-top: 6px;")
        lay.addWidget(tit)

        sub = QLabel("Resuelve sistemas, opera con matrices y vectores y consulta "
                     "los teoremas del curso.\nTodo con fracciones exactas y el "
                     "procedimiento paso a paso.")
        sub.setStyleSheet("color: {}; font-size: 11pt; margin: 8px 0 26px 0;"
                          .format(T.MUTED))
        lay.addWidget(sub)

        fila = QHBoxLayout()
        fila.setSpacing(18)
        self.tarjetas = [
            TarjetaAcceso("Ax", "Solucionador",
                          "Gauss y Gauss-Jordan con paso a paso: ecuación "
                          "matricial A·x = b, combinación lineal e independencia.",
                          T.NARANJA, "Ctrl+2",
                          lambda: ventana.ir_a("solucionador")),
            TarjetaAcceso("A+B", "Operaciones con matrices",
                          "Suma, resta, producto, transpuesta, determinante, "
                          "inversa, Cramer y verificación de propiedades.",
                          T.AZUL, "Ctrl+3",
                          lambda: ventana.ir_a("matrices")),
            TarjetaAcceso("∴", "Teoremas clave",
                          "Catálogo con buscador de los teoremas y criterios "
                          "del curso (Sesiones 1–11).",
                          T.MORADO, "Ctrl+4",
                          lambda: ventana.ir_a("teoremas")),
        ]
        for t in self.tarjetas:
            fila.addWidget(t)
        lay.addLayout(fila)
        lay.addStretch(1)

        pie = QLabel("Elaborado por: Anthony Sying González Chow · Jose Maria "
                     "Moncada Maya · Geanfranco Alexander Rodriguez Mendieta")
        pie.setObjectName("nota")
        lay.addWidget(pie)

    def showEvent(self, e):
        super().showEvent(e)
        # Las tarjetas entran una tras otra.
        for i, t in enumerate(self.tarjetas):
            aparecer(t, 420, retraso=90 * i)
