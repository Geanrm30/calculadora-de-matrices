# -*- coding: utf-8 -*-
"""
Componentes reutilizables con animaciones: botón, interruptor, tarjeta,
cuadrícula de matriz, pila de páginas con transición y avisos flotantes.
MTM0120 Álgebra Lineal — Universidad Americana.
"""
import re
from html.parser import HTMLParser

from PySide6.QtCore import (Qt, QEasingCurve, QEvent, QParallelAnimationGroup,
                            QPoint, QPointF, QPropertyAnimation, QRectF, QSize,
                            QTimer, QVariantAnimation, Signal)
from PySide6.QtGui import (QColor, QFont, QKeySequence, QLinearGradient,
                           QPainter, QPainterPath, QPen)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
                               QGraphicsOpacityEffect, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QMessageBox, QPushButton,
                               QScrollArea, QStackedWidget, QTabWidget,
                               QVBoxLayout, QWidget)

from core.fraccion import desde_texto, normalizar_texto_numerico
from qt import tema as T

MENSAJE_INVALIDO = ("Valor no válido. Usa un entero (-7), una fracción (3/4), "
                    "un decimal (2.5) o una raíz (√4).")


def mezclar(c0, c1, t):
    """Interpolación lineal entre dos QColor."""
    a, b = QColor(c0), QColor(c1)
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t))


class _Cortina(QWidget):
    """Capa lisa que cubre un widget y se vuelve transparente (fundido de entrada)."""

    def __init__(self, widget, color):
        super().__init__(widget)
        self._color = QColor(color)
        self._alfa = 255
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(widget.rect())

    def poner_alfa(self, alfa):
        self._alfa = alfa
        self.update()

    def paintEvent(self, _):
        c = QColor(self._color)
        c.setAlpha(self._alfa)
        p = QPainter(self)
        p.fillRect(self.rect(), c)


def aparecer(widget, duracion=260, retraso=0, color=None):
    """
    Hace aparecer un widget con un fundido. Encima se coloca una cortina del
    color del fondo (`color`, por defecto el del tema) que se desvanece.

    No se usa QGraphicsOpacityEffect porque falla con las QScrollArea (las
    cuadrículas de matriz, los cuadros de texto): su interior se pinta aparte
    y durante la animación mostraba restos de la pantalla anterior.
    """
    previa = getattr(widget, "_cortina_aparecer", None)
    if previa is not None:
        try:
            previa.hide()
            previa.deleteLater()
        except RuntimeError:
            pass

    cortina = _Cortina(widget, color or T.FONDO)
    cortina.show()
    cortina.raise_()
    widget._cortina_aparecer = cortina

    anim = QVariantAnimation(widget)
    anim.setDuration(duracion)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def paso(v):
        try:
            cortina.setGeometry(widget.rect())       # por si cambió de tamaño
            cortina.poner_alfa(int(255 * v))
        except RuntimeError:
            pass                                     # el widget ya se destruyó

    def fin():
        try:
            cortina.hide()
            cortina.deleteLater()
        except RuntimeError:
            pass

    def iniciar():
        try:
            anim.start()
        except RuntimeError:
            pass                                     # la ventana se cerró antes

    anim.valueChanged.connect(paso)
    anim.finished.connect(fin)
    QTimer.singleShot(retraso, iniciar)
    widget._anim_aparecer = anim                     # evita que se recolecte
    return anim


def desvanecer(widget, duracion=260, color=None):
    """Lo contrario de `aparecer`: una cortina lisa lo va tapando. Devuelve la cortina."""
    previa = getattr(widget, "_cortina_aparecer", None)
    if previa is not None:
        try:
            previa.hide()
            previa.deleteLater()
        except RuntimeError:
            pass
    cortina = _Cortina(widget, color or T.FONDO)
    cortina.poner_alfa(0)
    cortina.show()
    cortina.raise_()
    widget._cortina_aparecer = cortina

    anim = QVariantAnimation(widget)
    anim.setDuration(duracion)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.InCubic)

    def paso(v):
        try:
            cortina.setGeometry(widget.rect())
            cortina.poner_alfa(int(255 * v))
        except RuntimeError:
            pass

    anim.valueChanged.connect(paso)
    anim.start()
    widget._anim_desvanecer = anim
    return cortina


def mostrar_animado(widget, mostrar, duracion=360, color=None):
    """
    Muestra u oculta un widget con animación: crece o se encoge en altura mientras
    se funde, y los vecinos se acomodan suavemente.
    """
    maximo = 16777215
    previa = getattr(widget, "_anim_altura", None)
    if previa is not None:
        previa.stop()

    if mostrar:
        if widget.isVisible() and widget.maximumHeight() >= maximo:
            return
        inicio = widget.height() if widget.isVisible() else 0
        # Se prueba cómo quedará el diseño ya con el widget y se lee su altura final:
        # así la animación llega justo a donde el diseño lo va a dejar (sin salto).
        padre = widget.parentWidget()
        widget.setMaximumHeight(maximo)
        widget.show()
        if padre is not None and padre.layout() is not None:
            padre.layout().activate()
        fin = widget.height() if widget.height() > 60 else max(widget.sizeHint().height(), 60)
        widget.setMaximumHeight(inicio)
        aparecer(widget, duracion, color=color)
    else:
        if not widget.isVisible():
            return
        inicio, fin = widget.height(), 0
        cortina = desvanecer(widget, int(duracion * 0.9), color)

    anim = QVariantAnimation(widget)
    anim.setDuration(duracion)
    anim.setStartValue(inicio)
    anim.setEndValue(fin)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def paso(v):
        try:
            widget.setMaximumHeight(max(0, int(v)))
        except RuntimeError:
            pass

    def fin_anim():
        try:
            widget.setMaximumHeight(maximo)
            if not mostrar:
                widget.hide()
                c = getattr(widget, "_cortina_aparecer", None)
                if c is not None:
                    c.hide()
                    c.deleteLater()
        except RuntimeError:
            pass

    anim.valueChanged.connect(paso)
    anim.finished.connect(fin_anim)
    anim.start()
    widget._anim_altura = anim


