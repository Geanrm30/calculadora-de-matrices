# -*- coding: utf-8 -*-
"""
Imágenes para pegar en Word o PowerPoint: una matriz limpia entre corchetes y
los informes completos. Siguen el tema de la calculadora: fondo oscuro con letra
clara en el tema oscuro, y blanco con letra oscura en el claro.
"""
from math import sqrt

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage, QPainter, QPen,
                           QTextDocument)

from qt import render
from qt import tema as T

# Tope de píxeles de una imagen: un informe muy largo no debe agotar la memoria
MAXIMO_DE_PIXELES = 24_000_000


def _escala_segura(ancho, alto, escala):
    """Reduce la escala si la imagen resultante pasaría el tope de píxeles."""
    return min(escala, sqrt(MAXIMO_DE_PIXELES / max(1, ancho * alto)))


def imagen_de_matriz(textos, aumentada=False, paleta=None, escala=2):
    """
    Dibuja la matriz (lista de filas de texto) entre corchetes, con los números
    centrados por columna. Con aumentada=True añade la barra antes de la última columna.
    Los colores salen de la paleta (por defecto la de las imágenes del tema actual).
    """
    colores = T.PALETAS[paleta or T.paleta_de_imagen()]
    fuente = QFont(T.MONO)
    fuente.setPixelSize(round(24 * escala))
    medidas = QFontMetrics(fuente)
    filas, columnas = len(textos), len(textos[0])

    ancho_columna = [max(medidas.horizontalAdvance(textos[i][j]) for i in range(filas))
                     for j in range(columnas)]
    separacion = round(34 * escala)          # hueco entre columnas
    margen = round(26 * escala)              # hueco entre el corchete y los números
    alto_fila = medidas.height() + round(14 * escala)
    barra = round(14 * escala) if aumentada else 0

    ancho = (2 * margen + sum(ancho_columna) + separacion * (columnas - 1) + 2 * barra
             + round(8 * escala))
    alto = filas * alto_fila + round(16 * escala)
    imagen = QImage(ancho, alto, QImage.Format_ARGB32)
    imagen.fill(QColor(colores["FONDO"]))

    p = QPainter(imagen)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    tinta = QColor(colores["TEXTO"])
    p.setFont(fuente)
    p.setPen(tinta)

    x = float(margen + round(4 * escala))
    for j in range(columnas):
        if aumentada and j == columnas - 1:
            x += barra
            p.setPen(QPen(QColor(colores["MUTED"]), max(1.5, 1.6 * escala)))
            p.drawLine(QPointF(x - separacion / 2, round(8 * escala)),
                       QPointF(x - separacion / 2, alto - round(8 * escala)))
            p.setPen(tinta)
            x += barra
        for i in range(filas):
            p.drawText(round(x), round(8 * escala) + i * alto_fila,
                       ancho_columna[j], alto_fila, Qt.AlignCenter, textos[i][j])
        x += ancho_columna[j] + separacion

    # Corchetes izquierdo y derecho
    p.setPen(QPen(tinta, max(2.0, 2.4 * escala), Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
    y0, y1, brazo = round(5 * escala), alto - round(5 * escala), round(12 * escala)
    izq, der = round(6 * escala), ancho - round(6 * escala)
    p.drawPolyline([QPointF(izq + brazo, y0), QPointF(izq, y0),
                    QPointF(izq, y1), QPointF(izq + brazo, y1)])
    p.drawPolyline([QPointF(der - brazo, y0), QPointF(der, y0),
                    QPointF(der, y1), QPointF(der - brazo, y1)])
    p.end()
    return imagen


def imagen_de_html(cuerpo_html, paleta=None, ancho=980, escala=2):
    """
    Convierte HTML (el cuerpo de un informe) en imagen. El cuerpo debe haberse
    generado con la misma paleta (ver tema.paleta_temporal).
    """
    paleta = paleta or T.paleta_de_imagen()
    with T.paleta_temporal(paleta):
        html = render.pagina(cuerpo_html, impreso=True)
        fondo = QColor(T.FONDO)
    documento = QTextDocument()
    documento.setDocumentMargin(18)
    documento.setHtml(html)
    documento.setTextWidth(ancho)
    alto = int(documento.size().height()) + 1

    escala = _escala_segura(ancho, alto, escala)
    imagen = QImage(max(1, int(ancho * escala)), max(1, int(alto * escala)),
                    QImage.Format_ARGB32)
    imagen.fill(fondo)
    p = QPainter(imagen)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.scale(escala, escala)
    documento.drawContents(p)
    p.end()
    return imagen


def imagen_de_texto(texto, paleta=None, ancho=980):
    """Convierte un informe de texto plano (con sus colores de diagnóstico) en imagen."""
    paleta = paleta or T.paleta_de_imagen()
    with T.paleta_temporal(paleta):
        cuerpo = render.html_texto(texto)
    return imagen_de_html(cuerpo, paleta, ancho)
