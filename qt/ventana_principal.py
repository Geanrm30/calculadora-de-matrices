# -*- coding: utf-8 -*-
"""
Ventana principal: menú lateral con indicador animado y páginas que se
conservan entre cambios (lo escrito en cada herramienta no se pierde).
"""
from PySide6.QtCore import (QByteArray, QEasingCurve, QPoint,
                            QPropertyAnimation, QRect, Qt, QVariantAnimation)
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QVBoxLayout, QWidget)

from qt import tema as T
from qt import persistencia
from qt.componentes import BotonAnimado, PilaAnimada, mezclar
from qt.pagina_inicio import PaginaInicio
from qt.pagina_matrices import PaginaMatrices
from qt.pagina_solucionador import PaginaSolucionador
from qt.pagina_teoremas import PaginaTeoremas



def secciones():
    """(clave, texto, icono, color) con los colores del tema actual."""
    return [
        ("inicio",       "Inicio",       "⌂", T.TEXTO),
        ("solucionador", "Solucionador", "≡", T.NARANJA),
        ("matrices",     "Operaciones",  "▦", T.AZUL),
        ("teoremas",     "Teoremas",     "∴", T.MORADO),
    ]


class BotonNav(QPushButton):

    def __init__(self, texto, icono, color, atajo):
        super().__init__()
        self._texto, self._icono, self._color = texto, icono, QColor(color)
        self._atajo = atajo
        self._t = 0.0
        self._sel = 0.0
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setFocusPolicy(Qt.TabFocus)

        self._hov = QVariantAnimation(self)
        self._hov.setDuration(140)
        self._hov.valueChanged.connect(self._set_hover)
        self._selanim = QVariantAnimation(self)
        self._selanim.setDuration(220)
        self._selanim.setEasingCurve(QEasingCurve.OutCubic)
        self._selanim.valueChanged.connect(self._set_sel)
        self.toggled.connect(self._cambio)

    def _set_hover(self, v):
        self._t = v
        self.update()

    def _set_sel(self, v):
        self._sel = v
        self.update()

    def _cambio(self, marcado):
        self._selanim.stop()
        self._selanim.setStartValue(self._sel)
        self._selanim.setEndValue(1.0 if marcado else 0.0)
        self._selanim.start()

    def _hover_a(self, d):
        self._hov.stop()
        self._hov.setStartValue(self._t)
        self._hov.setEndValue(d)
        self._hov.start()

    def enterEvent(self, e):
        self._hover_a(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover_a(0.0)
        super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(8, 2, -8, -2)

        fondo = mezclar(T.PANEL, T.SUPERF, max(self._t * 0.6, self._sel))
        p.setPen(Qt.NoPen)
        p.setBrush(fondo)
        p.drawRoundedRect(r, 10, 10)

        color = mezclar(T.MUTED, self._color, max(self._sel, self._t * 0.5))
        p.setPen(color)
        p.setFont(QFont(T.FUENTE, 15))
        p.drawText(QRect(r.left() + 6, r.top(), 34, r.height()),
                   Qt.AlignCenter, self._icono)

        p.setPen(mezclar(T.MUTED, T.TEXTO, max(self._sel, self._t * 0.7)))
        f = QFont(T.FUENTE, 10)
        f.setWeight(QFont.DemiBold if self.isChecked() else QFont.Normal)
        p.setFont(f)
        p.drawText(QRect(r.left() + 46, r.top(), r.width() - 46, r.height()),
                   Qt.AlignVCenter | Qt.AlignLeft, self._texto)

        p.setPen(QColor(T.BORDE))
        p.setFont(QFont(T.FUENTE, 7))
        p.drawText(QRect(r.right() - 44, r.top(), 38, r.height()),
                   Qt.AlignVCenter | Qt.AlignRight, self._atajo)


class VentanaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora de Álgebra Lineal — MTM0120")
        self.resize(1480, 920)
        self.setMinimumSize(1240, 720)
        self._secciones = secciones()
        self._cambiando_tema = False

        central = QWidget()
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.pila = PilaAnimada()
        self.pagina_inicio = PaginaInicio(self)
        self.pagina_solucionador = PaginaSolucionador(self)
        self.pagina_matrices = PaginaMatrices(self)
        self.pagina_teoremas = PaginaTeoremas(self)
        self._claves = [s[0] for s in self._secciones]
        for pag in (self.pagina_inicio, self.pagina_solucionador,
                    self.pagina_matrices, self.pagina_teoremas):
            self.pila.addWidget(pag)

        lay.addWidget(self._crear_barra_lateral())
        lay.addWidget(self.pila, 1)

        for i in range(len(self._secciones)):
            QShortcut(QKeySequence("Ctrl+{}".format(i + 1)), self,
                      activated=lambda k=self._claves[i]: self.ir_a(k))

        self._boton_de = dict(zip(self._claves, self.botones))
        self.botones[0].setChecked(True)
        self._mover_indicador(0, animar=False)

    # ──────────────────────────────────────────────────────────

    def _crear_barra_lateral(self):
        barra = QFrame()
        barra.setFixedWidth(224)
        barra.setStyleSheet("QFrame {{ background-color: {}; }}".format(T.PANEL))
        v = QVBoxLayout(barra)
        v.setContentsMargins(0, 22, 0, 16)
        v.setSpacing(2)

        logo = QLabel("UAM")
        logo.setStyleSheet(
            "color: {}; font-size: 26pt; font-weight: 900; letter-spacing: 4px;"
            " background: transparent; padding-left: 22px;".format(T.NARANJA))
        v.addWidget(logo)
        nombre = QLabel("Álgebra Lineal")
        nombre.setStyleSheet("color: {}; font-size: 10pt; font-weight: 600;"
                             " background: transparent; padding-left: 24px;"
                             " margin-bottom: 22px;".format(T.TEXTO))
        v.addWidget(nombre)

        self.botones = []
        for i, (clave, texto, icono, color) in enumerate(self._secciones):
            b = BotonNav(texto, icono, color, "Ctrl+{}".format(i + 1))
            b.clicked.connect(lambda _=False, k=clave: self.ir_a(k))
            v.addWidget(b)
            self.botones.append(b)

        # Indicador deslizante (barra de color a la izquierda)
        self.indicador = QFrame(barra)
        self.indicador.setFixedSize(4, 26)
        self.indicador.setStyleSheet(
            "background-color: {}; border-radius: 2px;".format(T.NARANJA))
        self.indicador.raise_()
        self._barra = barra

        v.addStretch(1)

        nombre_btn = ("☀   Tema claro" if T.NOMBRE_TEMA == "oscuro"
                      else "☾   Tema oscuro")
        self.btn_tema = BotonAnimado(nombre_btn, "fantasma", pequeno=True)
        self.btn_tema.setToolTip("Cambiar entre tema claro y oscuro")
        self.btn_tema.clicked.connect(self.alternar_tema)
        marco_tema = QHBoxLayout()
        marco_tema.setContentsMargins(14, 0, 14, 8)
        marco_tema.addWidget(self.btn_tema)
        v.addLayout(marco_tema)

        pie = QLabel("MTM0120\nUniversidad Americana")
        pie.setStyleSheet("color: {}; font-size: 8pt; background: transparent;"
                          " padding-left: 24px;".format(T.MUTED))
        v.addWidget(pie)
        return barra

    def _mover_indicador(self, indice, animar=True):
        b = self.botones[indice]
        destino = b.mapTo(self._barra, b.rect().topLeft())
        y = destino.y() + (b.height() - self.indicador.height()) // 2
        color = self._secciones[indice][3]
        self.indicador.setStyleSheet(
            "background-color: {}; border-radius: 2px;".format(color))
        if not animar:
            self.indicador.move(4, y)
            return
        anim = QPropertyAnimation(self.indicador, b"pos", self)
        anim.setDuration(260)
        anim.setEasingCurve(QEasingCurve.OutBack)
        anim.setEndValue(QPoint(4, y))
        anim.start()
        self._anim_ind = anim

    def showEvent(self, e):
        super().showEvent(e)
        self._mover_indicador(self.pila.currentIndex(), animar=False)

    def ir_a(self, clave):
        if clave not in self._claves:
            return
        i = self._claves.index(clave)
        for k, b in enumerate(self.botones):
            b.blockSignals(True)
            b.setChecked(k == i)
            b.blockSignals(False)
            b._cambio(k == i)
        self._mover_indicador(i)
        self.pila.ir(i)

    # ──────────────────────────────────────────────────────────
    # Sesión: tema, tamaño y lo escrito en cada herramienta
    # ──────────────────────────────────────────────────────────

    def estado(self):
        return {
            "pagina": self._claves[self.pila.currentIndex()],
            "solucionador": self.pagina_solucionador.estado(),
            "matrices": self.pagina_matrices.estado(),
        }

    def restaurar(self, d):
        if not isinstance(d, dict):
            return
        if "solucionador" in d:
            self.pagina_solucionador.restaurar(d["solucionador"])
        if "matrices" in d:
            self.pagina_matrices.restaurar(d["matrices"])
        pagina = d.get("pagina", "inicio")
        if pagina in self._claves:
            i = self._claves.index(pagina)
            self.pila.setCurrentIndex(i)
            for k, b in enumerate(self.botones):
                b.blockSignals(True)
                b.setChecked(k == i)
                b.blockSignals(False)
                b._sel = 1.0 if k == i else 0.0

    def restaurar_sesion(self):
        """Recupera lo guardado la última vez que se cerró el programa."""
        geom = persistencia.leer("geometria")
        if geom:
            self.restoreGeometry(QByteArray.fromBase64(geom.encode()))
        self.restaurar(persistencia.leer("sesion"))

    def _guardar_sesion(self, estado=None):
        persistencia.escribir("sesion", estado or self.estado())
        persistencia.escribir(
            "geometria", bytes(self.saveGeometry().toBase64()).decode())

    def closeEvent(self, e):
        if not self._cambiando_tema:
            self._guardar_sesion()
        super().closeEvent(e)

    def alternar_tema(self):
        """Cambia entre claro y oscuro sin perder nada de lo escrito."""
        nuevo = "claro" if T.NOMBRE_TEMA == "oscuro" else "oscuro"
        estado = self.estado()
        geometria = self.saveGeometry()
        self._guardar_sesion(estado)

        T.aplicar(nuevo)
        persistencia.escribir("tema", nuevo)
        app = QApplication.instance()
        app.setStyleSheet(T.hoja_de_estilos())

        nueva = VentanaPrincipal()
        nueva.restoreGeometry(geometria)
        nueva.restaurar(estado)
        nueva.show()
        app._ventana_principal = nueva        # evita que la recolecte el GC

        self._cambiando_tema = True
        self.close()