def fundido_de_ventana(ventana, duracion=360):
    """Hace aparecer una ventana de primer nivel con un fundido (opacidad 0 → 1)."""
    anim = QVariantAnimation(ventana)
    anim.setDuration(duracion)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def paso(v):
        try:
            ventana.setWindowOpacity(v)
        except RuntimeError:
            pass

    anim.valueChanged.connect(paso)
    anim.start()
    ventana._anim_fundido = anim


def entrada_suave(widget, retraso=0, duracion=650):
    """
    Fundido de entrada de un widget con QGraphicsOpacityEffect. Sirve para
    etiquetas y botones (no para áreas con desplazamiento, ver `aparecer`).
    """
    previa = getattr(widget, "_anim_entrada", None)
    if previa is not None:
        previa.stop()
    efecto = QGraphicsOpacityEffect(widget)
    efecto.setOpacity(0.0)
    widget.setGraphicsEffect(efecto)

    anim = QVariantAnimation(widget)
    anim.setDuration(duracion)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def paso(v):
        try:
            efecto.setOpacity(v)
        except RuntimeError:
            pass                                     # el widget ya se destruyó

    def fin():
        try:
            widget.setGraphicsEffect(None)
        except RuntimeError:
            pass

    def iniciar():
        try:
            anim.start()
        except RuntimeError:
            pass

    anim.valueChanged.connect(paso)
    anim.finished.connect(fin)
    QTimer.singleShot(retraso, iniciar)
    widget._anim_entrada = anim


# ─────────────────────────────────────────────────────────────
# Botón animado
# ─────────────────────────────────────────────────────────────

class BotonAnimado(QPushButton):
    """Botón con color que se interpola al pasar el cursor."""

    @staticmethod
    def _estilo(nombre):
        """(color normal, color hover, color del texto) según el tema actual."""
        tb = T.TEXTO_BOTON
        return {
            "primario": (T.NARANJA, T.NAR_H,   tb),
            "azul":     (T.AZUL,    T.AZUL_H,  tb),
            "verde":    (T.VERDE,   T.VERDE_H, tb),
            "peligro":  (T.ROJO,    T.ROJO_H,  tb),
            "suave":    (T.SUPERF,  T.BORDE,   T.TEXTO),
            "fantasma": (T.PANEL,   T.SUPERF,  T.TEXTO),
        }[nombre]

    def __init__(self, texto, estilo="suave", pequeno=False, parent=None,
                 borde=False):
        super().__init__(texto, parent)
        self._borde = borde
        self._c0, self._c1, self._ct = self._estilo(estilo)
        self._t = 0.0
        self._pequeno = pequeno
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setMinimumHeight(30 if pequeno else 38)
        fuente = QFont(T.FUENTE, 9 if pequeno else 10)
        fuente.setWeight(QFont.DemiBold)
        self.setFont(fuente)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._paso)

        # Onda al pulsar (centro, avance 0→1) y destello periódico (-1 = apagado)
        self._onda = None
        self._brillo = -1.0
        self._ciclo = None
        self._anim_onda = QVariantAnimation(self)
        self._anim_onda.setDuration(520)
        self._anim_onda.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_onda.valueChanged.connect(self._paso_onda)
        self._anim_onda.finished.connect(self._fin_onda)
        self._anim_brillo = QVariantAnimation(self)
        self._anim_brillo.setDuration(950)
        self._anim_brillo.setStartValue(0.0)
        self._anim_brillo.setEndValue(1.0)
        self._anim_brillo.setEasingCurve(QEasingCurve.InOutSine)
        self._anim_brillo.valueChanged.connect(self._paso_brillo)
        self._anim_brillo.finished.connect(self._fin_brillo)

    def _paso(self, v):
        self._t = v
        self.update()

    def con_menu(self, opciones):
        """Al pulsar despliega un menú. opciones: [(texto, función) | None]."""
        self.setText(self.text() + "  ▾")

        def abrir():
            menu = QMenu(self)
            for op in opciones:
                if op is None:
                    menu.addSeparator()
                else:
                    menu.addAction(op[0], op[1])
            menu.exec(self.mapToGlobal(QPoint(0, self.height() + 4)))
        self.clicked.connect(abrir)
        return self

    def _ir(self, destino):
        self._anim.stop()
        self._anim.setStartValue(self._t)
        self._anim.setEndValue(destino)
        self._anim.start()

    def activar_brillo(self):
        """Un destello recorre el botón cada pocos segundos (para el botón principal)."""
        if self._ciclo is None:
            self._ciclo = QTimer(self)
            self._ciclo.setInterval(4200)
            self._ciclo.timeout.connect(self._lanzar_brillo)
            if self.isVisible():
                self._ciclo.start()

    def _lanzar_brillo(self):
        if self.isVisible() and self.isEnabled():
            self._anim_brillo.start()

    def _paso_brillo(self, v):
        self._brillo = v
        self.update()

    def _fin_brillo(self):
        self._brillo = -1.0
        self.update()

    def _paso_onda(self, v):
        if self._onda is not None:
            self._onda = (self._onda[0], v)
            self.update()

    def _fin_onda(self):
        self._onda = None
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.isEnabled():
            self._onda = (QPointF(e.position()), 0.0)
            self._anim_onda.stop()
            self._anim_onda.setStartValue(0.0)
            self._anim_onda.setEndValue(1.0)
            self._anim_onda.start()
        super().mousePressEvent(e)

    def showEvent(self, e):
        super().showEvent(e)
        if self._ciclo is not None:
            self._ciclo.start()

    def hideEvent(self, e):
        super().hideEvent(e)
        if self._ciclo is not None:
            self._ciclo.stop()

    def enterEvent(self, e):
        self._ir(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._ir(0.0)
        super().leaveEvent(e)

    def sizeHint(self):
        base = super().sizeHint()
        return QSize(base.width() + (8 if self._pequeno else 20),
                     self.minimumHeight())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        activo = self.isEnabled()

        if activo:
            fondo = mezclar(self._c0, self._c1, self._t)
            if self.isDown():
                fondo = fondo.darker(112)
            texto = QColor(self._ct)
        else:
            fondo = QColor(T.SUPERF)
            fondo.setAlpha(150)
            texto = QColor(T.MUTED)

        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.NoPen)
        p.setBrush(fondo)
        p.drawRoundedRect(r, 9, 9)
        if self._borde and activo:
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(mezclar(T.BORDE, T.MUTED, self._t), 1.2))
            p.drawRoundedRect(r, 9, 9)

        if self.hasFocus() and activo:
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(T.AZUL), 1.5))
            p.drawRoundedRect(r.adjusted(1.5, 1.5, -1.5, -1.5), 8, 8)

        if activo and (self._onda is not None or self._brillo >= 0):
            ruta = QPainterPath()
            ruta.addRoundedRect(r, 3, 3)
            p.save()
            p.setClipPath(ruta)
            if self._onda is not None:
                centro, avance = self._onda
                radio = avance * max(self.width(), self.height()) * 1.25
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, int(85 * (1.0 - avance))))
                p.drawEllipse(centro, radio, radio)
            if self._brillo >= 0:
                ancho = self.width()
                x = -0.45 * ancho + self._brillo * 1.9 * ancho
                banda = QLinearGradient(x, 0, x + 0.45 * ancho, 0)
                banda.setColorAt(0.0, QColor(255, 255, 255, 0))
                banda.setColorAt(0.5, QColor(255, 255, 255, 70))
                banda.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.fillRect(self.rect(), banda)
            p.restore()

        p.setPen(texto)
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self.text())


