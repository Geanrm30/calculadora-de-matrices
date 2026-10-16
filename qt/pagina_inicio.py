# -*- coding: utf-8 -*-
"""Pantalla de inicio: bienvenida y accesos a cada herramienta, con fondo animado."""
import math

from PySide6.QtCore import (Qt, QEasingCurve, QPointF, QRectF, QTimer,
                            QVariantAnimation)
from PySide6.QtGui import (QColor, QFont, QLinearGradient, QPainter,
                           QPainterPath, QPen, QRadialGradient)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from qt import tema as T
from qt.componentes import entrada_suave, mezclar


class TarjetaAcceso(QWidget):
    """
    Tarjeta grande clicable. Entra deslizándose desde abajo; al pasar el cursor
    se eleva, proyecta sombra y un foco de luz del color de la herramienta
    sigue al cursor por dentro.
    """

    def __init__(self, icono, titulo, detalle, color, atajo, al_pulsar):
        super().__init__()
        self._color = QColor(color)
        self._icono, self._titulo, self._detalle, self._atajo = (
            icono, titulo, detalle, atajo)
        self._al_pulsar = al_pulsar
        self._t = 0.0                           # avance del cursor encima
        self._ent = 0.0                         # avance de la entrada
        self._cursor = QPointF(0, 0)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setMinimumSize(250, 210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._paso)

        self._anim_ent = QVariantAnimation(self)
        self._anim_ent.setDuration(800)
        self._anim_ent.setStartValue(0.0)
        self._anim_ent.setEndValue(1.0)
        self._anim_ent.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_ent.valueChanged.connect(self._paso_ent)

    def entrar(self, retraso=0):
        """Reinicia la animación de entrada (se llama cada vez que se muestra Inicio)."""
        self._anim_ent.stop()
        self._ent = 0.0
        self.update()

        def iniciar():
            try:
                self._anim_ent.start()
            except RuntimeError:
                pass
        QTimer.singleShot(retraso, iniciar)

    def _paso(self, v):
        self._t = v
        self.update()

    def _paso_ent(self, v):
        self._ent = v
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

    def mouseMoveEvent(self, e):
        self._cursor = QPointF(e.position())
        self.update()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self._al_pulsar()

    def paintEvent(self, _):
        if self._ent <= 0.0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self._ent)
        p.translate(0, (1.0 - self._ent) * 40)

        elev = 8 * self._t                       # la tarjeta "sube" al pasar el cursor
        r = QRectF(3, 10 - elev, self.width() - 6, self.height() - 18)

        # Sombra suave que crece al pasar el cursor
        p.setPen(Qt.NoPen)
        for k in range(1, 8):
            p.setBrush(QColor(0, 0, 0, int((7 + 22 * self._t) / k * 2)))
            p.drawRoundedRect(r.adjusted(-k, k * 1.5, k, k * 2.4), 16 + k, 16 + k)

        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, mezclar(T.PANEL, T.SUPERF, 0.35 + 0.5 * self._t))
        grad.setColorAt(1, mezclar(T.PANEL, T.PANEL, 0))
        p.setPen(QPen(mezclar(T.SUPERF, self._color, self._t), 1.5))
        p.setBrush(grad)
        p.drawRoundedRect(r, 16, 16)

        # Foco de luz que sigue al cursor
        if self._t > 0.01:
            p.save()
            ruta = QPainterPath()
            ruta.addRoundedRect(r, 16, 16)
            p.setClipPath(ruta)
            luz = QRadialGradient(self._cursor + QPointF(0, -6), 260)
            c0 = QColor(self._color)
            c0.setAlpha(int(80 * self._t))
            c1 = QColor(self._color)
            c1.setAlpha(0)
            luz.setColorAt(0.0, c0)
            luz.setColorAt(1.0, c1)
            p.fillRect(r, luz)
            p.restore()

        # Insignia del icono
        ins = QRectF(r.left() + 22, r.top() + 22, 52, 52)
        fondo = QColor(self._color)
        fondo.setAlpha(int(40 + 50 * self._t))
        p.setPen(Qt.NoPen)
        p.setBrush(fondo)
        p.drawRoundedRect(ins, 14, 14)
        p.setPen(self._color)
        p.setFont(QFont(T.FUENTE, 20 if len(self._icono) <= 2 else 14, QFont.Bold))
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

        # Flecha que aparece deslizándose al pasar el cursor
        p.setPen(mezclar(T.PANEL, self._color, self._t))
        p.setFont(QFont(T.FUENTE, 14, QFont.Bold))
        p.drawText(QRectF(r.right() - 50 - 14 * (1.0 - self._t), r.bottom() - 40, 30, 28),
                   Qt.AlignCenter, "→")


