# -*- coding: utf-8 -*-
"""Icono de la aplicación, dibujado por código (no hace falta ningún archivo)."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QIcon, QLinearGradient, QPainter,
                           QPen, QPixmap)

TAMANOS = (16, 24, 32, 48, 64, 128, 256)


def dibujar(tamano):
    """Cuadrado redondeado oscuro con una matriz 2×2 entre corchetes."""
    pm = QPixmap(tamano, tamano)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    t = float(tamano)

    fondo = QLinearGradient(0, 0, 0, t)
    fondo.setColorAt(0, QColor("#3B3D52"))
    fondo.setColorAt(1, QColor("#181825"))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(fondo))
    p.drawRoundedRect(QRectF(0, 0, t, t), t * 0.22, t * 0.22)

    # Corchetes
    naranja = QColor("#FAB387")
    lapiz = QPen(naranja, max(1.2, t * 0.07), Qt.SolidLine, Qt.RoundCap,
                 Qt.RoundJoin)
    p.setPen(lapiz)
    p.setBrush(Qt.NoBrush)
    x0, x1 = t * 0.22, t * 0.78
    y0, y1 = t * 0.20, t * 0.80
    brazo = t * 0.10
    p.drawPolyline([QPointF(x0 + brazo, y0), QPointF(x0, y0),
                    QPointF(x0, y1), QPointF(x0 + brazo, y1)])
    p.drawPolyline([QPointF(x1 - brazo, y0), QPointF(x1, y0),
                    QPointF(x1, y1), QPointF(x1 - brazo, y1)])

    # Elementos de la matriz
    p.setPen(Qt.NoPen)
    radio = t * 0.075
    for cx, cy, color in ((0.40, 0.38, "#89B4FA"), (0.60, 0.38, "#FAB387"),
                          (0.40, 0.62, "#FAB387"), (0.60, 0.62, "#89B4FA")):
        p.setBrush(QColor(color))
        p.drawEllipse(QPointF(t * cx, t * cy), radio, radio)
    p.end()
    return pm


def crear_icono():
    icono = QIcon()
    for t in TAMANOS:
        icono.addPixmap(dibujar(t))
    return icono