# ─────────────────────────────────────────────────────────────
# Interruptor
# ─────────────────────────────────────────────────────────────

class Interruptor(QCheckBox):
    """Casilla con aspecto de interruptor, con animación de la perilla."""

    def __init__(self, texto, marcado=False, parent=None):
        super().__init__(texto, parent)
        self.setChecked(marcado)
        self.setCursor(Qt.PointingHandCursor)
        self._t = 1.0 if marcado else 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(170)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._paso)
        self.toggled.connect(self._cambio)

    def _paso(self, v):
        self._t = v
        self.update()

    def _cambio(self, marcado):
        self._anim.stop()
        self._anim.setStartValue(self._t)
        self._anim.setEndValue(1.0 if marcado else 0.0)
        self._anim.start()

    def sizeHint(self):
        base = super().sizeHint()
        return QSize(base.width() + 50, max(base.height(), 26))

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        alto = 20
        ancho = 38
        y = (self.height() - alto) / 2
        pista = QRectF(1, y, ancho, alto)

        p.setPen(Qt.NoPen)
        p.setBrush(mezclar(T.BORDE, T.NARANJA, self._t))
        p.drawRoundedRect(pista, alto / 2, alto / 2)

        d = alto - 6
        x = 4 + (ancho - d - 6) * self._t
        p.setBrush(QColor(T.PANEL if self._t > 0.5 else T.TEXTO))
        p.drawEllipse(QRectF(x, y + 3, d, d))

        p.setPen(QColor(T.TEXTO))
        p.setFont(self.font())
        p.drawText(QRectF(ancho + 14, 0, self.width() - ancho - 14,
                          self.height()),
                   Qt.AlignVCenter | Qt.AlignLeft, self.text())


# ─────────────────────────────────────────────────────────────
# Tarjeta
# ─────────────────────────────────────────────────────────────

class _ConPulso:
    """Pieza común: el borde del marco se ilumina un instante (`pulso`)."""

    def _iniciar_pulso(self):
        self._pulso = 0.0
        self._color_pulso = QColor(T.AZUL)
        self._anim_pulso = QVariantAnimation(self)
        self._anim_pulso.setDuration(1100)
        self._anim_pulso.setKeyValueAt(0.0, 0.0)
        self._anim_pulso.setKeyValueAt(0.22, 1.0)
        self._anim_pulso.setKeyValueAt(1.0, 0.0)
        self._anim_pulso.valueChanged.connect(self._paso_pulso)

    def pulso(self, color=None):
        """Ilumina el borde un instante (aviso de que hay algo nuevo)."""
        self._color_pulso = QColor(color or T.AZUL)
        self._anim_pulso.stop()
        self._anim_pulso.start()

    def _paso_pulso(self, v):
        self._pulso = v
        self.update()

    def _pintar_pulso(self):
        if self._pulso <= 0.01:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(Qt.NoBrush)
        for grosor, alfa in ((5.0, 40), (2.0, 200)):
            c = QColor(self._color_pulso)
            c.setAlpha(int(alfa * self._pulso))
            p.setPen(QPen(c, grosor))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 12, 12)