class LineaAcento(QWidget):
    """Línea fina con degradado que se dibuja de izquierda a derecha al entrar."""

    ANCHO = 380

    def __init__(self):
        super().__init__()
        self.setFixedHeight(4)
        self._p = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._paso)

    def _paso(self, v):
        self._p = v
        self.update()

    def iniciar(self, retraso=0):
        self._anim.stop()
        self._p = 0.0
        self.update()

        def ir():
            try:
                self._anim.start()
            except RuntimeError:
                pass
        QTimer.singleShot(retraso, ir)

    def paintEvent(self, _):
        p = QPainter(self)
        g = QLinearGradient(0, 0, self.ANCHO, 0)
        g.setColorAt(0.0, QColor(T.NARANJA))
        g.setColorAt(0.55, QColor(T.AZUL))
        g.setColorAt(1.0, QColor(T.MORADO))
        p.fillRect(QRectF(0, 1, self.ANCHO * self._p, 2.5), g)


class PaginaInicio(QWidget):

    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        self._fase = 0.0
        self._reloj = QTimer(self)
        self._reloj.setInterval(40)
        self._reloj.timeout.connect(self._avanzar)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 34, 40, 30)
        lay.setSpacing(0)

        self._sup = QLabel("MTM0120  ·  UNIVERSIDAD AMERICANA")
        self._sup.setStyleSheet("color: {}; font-size: 9pt; font-weight: 700;"
                                " letter-spacing: 3px;".format(T.NARANJA))
        lay.addWidget(self._sup)

        self._tit = QLabel("Calculadora de Álgebra Lineal")
        self._tit.setStyleSheet("font-size: 30pt; font-weight: 800; padding-top: 6px;")
        lay.addWidget(self._tit)

        for etiqueta in (self._sup, self._tit):
            etiqueta.setIndent(0)                # Qt sangra las etiquetas con estilo
        lay.addSpacing(8)
        self._linea = LineaAcento()
        lay.addWidget(self._linea)

        self._sub = QLabel("Resuelve sistemas, opera con matrices y vectores y consulta "
                           "los teoremas del curso.\nTodo con fracciones exactas y el "
                           "procedimiento paso a paso.")
        self._sub.setStyleSheet("color: {}; font-size: 11pt; margin: 12px 0 26px 0;"
                                .format(T.MUTED))
        self._sub.setIndent(0)
        lay.addWidget(self._sub)

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

        self._pie = QLabel("Elaborado por: Anthony Sying González Chow · Jose Maria "
                           "Moncada Maya · Geanfranco Alexander Rodriguez Mendieta")
        self._pie.setObjectName("nota")
        lay.addWidget(self._pie)

    # ── Fondo animado: manchas de color que derivan despacio ──

    def _avanzar(self):
        self._fase += 0.04
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(T.FONDO))
        ancho, alto = self.width(), self.height()
        alfa = 52 if T.NOMBRE_TEMA == "oscuro" else 38
        t = self._fase
        for k, color in enumerate((T.NARANJA, T.AZUL, T.MORADO)):
            cx = ancho * (0.5 + 0.40 * math.sin(t * 0.33 + k * 2.1))
            cy = alto * (0.38 + 0.24 * math.cos(t * 0.27 + k * 1.7))
            radio = max(ancho, alto) * (0.36 + 0.05 * math.sin(t * 0.5 + k))
            g = QRadialGradient(QPointF(cx, cy), radio)
            c0 = QColor(color)
            c0.setAlpha(alfa)
            c1 = QColor(color)
            c1.setAlpha(0)
            g.setColorAt(0.0, c0)
            g.setColorAt(1.0, c1)
            p.fillRect(self.rect(), g)

    def showEvent(self, e):
        super().showEvent(e)
        self._reloj.start()
        # Todo entra escalonado: título, línea, subtítulo y las tarjetas una a una
        entrada_suave(self._sup, 0)
        entrada_suave(self._tit, 130)
        self._linea.iniciar(300)
        entrada_suave(self._sub, 420)
        for i, t in enumerate(self.tarjetas):
            t.entrar(520 + 140 * i)
        entrada_suave(self._pie, 1000)

    def hideEvent(self, e):
        super().hideEvent(e)
        self._reloj.stop()
