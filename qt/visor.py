# -*- coding: utf-8 -*-
"""
Ventana independiente para leer un resultado con comodidad: informe con colores y
matrices dibujadas, respuesta destacada arriba, índice lateral, búsqueda (Ctrl+F),
zoom (botones o Ctrl+rueda), ajuste de línea y barras de desplazamiento horizontal y
vertical. Se puede copiar y guardar (texto o PDF). Es una ventana propia, con su
botón en la barra de tareas; se cierra junto con la calculadora (ver cerrar_todas).
"""
import re

from PySide6.QtCore import QEasingCurve, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import (QColor, QKeySequence, QShortcut, QTextCursor,
                           QTextDocument)
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QTextEdit,
                               QVBoxLayout, QWidget)

from qt import render
from qt import tema as T
from qt.componentes import BotonAnimado, aparecer, mostrar_aviso
from qt.exportar import escribir_pdf
from qt.imagen import imagen_de_html, imagen_de_texto

# Referencias a las ventanas abiertas: evitan que Python las recolecte y
# permiten cerrarlas todas al salir de la calculadora.
_ABIERTAS = []

_TITULO_SECCION = re.compile(r"^--- (.+) ---$")
_TITULO_BLOQUE = re.compile(r"^=== (.+) ===$")
_PRIMER_PASO = re.compile(r"^(.+) — Paso 1 / (\d+)$")
_PROPIEDAD = re.compile(r"^PROPIEDAD(?: \d+)?:\s+(.+)$")
_RESULTADOS = re.compile(
    r"^\s*(Resultado final|Comprobación\s+(?:de|A)|Matriz aumentada inicial|Matriz [LU] |"
    r"Producto L|Regla de Cramer|Solución  x)")
# Líneas que se repiten muchas veces: en el índice se agrupan en una sola entrada
_GRUPOS = (
    (re.compile(r"^\s*Paso \d+:"), "Pasos"),
    (re.compile(r"^\s*── Cofactor"), "Cofactores"),
    (re.compile(r"^\s*── Variable"), "Variables"),
    (re.compile(r"^--- Pivote "), "Pivotes"),
)


def _legible(titulo):
    """«5. SOLUCIÓN» → «5. Solución» (solo si todo está en mayúsculas y no lleva fórmulas)."""
    if not titulo.isupper() or any(c in titulo for c in "=·()"):
        return titulo                          # con fórmulas no se tocan las mayúsculas
    return re.sub(r"[^\W\d_]", lambda m: m.group(0).upper(), titulo.lower(), count=1)


def cerrar_todas():
    """Cierra todas las ventanas de resultado abiertas."""
    for ventana in list(_ABIERTAS):
        ventana.close()


class _Lector(QTextEdit):
    """Área de lectura: Ctrl+rueda cambia el tamaño de letra."""

    zoom = Signal(int)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            self.zoom.emit(1 if e.angleDelta().y() > 0 else -1)
            e.accept()
            return
        super().wheelEvent(e)


