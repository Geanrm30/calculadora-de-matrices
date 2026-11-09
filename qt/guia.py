# -*- coding: utf-8 -*-
"""
Guía para encontrar un botón: tras llevarte a la herramienta, marca el elemento
con anillos que se expanden y una burbuja que explica qué hacer. Se retira sola
(o con un clic, una tecla o al pulsar el propio elemento).
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import math

from PySide6.QtCore import (QEasingCurve, QEvent, QPoint, QPointF, QRectF, Qt, QTimer,
                            QVariantAnimation)
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen,
                           QPolygonF)
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget

from qt import tema as T


class Guia(QWidget):
    """Capa transparente sobre la ventana que señala un elemento."""

    DURACION = 8000

    def __init__(self, ventana, objetivo, texto):
        """Crea la capa de guía que resalta un elemento de la ventana con una burbuja."""
        super().__init__(ventana)
        self._ventana = ventana
        self._objetivo = objetivo
        self._texto = texto
        self._fase = 0.0
        self._alfa = 0.0
        self._cerrando = False
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(ventana.rect())
        self.show()
        self.raise_()

        padre = objetivo.parentWidget()
        while padre is not None:
            if isinstance(padre, QScrollArea):
                padre.ensureWidgetVisible(objetivo, 30, 40)
            padre = padre.parentWidget()

        self._reloj = QTimer(self)
        self._reloj.setInterval(16)
        self._reloj.timeout.connect(self._avanzar)
        self._reloj.start()

        self._entrada = QVariantAnimation(self)
        self._entrada.setDuration(380)
        self._entrada.setStartValue(0.0)
        self._entrada.setEndValue(1.0)
        self._entrada.setEasingCurve(QEasingCurve.OutCubic)
        self._entrada.valueChanged.connect(self._poner_alfa)
        self._entrada.start()

        QTimer.singleShot(self.DURACION, self.cerrar)
        QTimer.singleShot(350, lambda: QApplication.instance().installEventFilter(self))
        ventana.installEventFilter(self)

    def _poner_alfa(self, v):
        """Fija la opacidad de la capa."""
        self._alfa = v

    def _avanzar(self):
        """Avanza la fase de los anillos animados y repinta."""
        self._fase += 0.016
        self.update()

    def cerrar(self):
        """Desvanece la guía y la elimina."""
        if self._cerrando:
            return
        self._cerrando = True
        salida = QVariantAnimation(self)
        salida.setDuration(260)
        salida.setStartValue(self._alfa)
        salida.setEndValue(0.0)
        salida.valueChanged.connect(self._poner_alfa)
        salida.finished.connect(self._eliminar)
        salida.start()
        self._salida = salida

    def _eliminar(self):
        """Quita los filtros de eventos y destruye la capa."""
        try:
            QApplication.instance().removeEventFilter(self)
            self._ventana.removeEventFilter(self)
            self._reloj.stop()
            self.hide()
            self.deleteLater()
        except RuntimeError:
            pass

    def eventFilter(self, obj, e):
        """Reajusta la guía al cambiar el tamaño de la ventana y la cierra con un clic o una tecla."""
        tipo = e.type()
        if obj is self._ventana and tipo == QEvent.Resize:
            self.setGeometry(self._ventana.rect())
        elif tipo in (QEvent.MouseButtonPress, QEvent.KeyPress):
            self.cerrar()
        return False


    def _rect_objetivo(self):
        """Rectángulo del elemento resaltado en coordenadas de la ventana."""
        w = self._objetivo
        origen = w.mapTo(self._ventana, QPoint(0, 0))
        m = 7
        return QRectF(origen.x() - m, origen.y() - m, w.width() + 2 * m, w.height() + 2 * m)

    def paintEvent(self, _):
        """Dibuja el fondo atenuado, el hueco, los anillos y la burbuja."""
        try:
            if not self._objetivo.isVisible():
                return
            r = self._rect_objetivo()
        except RuntimeError:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor(T.NARANJA)

        p.setBrush(Qt.NoBrush)
        for k in range(3):
            t = (self._fase * 0.75 + k / 3.0) % 1.0
            crece = 4 + 26 * t
            c = QColor(color)
            c.setAlpha(int(170 * (1.0 - t) * self._alfa))
            p.setPen(QPen(c, 2.4))
            p.drawRoundedRect(r.adjusted(-crece, -crece, crece, crece), 12 + crece * 0.4, 12 + crece * 0.4)

        for grosor, alfa in ((7.0, 40), (2.6, 235)):
            c = QColor(color)
            c.setAlpha(int(alfa * self._alfa))
            p.setPen(QPen(c, grosor))
            p.drawRoundedRect(r, 12, 12)

        self._burbuja(p, r)

    def _burbuja(self, p, r):
        """Dibuja la burbuja con el texto de la indicación junto al elemento."""
        fuente = QFont(T.FUENTE, 10)
        fuente.setWeight(QFont.DemiBold)
        p.setFont(fuente)
        ancho_texto = min(330, max(200, self.width() - 80))
        caja = QFontMetrics(fuente).boundingRect(0, 0, ancho_texto, 1000,
                                                 Qt.TextWordWrap | Qt.AlignLeft, self._texto)
        ancho, alto = caja.width() + 36, caja.height() + 28
        W, H, hueco = self.width(), self.height(), 26

        abajo = r.bottom() + hueco + alto <= H - 10
        y = r.bottom() + hueco if abajo else r.top() - hueco - alto
        x = r.center().x() - ancho / 2
        x = max(12, min(x, W - ancho - 12))
        rebote = 5 * (0.5 + 0.5 * math.sin(self._fase * 6.0))
        y += 12 * (1.0 - self._alfa) * (1 if abajo else -1)

        cuerpo = QRectF(x, y, ancho, alto)
        p.setOpacity(self._alfa)
        ruta = QPainterPath()
        ruta.addRoundedRect(cuerpo, 10, 10)
        punta_x = max(cuerpo.left() + 22, min(r.center().x(), cuerpo.right() - 22))
        if abajo:
            y0, y1 = cuerpo.top(), cuerpo.top() - 12 - rebote
        else:
            y0, y1 = cuerpo.bottom(), cuerpo.bottom() + 12 + rebote
        flecha = QPolygonF([QPointF(punta_x - 11, y0), QPointF(punta_x + 11, y0), QPointF(punta_x, y1)])
        ruta.addPolygon(flecha)
        p.setPen(QPen(QColor(T.NARANJA), 1.6))
        p.setBrush(QColor(T.CRUST))
        p.drawPath(ruta.simplified())
        p.setPen(QColor(T.TEXTO))
        p.drawText(cuerpo.adjusted(18, 14, -18, -14), Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignVCenter,
                   self._texto)
        p.setOpacity(1.0)


def _prop(texto):
    """Texto que indica elegir la propiedad de la lista y verificarla."""
    return "Elige en esta lista una propiedad sobre {} y pulsa «Verificar la elegida» (o «Verificar todas»).".format(texto)


def especificacion_de_teorema(v, n):
    """
    (página, preparar, objetivo, texto) para el teorema número n (1-30), o None.
    `v` es la ventana principal; las funciones se evalúan cuando ya se llegó a la página.
    """
    s, m = v.pagina_solucionador, v.pagina_matrices

    def op():
        """Lleva Operaciones a la pestaña de operaciones."""
        m.tabs.setCurrentIndex(0)

    def propiedades():
        """Lleva Operaciones a la pestaña de propiedades."""
        m.tabs.setCurrentIndex(1)

    def enviar():
        """Lleva Operaciones a la pestaña de envío al solucionador."""
        m.tabs.setCurrentIndex(2)

    def numerica(pestana):
        """Devuelve la función que lleva Métodos Numéricos a la pestaña indicada."""
        return lambda: v.pagina_numerica.tabs.setCurrentIndex(pestana)

    tab_solucion = ("solucionador", lambda: s.tabs.setCurrentIndex(1), lambda: s.tabs.tabBar(),
                    "Pulsa RESOLVER y abre esta pestaña, «Solución y verificación»: ahí aparece la clasificación del sistema.")
    tabla = {
        1: ("solucionador", None, lambda: s.sw_vectores,
            "Activa «Incluir análisis en Rⁿ» y pulsa RESOLVER: el informe trae la sección «Ecuación matricial A·x = b»."),
        2: ("matrices", enviar, lambda: m.botones_enviar["combinacion"],
            "Aquí: «¿Es b combinación lineal de las columnas de A?». Manda A y b al Solucionador."),
        3: ("solucionador", None, lambda: s.btn_resolver,
            "Pulsa RESOLVER y recorre la eliminación de Gauss y Gauss-Jordan, paso a paso."),
        4: tab_solucion,
        5: ("solucionador", None, lambda: s.sw_jordan,
            "Con «Incluir forma escalonada reducida (Gauss-Jordan)» activo verás la matriz reducida, que es única."),
        6: ("matrices", propiedades, lambda: m.combo_prop, _prop("el producto matriz-vector")),
        7: ("matrices", propiedades, lambda: m.combo_prop, _prop("los vectores en Rⁿ")),
        8: ("matrices", propiedades, lambda: m.combo_prop, _prop("la suma y el escalar de matrices")),
        9: ("matrices", propiedades, lambda: m.combo_prop, _prop("la transpuesta")),
        10: ("matrices", propiedades, lambda: m.combo_prop, _prop("el producto de matrices")),
        11: ("matrices", enviar, lambda: m.botones_enviar["independencia"],
             "Aquí: «¿Son las columnas de A linealmente independientes?». Manda A al Solucionador."),
        12: ("matrices", enviar, lambda: m.botones_enviar["independencia"],
             "Este botón abre el análisis de independencia, con los criterios por inspección."),
        13: ("matrices", enviar, lambda: m.botones_enviar["independencia"],
             "Prueba con b = 0 (sistema homogéneo) usando este botón."),
        14: ("matrices", propiedades, lambda: m.combo_prop, _prop("la inversa")),
        15: tab_solucion,
        16: ("matrices", op, lambda: m.botones_op["inversa_gj"], "Pulsa «A⁻¹ Gauss-Jordan» con una A cuadrada."),
        17: ("matrices", op, lambda: m.botones_op["inversa_adj"], "Pulsa «A⁻¹ Adjunta» con una A cuadrada."),
        18: ("matrices", op, lambda: m.botones_op["det"],
             "Pulsa «det(A)» con una matriz triangular: su determinante es el producto de la diagonal."),
        19: ("matrices", op, lambda: m.combo_det,
             "Elige «Triangular (eliminación)» aquí y pulsa «det(A)»: la reducción aplica estas operaciones de fila."),
        20: ("matrices", propiedades, lambda: m.combo_prop, _prop("el determinante")),
        21: ("lu", None, lambda: v.pagina_lu.btn_lu, "Pulsa «Factorizar»; con b como vector también resuelve A·x = b."),
        22: ("numerico", numerica(0), lambda: v.pagina_numerica.btn_calc_a,
             "Prueba un intervalo sin cambio de signo, o 1/x en [−1, 1]: el programa explica por qué la bisección no se puede aplicar."),
        23: ("numerico", numerica(0), lambda: v.pagina_numerica.btn_calc_a,
             "Pulsa «Calcular bisección»: la tabla muestra xₗ, xᵤ, xᵣ, εₐ y f(xᵣ) en cada iteración."),
        24: ("numerico", numerica(0), lambda: v.pagina_numerica.btn_calc_a,
             "Tras calcular, el resultado muestra la cota del error Eᵦ de la raíz."),
        25: ("numerico", numerica(0), lambda: v.pagina_numerica.e_a,
             "Cambia la tolerancia E: el informe da el número teórico de iteraciones ⌈log₂((b − a)/E)⌉."),
        26: ("numerico", numerica(3), lambda: v.pagina_numerica.btn_errores,
             "Escribe el valor verdadero xᵥ y el aproximado xₐ, y pulsa «Calcular errores»."),
        27: ("numerico", numerica(3), lambda: v.pagina_numerica.btn_propagacion,
             "Pulsa «Calcular propagación»: compara Δy aproximado con Δy real."),
        28: ("numerico", numerica(2), lambda: v.pagina_numerica.btn_desc,
             "Escribe un número en base 10 o 2 y pulsa «Descomponer»: verás cada dígito por su potencia de la base."),
        29: ("numerico", numerica(3), lambda: v.pagina_numerica.btn_flotante,
             "Aquí ves por qué 0.1 + 0.2 != 0.3, el épsilon de máquina, el overflow y el underflow."),
        30: ("numerico", numerica(3), lambda: v.pagina_numerica.btn_tipos,
             "Este botón muestra cada tipo de error con un ejemplo."),
    }
    return tabla.get(n)