class Barra(_ConPulso, QFrame):
    """Franja con borde redondeado (estilo «barra») que puede iluminar su borde."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barra")
        self._iniciar_pulso()

    def paintEvent(self, e):
        super().paintEvent(e)
        self._pintar_pulso()


class Tarjeta(_ConPulso, QFrame):
    """Contenedor redondeado con título pequeño en mayúsculas."""

    def __init__(self, titulo="", color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.cuerpo = QVBoxLayout(self)
        self.cuerpo.setContentsMargins(16, 14, 16, 16)
        self.cuerpo.setSpacing(10)

        # Fila superior: título a la izquierda y acciones a la derecha.
        self.cabecera = QHBoxLayout()
        self.cabecera.setSpacing(4)
        self.lbl_titulo = QLabel(titulo.upper())
        self.lbl_titulo.setObjectName("tarjetaTitulo")
        if color:
            self.lbl_titulo.setStyleSheet(
                "color: {}; background: transparent;".format(color))
        self.cabecera.addWidget(self.lbl_titulo)
        self.cuerpo.addLayout(self.cabecera)
        # Se muestra DESPUÉS de meterla en la tarjeta: antes de eso es un widget sin
        # padre y mostrarlo abre, por un instante, una ventana suelta.
        self.lbl_titulo.setVisible(bool(titulo))
        self._iniciar_pulso()

    def paintEvent(self, e):
        super().paintEvent(e)
        self._pintar_pulso()

    def poner_titulo(self, texto):
        self.lbl_titulo.setText(texto.upper())
        self.lbl_titulo.setVisible(bool(texto))

    def agregar(self, widget, *args, **kw):
        self.cuerpo.addWidget(widget, *args, **kw)
        return widget

    def agregar_layout(self, layout):
        self.cuerpo.addLayout(layout)
        return layout


# ─────────────────────────────────────────────────────────────
# Cuadrícula de matriz
# ─────────────────────────────────────────────────────────────

def parsear_tabla(texto):
    """
    Convierte texto pegado (Excel, "1 2; 3 4", "[[1,2],[3,4]]"…) en una lista
    de filas de texto. Devuelve None si es un solo valor (pegado normal).
    """
    t = (texto or "").strip()
    if not t:
        return None
    if re.fullmatch(r"-?\d+,\d+", t):          # decimal con coma: 2,5
        return None
    if "■(" in t:
        return _tabla_de_ecuacion_lineal(t)

    if "\n" in t or "\t" in t:
        lineas = [l for l in t.splitlines() if l.strip()]
    else:
        lineas = re.split(r"\]\s*,?\s*\[|;", t)

    filas = []
    for l in lineas:
        l = l.strip().strip("[]() ").strip()
        if not l:
            continue
        if "\t" in l:
            toks = [x.strip() for x in l.split("\t")]
        elif re.search(r"\s", l):
            toks = [x.rstrip(",;") for x in re.split(r"\s+", l)]
        else:
            toks = [x.strip() for x in l.split(",")]
        toks = [x.strip("[]() ") for x in toks]
        filas.append(toks)

    if not filas or (len(filas) == 1 and len(filas[0]) <= 1):
        return None
    ancho = max(len(f) for f in filas)
    return [f + ["0"] * (ancho - len(f)) for f in filas]


def _tabla_de_ecuacion_lineal(texto):
    """
    Tabla de una matriz de ecuación de Office copiada como texto: ■(3&−7&−2@−3&5&1).
    Las columnas se separan con «&» y las filas con «@».
    """
    interior = texto[texto.index("■(") + 2:]
    profundidad, fin = 1, len(interior)
    for k, caracter in enumerate(interior):
        profundidad += (caracter == "(") - (caracter == ")")
        if profundidad == 0:
            fin = k
            break
    filas = [[celda.strip() for celda in fila.split("&")]
             for fila in interior[:fin].split("@") if fila.strip()]
    if not filas or (len(filas) == 1 and len(filas[0]) <= 1):
        return None
    ancho = max(len(f) for f in filas)
    return [f + ["0"] * (ancho - len(f)) for f in filas]


class _CeldasHTML(HTMLParser):
    """Recoge las filas y celdas de la primera tabla de un HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.filas, self._fila, self._celda = [], None, None
        self._tablas = 0

    def handle_starttag(self, etiqueta, atributos):
        if etiqueta == "table":
            self._tablas += 1
        elif self._tablas == 1 and etiqueta == "tr":
            self._fila = []
        elif self._tablas == 1 and etiqueta in ("td", "th") and self._fila is not None:
            self._celda = []

    def handle_data(self, datos):
        if self._celda is not None:
            self._celda.append(datos)

    def handle_endtag(self, etiqueta):
        if etiqueta == "table":
            self._tablas -= 1
        elif self._tablas == 1 and etiqueta in ("td", "th") and self._celda is not None:
            self._fila.append(" ".join("".join(self._celda).split()))
            self._celda = None
        elif self._tablas == 1 and etiqueta == "tr" and self._fila is not None:
            self.filas.append(self._fila)
            self._fila = None


def tabla_desde_html(html):
    """
    Filas de texto de la primera tabla de un HTML (lo que PowerPoint, Word y las
    páginas web dejan en el portapapeles). None si no hay una tabla de varias celdas.
    """
    lector = _CeldasHTML()
    lector.feed(html or "")
    filas = [f for f in lector.filas if any(celda for celda in f)]
    if not filas or (len(filas) == 1 and len(filas[0]) <= 1):
        return None
    ancho = max(len(f) for f in filas)
    return [f + ["0"] * (ancho - len(f)) for f in filas]


def tabla_del_portapapeles():
    """
    Tabla que hay en el portapapeles: primero como texto (Excel, Word, texto) y, si
    no hay texto, como tabla HTML (PowerPoint copia así una tabla seleccionada).
    """
    datos = QApplication.clipboard().mimeData()
    if datos is None:
        return None
    filas = parsear_tabla(datos.text()) if datos.hasText() else None
    if filas is None and datos.hasHtml():
        filas = tabla_desde_html(datos.html())
    return filas