class VisorTexto(QWidget):

    def __init__(self, titulo, texto, nombre_base="informe", cuerpo_pdf=None,
                 resumen=None):
        # Sin padre: ventana de primer nivel con su propio botón en la barra de tareas
        super().__init__(None)
        self.setWindowTitle(titulo)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(1100, 740)
        self.setMinimumSize(900, 380)
        self._titulo = titulo
        self._texto = texto.strip()
        self._nombre_base = nombre_base
        self._cuerpo_pdf = cuerpo_pdf
        self._resumen = resumen
        self._tam = 13
        self._ajustar = False
        self._entradas = []              # (nombre, número de bloque) del índice
        self._posiciones = []            # posición vertical de cada entrada

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(16, 14, 16, 16)
        raiz.setSpacing(10)

        barra = QHBoxLayout()
        barra.addStretch(1)       # el título ya está en la barra de la ventana
        self.btn_indice = BotonAnimado("Índice", "suave", pequeno=True)
        self.btn_indice.setToolTip("Mostrar u ocultar el índice de secciones")
        self.btn_indice.clicked.connect(self._alternar_indice)
        barra.addWidget(self.btn_indice)
        buscar = BotonAnimado("Buscar", "suave", pequeno=True)
        buscar.setToolTip("Buscar en el informe (Ctrl+F)")
        buscar.clicked.connect(self._abrir_busqueda)
        barra.addWidget(buscar)
        self.btn_ajuste = BotonAnimado("Líneas", "suave", pequeno=True)
        self.btn_ajuste.setToolTip(
            "Parte las líneas largas al ancho de la ventana; si no, se usa la barra horizontal")
        self.btn_ajuste.clicked.connect(self._alternar_ajuste)
        barra.addWidget(self.btn_ajuste)
        ancho = BotonAnimado("Ancho", "suave", pequeno=True)
        ancho.setToolTip("Ajustar al ancho: elige la letra más grande con la que todo cabe a lo ancho")
        ancho.clicked.connect(self._ajustar_al_ancho)
        barra.addWidget(ancho)
        for texto_b, cmd in (("A−", lambda: self._zoom(-1)),
                             ("A+", lambda: self._zoom(1))):
            b = BotonAnimado(texto_b, "suave", pequeno=True)
            b.clicked.connect(cmd)
            barra.addWidget(b)
        copiar = BotonAnimado("Copiar", "suave", pequeno=True)
        copiar.con_menu([("Copiar como texto", self._copiar),
                         ("Copiar como imagen", self._copiar_imagen)])
        barra.addWidget(copiar)
        guardar = BotonAnimado("Guardar", "suave", pequeno=True)
        guardar.con_menu([("Texto (.txt)", self._guardar_texto),
                          ("PDF (.pdf)", self._guardar_pdf)])
        barra.addWidget(guardar)
        cerrar = BotonAnimado("Cerrar", "suave", pequeno=True)
        cerrar.clicked.connect(self.close)
        barra.addWidget(cerrar)
        raiz.addLayout(barra)

        # Barra de búsqueda (oculta hasta Ctrl+F)
        self.caja_busqueda = QFrame()
        fila = QHBoxLayout(self.caja_busqueda)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)
        self.ed_buscar = QLineEdit()
        self.ed_buscar.setPlaceholderText("Buscar en el informe…")
        self.ed_buscar.textChanged.connect(lambda _t: self._buscar(0, desde_inicio=True))
        self.ed_buscar.returnPressed.connect(lambda: self._buscar(1))
        fila.addWidget(self.ed_buscar, 1)
        self.lbl_cuenta = QLabel("")
        self.lbl_cuenta.setObjectName("nota")
        fila.addWidget(self.lbl_cuenta)
        for texto_b, sentido in (("▲", -1), ("▼", 1)):
            b = BotonAnimado(texto_b, "suave", pequeno=True)
            b.clicked.connect(lambda _=False, d=sentido: self._buscar(d))
            fila.addWidget(b)
        cerrar_b = BotonAnimado("✕", "suave", pequeno=True)
        cerrar_b.clicked.connect(self._cerrar_busqueda)
        fila.addWidget(cerrar_b)
        self.caja_busqueda.hide()
        raiz.addWidget(self.caja_busqueda)

        # Respuesta destacada
        self.tarjeta = QFrame()
        self.tarjeta.hide()
        raiz.addWidget(self.tarjeta)

        # Índice + lectura
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(10)
        self.indice = QListWidget()
        self.indice.setFixedWidth(230)
        self.indice.setWordWrap(True)
        self.indice.setFocusPolicy(Qt.NoFocus)
        self.indice.currentRowChanged.connect(self._ir_a_entrada)
        cuerpo.addWidget(self.indice)

        self.edit = _Lector()
        self.edit.setReadOnly(True)
        self.edit.setLineWrapMode(QTextEdit.NoWrap)
        self.edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.edit.zoom.connect(self._zoom)
        self.edit.verticalScrollBar().valueChanged.connect(self._marcar_entrada_activa)
        cuerpo.addWidget(self.edit, 1)
        raiz.addLayout(cuerpo, 1)

        self._pintar_tarjeta()
        self._mostrar()
        hay_indice = self.indice.count() >= 2
        self.btn_indice.setEnabled(hay_indice)
        self.indice.setVisible(hay_indice)

        QShortcut(QKeySequence("Esc"), self, activated=self._escape)
        QShortcut(QKeySequence("Ctrl++"), self, activated=lambda: self._zoom(1))
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self._zoom(1))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self._zoom(-1))
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._abrir_busqueda)
        QShortcut(QKeySequence("F3"), self, activated=lambda: self._buscar(1))
        QShortcut(QKeySequence("Shift+F3"), self, activated=lambda: self._buscar(-1))
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._guardar_texto)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self._guardar_pdf)

    # ── Contenido ────────────────────────────────────────────

    def _html(self):
        """HTML del informe con la paleta del tema, al tamaño y ajuste actuales."""
        paleta = T.paleta_de_imagen()
        with T.paleta_temporal(paleta):
            if self._cuerpo_pdf is not None:
                cuerpo = self._cuerpo_pdf(paleta)
            else:
                cuerpo = render.html_texto(self._texto)
            return render.pagina(cuerpo, tam=self._tam, ajustar=self._ajustar)

    def _mostrar(self):
        """(Re)dibuja el informe conservando el punto donde se estaba leyendo."""
        vb, hb = self.edit.verticalScrollBar(), self.edit.horizontalScrollBar()
        v, h = vb.value(), hb.value()
        self.edit.setLineWrapMode(QTextEdit.WidgetWidth if self._ajustar
                                  else QTextEdit.NoWrap)
        self.edit.setStyleSheet("QTextEdit {{ padding: 14px; border: 1px solid {};"
                                " background-color: {}; }}".format(T.SUPERF, T.FONDO))
        self.edit.setHtml(self._html())
        self._construir_indice()
        vb.setValue(v)
        hb.setValue(h)

    def _construir_indice(self):
        """
        Entradas del índice a partir de los títulos del informe: secciones «--- … ---»
        y «=== … ===», propiedades, pasos, resultados y comprobaciones. Las líneas
        que se repiten (pasos, cofactores…) se agrupan en una sola entrada.
        """
        doc = self.edit.document()
        entradas = [["Inicio", 0]]
        grupos = {}                       # nombre → [entrada, cantidad]
        bloque = doc.begin()
        while bloque.isValid():
            crudo = bloque.text()
            t = crudo.strip()
            numero = bloque.blockNumber()
            bloque = bloque.next()
            if not t:
                continue
            grupo = next((g for patron, g in _GRUPOS if patron.match(crudo)), None)
            if grupo:
                if grupo in grupos:
                    grupos[grupo][1] += 1
                else:
                    entradas.append([grupo, numero])
                    grupos[grupo] = [entradas[-1], 1]
                continue
            nombre = self._nombre_de_entrada(crudo, t)
            if nombre:
                entradas.append([nombre, numero])
        for nombre, (entrada, cantidad) in grupos.items():
            entrada[0] = "{} ({})".format(nombre, cantidad)

        self._entradas = entradas
        self.indice.blockSignals(True)
        self.indice.clear()
        for nombre, _ in entradas:
            self.indice.addItem(nombre)
        self.indice.blockSignals(False)
        self._posiciones = []
        QTimer.singleShot(0, self._medir_entradas)

    @staticmethod
    def _nombre_de_entrada(crudo, t):
        """Nombre que lleva la línea en el índice, o None si no es un título."""
        t = re.sub(r"\s{2,}", " ", t)              # los dobles espacios del texto plano
        m = _TITULO_SECCION.match(t) or _TITULO_BLOQUE.match(t)
        if m:
            return _legible(m.group(1).split(" (")[0])
        m = _PRIMER_PASO.match(t)
        if m:
            return "{}: {} pasos".format(m.group(1), m.group(2))
        m = _PROPIEDAD.match(t)
        if m:
            return m.group(1)
        if t == "RESUMEN DE PROPIEDADES":
            return "Resumen de propiedades"
        if t.startswith("PASO A PASO"):
            return "Paso a paso"
        if _RESULTADOS.match(crudo):
            return t.rstrip(":= ").strip()
        if not crudo[:1].isspace() and t.endswith("=") and len(t) < 40:
            return t.rstrip("= ").strip()         # «A⁻¹ (Gauss-Jordan) =», «x =», …
        return None

    def _medir_entradas(self):
        doc = self.edit.document()
        capa = doc.documentLayout()
        self._posiciones = []
        for _, numero in self._entradas:
            b = doc.findBlockByNumber(numero)
            self._posiciones.append(int(capa.blockBoundingRect(b).top()))
        self._marcar_entrada_activa()

    def _ir_a_entrada(self, fila):
        if 0 <= fila < len(self._posiciones):
            self.edit.verticalScrollBar().setValue(max(0, self._posiciones[fila] - 6))

    def _marcar_entrada_activa(self, *_):
        if not self._posiciones:
            return
        y = self.edit.verticalScrollBar().value() + 40
        activa = 0
        for i, pos in enumerate(self._posiciones):
            if pos <= y:
                activa = i
        self.indice.blockSignals(True)
        self.indice.setCurrentRow(activa)
        self.indice.blockSignals(False)

    # ── Respuesta destacada ──────────────────────────────────

    def _pintar_tarjeta(self):
        r = self._resumen
        if not r:
            return
        color = {"ok": T.VERDE, "error": T.ROJO}.get(r.get("estado"), T.NARANJA)
        self.tarjeta.setObjectName("tarjeta")
        self.tarjeta.setStyleSheet(
            "QFrame#tarjeta {{ background-color: {}; border: 1px solid {};"
            " border-left: 5px solid {}; border-radius: 8px; }}"
            " QFrame#tarjeta QLabel {{ background: transparent; border: none; }}".format(
                T.SUPERF, T.BORDE, color))
        lay = QHBoxLayout(self.tarjeta)
        lay.setContentsMargins(16, 10, 16, 10)
        izq = QVBoxLayout()
        izq.setSpacing(2)
        tipo = QLabel(r.get("tipo", ""))
        tipo.setStyleSheet("color: {}; font-size: 9pt;".format(T.MUTED))
        resp = QLabel(r.get("respuesta", ""))
        resp.setTextInteractionFlags(Qt.TextSelectableByMouse)
        resp.setWordWrap(True)
        resp.setStyleSheet("color: {}; font-family: '{}'; font-size: 15pt;"
                           " font-weight: 700;".format(T.TEXTO, T.MONO))
        izq.addWidget(tipo)
        izq.addWidget(resp)
        lay.addLayout(izq, 1)
        if r.get("insignia"):
            ins = QLabel(r["insignia"])
            ins.setStyleSheet("color: {}; font-weight: 700; font-size: 11pt;".format(color))
            lay.addWidget(ins, 0, Qt.AlignVCenter)
        self.tarjeta.show()

    # ── Índice, tamaño y ajuste ──────────────────────────────

    def _alternar_indice(self):
        self.indice.setVisible(not self.indice.isVisible())

    def _alternar_ajuste(self):
        self._ajustar = not self._ajustar
        self.btn_ajuste.setText("Sin partir" if self._ajustar else "Líneas")
        self._mostrar()

    def _zoom(self, d):
        nuevo = max(8, min(32, self._tam + d))
        if nuevo != self._tam:
            self._tam = nuevo
            self._mostrar()

    def _ajustar_al_ancho(self):
        """Busca el mayor tamaño de letra con el que no hace falta barra horizontal."""
        if self._ajustar:                       # con líneas partidas ya cabe siempre
            self._alternar_ajuste()
        util = self.edit.viewport().width() - 30
        for _ in range(3):
            ideal = self.edit.document().idealWidth()
            if ideal <= 0:
                break
            nuevo = int(max(8, min(32, self._tam * util / ideal)))
            if nuevo == self._tam:
                break
            self._tam = nuevo
            self._mostrar()
        mostrar_aviso(self, "Tamaño de letra: {} pt".format(self._tam))

    # ── Búsqueda ─────────────────────────────────────────────

    def _abrir_busqueda(self):
        self.caja_busqueda.show()
        self.ed_buscar.setFocus()
        self.ed_buscar.selectAll()

    def _cerrar_busqueda(self):
        self.caja_busqueda.hide()
        self.edit.setExtraSelections([])
        self.lbl_cuenta.setText("")
        self.edit.setFocus()

    def _escape(self):
        if self.caja_busqueda.isVisible():
            self._cerrar_busqueda()
        else:
            self.close()

    def _buscar(self, sentido, desde_inicio=False):
        """Resalta todas las coincidencias y salta a la siguiente (1) o anterior (-1)."""
        texto = self.ed_buscar.text()
        if not texto:
            self.edit.setExtraSelections([])
            self.lbl_cuenta.setText("")
            return
        doc = self.edit.document()
        resaltado = QColor(T.NARANJA)
        resaltado.setAlpha(110)
        seleccion = []
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(texto, cursor)
            if cursor.isNull():
                break
            extra = QTextEdit.ExtraSelection()
            extra.cursor = cursor
            extra.format.setBackground(resaltado)
            seleccion.append(extra)
        self.edit.setExtraSelections(seleccion)
        if not seleccion:
            self.lbl_cuenta.setText("Sin resultados")
            return

        if desde_inicio:
            hallado = doc.find(texto, QTextCursor(doc))
        else:
            opciones = (QTextDocument.FindBackward if sentido < 0
                        else QTextDocument.FindFlag(0))
            hallado = doc.find(texto, self.edit.textCursor(), opciones)
            if hallado.isNull():                 # da la vuelta al llegar al final
                borde = QTextCursor(doc)
                borde.movePosition(QTextCursor.End if sentido < 0 else QTextCursor.Start)
                hallado = doc.find(texto, borde, opciones)
        if not hallado.isNull():
            self.edit.setTextCursor(hallado)
            self.edit.ensureCursorVisible()
            numero = 1 + sum(1 for e in seleccion
                             if e.cursor.selectionStart() < hallado.selectionStart())
            self.lbl_cuenta.setText("{} de {}".format(numero, len(seleccion)))

    # ── Ventana ──────────────────────────────────────────────

    def showEvent(self, e):
        super().showEvent(e)
        aparecer(self.edit, 300)
        if not getattr(self, "_ya_aparecio", False):
            self._ya_aparecio = True
            self.setWindowOpacity(0.0)
            anim = QVariantAnimation(self)
            anim.setDuration(280)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.valueChanged.connect(self.setWindowOpacity)
            anim.start()
            self._anim_ventana = anim

    def closeEvent(self, e):
        if self in _ABIERTAS:
            _ABIERTAS.remove(self)
        super().closeEvent(e)

    # ── Copiar y guardar ─────────────────────────────────────

    def _copiar(self):
        QApplication.clipboard().setText(self._texto)
        mostrar_aviso(self, "Copiado al portapapeles")

    def _copiar_imagen(self):
        paleta = T.paleta_de_imagen()
        if self._cuerpo_pdf is not None:
            imagen = imagen_de_html(self._cuerpo_pdf(paleta), paleta)
        else:
            imagen = imagen_de_texto(self._texto, paleta)
        QApplication.clipboard().setImage(imagen)
        mostrar_aviso(self, "Copiado como imagen")

    def _guardar_texto(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", self._nombre_base + ".txt",
            "Texto (*.txt);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._texto + "\n")
            mostrar_aviso(self, "Informe guardado")
        except OSError as ex:
            mostrar_aviso(self, "No se pudo guardar: {}".format(ex), "error")

    def _guardar_pdf(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar como PDF", self._nombre_base + ".pdf", "PDF (*.pdf)")
        if not ruta:
            return
        try:
            if self._cuerpo_pdf is not None:
                cuerpo = self._cuerpo_pdf()
            else:
                with T.paleta_temporal("impreso"):
                    cuerpo = render.html_texto(self._texto)
            escribir_pdf(ruta, self._titulo, cuerpo)
            mostrar_aviso(self, "PDF guardado")
        except OSError as ex:
            mostrar_aviso(self, "No se pudo guardar: {}".format(ex), "error")


def abrir_visor(titulo, texto, nombre_base="informe", cuerpo_pdf=None, resumen=None):
    """
    Abre el resultado en una ventana propia, junto a la última ventana activa.
    `cuerpo_pdf` (opcional) devuelve el HTML del informe; si falta, se usa el texto.
    `resumen` (opcional) es la respuesta destacada: dict con tipo, respuesta,
    estado ("ok", "error" o nada) e insignia.
    """
    if not texto or not texto.strip():
        return None
    v = VisorTexto(titulo, texto, nombre_base, cuerpo_pdf, resumen)
    activa = QApplication.activeWindow()
    if activa is not None:
        # Cada ventana nueva se desplaza un poco para que no queden idénticas
        v.move(activa.x() + 40 + 28 * len(_ABIERTAS),
               activa.y() + 40 + 28 * len(_ABIERTAS))
    _ABIERTAS.append(v)
    v.show()
    return v
