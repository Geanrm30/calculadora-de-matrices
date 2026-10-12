# -*- coding: utf-8 -*-
"""Exportación de informes a PDF (A4, fondo blanco, texto negro)."""
import datetime

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument

from qt import render
from qt import tema as T


def encabezado_html(titulo):
    fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    return (
        "<h1 style=\"font-family:'{f}'; color:{t}; margin:0 0 2px 0;"
        " font-size:20pt;\">{titulo}</h1>"
        "<p style=\"font-family:'{f}'; color:{m}; margin:0 0 6px 0;"
        " font-size:9pt;\">Calculadora de Álgebra Lineal · MTM0120 · "
        "Universidad Americana · {fecha}</p>"
        "<hr style=\"color:{b}\">".format(
            f=T.FUENTE, t=T.TEXTO, m=T.MUTED, b=T.BORDE,
            titulo=titulo, fecha=fecha))


def escribir_pdf(ruta, titulo, cuerpo_html):
    """
    Escribe el PDF. 'cuerpo_html' debe haberse generado dentro de
    `with tema.paleta_temporal("impreso")` para que use colores de impresión.
    """
    with T.paleta_temporal("impreso"):
        html = render.pagina(encabezado_html(titulo) + cuerpo_html, impreso=True)

    doc = QTextDocument()
    doc.setHtml(html)

    escritor = QPdfWriter(ruta)
    escritor.setPageSize(QPageSize(QPageSize.A4))
    escritor.setPageMargins(QMarginsF(16, 16, 16, 16), QPageLayout.Millimeter)
    escritor.setTitle(titulo)
    doc.print_(escritor)