class Celda(QLineEdit):
    """Casilla numérica; Enter/↓/↑ mueven el foco, Ctrl+Z/Y deshacen la matriz."""

    mover = Signal(int, int)
    pegar = Signal(object)
    deshacer = Signal()
    rehacer = Signal()

    def __init__(self, texto="0", parent=None):
        super().__init__(texto, parent)
        self.setObjectName("celda")
        self.setProperty("escala", str(T.ESCALA))
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(round(66 * T.ESCALA), round(36 * T.ESCALA))
        self.setProperty("error", False)
        self._destello = 0.0
        self._anim_destello = QVariantAnimation(self)
        self._anim_destello.setDuration(700)
        self._anim_destello.setStartValue(1.0)
        self._anim_destello.setEndValue(0.0)
        self._anim_destello.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_destello.valueChanged.connect(self._paso_destello)
        self._intensidad = 1.0
        self._color_destello = QColor(T.NARANJA)
        self._foco = 0.0
        self._texto_al_entrar = texto
        self._anim_foco = QVariantAnimation(self)
        self._anim_foco.setDuration(200)
        self._anim_foco.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_foco.valueChanged.connect(self._paso_foco)
        self.editingFinished.connect(self._confirmado)

        # Validación en vivo: se revisa cuando dejas de teclear.
        self._revision = QTimer(self)
        self._revision.setSingleShot(True)
        self._revision.setInterval(500)
        self._revision.timeout.connect(self.validar)
        self.textChanged.connect(lambda _: self._revision.start())
        self.validar()

    def destellar(self, retraso=0, intensidad=1.0, color=None):
        """Un resplandor de color cruza la celda (se usa en la ola de la cuadrícula)."""
        def iniciar():
            try:
                self._intensidad = intensidad
                self._color_destello = QColor(color or T.NARANJA)
                self._anim_destello.start()
            except RuntimeError:
                pass                                 # la celda ya no existe
        QTimer.singleShot(retraso, iniciar)

    def _paso_destello(self, v):
        self._destello = v
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._destello <= 0.01 and self._foco <= 0.01:
            return
        p = QPainter(self)                           # un solo pintor para ambos efectos
        p.setRenderHint(QPainter.Antialiasing)
        if self._destello > 0.01:
            color = QColor(self._color_destello)
            color.setAlpha(int(110 * self._destello * self._intensidad))
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 3, 3)
        if self._foco > 0.01:
            anillo = QColor(T.NARANJA)
            anillo.setAlpha(int(150 * self._foco))
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(anillo, 2.2))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5), 3, 3)
            suave = QColor(T.NARANJA)
            suave.setAlpha(int(45 * self._foco))
            p.setPen(QPen(suave, 2.2))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0.4, 0.4, -0.4, -0.4), 3.5, 3.5)

    def _paso_foco(self, v):
        self._foco = v
        self.update()

    def _confirmado(self):
        """Si el valor cambió al salir de la celda, un destello suave lo confirma."""
        if self.text() != self._texto_al_entrar:
            self._texto_al_entrar = self.text()
            self.destellar(0, 0.5)

    def es_valida(self):
        try:
            desde_texto(self.text())
            return True
        except (ValueError, ZeroDivisionError):
            return False

    def marcar(self, invalida):
        """Pinta la celda en rojo (o la deja normal) y explica el motivo."""
        if bool(self.property("error")) == invalida:
            return
        self.setProperty("error", invalida)
        self.setToolTip(MENSAJE_INVALIDO if invalida else "")
        self.style().unpolish(self)
        self.style().polish(self)

    def validar(self):
        self.marcar(not self.es_valida())
        return not self.property("error")

    @staticmethod
    def _es_rehacer(e):
        return (e.matches(QKeySequence.Redo)
                or (e.key() == Qt.Key_Z
                    and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)))

    def event(self, e):
        # Sin esto, QLineEdit se queda con Ctrl+Z para deshacer solo su texto.
        if e.type() == QEvent.ShortcutOverride:
            if e.matches(QKeySequence.Undo) or self._es_rehacer(e):
                e.accept()
                return True
        return super().event(e)

    def keyPressEvent(self, e):
        if e.matches(QKeySequence.Undo):
            self.deshacer.emit()
            return
        if self._es_rehacer(e):
            self.rehacer.emit()
            return
        if e.matches(QKeySequence.Paste):
            filas = tabla_del_portapapeles()
            if filas is not None:
                self.pegar.emit(filas)
                return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down):
            if e.modifiers() & Qt.ControlModifier:
                e.ignore()            # Ctrl+Enter lo atiende la página
                return
            self.mover.emit(1, 0)
        elif e.key() == Qt.Key_Up:
            self.mover.emit(-1, 0)
        else:
            super().keyPressEvent(e)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._texto_al_entrar = self.text()
        self._anim_foco.stop()
        self._anim_foco.setStartValue(self._foco)
        self._anim_foco.setEndValue(1.0)
        self._anim_foco.start()
        QTimer.singleShot(0, self.selectAll)

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self._anim_foco.stop()
        self._anim_foco.setStartValue(self._foco)
        self._anim_foco.setEndValue(0.0)
        self._anim_foco.start()


class _Lienzo(QWidget):
    """Contenedor de celdas que dibuja los corchetes de la matriz."""

    def __init__(self, corchetes, parent=None):
        super().__init__(parent)
        self._corchetes = corchetes

    def paintEvent(self, _):
        if not self._corchetes:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(T.MUTED), 2.2, Qt.SolidLine, Qt.RoundCap))
        w, h, g = self.width(), self.height(), 7
        p.drawPolyline([QPoint(g + 5, 2), QPoint(g, 2), QPoint(g, h - 2),
                        QPoint(g + 5, h - 2)])
        p.drawPolyline([QPoint(w - g - 5, 2), QPoint(w - g, 2),
                        QPoint(w - g, h - 2), QPoint(w - g - 5, h - 2)])


