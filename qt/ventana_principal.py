# -*- coding: utf-8 -*-
"""
Ventana principal: menú lateral con indicador animado y páginas que se
conservan entre cambios (lo escrito en cada herramienta no se pierde).
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import importlib.util
import time

from PySide6.QtCore import (QByteArray, QCoreApplication, QEasingCurve, QEvent,
                            QPoint, QPropertyAnimation, QRect, Qt, QTimer,
                            QVariantAnimation)
from PySide6.QtGui import QColor, QCursor, QFont, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from qt import tema as T
from qt import persistencia
from qt.ayuda import DialogoAyuda
from qt.componentes import (BotonAnimado, PilaAnimada, entrada_suave,
                            fundido_de_ventana, mezclar, mostrar_aviso)
from qt.guia import Guia, especificacion_de_teorema
from qt.tour import PasoTour, Tour
from qt.visor import cerrar_todas as cerrar_ventanas_de_resultado
from qt.pagina_inicio import PaginaInicio
from qt.pagina_lu import PaginaLU
from qt.pagina_numerica import PaginaNumerica
from qt.pagina_matrices import PaginaMatrices
from qt.pagina_solucionador import PaginaSolucionador
from qt.pagina_teoremas import PaginaTeoremas


def secciones():
    """(clave, texto, icono, color) con los colores del tema actual."""
    return [
        ("inicio",       "Inicio",       "⌂", T.TEXTO),
        ("solucionador", "Solucionador", "≡", T.NARANJA),
        ("matrices",     "Operaciones",  "▦", T.AZUL),
        ("lu",           "Factorización LU", "▤", T.VERDE),
        ("numerico",     "Métodos Numéricos", "∫", T.ROJO),
        ("teoremas",     "Teoremas",     "∴", T.MORADO),
    ]


class BotonNav(QPushButton):

    """Botón de la barra lateral con icono, texto, atajo y animaciones de selección."""
    def __init__(self, texto, icono, color, atajo):
        """Crea el botón con su texto, icono, color y atajo."""
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

        self._pop = 0.0
        self._pop_anim = QVariantAnimation(self)
        self._pop_anim.setDuration(560)
        self._pop_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._pop_anim.setKeyValueAt(0.0, 0.0)
        self._pop_anim.setKeyValueAt(0.35, 1.0)
        self._pop_anim.setKeyValueAt(1.0, 0.0)
        self._pop_anim.valueChanged.connect(self._set_pop)

    def _set_pop(self, v):
        """Guarda el avance del rebote al seleccionar y repinta."""
        self._pop = v
        self.update()

    def _set_hover(self, v):
        """Guarda el avance del resalte y repinta."""
        self._t = v
        self.update()

    def _set_sel(self, v):
        """Guarda el avance de la selección y repinta."""
        self._sel = v
        self.update()

    def _cambio(self, marcado):
        """Anima la selección al marcarse o desmarcarse."""
        if marcado:
            self._pop_anim.stop()
            self._pop_anim.start()
        self._selanim.stop()
        self._selanim.setStartValue(self._sel)
        self._selanim.setEndValue(1.0 if marcado else 0.0)
        self._selanim.start()

    def _hover_a(self, d):
        """Anima el resalte hasta el valor dado."""
        self._hov.stop()
        self._hov.setStartValue(self._t)
        self._hov.setEndValue(d)
        self._hov.start()

    def enterEvent(self, e):
        """Resalta el botón cuando el ratón entra."""
        self._hover_a(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        """Quita el resalte cuando el ratón sale."""
        self._hover_a(0.0)
        super().leaveEvent(e)

    def paintEvent(self, _):
        """Dibuja el fondo, el icono, el texto y el atajo del botón."""
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
        caja = QRect(r.left() + 6, r.top(), 34, r.height())
        p.save()
        p.translate(caja.center())
        escala = 1.0 + 0.45 * self._pop
        p.scale(escala, escala)
        p.rotate(-14 * self._pop)
        p.translate(-caja.center())
        p.drawText(caja, Qt.AlignCenter, self._icono)
        p.restore()

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


def _rehacer_ventana(tema_nuevo, estado, geometria, vieja):
    """
    Cambio de tema: se destruye la ventana vieja ANTES de aplicar el estilo nuevo
    (así Qt no vuelve a estilizar sus cientos de widgets) y la nueva entra con un
    fundido. Solo se construye la página que se estaba viendo.
    """
    app = QApplication.instance()
    vieja.hide()
    vieja.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    T.aplicar(tema_nuevo)
    persistencia.escribir("tema", tema_nuevo)
    app.setStyleSheet(T.hoja_de_estilos())

    nueva = VentanaPrincipal()
    nueva.restoreGeometry(geometria)
    nueva.restaurar(estado)
    nueva.setWindowOpacity(0.0)
    nueva.show()
    fundido_de_ventana(nueva, 420)
    app._ventana_principal = nueva
    nueva.precargar_paginas(retraso=2200)


class VentanaPrincipal(QMainWindow):

    """Ventana principal: barra lateral, páginas de cada sección, tema, ayuda y recorrido."""
    _FABRICAS = {"inicio": PaginaInicio, "solucionador": PaginaSolucionador,
                 "matrices": PaginaMatrices, "lu": PaginaLU,
                 "teoremas": PaginaTeoremas,
                 "numerico": PaginaNumerica}

    def __init__(self):
        """Crea la ventana, la barra lateral y la pila de páginas; restaura la sesión guardada."""
        super().__init__()
        self.setWindowTitle("Calculadora de Álgebra Lineal — MTM0120")
        self.resize(1480, 920)
        self.setMinimumSize(980, 600)
        self._secciones = secciones()
        self._cambiando_tema = False
        self._tour = None
        self._guia = None
        self._exposicion = False

        central = QWidget()
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.pila = PilaAnimada()
        self._claves = [s[0] for s in self._secciones]
        self._paginas = {}
        self._pendiente = {}
        self._marcos = {}
        for clave in self._claves:
            marco = self._con_desplazamiento(None)
            self._marcos[clave] = marco
            self.pila.addWidget(marco)
        self._pagina("inicio")

        lay.addWidget(self._crear_barra_lateral())
        lay.addWidget(self.pila, 1)

        for i in range(len(self._secciones)):
            QShortcut(QKeySequence("Ctrl+{}".format(i + 1)), self,
                      activated=lambda k=self._claves[i]: self.ir_a(k))

        QShortcut(QKeySequence("F1"), self, activated=lambda: self.abrir_ayuda(0))
        QShortcut(QKeySequence("F11"), self, activated=self.alternar_exposicion)
        QShortcut(QKeySequence("Esc"), self, activated=self._salir_de_exposicion)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self.alternar_tema)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)
        for tecla in ("Ctrl++", "Ctrl+="):
            QShortcut(QKeySequence(tecla), self,
                      activated=lambda: self.cambiar_escala(1))
        QShortcut(QKeySequence("Ctrl+-"), self,
                  activated=lambda: self.cambiar_escala(-1))
        QShortcut(QKeySequence("Ctrl+0"), self,
                  activated=lambda: self.cambiar_escala(0))

        self._crear_barra_de_estado()
        self._boton_de = dict(zip(self._claves, self.botones))
        self.botones[0].setChecked(True)
        self._mover_indicador(0, animar=False)
        self._entrada_barra()

    def _entrada_barra(self):
        """Las pestañas y las herramientas de la barra entran una tras otra."""
        elementos = list(self.botones) + [self.btn_menos, self.lbl_escala,
                                          self.btn_mas, self.btn_tema, self.btn_ayuda,
                                          self.btn_acerca]
        for i, w in enumerate(elementos):
            entrada_suave(w, retraso=120 + 70 * i, duracion=420)


    def _pagina(self, clave):
        """Devuelve la página, construyéndola la primera vez que se pide."""
        pag = self._paginas.get(clave)
        if pag is None:
            pag = self._FABRICAS[clave](self)
            self._paginas[clave] = pag
            self._marcos[clave].setWidget(pag)
            estado = self._pendiente.pop(clave, None)
            if estado is not None:
                pag.restaurar(estado)
        return pag

    pagina_inicio = property(lambda self: self._pagina("inicio"))
    pagina_solucionador = property(lambda self: self._pagina("solucionador"))
    pagina_matrices = property(lambda self: self._pagina("matrices"))
    pagina_lu = property(lambda self: self._pagina("lu"))
    pagina_numerica = property(lambda self: self._pagina("numerico"))
    pagina_teoremas = property(lambda self: self._pagina("teoremas"))

    def precargar_paginas(self, retraso=1400, separacion=500, quietud=0.8):
        """Construye en segundo plano las páginas que faltan, solo cuando el programa está en reposo.
        Así un clic no coincide con los 100-300 ms que tarda construir una página.
        """
        pendientes = [c for c in self._claves if c not in self._paginas]
        reposo = {"pos": QCursor.pos(), "desde": time.perf_counter()}

        def siguiente():
            """Construye la siguiente página pendiente si sigue en reposo."""
            try:
                if not pendientes or self._cambiando_tema:
                    return
                pos = QCursor.pos()
                if pos != reposo["pos"] or QApplication.mouseButtons() != Qt.NoButton:
                    reposo["pos"], reposo["desde"] = pos, time.perf_counter()
                en_uso = time.perf_counter() - reposo["desde"] < quietud
                if en_uso or self.pila._anim is not None:
                    QTimer.singleShot(250, siguiente)
                    return
                self._pagina(pendientes.pop(0))
                reposo["desde"] = time.perf_counter()
                if pendientes:
                    QTimer.singleShot(separacion, siguiente)
            except RuntimeError:
                pass

        QTimer.singleShot(retraso, siguiente)

    @staticmethod
    def _con_desplazamiento(pagina):
        """
        Mete la página en un área con desplazamiento. Si la ventana es más
        pequeña de lo que la página necesita, aparecen barras en lugar de que
        el contenido se apriete (botones montados, textos cortados).
        """
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        if pagina is not None:
            area.setWidget(pagina)
        return area

    def _crear_barra_lateral(self):
        """Crea la barra lateral con los botones de navegación, el tema y la ayuda."""
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

        self.indicador = QFrame(barra)
        self.indicador.setFixedSize(4, 26)
        self.indicador.setStyleSheet(
            "background-color: {}; border-radius: 2px;".format(T.NARANJA))
        self.indicador.raise_()
        self._barra = barra

        v.addStretch(1)

        grupo_escala = QFrame()
        grupo_escala.setObjectName("grupoEscala")
        grupo_escala.setStyleSheet(
            "QFrame#grupoEscala {{ background: transparent; border: 1px solid {};"
            " border-radius: 10px; }}".format(T.BORDE))
        self.grupo_escala = grupo_escala
        fila_escala = QHBoxLayout(grupo_escala)
        fila_escala.setContentsMargins(6, 3, 6, 3)
        fila_escala.setSpacing(2)
        self.btn_menos = BotonAnimado("A−", "fantasma", pequeno=True)
        self.btn_menos.setToolTip("Reducir la letra de cuadrículas y resultados (Ctrl+−)")
        self.btn_menos.clicked.connect(lambda: self.cambiar_escala(-1))
        self.lbl_escala = QLabel("")
        self.lbl_escala.setAlignment(Qt.AlignCenter)
        self.lbl_escala.setToolTip("Tamaño de letra (Ctrl+0 para restablecer)")
        self.lbl_escala.setStyleSheet(
            "color: {}; font-weight: 600; background: transparent;".format(T.MUTED))
        self.btn_mas = BotonAnimado("A+", "fantasma", pequeno=True)
        self.btn_mas.setToolTip("Agrandar la letra de cuadrículas y resultados (Ctrl++)")
        self.btn_mas.clicked.connect(lambda: self.cambiar_escala(1))
        fila_escala.addWidget(self.btn_menos)
        fila_escala.addWidget(self.lbl_escala, 1)
        fila_escala.addWidget(self.btn_mas)
        marco_escala = QHBoxLayout()
        marco_escala.setContentsMargins(14, 0, 14, 8)
        marco_escala.addWidget(grupo_escala)
        v.addLayout(marco_escala)
        self._refrescar_escala()

        nombre_btn = ("☀   Tema claro" if T.NOMBRE_TEMA == "oscuro"
                      else "☾   Tema oscuro")
        self.btn_tema = BotonAnimado(nombre_btn, "fantasma", pequeno=True, borde=True)
        self.btn_tema.setToolTip("Cambiar entre tema claro y oscuro (Ctrl+Shift+T)")
        self.btn_tema.clicked.connect(self.alternar_tema)
        marco_tema = QHBoxLayout()
        marco_tema.setContentsMargins(14, 0, 14, 6)
        marco_tema.addWidget(self.btn_tema)
        v.addLayout(marco_tema)

        self.btn_exposicion = BotonAnimado("▢   Modo exposición", "fantasma",
                                           pequeno=True, borde=True)
        self.btn_exposicion.setToolTip("Letra grande y pantalla completa para proyectar (F11)")
        self.btn_exposicion.clicked.connect(self.alternar_exposicion)
        marco_expo = QHBoxLayout()
        marco_expo.setContentsMargins(14, 0, 14, 6)
        marco_expo.addWidget(self.btn_exposicion)
        v.addLayout(marco_expo)

        fila_ayuda = QHBoxLayout()
        fila_ayuda.setContentsMargins(14, 0, 14, 8)
        fila_ayuda.setSpacing(4)
        self.btn_ayuda = BotonAnimado("?  Ayuda", "fantasma", pequeno=True, borde=True)
        self.btn_ayuda.setToolTip("Atajos de teclado y recorrido guiado (F1)")
        self.btn_ayuda.clicked.connect(lambda: self.abrir_ayuda(0))
        self.btn_acerca = BotonAnimado("Acerca de", "fantasma", pequeno=True, borde=True)
        self.btn_acerca.clicked.connect(lambda: self.abrir_ayuda(1))
        fila_ayuda.addWidget(self.btn_ayuda)
        fila_ayuda.addWidget(self.btn_acerca)
        v.addLayout(fila_ayuda)

        pie = QLabel("MTM0120\nUniversidad Americana")
        pie.setStyleSheet("color: {}; font-size: 8pt; background: transparent;"
                          " padding-left: 24px;".format(T.MUTED))
        v.addWidget(pie)
        return barra

    def _mover_indicador(self, indice, animar=True):
        """Mueve la marca de selección junto al botón del índice dado."""
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
        """Coloca la marca de selección al mostrarse la ventana."""
        super().showEvent(e)
        self._mover_indicador(self.pila.currentIndex(), animar=False)

    def ir_a(self, clave):
        """Cambia a la sección identificada por 'clave'."""
        if clave not in self._claves:
            return
        i = self._claves.index(clave)
        self._pagina(clave)
        for k, b in enumerate(self.botones):
            b.blockSignals(True)
            b.setChecked(k == i)
            b.blockSignals(False)
            b._cambio(k == i)
        self._mover_indicador(i)
        self.pila.ir(i)


    def estado(self):
        """Devuelve la sección actual y el estado de las páginas que lo guardan."""
        d = {"pagina": self._claves[self.pila.currentIndex()]}
        for clave in ("solucionador", "matrices", "lu", "numerico"):
            if clave in self._paginas:
                d[clave] = self._paginas[clave].estado()
            elif clave in self._pendiente:
                d[clave] = self._pendiente[clave]
        return d

    def restaurar(self, d):
        """Restaura la sección y el estado de las páginas desde 'estado'."""
        if not isinstance(d, dict):
            return
        for clave in ("solucionador", "matrices", "lu", "numerico"):
            if clave in d:
                if clave in self._paginas:
                    self._paginas[clave].restaurar(d[clave])
                else:
                    self._pendiente[clave] = d[clave]
        pagina = d.get("pagina", "inicio")
        if pagina in self._claves:
            self._pagina(pagina)
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
        """Guarda el estado de las páginas y la geometría de la ventana."""
        persistencia.escribir("sesion", estado or self.estado())
        persistencia.escribir(
            "geometria", bytes(self.saveGeometry().toBase64()).decode())

    def closeEvent(self, e):
        """Guarda la sesión y cierra las ventanas de resultados al salir."""
        self._salir_de_exposicion()
        if not self._cambiando_tema:
            self._guardar_sesion()
            cerrar_ventanas_de_resultado()
        super().closeEvent(e)

    def alternar_tema(self):
        """Cambia entre claro y oscuro sin perder nada de lo escrito."""
        if self._cambiando_tema:
            return
        self._salir_de_exposicion()
        nuevo = "claro" if T.NOMBRE_TEMA == "oscuro" else "oscuro"
        if self._tour is not None:
            self._tour.terminar()
        cerrar_ventanas_de_resultado()
        estado = self.estado()
        geometria = self.saveGeometry()
        self._guardar_sesion(estado)

        self._cambiando_tema = True
        salida = QVariantAnimation(self)
        salida.setDuration(170)
        salida.setStartValue(1.0)
        salida.setEndValue(0.0)
        salida.setEasingCurve(QEasingCurve.InCubic)
        salida.valueChanged.connect(self.setWindowOpacity)
        salida.finished.connect(lambda: QTimer.singleShot(
            0, lambda: _rehacer_ventana(nuevo, estado, geometria, self)))
        salida.start()
        self._anim_salida = salida


    def abrir_ayuda(self, pestana=0):
        """Abre el diálogo de ayuda en la pestaña indicada."""
        d = DialogoAyuda(self, pestana)
        d.repetir_tour.connect(self.iniciar_tour)
        d.borrar_datos.connect(lambda: QTimer.singleShot(0, self.restablecer_todo))
        d.exec()

    def restablecer_todo(self):
        """Borra todo lo guardado y deja la calculadora como recién instalada."""
        if self._tour is not None:
            self._tour.terminar()
        cerrar_ventanas_de_resultado()
        persistencia.borrar_todo()
        T.aplicar("oscuro")
        T.poner_escala(1.0)
        app = QApplication.instance()
        app.setStyleSheet(T.hoja_de_estilos())

        nueva = VentanaPrincipal()
        nueva.show()
        app._ventana_principal = nueva

        self._cambiando_tema = True
        self.close()
        mostrar_aviso(nueva, "Calculadora restablecida a sus valores por defecto")

    def mostrar_tour_si_corresponde(self):
        """El recorrido se muestra solo la primera vez que se abre el programa."""
        if not persistencia.leer("tour_visto", False):
            QTimer.singleShot(800, self.iniciar_tour)

    def iniciar_tour(self):
        """Inicia el recorrido guiado por todas las secciones."""
        if self._tour is not None:
            return
        s, m, t = self.pagina_solucionador, self.pagina_matrices, self.pagina_teoremas
        lu = self.pagina_lu
        num = self.pagina_numerica
        pasos = [
            PasoTour("Menú lateral",
                     "Cambia de herramienta aquí o con Ctrl+1 … Ctrl+6. Al pie "
                     "tienes la letra, el tema, la ayuda (F1) y «Acerca de».",
                     lambda: self._barra, "inicio"),
            PasoTour("Inicio",
                     "Cuatro tarjetas llevan a cada herramienta. Al pasar el cursor "
                     "se iluminan; también puedes entrar con Ctrl+2 … Ctrl+6.",
                     lambda: self.pagina_inicio.tarjetas[0], "inicio"),
            PasoTour("Prueba un ejemplo",
                     "Carga un sistema ya armado y lo resuelve al instante: "
                     "con solución única, infinitas soluciones o sin solución.",
                     lambda: s.b_ej, "solucionador"),
            PasoTour("Tamaño del sistema",
                     "Elige cuántas ecuaciones y variables tiene tu sistema y pulsa "
                     "«Generar cuadrícula». Solo la cuadrícula que cambia se anima.",
                     lambda: s.tarjeta_tamano),
            PasoTour("Escribe tu sistema",
                     "Acepta enteros, fracciones (3/4), decimales y raíces. "
                     "Enter baja de fila, Ctrl+V pega tablas de Excel y Ctrl+Z "
                     "deshace. Las celdas inválidas se ponen en rojo.",
                     lambda: s.tarjeta_cuadricula),
            PasoTour("Menú «Tabla»",
                     "Copia la matriz como tabla (para Excel) o como imagen "
                     "(para Word o PowerPoint) y pega tablas desde esos programas.",
                     lambda: s.tarjeta_cuadricula.btn_tabla),
            PasoTour("Qué incluir en el informe",
                     "Activa o quita la forma escalonada reducida (Gauss-Jordan) y "
                     "el análisis en Rⁿ (combinación lineal e independencia).",
                     lambda: s.sw_jordan),
            PasoTour("Resolver",
                     "Pulsa RESOLVER o usa Ctrl+Enter. Verás el proceso de "
                     "Gauss y Gauss-Jordan, la clasificación y la verificación. "
                     "Aquí se carga un ejemplo para que veas el resultado.",
                     lambda: s.btn_resolver, None, lambda: s.cargar_ejemplo(0)),
            PasoTour("Reproduce los pasos",
                     "Recorre el procedimiento a mano o en automático. La fila "
                     "que cambia en cada operación se resalta.",
                     lambda: s.b_play),
            PasoTour("Solución y verificación",
                     "Esta pestaña muestra la clasificación del sistema, la "
                     "solución general o particular y la verificación exacta.",
                     lambda: s.tabs.tabBar(), None, lambda: s.tabs.setCurrentIndex(1)),
            PasoTour("Informe en su propia ventana",
                     "Ábrelo aparte, con índice lateral, búsqueda (Ctrl+F), zoom y "
                     "barras de desplazamiento. También puedes copiarlo como imagen "
                     "o guardarlo en PDF.",
                     lambda: s.botones_informe["Abrir en ventana"], None,
                     lambda: s.tabs.setCurrentIndex(0)),
            PasoTour("Enviar a Operaciones",
                     "Pasa tu sistema [A | b] a Operaciones para calcular "
                     "determinantes, inversas o usar la Regla de Cramer.",
                     lambda: s.botones_informe["Enviar [A | b] a Operaciones"]),
            PasoTour("Tus matrices A, B y C",
                     "Escribe aquí las matrices. Cada una tiene su tamaño, deshacer y "
                     "rehacer, y el menú «Tabla». Con 1 columna trabajas con vectores.",
                     lambda: m.tarjetas["A"], "matrices"),
            PasoTour("Quitar, intercambiar y limpiar",
                     "«Quitar matriz B/C» la oculta (y la vuelve a agregar), "
                     "«Intercambiar» cambia A por B y «Limpiar» pone todo en cero.",
                     lambda: m.btn_toggle_B),
            PasoTour("Operaciones básicas",
                     "Suma, resta, producto, escalar y transpuesta. Activa «Mostrar "
                     "el paso a paso» para ver el desarrollo.",
                     lambda: m.botones_op["suma"], None, lambda: m.tabs.setCurrentIndex(0)),
            PasoTour("Determinante e inversa",
                     "Calcula det(A) por cofactores o por reducción triangular, y la "
                     "inversa por Gauss-Jordan o por la adjunta, con verificación.",
                     lambda: m.botones_op["det"]),
            PasoTour("Regla de Cramer",
                     "Resuelve A·x = b con determinantes. B debe ser el vector b "
                     "y A cuadrada con det(A) distinto de cero.",
                     lambda: m.btn_cramer),
            PasoTour("Propiedades",
                     "Verifica 31 propiedades con tus propias matrices: elige una "
                     "de la lista o pulsa «Verificar todas». Cada una dice si se cumple.",
                     lambda: m.combo_prop, "matrices", lambda: m.tabs.setCurrentIndex(1)),
            PasoTour("Resultado e informes",
                     "Aquí aparece el resultado. Puedes abrirlo en una ventana "
                     "aparte, copiarlo como texto o imagen, o guardarlo en PDF.",
                     lambda: m.tarjeta_resultado),
            PasoTour("Historial",
                     "Vuelve a cualquier resultado anterior sin recalcularlo, y úsalo "
                     "como A, B o C con los botones «Usar como».",
                     lambda: m.btn_historial),
            PasoTour("Factorización LU",
                     "Sección propia: escribe A y b, y obtén L, U, y y x. Resuelve "
                     "A·x = b en dos etapas y te avisa si hace falta permutar filas.",
                     lambda: lu.btn_lu, "lu"),
            PasoTour("LU: agrega L, U o x",
                     "Con «Agregar matriz L / U / vector x» ves cada resultado en su "
                     "propia tarjeta. Con L y U a la vista (sin A) calcula A = L·U.",
                     lambda: lu.btn_toggle["L"]),
            PasoTour("Métodos numéricos: bisección",
                     "Escribe f(x), el intervalo [a, b] y la tolerancia E. Verifica "
                     "el cambio de signo, calcula las iteraciones teóricas y "
                     "contrasta la raíz con SciPy.",
                     lambda: num.b_ej_a, "numerico",
                     lambda: (num.tabs.setCurrentIndex(0), num.cargar_ejemplo_a(0))),
            PasoTour("Tabla de iteraciones",
                     "La tabla a 6 decimales: i, xₗ, xᵤ, xᵣ, εₐ (%), f(xᵣ) y xᵤ − xₗ. "
                     "En «Informe paso a paso» se va construyendo fila por fila "
                     "y al final aparece completa.",
                     lambda: num.sub_a),
            PasoTour("Graficar la raíz",
                     "Manda la función al Graficador con la raíz aproximada y el "
                     "intervalo (inicial o final) marcados.",
                     lambda: num.btn_graf_raiz),
            PasoTour("Graficador, posicional y errores",
                     "Estas pestañas grafican funciones sin unir asíntotas, "
                     "descomponen enteros en base 10 y 2, y explican los errores "
                     "numéricos (0.1 + 0.2, épsilon, propagación).",
                     lambda: num.tabs.tabBar()),
            PasoTour("Teoremas: busca y filtra",
                     "Busca por nombre o enunciado (Ctrl+F) y filtra por categoría. "
                     "Lo encontrado sale resaltado y las coincidencias se abren solas.",
                     lambda: t.buscador, "teoremas"),
            PasoTour("Teoremas: ábrelos y úsalos",
                     "Pulsa una tarjeta para leerla. «Abrir en…» te lleva a la "
                     "herramienta y marca el botón exacto donde se usa.",
                     lambda: t.tarjetas[0][0], None, lambda: t.tarjetas[0][0].fijar(True)),
            PasoTour("Tamaño de letra",
                     "Agranda o reduce la letra de cuadrículas y resultados "
                     "(Ctrl++ / Ctrl+−; Ctrl+0 la restablece).",
                     lambda: self.grupo_escala, None, lambda: t.tarjetas[0][0].fijar(False)),
            PasoTour("Tema claro u oscuro",
                     "Cambia el aspecto cuando quieras. No pierdes nada de lo "
                     "que escribiste y el programa lo recuerda.",
                     lambda: self.btn_tema),
            PasoTour("Ayuda siempre a mano",
                     "Aquí están todos los atajos y puedes repetir este "
                     "recorrido cuando quieras. ¡Listo para empezar!",
                     lambda: self.btn_ayuda),
        ]
        self._estado_previo_tour = self.estado()
        self._tour = Tour(self, pasos, al_terminar=self._tour_terminado)


    def ir_y_mostrar(self, numero):
        """Lleva a la herramienta donde se usa el teorema y marca el botón exacto."""
        espec = especificacion_de_teorema(self, numero)
        if espec is None:
            return
        pagina, preparar, objetivo, texto = espec
        if self._guia is not None:
            self._guia.cerrar()
            self._guia = None
        self.ir_a(pagina)

        def mostrar():
            """Va a la sección, prepara la página y señala el elemento con la guía."""
            if preparar:
                preparar()
            QTimer.singleShot(140, lambda: self._poner_guia(objetivo, texto))

        QTimer.singleShot(560, mostrar)

    def _poner_guia(self, objetivo, texto):
        """Muestra la guía sobre el elemento si todavía existe."""
        try:
            widget = objetivo()
        except (KeyError, AttributeError):
            return
        if widget is None or not widget.isVisible():
            return
        self._guia = Guia(self, widget, texto)

    def _tour_terminado(self):
        """Al terminar el recorrido restaura el estado previo, lo marca como visto y vuelve a Inicio."""
        self._tour = None
        previo, self._estado_previo_tour = getattr(self, "_estado_previo_tour", None), None
        if previo:
            self.restaurar(previo)
        persistencia.escribir("tour_visto", True)
        self.ir_a("inicio")

    def _crear_barra_de_estado(self):
        """Crea la barra de estado: mensajes a la izquierda y tema, letra y SciPy a la derecha."""
        barra = self.statusBar()
        barra.setSizeGripEnabled(False)
        barra.setStyleSheet(
            "QStatusBar {{ background: {p}; color: {m}; border-top: 1px solid {b}; }}"
            "QStatusBar::item {{ border: 0; }}".format(p=T.PANEL, m=T.MUTED, b=T.BORDE))
        self._lbl_estado = QLabel("")
        self._lbl_estado.setStyleSheet("background: transparent; padding-right: 10px;")
        barra.addPermanentWidget(self._lbl_estado)
        self._refrescar_estado()
        barra.showMessage("Listo", 4000)

    def _refrescar_estado(self):
        """Actualiza el resumen de la derecha de la barra de estado."""
        scipy = "disponible" if importlib.util.find_spec("scipy") else "no instalado"
        self._lbl_estado.setText("Tema {}  ·  Letra {}%  ·  SciPy {}".format(
            T.NOMBRE_TEMA, round(T.ESCALA * 100), scipy))

    def alternar_exposicion(self):
        """Entra o sale del modo exposición: pantalla completa, letra grande y sin barra lateral."""
        if not self._exposicion:
            self._exposicion = True
            self._escala_previa = T.ESCALA
            self._maximizada_previa = self.isMaximized()
            self._barra.hide()
            self.statusBar().hide()
            self._poner_escala(1.5, guardar=False)
            self.showFullScreen()
            mostrar_aviso(self, "Modo exposición · F11 o Esc para salir", "info")
        else:
            self._exposicion = False
            self._barra.show()
            self.statusBar().show()
            self._poner_escala(self._escala_previa, guardar=False)
            if self._maximizada_previa:
                self.showMaximized()
            else:
                self.showNormal()

    def _salir_de_exposicion(self):
        """Esc: sale del modo exposición si está activo."""
        if self._exposicion:
            self.alternar_exposicion()

    def _refrescar_escala(self):
        """Muestra el porcentaje de escala, animándolo cuando cambia."""
        nuevo = round(T.ESCALA * 100)
        actual = getattr(self, "_escala_mostrada", None)
        self._escala_mostrada = nuevo
        if actual is None or actual == nuevo or not self.isVisible():
            self.lbl_escala.setText("{}%".format(nuevo))
            return
        anim = QVariantAnimation(self)
        anim.setDuration(280)
        anim.setStartValue(actual)
        anim.setEndValue(nuevo)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(
            lambda v: self.lbl_escala.setText("{}%".format(round(v))))
        anim.finished.connect(
            lambda: self.lbl_escala.setText("{}%".format(nuevo)))
        anim.start()
        self._anim_escala = anim

    def _poner_escala(self, nuevo, guardar=True):
        """Aplica la escala de letra a todas las páginas; devuelve False si ya era esa."""
        if nuevo == T.ESCALA:
            return False
        T.poner_escala(nuevo)
        if guardar:
            persistencia.escribir("escala", nuevo)
        for clave in ("solucionador", "matrices", "lu", "numerico"):
            if clave in self._paginas:
                self._paginas[clave].aplicar_escala()
        self._refrescar_escala()
        self._refrescar_estado()
        return True

    def cambiar_escala(self, paso):
        """paso = +1 / -1 para subir o bajar un nivel; 0 para restablecer."""
        escalas = T.ESCALAS
        if paso == 0:
            nuevo = 1.0
        else:
            i = escalas.index(T.ESCALA) + paso
            nuevo = escalas[max(0, min(len(escalas) - 1, i))]
        if not self._poner_escala(nuevo):
            return
        mostrar_aviso(self, "Tamaño de letra: {}%".format(round(nuevo * 100)), "info")
