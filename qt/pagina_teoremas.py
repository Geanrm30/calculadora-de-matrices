# -*- coding: utf-8 -*-
"""
Catálogo de teoremas y criterios del curso: filtros por categoría, buscador que
resalta lo encontrado y tarjetas que se despliegan con animación.
"""
import html
import re
import time

from PySide6.QtCore import (QEasingCurve, QPoint, QPointF, QRectF, QSize, Qt, QTimer,
                            QVariantAnimation)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from core.teoremas import TEOREMAS
from qt import tema as T
from qt.componentes import BotonAnimado, entrada_suave, mezclar, mostrar_aviso
from qt.pagina_base import PaginaBase

_MAXIMO = 16777215                       # QWIDGETSIZE_MAX


def _a_html(texto):
    """Texto plano → HTML que respeta saltos de línea y sangrías."""
    return (html.escape(texto).replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;"))


def _resaltado(texto, consulta):
    """HTML del texto con las coincidencias de la consulta marcadas."""
    if not consulta:
        return _a_html(texto)
    fondo = mezclar(T.FONDO, T.NARANJA, 0.42).name()
    partes, pos = [], 0
    for m in re.finditer(re.escape(consulta), texto, re.IGNORECASE):
        partes.append(_a_html(texto[pos:m.start()]))
        partes.append("<span style='background-color:{}; color:{};'>{}</span>".format(
            fondo, T.TEXTO, _a_html(m.group(0))))
        pos = m.end()
    partes.append(_a_html(texto[pos:]))
    return "".join(partes)


class Filtro(QPushButton):
    """Botón en forma de píldora para filtrar por categoría."""

    def __init__(self, texto):
        super().__init__(texto)
        self._texto = texto
        self._sel = 0.0
        self._hov = 0.0
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        self.setFocusPolicy(Qt.TabFocus)
        self._a_sel = QVariantAnimation(self)
        self._a_sel.setDuration(240)
        self._a_sel.setEasingCurve(QEasingCurve.OutCubic)
        self._a_sel.valueChanged.connect(self._poner_sel)
        self._a_hov = QVariantAnimation(self)
        self._a_hov.setDuration(140)
        self._a_hov.valueChanged.connect(self._poner_hov)
        self.toggled.connect(self._cambio)

    def poner_texto(self, texto):
        self._texto = texto
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        f = QFont(T.FUENTE, 9)
        f.setWeight(QFont.DemiBold)
        return QSize(QFontMetrics(f).horizontalAdvance(self._texto) + 34, 32)

    def _poner_sel(self, v):
        self._sel = v
        self.update()

    def _poner_hov(self, v):
        self._hov = v
        self.update()

    def _cambio(self, marcado):
        self._a_sel.stop()
        self._a_sel.setStartValue(self._sel)
        self._a_sel.setEndValue(1.0 if marcado else 0.0)
        self._a_sel.start()

    def enterEvent(self, e):
        self._a_hov.stop()
        self._a_hov.setStartValue(self._hov)
        self._a_hov.setEndValue(1.0)
        self._a_hov.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._a_hov.stop()
        self._a_hov.setStartValue(self._hov)
        self._a_hov.setEndValue(0.0)
        self._a_hov.start()
        super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        base = mezclar(T.SUPERF, T.BORDE, self._hov * 0.6)
        fondo = mezclar(base, T.NARANJA, self._sel)
        p.setPen(Qt.NoPen)
        p.setBrush(fondo)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        f = QFont(T.FUENTE, 9)
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(mezclar(T.TEXTO, T.TEXTO_BOTON, self._sel))
        p.drawText(self.rect(), Qt.AlignCenter, self._texto)


class Flecha(QWidget):
    """Chevron que gira 90° al abrir la tarjeta."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(20, 20)
        self._giro = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def poner(self, v):
        self._giro = v
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(90 * self._giro)
        p.setPen(QPen(mezclar(T.MUTED, T.NARANJA, self._giro), 2.0, Qt.SolidLine,
                      Qt.RoundCap, Qt.RoundJoin))
        p.drawPolyline([QPointF(-2.5, -5), QPointF(2.5, 0), QPointF(-2.5, 5)])


class TarjetaTeorema(QFrame):
    """Teorema plegable: título y vista previa; al pulsar se despliega el enunciado."""

    _moviendo = 0              # cuántas tarjetas se están moviendo ahora mismo
    _UMBRAL_LENTO = 0.032      # si los cuadros tardan más (s), el movimiento termina de golpe

    def __init__(self, n, nombre, enunciado, uso, ventana):
        super().__init__()
        self.setObjectName("tarjeta")
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self._n = n
        self._nombre, self._enunciado, self._uso = nombre, enunciado, uso
        self._ventana = ventana
        self._abierta = False
        self._auto = False                      # la abrió una búsqueda
        self._hover = 0.0
        self._acento = 0.0
        self._animando = False
        self._contando = False
        self._a_alto = None

        # El contenido va en un panel interior de tamaño fijo: la tarjeta solo lo
        # «recorta» al achicarse o crecer, así el texto no se reacomoda ni se aprieta
        # mientras se mueve.
        self.interior = QWidget(self)
        self.interior.setStyleSheet("background: transparent;")
        self._alto_interior = 0
        raiz = QVBoxLayout(self.interior)
        self._raiz = raiz
        raiz.setContentsMargins(18, 12, 14, 12)
        raiz.setSpacing(0)

        cab = QHBoxLayout()
        cab.setSpacing(12)
        self.lbl_num = QLabel("{:02d}".format(n))
        self.lbl_num.setFixedWidth(26)
        self.lbl_num.setStyleSheet("color: {}; font-family: '{}'; font-size: 10pt;"
                                   " font-weight: 700; background: transparent;"
                                   .format(T.NARANJA, T.MONO))
        self.lbl_nombre = QLabel(nombre)
        self.lbl_nombre.setWordWrap(True)
        self.lbl_nombre.setStyleSheet("color: {}; font-size: 11.5pt; font-weight: 700;"
                                      " background: transparent;".format(T.TEXTO))
        self.flecha = Flecha()
        cab.addWidget(self.lbl_num)
        cab.addWidget(self.lbl_nombre, 1)
        cab.addWidget(self.flecha)
        self.cabecera = QWidget()
        self.cabecera.setLayout(cab)
        self.cabecera.setStyleSheet("background: transparent;")
        raiz.addWidget(self.cabecera)

        primera = enunciado.split("\n")[0].strip()
        self.lbl_prev = QLabel(primera if len(primera) <= 118 else primera[:117] + "…")
        self.lbl_prev.setStyleSheet("color: {}; font-size: 9.5pt; padding-left: 38px;"
                                    " background: transparent;".format(T.MUTED))
        raiz.addWidget(self.lbl_prev)

        self.cuerpo = QWidget()
        self.cuerpo.setStyleSheet("background: transparent;")
        vb = QVBoxLayout(self.cuerpo)
        vb.setContentsMargins(38, 2, 4, 4)
        vb.setSpacing(10)
        self.lbl_enun = QLabel()
        self.lbl_enun.setWordWrap(True)
        self.lbl_enun.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_enun.setCursor(Qt.IBeamCursor)
        self.lbl_enun.setStyleSheet("font-size: 10.5pt; background: transparent;")
        vb.addWidget(self.lbl_enun)
        self.lbl_uso = QLabel()
        self.lbl_uso.setWordWrap(True)
        self.lbl_uso.setStyleSheet("color: {}; font-style: italic; background: transparent;"
                                   .format(T.AZUL))
        vb.addWidget(self.lbl_uso)

        acciones = QHBoxLayout()
        acciones.setSpacing(8)
        clave, etiqueta = self._destino(uso)
        if clave:
            ir = BotonAnimado("Abrir en {}  →".format(etiqueta), "suave", pequeno=True)
            ir.clicked.connect(lambda: ventana.ir_y_mostrar(self._n))
            acciones.addWidget(ir)
        copiar = BotonAnimado("Copiar", "fantasma", pequeno=True)
        copiar.clicked.connect(self._copiar)
        acciones.addWidget(copiar)
        acciones.addStretch(1)
        vb.addLayout(acciones)
        raiz.addWidget(self.cuerpo)
        self.cuerpo.hide()

        self.resaltar("")

        self._a_giro = QVariantAnimation(self)
        self._a_giro.setDuration(280)
        self._a_giro.setEasingCurve(QEasingCurve.OutCubic)
        self._a_giro.valueChanged.connect(self._poner_giro)
        self._a_hov = QVariantAnimation(self)
        self._a_hov.setDuration(180)
        self._a_hov.valueChanged.connect(self._poner_hover)
        self._a_alto = None

    @staticmethod
    def _destino(uso):
        if uso.startswith("Solucionador"):
            return "solucionador", "Solucionador"
        if uso.startswith("Operaciones"):
            return "matrices", "Operaciones"
        return None, None

    # ── Contenido ──

    def resaltar(self, consulta):
        """Muestra los textos con las coincidencias marcadas (texto plano si no hay búsqueda)."""
        etiquetas = ((self.lbl_nombre, self._nombre), (self.lbl_enun, self._enunciado),
                     (self.lbl_uso, "Se usa en: " + self._uso))
        for etiqueta, texto in etiquetas:
            if consulta:
                etiqueta.setTextFormat(Qt.RichText)
                etiqueta.setText(_resaltado(texto, consulta))
            else:
                etiqueta.setTextFormat(Qt.PlainText)
                etiqueta.setText(texto)
        self._fijar_altura()

    def _copiar(self):
        QApplication.clipboard().setText("{}\n{}".format(self._nombre, self._enunciado))
        mostrar_aviso(self.window(), "Teorema copiado")

    # ── Despliegue ──

    def abierta(self):
        return self._abierta

    def _ancho_util(self):
        m = self._raiz.contentsMargins()
        return max(240, self.width() - m.left() - m.right())

    def _alto_cuerpo(self):
        alto = self.cuerpo.layout().totalHeightForWidth(self._ancho_util())
        return alto if alto > 0 else self.cuerpo.sizeHint().height()

    def _altura(self, abierta):
        """Alto de la tarjeta plegada o desplegada, calculado sin tocar el diseño."""
        m = self._raiz.contentsMargins()
        cab = self.cabecera.layout().totalHeightForWidth(self._ancho_util())
        if cab <= 0:
            cab = self.cabecera.sizeHint().height()
        resto = self._alto_cuerpo() if abierta else self.lbl_prev.sizeHint().height()
        return m.top() + m.bottom() + cab + resto

    def _poner_interior(self, alto):
        self._alto_interior = alto
        self.interior.setGeometry(0, 0, self.width(), alto)

    def _mostrar_contenido(self, abierta):
        """Plegada: título y vista previa. Desplegada: título y enunciado completo."""
        self.cuerpo.setVisible(abierta)
        self.lbl_prev.setVisible(not abierta)

    def _fijar_altura(self):
        """
        Cada tarjeta tiene una altura fija ya calculada: así la lista no tiene que
        volver a medir el texto de las 21 tarjetas en cada fotograma del despliegue.
        """
        if not self._animando:
            alto = self._altura(self._abierta)
            self.setFixedHeight(alto)
            self._poner_interior(alto)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._animando:
            self.interior.setGeometry(0, 0, self.width(), self._alto_interior)
        else:
            self._fijar_altura()

    def fijar(self, abierta, animar=True, auto=False):
        if abierta == self._abierta:
            return
        visible = self.isVisible()
        self._abierta = abierta
        self._auto = auto and abierta
        if self._a_alto is not None:
            self._a_alto.stop()
        self._soltar_conteo()

        h_cerrada, h_abierta = self._altura(False), self._altura(True)
        desde = self.height() if visible else (h_cerrada if abierta else h_abierta)
        hasta = h_abierta if abierta else h_cerrada

        # Mientras se mueve, el contenido es siempre el de la tarjeta desplegada y con su
        # tamaño completo: no se reacomoda nada, solo se recorta por abajo.
        self._animando = True
        self._mostrar_contenido(True)
        self._poner_interior(max(h_abierta, h_cerrada))

        def fin():
            self._animando = False
            self._mostrar_contenido(self._abierta)
            self._fijar_altura()

        self._a_giro.stop()
        self._a_giro.setStartValue(self.flecha._giro)
        self._a_giro.setEndValue(1.0 if abierta else 0.0)
        if not (animar and visible):
            fin()
            self._a_giro.setDuration(0)
            self._a_giro.start()
            self._a_giro.setDuration(280)
            return

        anim = QVariantAnimation(self)
        anim.setDuration(260)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(desde)
        anim.setEndValue(hasta)
        marcas = []

        def paso(v):
            self.setFixedHeight(int(v))
            marcas.append(time.perf_counter())
            # Si los cuadros salen lentos (equipo justo), mejor terminar ya que arrastrar el tirón
            if len(marcas) == 5 and (marcas[4] - marcas[1]) / 3 > TarjetaTeorema._UMBRAL_LENTO:
                QTimer.singleShot(0, lambda: anim.setCurrentTime(anim.duration()))

        def terminar():
            self._soltar_conteo()
            fin()
            if not TarjetaTeorema._moviendo:        # vuelve el resaltado bajo el cursor
                self._hover_a(1.0 if self.underMouse() else 0.0)

        anim.valueChanged.connect(paso)
        anim.finished.connect(terminar)
        TarjetaTeorema._moviendo += 1
        self._contando = True
        anim.start()
        self._a_alto = anim
        self._a_giro.start()

    def _soltar_conteo(self):
        """Resta esta tarjeta del conteo de las que se mueven (una sola vez)."""
        if self._contando:
            self._contando = False
            TarjetaTeorema._moviendo = max(0, TarjetaTeorema._moviendo - 1)

    def alternar(self):
        self.fijar(not self._abierta, auto=False)

    def _poner_giro(self, v):
        self.flecha.poner(v)
        self._acento = max(v, self._hover * 0.6)
        self.update()

    def _poner_hover(self, v):
        self._hover = v
        self._acento = max(self.flecha._giro, v * 0.6)
        self.update()

    # ── Eventos ──

    def _hover_a(self, destino):
        self._a_hov.stop()
        self._a_hov.setStartValue(self._hover)
        self._a_hov.setEndValue(destino)
        self._a_hov.start()

    def enterEvent(self, e):
        # Al deslizarse las tarjetas bajo el cursor llegan muchos eventos de entrada y
        # salida: mientras se mueven no se animan los resaltados (menos repintados).
        if not TarjetaTeorema._moviendo:
            self._hover_a(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        if not TarjetaTeorema._moviendo:
            self._hover_a(0.0)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        limite = self.cabecera.geometry().bottom() + (
            self.lbl_prev.geometry().height() if self.lbl_prev.isVisible() else 0) + 6
        if e.button() == Qt.LeftButton and e.position().y() <= limite:
            self.alternar()
        super().mousePressEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._hover > 0.01 or self._acento > 0.01:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            if self._hover > 0.01:
                velo = QColor(T.SUPERF)
                velo.setAlpha(int(70 * self._hover))
                p.setPen(Qt.NoPen)
                p.setBrush(velo)
                p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 11, 11)
            if self._acento > 0.01:
                alto = (self.height() - 22) * self._acento
                p.setBrush(QColor(T.NARANJA))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(QRectF(0, (self.height() - alto) / 2, 4, alto), 2, 2)


class PaginaTeoremas(PaginaBase):

    CATEGORIAS = (
        ("todos", "Todos"),
        ("solucionador", "Solucionador"),
        ("operaciones", "Operaciones"),
        ("propiedades", "Propiedades"),
    )

    def __init__(self, ventana):
        super().__init__(ventana, "Teoremas y criterios",
                         "Catálogo de teoremas del curso (Sesiones 1–11)")
        self._categoria = "todos"
        self._consulta = ""

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar por nombre, enunciado o herramienta…  (Ctrl+F)")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setMinimumHeight(38)
        self.buscador.textChanged.connect(self._al_buscar)
        self.raiz.addWidget(self.buscador)
        self.atajo("Ctrl+F", lambda: (self.buscador.setFocus(), self.buscador.selectAll()))

        # Filtros por categoría y control de despliegue
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(True)
        self.filtros = {}
        for clave, texto in self.CATEGORIAS:
            f = Filtro(texto)
            self.grupo.addButton(f)
            f.clicked.connect(lambda _=False, c=clave: self._al_filtrar(c))
            fila.addWidget(f)
            self.filtros[clave] = f
        self.filtros["todos"].setChecked(True)
        fila.addStretch(1)
        self.btn_desplegar = BotonAnimado("Expandir todo", "fantasma", pequeno=True)
        self.btn_desplegar.clicked.connect(self._desplegar_todo)
        fila.addWidget(self.btn_desplegar)
        self.raiz.addLayout(fila)

        self.lbl_cuenta = QLabel("")
        self.lbl_cuenta.setObjectName("nota")
        self.raiz.addWidget(self.lbl_cuenta)

        cont = QWidget()
        self.lista = QVBoxLayout(cont)
        self.lista.setContentsMargins(0, 0, 8, 0)
        self.lista.setSpacing(10)

        self.tarjetas = []                       # (tarjeta, texto en minúsculas, categorías)
        for i, (nombre, enunciado, uso) in enumerate(TEOREMAS, start=1):
            t = TarjetaTeorema(i, nombre, enunciado, uso, ventana)
            self.lista.addWidget(t)
            self.tarjetas.append((t, "{} {} {}".format(nombre, enunciado, uso).lower(),
                                  self._categorias(nombre, uso)))

        self.lbl_vacio = QLabel("")
        self.lbl_vacio.setAlignment(Qt.AlignCenter)
        self.lbl_vacio.setStyleSheet("color: {}; font-style: italic; font-size: 11pt;"
                                     " padding: 40px; background: transparent;".format(T.MUTED))
        self.lbl_vacio.hide()
        self.lista.addWidget(self.lbl_vacio)
        self.lista.addStretch(1)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(cont)
        self.raiz.addWidget(area, 1)

        for clave, f in self.filtros.items():
            n = sum(1 for _, _, cats in self.tarjetas if clave in cats)
            f.poner_texto("{}  ·  {}".format(dict(self.CATEGORIAS)[clave], n))
        self._aplicar(animar=False)

    @staticmethod
    def _categorias(nombre, uso):
        cats = {"todos"}
        if uso.startswith("Solucionador"):
            cats.add("solucionador")
        if uso.startswith("Operaciones"):
            cats.add("operaciones")
        if nombre.lower().startswith("propiedades"):
            cats.add("propiedades")
        return cats

    # ── Filtros y búsqueda ──

    def _al_filtrar(self, clave):
        self._categoria = clave
        self._aplicar()

    def _al_buscar(self, texto):
        self._consulta = texto.strip().lower()
        self._aplicar()

    def _aplicar(self, animar=True):
        q = self._consulta
        visibles, nuevas = 0, []
        for t, clave, cats in self.tarjetas:
            mostrar = self._categoria in cats and q in clave
            if mostrar and not t.isVisible():
                nuevas.append(t)
            t.setVisible(mostrar)
            if mostrar:
                visibles += 1
                t.resaltar(q if len(q) >= 2 else "")
                if len(q) >= 2:
                    t.fijar(True, animar, auto=True)
                elif t._auto:
                    t.fijar(False, animar)
        total = len(self.tarjetas)
        if self._categoria == "todos" and not q:
            self.lbl_cuenta.setText("{} teoremas".format(total))
        else:
            self.lbl_cuenta.setText("{} de {} teoremas".format(visibles, total))
        self.lbl_vacio.setVisible(visibles == 0)
        if visibles == 0:
            self.lbl_vacio.setText("Ningún teorema coincide con «{}».".format(
                self.buscador.text().strip()) if q else "No hay teoremas en esta categoría.")
        if animar:
            for i, t in enumerate(nuevas[:10]):
                entrada_suave(t, 40 * i, 380)
        self._actualizar_boton()

    def _visibles(self):
        return [t for t, _, _ in self.tarjetas if t.isVisible()]

    def _actualizar_boton(self):
        visibles = self._visibles()
        todo_abierto = bool(visibles) and all(t.abierta() for t in visibles)
        self.btn_desplegar.setText("Contraer todo" if todo_abierto else "Expandir todo")

    def _desplegar_todo(self):
        visibles = self._visibles()
        abrir = not (visibles and all(t.abierta() for t in visibles))
        area = self.findChild(QScrollArea)
        barra, vista = area.verticalScrollBar(), area.viewport()
        valor_antes = barra.value()                  # referencia: Qt lo recorta al achicarse la lista
        compensar = 0
        # Primero se mide dónde está cada una (en cuanto cambia una, las demás se corren)
        posiciones = [(t, t.mapTo(vista, QPoint(0, 0)).y()) for t in visibles]
        for t, y in posiciones:
            if 0 <= y < vista.height():
                t.fijar(abrir)                       # las que se ven enteras desde arriba, animadas
            else:
                antes = t.height()
                t.fijar(abrir, animar=False)         # las demás cambian al instante
                if y < 0:                            # por encima del borde: empujarían lo que se ve
                    compensar += t._altura(abrir) - antes   # la altura nueva aún no se aplicó

        def mantener_vista():
            try:
                barra.setValue(valor_antes + compensar)
            except RuntimeError:
                pass

        if compensar:
            area.widget().layout().activate()        # que la lista ya tenga su nuevo largo
            mantener_vista()
            QTimer.singleShot(0, mantener_vista)
        self.btn_desplegar.setText("Contraer todo" if abrir else "Expandir todo")

    def showEvent(self, e):
        super().showEvent(e)
        for i, t in enumerate(self._visibles()[:10]):
            entrada_suave(t, 45 * i, 420)