class CuadriculaMatriz(QScrollArea):
    """
    Cuadrícula editable de filas × columnas. Con aumentada=True, la última
    columna es el vector b y se dibuja una barra separadora.

    Guarda un historial de estados (deshacer / rehacer) y sabe copiar y pegar
    tablas desde Excel o texto.
    """

    cambiado = Signal()
    # Se emite cuando deshacer/rehacer/pegar cambian el tamaño: (filas, columnas)
    forma_cambiada = Signal(int, int)
    # (puede_deshacer, puede_rehacer)
    historial_cambiado = Signal(bool, bool)

    MAX_HISTORIAL = 100

    def __init__(self, corchetes=True, aumentada=False, max_filas=20,
                 max_cols=20, parent=None):
        super().__init__(parent)
        self._aumentada = aumentada
        self._corchetes = corchetes
        self.max_filas = max_filas
        self.max_cols = max_cols + (1 if aumentada else 0)
        self.celdas = []
        self.setWidgetResizable(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.viewport().setAutoFillBackground(False)
        self._lienzo = None
        self.setMinimumHeight(70)

        self._hist = []
        self._pos = -1
        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.setInterval(450)
        self._temporizador.timeout.connect(self._registrar)

    def filas(self):
        return len(self.celdas)

    def columnas(self):
        return len(self.celdas[0]) if self.celdas else 0

    def textos(self):
        return [[c.text() for c in fila] for fila in self.celdas]

    # ── Construcción ──────────────────────────────────────────

    def reconstruir(self, filas, columnas, anteriores=None, registrar=True,
                    animar=None):
        """
        Dibuja de nuevo conservando lo que ya estaba escrito. La ola de luz se
        lanza solo si cambió el tamaño o el contenido (`animar` la fuerza o la
        evita: p. ej. al cambiar el tamaño de letra no debe haber ola).
        """
        previas = getattr(self, "celdas", None)
        antes = (len(previas), len(previas[0]), self.textos()) if previas else None
        if anteriores is None:
            anteriores = self.textos()

        lienzo = _Lienzo(self._corchetes)
        grid = QGridLayout(lienzo)
        m = 16 if self._corchetes else 4
        grid.setContentsMargins(m + 4, 6, m + 4, 6)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)

        n_vars = columnas - 1 if self._aumentada else columnas

        if self._aumentada:
            for j in range(n_vars):
                grid.addWidget(self._cabecera("x" + _sub(j + 1)), 0, j,
                               Qt.AlignCenter)
            barra = QLabel("│")
            barra.setStyleSheet("color: {}; background: transparent;".format(T.BORDE))
            grid.addWidget(barra, 0, n_vars, Qt.AlignCenter)
            grid.addWidget(self._cabecera("b"), 0, n_vars + 1, Qt.AlignCenter)

        fila0 = 1 if self._aumentada else 0
        celdas = []
        for i in range(filas):
            fila = []
            for j in range(columnas):
                col = j if (not self._aumentada or j < n_vars) else j + 1
                c = Celda(self._valor(anteriores, i, j))
                c.mover.connect(lambda dr, dc, a=i, b=j: self._mover(a, b, dr, dc))
                c.pegar.connect(lambda filas, a=i, b=j: self.pegar_filas(filas, a, b))
                c.deshacer.connect(self.deshacer)
                c.rehacer.connect(self.rehacer)
                c.textChanged.connect(self._al_editar)
                grid.addWidget(c, fila0 + i, col)
                fila.append(c)
            if self._aumentada:
                barra = QLabel("│")
                barra.setStyleSheet(
                    "color: {}; background: transparent;".format(T.BORDE))
                grid.addWidget(barra, fila0 + i, n_vars, Qt.AlignCenter)
            celdas.append(fila)

        self.celdas = celdas
        self._lienzo = lienzo
        self.setWidget(lienzo)
        lienzo.adjustSize()
        alto = lienzo.sizeHint().height()
        self.setMinimumHeight(min(alto + 4, 260))

        if registrar:
            self._registrar()
        if animar is None:
            animar = (antes is not None and
                      (antes[0] != filas or antes[1] != columnas
                       or antes[2] != self.textos()))
        if animar:
            self.ola()

    def ola(self, color=None):
        """Una ola de luz recorre las celdas en diagonal (no en cuadrículas enormes)."""
        if not getattr(self, "celdas", None) or self.filas() * self.columnas() > 80:
            return
        for i, fila in enumerate(self.celdas):
            for j, celda in enumerate(fila):
                celda.destellar(60 + 55 * (i + j), 1.0, color)

    @staticmethod
    def _valor(anteriores, i, j):
        if anteriores and i < len(anteriores) and j < len(anteriores[i]):
            return anteriores[i][j]
        return "0"

    @staticmethod
    def _cabecera(texto):
        l = QLabel(texto)
        l.setAlignment(Qt.AlignCenter)
        l.setStyleSheet("color: {}; background: transparent; font-weight: 700;"
                        .format(T.AZUL))
        return l

    def _al_editar(self, _):
        self._temporizador.start()          # se registra al dejar de teclear
        self.cambiado.emit()

    def _mover(self, i, j, dr, dc):
        i2, j2 = i + dr, j + dc
        if 0 <= i2 < len(self.celdas) and 0 <= j2 < len(self.celdas[0]):
            self.celdas[i2][j2].setFocus()
        elif dr == 1 and i2 >= len(self.celdas):
            # Enter en la última fila: pasa a la primera de la columna siguiente.
            if j + 1 < len(self.celdas[0]):
                self.celdas[0][j + 1].setFocus()

    def poner_textos(self, textos):
        self.reconstruir(len(textos), len(textos[0]), textos)

    def limpiar(self):
        habia_datos = any(c.text() != "0" for fila in self.celdas for c in fila)
        for fila in self.celdas:
            for c in fila:
                c.setText("0")
        self._registrar()
        if habia_datos:
            self.ola(T.AZUL)                 # barrido azul: todo vuelve a cero

    # ── Historial ─────────────────────────────────────────────

    def _avisar_historial(self):
        self.historial_cambiado.emit(self._pos > 0,
                                     self._pos < len(self._hist) - 1)

    def _registrar(self):
        """Guarda el estado actual como un punto del historial."""
        self._temporizador.stop()
        if not self.celdas:
            return
        snap = self.textos()
        if 0 <= self._pos < len(self._hist) and self._hist[self._pos] == snap:
            return
        del self._hist[self._pos + 1:]
        self._hist.append(snap)
        if len(self._hist) > self.MAX_HISTORIAL:
            del self._hist[0]
        self._pos = len(self._hist) - 1
        self._avisar_historial()

    def _ir_a_historial(self, pos):
        snap = self._hist[pos]
        self._pos = pos
        self.reconstruir(len(snap), len(snap[0]), snap, registrar=False)
        self._avisar_historial()
        self.forma_cambiada.emit(len(snap), len(snap[0]))

    def deshacer(self):
        self._registrar()                   # lo escrito y aún no registrado
        if self._pos > 0:
            self._ir_a_historial(self._pos - 1)

    def rehacer(self):
        self._temporizador.stop()
        if self._pos < len(self._hist) - 1:
            self._ir_a_historial(self._pos + 1)

    # ── Copiar y pegar ────────────────────────────────────────

    def copiar(self):
        """Copia la matriz como tabla con tabuladores (se pega bien en Excel)."""
        QApplication.clipboard().setText(
            "\n".join("\t".join(f) for f in self.textos()))

    def copiar_imagen(self):
        """Copia la matriz como imagen limpia (fondo blanco) para Word o PowerPoint."""
        from qt.imagen import imagen_de_matriz
        QApplication.clipboard().setImage(
            imagen_de_matriz(self.textos(), self._aumentada))
        mostrar_aviso(self, "Matriz copiada como imagen")

    def pegar(self):
        """Pega la tabla del portapapeles desde la primera celda. False si no hay tabla."""
        filas = tabla_del_portapapeles()
        if filas is None:
            return False
        return self.pegar_filas(filas, 0, 0)

    def pegar_con_aviso(self):
        """Como pegar(), pero explica qué pasó si no había una tabla."""
        if self.pegar():
            return
        datos = QApplication.clipboard().mimeData()
        if datos is not None and datos.hasImage():
            motivo = ("El portapapeles solo tiene una imagen. Copia la tabla de "
                      "PowerPoint (seleccionándola) o las celdas de Excel, no una captura.")
        else:
            motivo = "No hay una tabla en el portapapeles."
        mostrar_aviso(self, motivo, "info")

    def pegar_texto(self, texto, i0=0, j0=0):
        filas = parsear_tabla(texto)
        if filas is None:
            return False
        return self.pegar_filas(filas, i0, j0)

    def pegar_filas(self, filas, i0=0, j0=0):
        """Escribe las filas desde la celda (i0, j0); la cuadrícula crece si hace falta."""
        actual = self.textos()
        n_f = min(max(len(actual), i0 + len(filas)), self.max_filas)
        n_c = min(max(self.columnas(), j0 + len(filas[0])), self.max_cols)
        base = [[self._valor(actual, i, j) for j in range(n_c)]
                for i in range(n_f)]
        for di, fila in enumerate(filas):
            for dj, valor in enumerate(fila):
                if i0 + di < n_f and j0 + dj < n_c:
                    # Excel/Word traen «−» y celdas vacías: se dejan como 0 y «-»
                    base[i0 + di][j0 + dj] = normalizar_texto_numerico(valor) or "0"
        self.reconstruir(n_f, n_c, base)
        self.forma_cambiada.emit(n_f, n_c)
        return True

    def marcar_error(self, i, j):
        """Deja la celda en rojo hasta que se corrija y le da el foco."""
        c = self.celdas[i][j]
        c._revision.stop()
        c.marcar(True)
        c.setFocus()

    def hay_invalidas(self):
        return any(not c.es_valida() for fila in self.celdas for c in fila)


