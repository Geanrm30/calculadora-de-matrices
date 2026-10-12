# -*- coding: utf-8 -*-
"""
Componentes reutilizables con animaciones: botón, interruptor, tarjeta,
cuadrícula de matriz, pila de páginas con transición y avisos flotantes.
MTM0120 Álgebra Lineal — Universidad Americana.
"""
import re

from PySide6.QtCore import (Qt, QEasingCurve, QEvent, QParallelAnimationGroup,
                            QPoint, QPropertyAnimation, QRectF, QSize, QTimer,
                            QVariantAnimation, Signal)
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame,
                               QGraphicsOpacityEffect, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QPushButton,
                               QScrollArea, QStackedWidget, QVBoxLayout,
                               QWidget)

from qt import tema as T


def mezclar(c0, c1, t):
    """Interpolación lineal entre dos QColor."""
    a, b = QColor(c0), QColor(c1)
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t))


def aparecer(widget, duracion=260, retraso=0):
    """Desvanece un widget al mostrarse."""
    efecto = QGraphicsOpacityEffect(widget)
    efecto.setOpacity(0.0)
    widget.setGraphicsEffect(efecto)

    anim = QPropertyAnimation(efecto, b"opacity", widget)
    anim.setDuration(duracion)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def limpiar():
        widget.setGraphicsEffect(None)

    anim.finished.connect(limpiar)
    QTimer.singleShot(retraso, anim.start)
    widget._anim_aparecer = anim          # evita que se recolecte
    return anim


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

    def __init__(self, texto, estilo="suave", pequeno=False, parent=None):
        super().__init__(texto, parent)
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

        if self.hasFocus() and activo:
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(T.AZUL), 1.5))
            p.drawRoundedRect(r.adjusted(1.5, 1.5, -1.5, -1.5), 8, 8)

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

class Tarjeta(QFrame):
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
        self.lbl_titulo.setVisible(bool(titulo))
        self.cabecera.addWidget(self.lbl_titulo)
        self.cuerpo.addLayout(self.cabecera)

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


class Celda(QLineEdit):
    """Casilla numérica; Enter/↓/↑ mueven el foco, Ctrl+Z/Y deshacen la matriz."""

    mover = Signal(int, int)
    pegar = Signal(str)
    deshacer = Signal()
    rehacer = Signal()

    def __init__(self, texto="0", parent=None):
        super().__init__(texto, parent)
        self.setObjectName("celda")
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(66, 36)
        self.setProperty("error", False)

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
            if parsear_tabla(QApplication.clipboard().text()) is not None:
                self.pegar.emit(QApplication.clipboard().text())
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
        QTimer.singleShot(0, self.selectAll)


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

    def reconstruir(self, filas, columnas, anteriores=None, registrar=True):
        """Dibuja de nuevo conservando lo que ya estaba escrito."""
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
                c.pegar.connect(lambda txt, a=i, b=j: self.pegar_texto(txt, a, b))
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
        for fila in self.celdas:
            for c in fila:
                c.setText("0")
        self._registrar()

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

    def pegar(self):
        """Pega el portapapeles desde la primera celda. False si no era tabla."""
        return self.pegar_texto(QApplication.clipboard().text(), 0, 0)

    def pegar_texto(self, texto, i0=0, j0=0):
        filas = parsear_tabla(texto)
        if filas is None:
            return False
        actual = self.textos()
        n_f = min(max(len(actual), i0 + len(filas)), self.max_filas)
        n_c = min(max(self.columnas(), j0 + len(filas[0])), self.max_cols)
        base = [[self._valor(actual, i, j) for j in range(n_c)]
                for i in range(n_f)]
        for di, fila in enumerate(filas):
            for dj, valor in enumerate(fila):
                if i0 + di < n_f and j0 + dj < n_c:
                    base[i0 + di][j0 + dj] = valor
        self.reconstruir(n_f, n_c, base)
        self.forma_cambiada.emit(n_f, n_c)
        return True

    def marcar_error(self, i, j):
        c = self.celdas[i][j]
        c.setProperty("error", True)
        c.style().unpolish(c)
        c.style().polish(c)
        c.setFocus()

        def quitar():
            try:
                c.setProperty("error", False)
                c.style().unpolish(c)
                c.style().polish(c)
            except RuntimeError:
                pass                  # la celda ya se destruyó
        QTimer.singleShot(2500, quitar)


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
    b_tabla.setToolTip("Copiar o pegar como tabla (compatible con Excel)")
    b_tabla.con_menu([("Copiar como tabla", grid.copiar),
                      ("Pegar tabla (Excel o texto)", grid.pegar)])
    tarjeta.cabecera.addWidget(b_tabla)

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

class PilaAnimada(QStackedWidget):
    """QStackedWidget que al cambiar de página la desvanece y la sube."""

    def ir(self, indice):
        if indice == self.currentIndex():
            return
        self.setCurrentIndex(indice)
        w = self.currentWidget()

        efecto = QGraphicsOpacityEffect(w)
        efecto.setOpacity(0.0)
        w.setGraphicsEffect(efecto)

        fade = QPropertyAnimation(efecto, b"opacity", w)
        fade.setDuration(280)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)

        grupo = QParallelAnimationGroup(w)
        grupo.addAnimation(fade)
        grupo.finished.connect(lambda: w.setGraphicsEffect(None))
        grupo.start()
        self._grupo = grupo


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
        a2.setEasingCurve(QEasingCurve.OutCubic)
        entrada.addAnimation(a1)
        entrada.addAnimation(a2)
        entrada.start()

        salida = QPropertyAnimation(efecto, b"opacity", self)
        salida.setDuration(400)
        salida.setStartValue(1.0)
        salida.setEndValue(0.0)
        salida.finished.connect(self.deleteLater)
        QTimer.singleShot(2400, salida.start)
        self._anims = (entrada, salida)


def mostrar_aviso(ventana, texto, tipo="ok"):
    return Aviso(ventana.window(), texto, tipo)