def agregar_acciones_grid(tarjeta, grid):
    """Pone en el encabezado de la tarjeta: ↶ ↷ y un menú Tabla (copiar/pegar)."""
    tarjeta.cabecera.addStretch(1)

    def icono(texto, tip, cmd):
        b = BotonAnimado(texto, "fantasma", pequeno=True)
        b.setFixedSize(30, 28)
        b.setToolTip(tip)
        b.clicked.connect(cmd)
        tarjeta.cabecera.addWidget(b)
        return b

    b_des = icono("↶", "Deshacer (Ctrl+Z)", grid.deshacer)
    b_reh = icono("↷", "Rehacer (Ctrl+Y)", grid.rehacer)

    b_tabla = BotonAnimado("Tabla", "fantasma", pequeno=True)
    b_tabla.setMinimumHeight(28)
    b_tabla.setFixedWidth(78)
    b_tabla.setToolTip("Copiar como tabla o imagen, o pegar desde Excel o PowerPoint")
    b_tabla.con_menu([("Copiar como tabla (Excel)", grid.copiar),
                      ("Copiar como imagen", grid.copiar_imagen),
                      None,
                      ("Pegar tabla (Excel, PowerPoint o texto)", grid.pegar_con_aviso)])
    tarjeta.cabecera.addWidget(b_tabla)
    tarjeta.btn_tabla = b_tabla

    def actualizar(puede_des, puede_reh):
        b_des.setEnabled(puede_des)
        b_reh.setEnabled(puede_reh)

    grid.historial_cambiado.connect(actualizar)
    actualizar(False, False)


def _sub(n):
    tabla = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return str(n).translate(tabla)


# ─────────────────────────────────────────────────────────────
# Pila de páginas con transición
# ─────────────────────────────────────────────────────────────

class _Instantanea(QWidget):
    """
    Capa de transición entre páginas. Primera mitad: la foto de la página que
    se va se apaga hacia el color de fondo. Segunda mitad: el fondo se aclara y
    deja ver la página nueva. Las dos páginas nunca se ven mezcladas (al
    mezclar dos páginas con mucho texto se superponen y parece un defecto).
    """

    def __init__(self, padre, foto, color, direccion=1, eje="v"):
        super().__init__(padre)
        self._foto = foto
        self._color = QColor(color)
        self._direccion = direccion            # +1: la nueva entra desde abajo / la derecha
        self._eje = eje                        # "v" vertical, "h" horizontal
        self._progreso = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(padre.rect())

    def poner_progreso(self, valor):
        self._progreso = valor
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        t = self._progreso
        vertical = self._eje == "v"
        largo = self.height() if vertical else self.width()
        if t < 0.5:
            # La foto de la página que se va se desliza y se apaga
            u = 2.0 * t
            salida = u * u * (3 - 2 * u)
            desp = int(-self._direccion * 60 * salida)
            p.fillRect(self.rect(), self._color)
            p.setOpacity(1.0 - u)
            p.drawPixmap(0 if vertical else desp, desp if vertical else 0, self._foto)
        else:
            # El telón se retira con un borde difuminado y deja ver la página nueva
            u = 2.0 * t - 1.0
            avance = 1.0 - (1.0 - u) ** 3
            blando = 130.0
            transparente = QColor(self._color)
            transparente.setAlpha(0)
            if self._direccion >= 0:
                borde = largo * (1.0 - avance) + blando * (1.0 - avance)
                ini, fin = borde - blando, borde
            else:
                borde = largo * avance - blando * (1.0 - avance)
                ini, fin = borde + blando, borde
            g = QLinearGradient(0, ini, 0, fin) if vertical else QLinearGradient(ini, 0, fin, 0)
            g.setColorAt(0.0, self._color)
            g.setColorAt(1.0, transparente)
            p.fillRect(self.rect(), g)


class PestanasAnimadas(QTabWidget):
    """QTabWidget que desliza el contenido (en horizontal) al cambiar de pestaña."""

    DURACION = 340

    def __init__(self, color_fondo=None, parent=None):
        super().__init__(parent)
        self._color = color_fondo
        self._foto = None
        self._previo = 0
        self._capa = None
        self._anim = None
        self.tabBar().tabBarClicked.connect(self._antes)
        self.currentChanged.connect(self._despues)

    def _antes(self, indice):
        """Se llama al pulsar una pestaña, antes de que cambie el contenido."""
        if indice != self.currentIndex() and self.currentWidget() is not None:
            self._foto = self.currentWidget().grab()
            self._previo = self.currentIndex()

    def _terminar(self):
        if self._anim is not None:
            self._anim.stop()
            self._anim = None
        if self._capa is not None:
            try:
                self._capa.hide()
                self._capa.deleteLater()
            except RuntimeError:
                pass
            self._capa = None

    def _despues(self, indice):
        foto, self._foto = self._foto, None
        if foto is None:
            return
        pila = self.findChild(QStackedWidget, options=Qt.FindDirectChildrenOnly)
        if pila is None:
            return
        self._terminar()
        capa = _Instantanea(pila, foto, self._color or T.FONDO,
                            1 if indice > self._previo else -1, "h")
        capa.show()
        capa.raise_()
        anim = QVariantAnimation(self)
        anim.setDuration(self.DURACION)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(capa.poner_progreso)
        anim.finished.connect(self._terminar)
        self._capa, self._anim = capa, anim
        anim.start()


class PilaAnimada(QStackedWidget):
    """
    QStackedWidget que al cambiar de página apaga la anterior y enciende la
    nueva (fundido a través del fondo, en unos 230 ms).

    Se saca una foto de la página que se va; la nueva se dibuja normal por
    debajo. Así no se aplica ningún efecto gráfico a las páginas
    (QGraphicsOpacityEffect dejaba las cuadrículas en blanco y mostraba restos
    de la página anterior).
    """

    DURACION = 460

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capa = None
        self._anim = None

    def _terminar_transicion(self):
        if self._anim is not None:
            self._anim.stop()
            self._anim = None
        if self._capa is not None:
            try:
                self._capa.hide()
                self._capa.deleteLater()
            except RuntimeError:
                pass
            self._capa = None

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._capa is not None:
            self._capa.setGeometry(self.rect())

    def ir(self, indice):
        if indice == self.currentIndex():
            return
        self._terminar_transicion()
        direccion = 1 if indice > self.currentIndex() else -1
        foto = self.grab()                     # cómo se ve ahora la página que se va
        self.setCurrentIndex(indice)

        capa = _Instantanea(self, foto, T.FONDO, direccion)
        capa.show()
        capa.raise_()
        anim = QVariantAnimation(self)
        anim.setDuration(self.DURACION)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Linear)
        anim.valueChanged.connect(capa.poner_progreso)
        anim.finished.connect(self._terminar_transicion)
        self._capa, self._anim = capa, anim
        anim.start()


# ─────────────────────────────────────────────────────────────
# Diálogos con entrada y salida animadas
# ─────────────────────────────────────────────────────────────

class _AparicionDeDialogo:
    """
    Pieza común: el diálogo entra con un fundido y un pequeño deslizamiento hacia
    arriba, y sale con un fundido. `_al_cerrar` (opcional) se ejecuta cuando ya
    terminó de cerrarse (útil para lanzar algo que no debe ocurrir con él abierto).
    """

    DESPLAZAMIENTO = 26

    def _preparar_animacion(self):
        self._ya_aparecio = False
        self._cerrando = False
        self._al_cerrar = None

    def showEvent(self, e):
        super().showEvent(e)
        if self._ya_aparecio:
            return
        self._ya_aparecio = True
        destino = self.pos()
        desp = self.DESPLAZAMIENTO
        self.setWindowOpacity(0.0)
        self.move(destino.x(), destino.y() + desp)

        anim = QVariantAnimation(self)
        anim.setDuration(340)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def paso(v):
            self.setWindowOpacity(v)
            self.move(destino.x(), destino.y() + int(desp * (1.0 - v)))

        anim.valueChanged.connect(paso)
        anim.start()
        self._anim_entrada_dialogo = anim

    def _terminar_cierre(self, resultado):
        super().done(resultado)
        pendiente, self._al_cerrar = self._al_cerrar, None
        if pendiente:
            pendiente()

    def done(self, resultado):
        if self._cerrando or not self.isVisible():
            self._terminar_cierre(resultado)
            return
        self._cerrando = True
        origen = self.pos()
        anim = QVariantAnimation(self)
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)

        def paso(v):
            self.setWindowOpacity(v)
            self.move(origen.x(), origen.y() + int(14 * (1.0 - v)))

        anim.valueChanged.connect(paso)
        anim.finished.connect(lambda: self._terminar_cierre(resultado))
        anim.start()
        self._anim_salida_dialogo = anim


class DialogoAnimado(_AparicionDeDialogo, QDialog):
    """QDialog que entra y sale con animación."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self._preparar_animacion()


class CajaAnimada(_AparicionDeDialogo, QMessageBox):
    """QMessageBox que entra y sale con animación."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self._preparar_animacion()


# ─────────────────────────────────────────────────────────────
# Aviso flotante
# ─────────────────────────────────────────────────────────────

class Aviso(QLabel):
    """Mensaje breve que aparece abajo, centrado, y se desvanece solo."""

    def __init__(self, ventana, texto, tipo="ok"):
        super().__init__(texto, ventana)
        color = {"ok": T.VERDE, "info": T.AZUL, "error": T.ROJO}.get(tipo, T.AZUL)
        self.setStyleSheet(
            "background-color: {}; color: {}; border: 1px solid {};"
            "border-left: 4px solid {}; border-radius: 10px;"
            "padding: 11px 20px; font-weight: 600;"
            .format(T.CRUST, T.TEXTO, T.BORDE, color))
        self.adjustSize()
        x = (ventana.width() - self.width()) // 2
        y_final = 22
        self.move(x, y_final - 20)
        self.show()
        self.raise_()

        efecto = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(efecto)

        entrada = QParallelAnimationGroup(self)
        a1 = QPropertyAnimation(efecto, b"opacity")
        a1.setDuration(220)
        a1.setStartValue(0.0)
        a1.setEndValue(1.0)
        a2 = QPropertyAnimation(self, b"pos")
        a2.setDuration(260)
        a2.setStartValue(QPoint(x, y_final - 20))
        a2.setEndValue(QPoint(x, y_final))
        a2.setEasingCurve(QEasingCurve.OutBack)
        entrada.addAnimation(a1)
        entrada.addAnimation(a2)
        entrada.start()

        salida = QPropertyAnimation(efecto, b"opacity", self)
        salida.setDuration(400)
        salida.setStartValue(1.0)
        salida.setEndValue(0.0)
        salida.finished.connect(self.deleteLater)
        def iniciar_salida():
            try:
                salida.start()
            except RuntimeError:
                pass
        QTimer.singleShot(2400, iniciar_salida)
        self._anims = (entrada, salida)

        # Barra inferior que se acorta hasta que el aviso se retira
        self._color_barra = QColor(color)
        self._resta = 1.0
        self._anim_resta = QVariantAnimation(self)
        self._anim_resta.setDuration(2400)
        self._anim_resta.setStartValue(1.0)
        self._anim_resta.setEndValue(0.0)
        self._anim_resta.valueChanged.connect(self._paso_resta)
        self._anim_resta.start()

    def _paso_resta(self, v):
        self._resta = v
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.fillRect(QRectF(4, self.height() - 3, (self.width() - 8) * self._resta, 2),
                   self._color_barra)


def mostrar_aviso(ventana, texto, tipo="ok"):
    return Aviso(ventana.window(), texto, tipo)
