# -*- coding: utf-8 -*-
"""
Métodos Numéricos (Programa 7): A) Bisección, B) Graficador de funciones,
C) Notación posicional en base 10 y base 2, D) Errores numéricos.
Unidad: Programa 7: Métodos Numéricos.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import datetime
import functools
import time

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QMenu,
                               QFileDialog, QFrame, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QPlainTextEdit, QScrollArea,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from core.evaluador import ErrorFuncion, compilar
from core.formato import subindices_numericos
from modulos import modulo_numerico as N

from qt import autocompletar, render
from qt import tema as T
from qt.componentes import (BotonAnimado, Interruptor, PestanasAnimadas, Tarjeta,
                            aparecer, mostrar_aviso)
from qt.ejemplos import (EJEMPLOS_BISECCION, EJEMPLOS_GRAFICA,
                         EJEMPLOS_POSICIONAL)
from qt.exportar import escribir_pdf
from qt.imagen import imagen_de_texto
from qt.pagina_base import PaginaBase
from qt.teclado import TecladoFunciones
from qt.visor import abrir_visor


def _etiqueta(texto):
    """Crea una etiqueta pequeña de nota con el texto dado."""
    rotulo = QLabel(texto)
    rotulo.setObjectName("nota")
    return rotulo


def _medido(descripcion):
    """Decorador: tras ejecutar el método muestra en la barra de estado cuánto tardó."""
    def decorador(metodo):
        """Envuelve el método con la medición del tiempo."""
        @functools.wraps(metodo)
        def interno(self, *args, **kwargs):
            """Ejecuta el método y publica la duración en milisegundos."""
            t0 = time.perf_counter()
            resultado = metodo(self, *args, **kwargs)
            self.estado_barra("{} en {:.0f} ms".format(
                descripcion, (time.perf_counter() - t0) * 1000))
            return resultado
        return interno
    return decorador


def _campo(texto="", marcador="", ancho=None):
    """Crea un campo de texto con valor inicial, texto de ejemplo y ancho opcional."""
    c = QLineEdit(texto)
    c.setPlaceholderText(marcador)
    if ancho:
        c.setMaximumWidth(ancho)
    c.textChanged.connect(lambda _=None, w=c: _marcar(w, False))
    return c


def _marcar(campo, malo):
    """Marca o desmarca el campo en rojo como erróneo."""
    if bool(campo.property("error")) == malo:
        return
    campo.setProperty("error", malo)
    campo.style().unpolish(campo)
    campo.style().polish(campo)


def _con_etiqueta(texto, campo):
    """Coloca una etiqueta sobre el widget en una columna."""
    col = QVBoxLayout()
    col.setSpacing(3)
    col.addWidget(_etiqueta(texto))
    col.addWidget(campo)
    return col


class TarjetaInforme(Tarjeta):
    """Informe en texto con guardar, abrir en ventana y copiar."""

    def __init__(self, pagina, titulo, nombre_base, color=None):
        """Crea la tarjeta de resultado con su título y las acciones de copiar, abrir y guardar."""
        super().__init__("Resultado", color)
        self._pagina = pagina
        self._titulo = titulo
        self._nombre = nombre_base
        self.texto = ""
        self.etiqueta = ""
        self.resumen = None
        self.historial = []

        acc = QHBoxLayout()
        acc.setSpacing(5)
        b_guardar = BotonAnimado("Guardar informe", "suave", pequeno=True)
        b_guardar.con_menu([("Texto (.txt)", self.guardar_txt),
                            ("PDF (.pdf)", self.guardar_pdf)])
        acc.addWidget(b_guardar)
        b_abrir = BotonAnimado("Abrir en ventana", "suave", pequeno=True)
        b_abrir.clicked.connect(self.abrir)
        acc.addWidget(b_abrir)
        b_copiar = BotonAnimado("Copiar", "suave", pequeno=True)
        b_copiar.con_menu([("Copiar como texto", self.copiar),
                           ("Copiar como imagen", self.copiar_imagen)])
        acc.addWidget(b_copiar)
        self.btn_historial = BotonAnimado("Historial", "suave", pequeno=True)
        self.btn_historial.clicked.connect(self._menu_historial)
        acc.addWidget(self.btn_historial)
        acc.addStretch(1)
        self.agregar_layout(acc)

        self.txt = QPlainTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.txt.setPlaceholderText("El resultado aparecerá aquí.")
        self.estilo()
        self.agregar(self.txt, 1)

    def estilo(self):
        """Aplica al informe la fuente monoespaciada y el tamaño de letra actuales."""
        self.txt.setStyleSheet("font-family: '{}'; font-size: {}pt;".format(
            T.MONO, T.tam(11)))

    def poner(self, texto, etiqueta="", registrar=True, pulso=True, resumen=None):
        """Muestra el informe, lo registra en el historial y guarda su resumen de respuesta."""
        self.resumen = resumen
        texto = N.ajustar(subindices_numericos(texto))
        self.texto = texto.strip()
        self.etiqueta = etiqueta
        self.txt.setPlainText(("\n" + texto + "\n") if texto else "")
        self.txt.moveCursor(QTextCursor.Start)
        if texto:
            aparecer(self.txt, 240, color=T.PANEL)
            if pulso:
                self.pulso(T.AZUL)
        if texto and etiqueta and registrar:
            self.historial.insert(0, {
                "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                "etiqueta": etiqueta, "texto": texto})
            del self.historial[40:]

    def _menu_historial(self):
        """Despliega el menú con los informes anteriores."""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        if not self.historial:
            menu.addAction("Todavía no hay resultados").setEnabled(False)
        else:
            for i, e in enumerate(self.historial):
                menu.addAction("{}  ·  {}".format(e["hora"], e["etiqueta"]),
                               lambda _=False, k=i: self.poner(
                                   self.historial[k]["texto"],
                                   self.historial[k]["etiqueta"], False))
            menu.addSeparator()
            menu.addAction("Borrar historial", self.historial.clear)
        b = self.btn_historial
        menu.exec(b.mapToGlobal(QPoint(0, b.height() + 4)))

    def _vacio(self):
        """Avisa y devuelve True si todavía no hay informe."""
        if not self.texto:
            self._pagina.info("Sin resultado", "Todavía no hay nada que mostrar.")
            return True
        return False

    def copiar(self):
        """Copia el informe al portapapeles como texto."""
        if self._vacio():
            return
        QApplication.clipboard().setText(self.texto)
        mostrar_aviso(self._pagina, "Resultado copiado al portapapeles")

    def copiar_imagen(self):
        """Copia el informe al portapapeles como imagen."""
        if self._vacio():
            return
        QApplication.clipboard().setImage(imagen_de_texto(self.texto))
        mostrar_aviso(self._pagina, "Resultado copiado como imagen")

    def abrir(self):
        """Abre el informe en la ventana de resultados con índice y colores."""
        if self._vacio():
            return
        abrir_visor(self._titulo, self.texto, self._nombre, resumen=self.resumen)

    def guardar_txt(self):
        """Pide una ruta y guarda el informe como texto."""
        if self._vacio():
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", self._nombre + ".txt",
            "Texto (*.txt);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.texto + "\n")
            mostrar_aviso(self._pagina, "Informe guardado")
        except OSError as ex:
            self._pagina.error("Error al guardar", str(ex))

    def guardar_pdf(self):
        """Pide una ruta y guarda el informe como PDF."""
        if self._vacio():
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", self._nombre + ".pdf", "PDF (*.pdf)")
        if not ruta:
            return
        try:
            with T.paleta_temporal("impreso"):
                cuerpo = render.html_texto(self.texto)
            escribir_pdf(ruta, self._titulo, cuerpo)
            mostrar_aviso(self._pagina, "PDF guardado")
        except OSError as ex:
            self._pagina.error("Error al guardar", str(ex))




class PaginaNumerica(PaginaBase):

    """Sección de métodos numéricos: bisección, graficador, notación posicional y errores."""
    def __init__(self, ventana):
        """Construye las cuatro pestañas y la barra de atajos."""
        super().__init__(ventana, "Métodos Numéricos",
                         "Bisección  ·  Graficador de funciones  ·  Notación "
                         "posicional  ·  Errores numéricos")
        self._res_a = None
        self._raiz_marcada = None
        self._grafica_hecha = False
        self._fijado = None
        self._deshacer = None

        self.tabs = PestanasAnimadas(T.FONDO)
        self.tabs.addTab(self._tab_biseccion(), "A · Bisección")
        self.tabs.addTab(self._tab_grafica(), "B · Graficador")
        self.tabs.addTab(self._tab_posicional(), "C · Notación posicional")
        self.tabs.addTab(self._tab_errores(), "D · Errores numéricos")
        self.tabs.currentChanged.connect(self.ocultar_error)
        self.raiz.addWidget(self.tabs, 1)
        self._conectar_enter()

        self.atajo("Ctrl+Return", self.calcular_actual)
        self.atajo("Ctrl+L", self.limpiar_actual)
        self.atajo("Ctrl+Shift+Z", self.deshacer_limpieza)
        self.atajo("Ctrl+G", self._graficar_raiz_si_hay)
        self.atajo("Ctrl+S", lambda: self._informe_actual().guardar_txt())
        self.atajo("Ctrl+P", lambda: self._informe_actual().guardar_pdf())

    @staticmethod
    def _panel_izq(ancho_max=370):
        """Crea el panel izquierdo de una pestaña y devuelve (panel, layout)."""
        w = QWidget()
        w.setMinimumWidth(290)
        w.setMaximumWidth(ancho_max)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(10)
        return w, lay

    @staticmethod
    def _con_desplazo(w):
        """Envuelve el widget en un área con desplazamiento sin marco."""
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(w)
        area.setMinimumWidth(w.minimumWidth() + 24)
        area.setMaximumWidth(w.maximumWidth() + 24)
        return area

    def _informe_actual(self):
        """Tarjeta de informe de la pestaña actual."""
        i = self.tabs.currentIndex()
        return {0: self.inf_a, 1: self.inf_a, 2: self.inf_c, 3: self.inf_d}[i]

    def calcular_actual(self):
        """Ejecuta la acción principal de la pestaña actual (Ctrl+Enter)."""
        {0: self.calcular_biseccion, 1: self.graficar, 2: self.descomponer,
         3: self.informe_completo}[self.tabs.currentIndex()]()

    def limpiar_actual(self):
        """Limpia los campos de la pestaña actual (se puede deshacer)."""
        self._limpiable({0: self.limpiar_a, 1: self.limpiar_b, 2: self.limpiar_c,
                         3: self.limpiar_d}[self.tabs.currentIndex()])()

    def _limpiable(self, limpiar):
        """Devuelve una acción que limpia con `limpiar` guardando antes lo escrito para deshacer."""
        def accion():
            """Guarda el estado, limpia y avisa de cómo recuperarlo."""
            anterior = self.estado()
            limpiar()
            self._deshacer = anterior
            mostrar_aviso(self, "Se limpió la pestaña · Ctrl+Shift+Z para deshacer", "info")
        return accion

    def deshacer_limpieza(self):
        """Recupera lo que había antes de la última limpieza."""
        if self._deshacer is None:
            return
        anterior, self._deshacer = self._deshacer, None
        self.restaurar(anterior)
        mostrar_aviso(self, "Datos recuperados")

    def _conectar_enter(self):
        """Enter en cualquier campo calcula la pestaña; activa también el autocompletado de f(x)."""
        for campo in (self.f_a, self.a_a, self.b_b, self.e_a, self.n_a):
            autocompletar.al_pulsar_enter(campo, self.calcular_biseccion)
        for campo in (self.f_b, self.xmin_b, self.xmax_b):
            autocompletar.al_pulsar_enter(campo, self.graficar)
        for campo in (self.xv_d, self.xa_d):
            autocompletar.al_pulsar_enter(campo, self.ver_errores)
        for campo in (self.x_d, self.dx_d):
            autocompletar.al_pulsar_enter(campo, self.ver_propagacion)
        for campo in (self.f_a, self.f_b):
            autocompletar.instalar(campo)

    def _graficar_raiz_si_hay(self):
        """Ctrl+G: grafica la raíz de la bisección si ya se calculó."""
        if self.btn_graf_raiz.isEnabled():
            self.graficar_raiz()

    def _fila_tab(self, izq, der):
        """Crea el contenedor horizontal de una pestaña."""
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(12)
        lay.addWidget(izq)
        lay.addWidget(der, 1)
        return w

    def _tab_biseccion(self):
        """Construye la pestaña A: datos, ejemplos, tabla de iteraciones e informe."""
        izq, lay = self._panel_izq()
        self.b_ej_a = BotonAnimado("Probar un ejemplo", "azul")
        self.b_ej_a.con_menu([(e["nombre"], lambda _=False, i=i: self.cargar_ejemplo_a(i))
                              for i, e in enumerate(EJEMPLOS_BISECCION)])
        lay.addWidget(self.b_ej_a)

        t = self.tarjeta_datos_a = Tarjeta("Datos del método")
        self.f_a = _campo("x**3 - 2*x - 5", "f(x), por ejemplo x**3 - 2*x - 5")
        t.agregar_layout(_con_etiqueta("Función f(x)", self.f_a))
        self.teclado_a = TecladoFunciones(self.f_a)
        t.agregar(self.teclado_a)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.a_a, self.b_b = _campo("", "2"), _campo("", "3")
        fila.addLayout(_con_etiqueta("Extremo inferior a (xₗ)", self.a_a))
        fila.addLayout(_con_etiqueta("Extremo superior b (xᵤ)", self.b_b))
        t.agregar_layout(fila)
        fila2 = QHBoxLayout()
        fila2.setSpacing(8)
        self.e_a, self.n_a = _campo("0.0001", "0.0001"), _campo("100", "100")
        fila2.addLayout(_con_etiqueta("Tolerancia E > 0", self.e_a))
        fila2.addLayout(_con_etiqueta("Iteraciones máx.", self.n_a))
        t.agregar_layout(fila2)
        self.sw_scipy = Interruptor("Contrastar la raíz con SciPy", True)
        self.sw_scipy.setToolTip(
            "Calcula la misma raíz con SciPy (bisect y brentq) y la compara con la tuya.\n"
            "Solo sirve para verificar: no cambia tu resultado ni la tabla.")
        t.agregar(self.sw_scipy)
        aviso_scipy = _etiqueta("Activado: además de tu bisección se calcula la raíz con SciPy "
                                "y el informe las compara (diferencia frente a Eᵦ). "
                                "No cambia tu resultado.")
        aviso_scipy.setWordWrap(True)
        t.agregar(aviso_scipy)
        self.sw_ext = Interruptor("Tabla completa (f(xₗ), f(xᵤ) y Eᵦ)", False)
        self.sw_ext.setToolTip(
            "Añade a la tabla f(xₗ), f(xᵤ) y Eᵦ, como pide la Tarea 7.\n"
            "Desactivado: tabla básica (i, xₗ, xᵤ, xᵣ, εₐ, f(xᵣ) y xᵤ − xₗ).")
        self.sw_ext.toggled.connect(self._cambiar_tabla)
        t.agregar(self.sw_ext)
        n = _etiqueta("Potencia: ** o ^.  Constantes: pi, e.  Funciones: sin, cos, "
                      "tan, exp, log (ln), sqrt, abs… También se acepta 2x.")
        n.setWordWrap(True)
        t.agregar(n)
        lay.addWidget(t)

        self.btn_calc_a = BotonAnimado("Calcular bisección", "verde")
        self.btn_calc_a.clicked.connect(self.calcular_biseccion)
        lay.addWidget(self.btn_calc_a)
        self.btn_graf_raiz = BotonAnimado("Graficar esta raíz", "azul")
        self.btn_graf_raiz.clicked.connect(self.graficar_raiz)
        self.btn_graf_raiz.setEnabled(False)
        lay.addWidget(self.btn_graf_raiz)
        self.btn_fijar = BotonAnimado("Fijar para comparar", "suave")
        self.btn_fijar.setToolTip("Guarda este resultado para compararlo con el siguiente "
                                  "(por ejemplo, al cambiar la tolerancia).")
        self.btn_fijar.clicked.connect(self.fijar_comparacion)
        lay.addWidget(self.btn_fijar)
        b = BotonAnimado("Limpiar", "suave")
        b.clicked.connect(self._limpiable(self.limpiar_a))
        lay.addWidget(b)
        lay.addStretch(1)

        der = QWidget()
        dl = QVBoxLayout(der)
        dl.setContentsMargins(8, 0, 0, 0)
        dl.setSpacing(10)
        self.tarjeta_resumen_a = Tarjeta("Resumen")
        self.lbl_resumen_a = QLabel("Introduce los datos y pulsa «Calcular bisección».")
        self.lbl_resumen_a.setWordWrap(True)
        self.lbl_resumen_a.setTextFormat(Qt.RichText)
        self.lbl_resumen_a.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.tarjeta_resumen_a.agregar(self.lbl_resumen_a)
        dl.addWidget(self.tarjeta_resumen_a)

        self.sub_a = QTabWidget()
        self.tabla_a = QTableWidget(0, len(N.columnas()))
        self.tabla_a.setHorizontalHeaderLabels(N.columnas())
        self.tabla_a.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_a.setAlternatingRowColors(True)
        self.tabla_a.verticalHeader().setVisible(False)
        self.tabla_a.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_a.setFrameShape(QFrame.NoFrame)
        self.tabla_a.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_a.customContextMenuRequested.connect(self._menu_tabla)
        QShortcut(QKeySequence.Copy, self.tabla_a, context=Qt.WidgetShortcut,
                  activated=lambda: self._copiar_tabla(self.tabla_a.currentRow()))
        self._timer_tabla = QTimer(self)
        self._timer_tabla.timeout.connect(self._siguiente_fila)
        self._pendientes = []
        self._estilo_tabla()
        self.inf_a = TarjetaInforme(self, "Método de Bisección", "informe_biseccion",
                                    T.VERDE)
        self.sub_a.addTab(self.tabla_a, "Tabla de iteraciones")
        self.sub_a.addTab(self.inf_a, "Informe paso a paso")
        dl.addWidget(self.sub_a, 1)
        return self._fila_tab(self._con_desplazo(izq), der)

    def _estilo_tabla(self):
        """Aplica a la tabla de iteraciones los colores del tema."""
        t = self.tabla_a
        t.setStyleSheet(
            "QTableWidget {{ background: {p}; alternate-background-color: {f};"
            " color: {tx}; gridline-color: {b}; border: 0;"
            " font-family: '{mono}'; font-size: {tam}pt; }}"
            "QHeaderView::section {{ background: {s}; color: {tx}; border: 0;"
            " border-right: 1px solid {b}; padding: 6px; font-weight: 600; }}"
            .format(p=T.PANEL, f=T.FONDO, tx=T.TEXTO, b=T.BORDE, s=T.SUPERF,
                    mono=T.MONO, tam=T.tam(10)))
        t.verticalHeader().setDefaultSectionSize(int(T.tam(10) * 2.6))

    def cargar_ejemplo_a(self, i):
        """Carga en la pestaña A el ejemplo con el índice dado."""
        e = EJEMPLOS_BISECCION[i]
        self.f_a.setText(e["f"])
        self.a_a.setText(e["a"])
        self.b_b.setText(e["b"])
        self.e_a.setText(e["E"])
        self.n_a.setText(e["nmax"])
        self.calcular_biseccion()
        mostrar_aviso(self, "Ejemplo: {}. {}".format(e["nombre"], e["sugerencia"]),
                      "info")

    def _marcar_a(self, mensaje):
        """Pinta de rojo el campo culpable según el mensaje de error."""
        m = mensaje.lower()
        malos = []
        if "mal escrita" in m or "función" in m or "símbolo" in m or "escribe una" in m:
            malos.append(self.f_a)
        if "a < b" in m or "extremo inferior" in m:
            malos += [self.a_a, self.b_b]
        if "extremo superior" in m:
            malos.append(self.b_b)
        if "tolerancia debe" in m or "la tolerancia" in m:
            malos.append(self.e_a)
        if "iteraciones máximas" in m:
            malos.append(self.n_a)
        if "f(a)" in m:
            malos.append(self.a_a)
        if "f(b)" in m:
            malos.append(self.b_b)
        for c in malos:
            _marcar(c, True)

    @_medido("Bisección")
    def calcular_biseccion(self):
        """Valida los datos, ejecuta la bisección y llena la tabla y el informe."""
        self.ocultar_error()
        for c in (self.f_a, self.a_a, self.b_b, self.e_a, self.n_a):
            _marcar(c, False)
        r = N.biseccion(self.f_a.text(), self.a_a.text(), self.b_b.text(),
                        self.e_a.text(), self.n_a.text(),
                        self.sw_scipy.isChecked(), self.sw_ext.isChecked())
        self._res_a = r
        self.btn_graf_raiz.setEnabled(r["valido"] and r["raiz"] is not None)
        self._llenar_tabla(r["filas"], animar=True)
        self.inf_a.poner(r["informe"], "Bisección", pulso=r["valido"],
                         resumen=self._resumen_ventana_a(r))
        if not r["valido"]:
            self._marcar_a(r["mensaje"])
            self.error("Bisección", r["mensaje"])
            self._resumen_a(r)
            if r["informe"]:
                self.sub_a.setCurrentIndex(1)
            return
        self._resumen_a(r)
        self.sub_a.setCurrentIndex(0)
        self.tarjeta_resumen_a.pulso(T.VERDE if r["motivo"] != "maximo" else T.NARANJA)
        if r["motivo"] == "maximo":
            mostrar_aviso(self, "Se alcanzó el máximo de iteraciones sin cumplir "
                                "la tolerancia", "info")

    def _resumen_ventana_a(self, r):
        """Respuesta destacada de la ventana de resultado."""
        if not r["valido"]:
            return {"tipo": "Método de bisección", "respuesta": "No se pudo aplicar",
                    "estado": "error", "insignia": ""}
        ok = r["motivo"] != "maximo"
        return {"tipo": "Método de bisección  ·  f(x) = {}".format(r["funcion"]),
                "respuesta": "xr = {}".format(N.num(r["raiz"])),
                "estado": "ok" if ok else None,
                "insignia": ("✓ Tolerancia alcanzada" if r["motivo"] == "tolerancia"
                             else "✓ Raíz exacta" if r["motivo"] == "exacta"
                             else "⚠ Máximo de iteraciones")}

    def _resumen_a(self, r):
        """Muestra bajo la tabla la raíz, el motivo de parada y el contraste con SciPy."""
        if not r["valido"]:
            self.lbl_resumen_a.setText(
                "<span style='color:{}'><b>No se pudo aplicar el método.</b></span>"
                "<br>{}".format(T.ROJO, _html(r["mensaje"])))
            return
        color = T.VERDE if r["motivo"] != "maximo" else T.NARANJA
        partes = [
            "<span style='color:{c}; font-size:{t}pt'><b>xᵣ = {xr}</b></span>"
            .format(c=color, t=int(T.tam(14)), xr=N.num(r["raiz"])),
            "f(xᵣ) = {}".format(N.num_signo(r["f_raiz"])),
            "cota del error Eᵦ = {}".format(N.num(r["cota"])),
            "iteraciones: {} (teóricas: {})".format(r["n_real"], r["n_teorico"]),
        ]
        txt = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(partes)
        txt += "<br><span style='color:{}'>{}</span>".format(
            color, _html(r["mensaje"]))
        if r["scipy"] is not None:
            ok = r["dif_scipy"] <= r["cota"] * (1 + 1e-9) + 1e-12
            txt += ("<br><span style='color:{}'>SciPy: {} &nbsp;·&nbsp; diferencia "
                    "= {} {} Eᵦ</span>".format(
                        T.VERDE if ok else T.ROJO,
                        " · ".join("{} = {}".format(m["nombre"].split(".")[-1],
                                                    N.num(m["raiz"]))
                                   for m in r["scipy_metodos"]),
                        N.num(r["dif_scipy"]), "≤" if ok else ">"))
        if self._fijado is not None:
            fj = self._fijado
            dn = r["n_real"] - fj["n"]
            txt += ("<br><span style='color:{}'>Comparación · fijado: E = {} → {} iteraciones, "
                    "xᵣ = {} &nbsp;|&nbsp; actual: E = {} → {} iteraciones, xᵣ = {} "
                    "&nbsp;|&nbsp; {:+d} iteraciones, |Δxᵣ| = {}</span>".format(
                        T.AZUL, N.num(fj["E"]), fj["n"], N.num(fj["raiz"]),
                        N.num(r["E"]), r["n_real"], N.num(r["raiz"]), dn,
                        N.num(abs(r["raiz"] - fj["raiz"]))))
        for adv in r["advertencias"]:
            txt += "<br><span style='color:{}'>Aviso: {}</span>".format(
                T.NARANJA, _html(adv))
        self.lbl_resumen_a.setText(txt)

    def _menu_tabla(self, pos):
        """Menú de clic derecho de la tabla: copiar la fila o toda la tabla."""
        t = self.tabla_a
        fila = t.rowAt(pos.y())
        menu = QMenu(self)
        if fila >= 0:
            menu.addAction("Copiar fila", lambda: self._copiar_tabla(fila))
        if t.rowCount():
            menu.addAction("Copiar toda la tabla", lambda: self._copiar_tabla(-1))
        if not menu.isEmpty():
            menu.exec(t.viewport().mapToGlobal(pos))

    def _copiar_tabla(self, fila):
        """Copia al portapapeles una fila (o toda la tabla con -1) separada por tabuladores."""
        t = self.tabla_a
        if t.rowCount() == 0:
            return
        filas = range(t.rowCount()) if fila < 0 else [fila]
        lineas = []
        if fila < 0:
            lineas.append("\t".join(t.horizontalHeaderItem(c).text()
                                     for c in range(t.columnCount())))
        for f in filas:
            lineas.append("\t".join(t.item(f, c).text() for c in range(t.columnCount())))
        QApplication.clipboard().setText("\n".join(lineas))
        mostrar_aviso(self, "Copiado: pégalo en Excel o Word")

    def fijar_comparacion(self):
        """Guarda el resultado actual para compararlo con el siguiente, o quita la comparación."""
        r = self._res_a
        if self._fijado is not None:
            self._fijado = None
            self.btn_fijar.setText("Fijar para comparar")
        elif r and r["valido"] and r["raiz"] is not None:
            self._fijado = {"E": r["E"], "n": r["n_real"], "raiz": r["raiz"], "cota": r["cota"]}
            self.btn_fijar.setText("Quitar comparación")
            mostrar_aviso(self, "Resultado fijado: cambia los datos y vuelve a calcular", "info")
        else:
            mostrar_aviso(self, "Calcula primero la bisección", "info")
            return
        if r:
            self._resumen_a(r)

    def _llenar_tabla(self, filas, animar=False):
        """Pone las filas; con `animar` se van añadiendo una a una."""
        self._timer_tabla.stop()
        self.tabla_a.setRowCount(0)
        nombres = N.columnas(self.sw_ext.isChecked())
        self.tabla_a.setColumnCount(len(nombres))
        self.tabla_a.setHorizontalHeaderLabels(nombres)
        if not animar:
            self._pendientes = []
            for fi in filas:
                self._agregar_fila(fi)
            return
        self._pendientes = list(filas)
        self._timer_tabla.start(max(45, min(170, int(1700 / max(1, len(filas))))))
        self._siguiente_fila()

    def _siguiente_fila(self):
        """Agrega a la tabla la siguiente fila pendiente o detiene la animación."""
        if not self._pendientes:
            self._timer_tabla.stop()
            return
        self._agregar_fila(self._pendientes.pop(0))
        if not self._pendientes:
            self._timer_tabla.stop()

    def _agregar_fila(self, fi):
        """Inserta una fila de la bisección en la tabla con los colores de sus signos."""
        t = self.tabla_a
        r = t.rowCount()
        t.insertRow(r)
        verde, rojo = QColor(T.VERDE), QColor(T.ROJO)
        extendida = self.sw_ext.isChecked()
        nombres = N.columnas(extendida)
        for c, v in enumerate(N.valores_fila(fi, extendida)):
            it = QTableWidgetItem(v)
            it.setTextAlignment(Qt.AlignCenter if c == 0
                                else Qt.AlignRight | Qt.AlignVCenter)
            if nombres[c].startswith("f(") and v.startswith(("+", "\u2212")):
                it.setForeground(verde if v.startswith("+") else rojo)
            if c == 3:
                f = it.font()
                f.setBold(True)
                it.setFont(f)
            t.setItem(r, c, it)
        t.selectRow(r)
        t.scrollToBottom()

    def _cambiar_tabla(self, _marcado):
        """Al cambiar entre la tabla básica y la completa vuelve a calcular con los mismos datos."""
        if self._res_a is not None:
            self._recalcular_silencioso()
        else:
            self._llenar_tabla([])

    def limpiar_a(self):
        """Limpia la pestaña A: campos, tabla e informe."""
        for c in (self.f_a, self.a_a, self.b_b):
            c.clear()
            _marcar(c, False)
        self.e_a.setText("0.0001")
        self.n_a.setText("100")
        self._res_a = None
        self.tabla_a.setRowCount(0)
        self.inf_a.poner("")
        self.lbl_resumen_a.setText("Introduce los datos y pulsa «Calcular bisección».")
        self.btn_graf_raiz.setEnabled(False)
        self.ocultar_error()

    def _tab_grafica(self):
        """Construye la pestaña B: función, rango, ejemplos y gráfica."""
        from qt.grafica import Grafica
        izq, lay = self._panel_izq()
        b_ej = BotonAnimado("Probar un ejemplo", "azul")
        b_ej.con_menu([(e["nombre"], lambda _=False, i=i: self.cargar_ejemplo_b(i))
                       for i, e in enumerate(EJEMPLOS_GRAFICA)])
        lay.addWidget(b_ej)

        t = self.tarjeta_datos_b = Tarjeta("Función y rango")
        self.f_b = _campo("1/x", "f(x); varias separadas por «;»")
        t.agregar_layout(_con_etiqueta("Función f(x)", self.f_b))
        self.teclado_b = TecladoFunciones(self.f_b, con_punto_y_coma=True)
        t.agregar(self.teclado_b)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.xmin_b, self.xmax_b = _campo("-5", "-5"), _campo("5", "5")
        fila.addLayout(_con_etiqueta("x mínimo", self.xmin_b))
        fila.addLayout(_con_etiqueta("x máximo", self.xmax_b))
        t.agregar_layout(fila)
        n = _etiqueta("Admite lineales, polinomios, racionales, radicales, "
                      "exponenciales, logaritmos, trigonométricas y valor "
                      "absoluto. Se usan 2000 puntos y solo se grafica donde "
                      "f está definida; las asíntotas no se unen.")
        n.setWordWrap(True)
        t.agregar(n)
        lay.addWidget(t)

        self.btn_graf = BotonAnimado("Graficar", "verde")
        self.btn_graf.clicked.connect(self.graficar)
        lay.addWidget(self.btn_graf)

        self.tarjeta_raiz_b = Tarjeta("Raíz de la bisección", T.MORADO)
        self.lbl_raiz_b = _etiqueta("")
        self.lbl_raiz_b.setWordWrap(True)
        self.tarjeta_raiz_b.agregar(self.lbl_raiz_b)
        self.combo_int = QComboBox()
        self.combo_int.addItems(["Intervalo inicial [a, b]",
                                 "Intervalo final (última iteración)"])
        self.combo_int.currentIndexChanged.connect(lambda _: self._redibujar_b())
        self.tarjeta_raiz_b.agregar(self.combo_int)
        b_quitar = BotonAnimado("Quitar la raíz marcada", "suave", pequeno=True)
        b_quitar.clicked.connect(self.quitar_raiz)
        self.tarjeta_raiz_b.agregar(b_quitar)
        lay.addWidget(self.tarjeta_raiz_b)
        self.tarjeta_raiz_b.setVisible(False)

        fila_b = QHBoxLayout()
        fila_b.setSpacing(6)
        b_png = BotonAnimado("Guardar imagen", "suave", pequeno=True)
        b_png.clicked.connect(self.guardar_imagen)
        b_cop = BotonAnimado("Copiar imagen", "suave", pequeno=True)
        b_cop.clicked.connect(self.copiar_grafica)
        b_lim = BotonAnimado("Limpiar", "suave", pequeno=True)
        b_lim.clicked.connect(self._limpiable(self.limpiar_b))
        for b in (b_png, b_cop, b_lim):
            fila_b.addWidget(b)
        lay.addLayout(fila_b)
        b_ven = BotonAnimado("Abrir en ventana", "suave")
        b_ven.clicked.connect(self.abrir_ventana_b)
        lay.addWidget(b_ven)
        lay.addStretch(1)

        der = Tarjeta("Gráfica")
        self.grafica = Grafica()
        der.agregar(self.grafica, 1)
        self.lbl_resumen_b = _etiqueta("")
        self.lbl_resumen_b.setWordWrap(True)
        self.lbl_resumen_b.setTextInteractionFlags(Qt.TextSelectableByMouse)
        der.agregar(self.lbl_resumen_b)
        return self._fila_tab(self._con_desplazo(izq), der)

    def cargar_ejemplo_b(self, i):
        """Carga en la pestaña B el ejemplo con el índice dado."""
        e = EJEMPLOS_GRAFICA[i]
        self.f_b.setText(e["f"])
        self.xmin_b.setText(e["xmin"])
        self.xmax_b.setText(e["xmax"])
        self._raiz_marcada = None
        self.tarjeta_raiz_b.setVisible(False)
        self.graficar()
        mostrar_aviso(self, "Ejemplo: {}. {}".format(e["nombre"], e["sugerencia"]),
                      "info")

    @_medido("Gráfica")
    def graficar(self):
        """Valida la función y el rango, y dibuja la gráfica con animación."""
        self.ocultar_error()
        for c in (self.f_b, self.xmin_b, self.xmax_b):
            _marcar(c, False)
        d = N.preparar_grafica(self.f_b.text(), self.xmin_b.text(),
                               self.xmax_b.text())
        if not d["valido"]:
            m = d["mensaje"].lower()
            if "x mínimo" in m or "x máximo" in m or "intervalo" in m:
                _marcar(self.xmin_b, True)
                _marcar(self.xmax_b, True)
            else:
                _marcar(self.f_b, True)
            self.error("Graficador", d["mensaje"])
            return
        self._datos_b = d
        self._grafica_hecha = True
        self._redibujar_b(animar=True)
        self.lbl_resumen_b.setText(d["resumen"])

    def _marcas_b(self):
        """(raíz, intervalo) a marcar si la función es la de la bisección."""
        d = getattr(self, "_datos_b", None)
        rm = self._raiz_marcada
        if d is None or rm is None or not d["curvas"] or \
                not _misma(d["curvas"][0]["texto"], rm["f"]):
            return None, None
        inicial = self.combo_int.currentIndex() == 0
        a, b = (rm["a0"], rm["b0"]) if inicial else (rm["xl"], rm["xu"])
        return (rm["xr"], rm["fxr"]), (a, b, "inicial" if inicial else "final")

    def _redibujar_b(self, animar=False):
        """Redibuja la gráfica con la raíz o intervalo marcados, con o sin animación."""
        d = getattr(self, "_datos_b", None)
        if d is None:
            return
        raiz, intervalo = self._marcas_b()
        self.grafica.dibujar(d, raiz, intervalo, animar=animar)

    def abrir_ventana_b(self):
        """Abre la gráfica en una ventana grande."""
        d = getattr(self, "_datos_b", None)
        if not self._grafica_hecha or d is None:
            self.info("Sin gráfica", "Primero grafica una función.")
            return
        from qt.grafica import abrir_ventana_grafica
        raiz, intervalo = self._marcas_b()
        textos = " ; ".join(c["texto"] for c in d["curvas"])
        abrir_ventana_grafica("Gráfica — f(x) = {}".format(textos), d, raiz,
                              intervalo, d["resumen"])

    def graficar_raiz(self):
        """Grafica la función de la bisección marcando su raíz y su intervalo."""
        r = self._res_a
        if not r or not r["valido"] or r["raiz"] is None:
            return
        ult = r["filas"][-1] if r["filas"] else None
        self._raiz_marcada = {
            "f": r["funcion"], "xr": r["raiz"], "fxr": r["f_raiz"],
            "a0": r["a0"], "b0": r["b0"],
            "xl": ult["xl"] if ult else r["raiz"],
            "xu": ult["xu"] if ult else r["raiz"]}
        ancho = r["b0"] - r["a0"]
        self.f_b.setText(r["funcion"])
        self.xmin_b.setText("{:.6g}".format(r["a0"] - 0.3 * ancho))
        self.xmax_b.setText("{:.6g}".format(r["b0"] + 0.3 * ancho))
        self.lbl_raiz_b.setText("f(x) = {}\nraíz xᵣ = {}".format(
            r["funcion"], N.num(r["raiz"])))
        self.tarjeta_raiz_b.setVisible(True)
        self.tabs.setCurrentIndex(1)
        self.graficar()

    def quitar_raiz(self):
        """Quita de la gráfica la raíz marcada."""
        self._raiz_marcada = None
        self.tarjeta_raiz_b.setVisible(False)
        self._redibujar_b()

    def guardar_imagen(self):
        """Pide una ruta y guarda la gráfica como imagen."""
        if not self._grafica_hecha:
            self.info("Sin gráfica", "Primero grafica una función.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfica", "grafica.png",
            "Imagen PNG (*.png);;PDF (*.pdf);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            self.grafica.guardar(ruta)
            mostrar_aviso(self, "Gráfica guardada")
        except (OSError, ValueError) as ex:
            self.error("Error al guardar", str(ex))

    def copiar_grafica(self):
        """Copia la gráfica al portapapeles como imagen."""
        if not self._grafica_hecha:
            self.info("Sin gráfica", "Primero grafica una función.")
            return
        QApplication.clipboard().setImage(self.grafica.imagen())
        mostrar_aviso(self, "Gráfica copiada como imagen")

    def limpiar_b(self):
        """Limpia la pestaña B: campos y gráfica."""
        for c in (self.f_b, self.xmin_b, self.xmax_b):
            c.clear()
            _marcar(c, False)
        self._datos_b = None
        self._grafica_hecha = False
        self._raiz_marcada = None
        self.tarjeta_raiz_b.setVisible(False)
        self.grafica.vaciar()
        self.lbl_resumen_b.setText("")
        self.ocultar_error()

    def _tab_posicional(self):
        """Construye la pestaña C: descomposición posicional de un número."""
        izq, lay = self._panel_izq()
        b_ej = BotonAnimado("Probar un ejemplo", "azul")
        b_ej.con_menu([(e["nombre"], lambda _=False, i=i: self.cargar_ejemplo_c(i))
                       for i, e in enumerate(EJEMPLOS_POSICIONAL)])
        lay.addWidget(b_ej)

        t = Tarjeta("Número entero")
        self.num_c = _campo("", "84506")
        t.agregar_layout(_con_etiqueta("Número", self.num_c))
        self.base_c = QComboBox()
        self.base_c.addItems(["Base de origen 10 (decimal)",
                              "Base de origen 2 (binario)"])
        t.agregar_layout(_con_etiqueta("Base de origen", self.base_c))
        n = _etiqueta("Solo enteros. Si es negativo, el signo se conserva y la "
                      "descomposición se hace sobre el valor absoluto. El "
                      "resultado se da en la otra base (10 ↔ 2).")
        n.setWordWrap(True)
        t.agregar(n)
        lay.addWidget(t)
        self.btn_desc = BotonAnimado("Descomponer", "verde")
        self.btn_desc.clicked.connect(self.descomponer)
        lay.addWidget(self.btn_desc)
        b = BotonAnimado("Limpiar", "suave")
        b.clicked.connect(self._limpiable(self.limpiar_c))
        lay.addWidget(b)
        lay.addStretch(1)
        self.num_c.returnPressed.connect(self.descomponer)
        self.inf_c = TarjetaInforme(self, "Notación posicional", "informe_posicional",
                                    T.AZUL)
        return self._fila_tab(self._con_desplazo(izq), self.inf_c)

    def cargar_ejemplo_c(self, i):
        """Carga en la pestaña C el ejemplo con el índice dado."""
        e = EJEMPLOS_POSICIONAL[i]
        self.num_c.setText(e["numero"])
        self.base_c.setCurrentIndex(0 if e["base"] == 10 else 1)
        self.descomponer()

    @_medido("Notación posicional")
    def descomponer(self):
        """Descompone el número en su base (10 o 2) y muestra el procedimiento."""
        self.ocultar_error()
        _marcar(self.num_c, False)
        base = 10 if self.base_c.currentIndex() == 0 else 2
        r = N.descomponer(self.num_c.text(), base)
        if not r["informe"]:
            _marcar(self.num_c, True)
            self.error("Notación posicional", r["mensaje"])
            return
        v = abs(r["valor"])
        signo = "−" if r["valor"] < 0 else ""
        if base == 10:
            resp = "({}{}){} = ({}{}){}".format(signo, v, N._sub(10), signo,
                                                r["binario"], N._sub(2))
        else:
            resp = "({}{}){} = ({}{}){}".format(signo, r["binario"], N._sub(2),
                                                signo, v, N._sub(10))
        self.inf_c.poner(r["informe"], "({}){}".format(
            self.num_c.text().strip(), N._sub(base)),
            resumen={"tipo": "Notación posicional  ·  base {} → base {}".format(
                         base, 2 if base == 10 else 10),
                     "respuesta": resp, "estado": "ok",
                     "insignia": "✓ Equivalentes"})

    def limpiar_c(self):
        """Limpia la pestaña C: campo e informe."""
        self.num_c.clear()
        _marcar(self.num_c, False)
        self.inf_c.poner("")
        self.ocultar_error()

    def _tab_errores(self):
        """Construye la pestaña D: punto flotante, tipos de error, error absoluto y propagación."""
        izq, lay = self._panel_izq()

        t1 = Tarjeta("Punto flotante y tipos de error")
        self.btn_flotante = b1 = BotonAnimado("0.1 + 0.2, épsilon, overflow y underflow", "azul")
        b1.clicked.connect(self.ver_punto_flotante)
        t1.agregar(b1)
        self.btn_tipos = b2 = BotonAnimado("Tipos de error con ejemplos", "azul")
        b2.clicked.connect(self.ver_tipos)
        t1.agregar(b2)
        lay.addWidget(t1)

        t2 = self.tarjeta_err = Tarjeta("Error absoluto y relativo")
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.xv_d, self.xa_d = _campo("", "3.14159265"), _campo("", "3.14")
        fila.addLayout(_con_etiqueta("Valor verdadero xᵥ", self.xv_d))
        fila.addLayout(_con_etiqueta("Valor aproximado xₐ", self.xa_d))
        t2.agregar_layout(fila)
        self.btn_errores = b3 = BotonAnimado("Calcular errores", "verde")
        b3.clicked.connect(self.ver_errores)
        t2.agregar(b3)
        lay.addWidget(t2)

        t3 = self.tarjeta_prop = Tarjeta("Propagación del error")
        t3.agregar(_etiqueta("f(x) = sen(x) + x²   ·   f′(x) = cos(x) + 2x"))
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.x_d, self.dx_d = _campo("", "1"), _campo("", "0.1")
        fila.addLayout(_con_etiqueta("x", self.x_d))
        fila.addLayout(_con_etiqueta("Perturbación Δx", self.dx_d))
        t3.agregar_layout(fila)
        self.btn_propagacion = b4 = BotonAnimado("Calcular propagación", "verde")
        b4.clicked.connect(self.ver_propagacion)
        t3.agregar(b4)
        lay.addWidget(t3)

        b5 = BotonAnimado("Informe completo del módulo", "primario")
        b5.clicked.connect(self.informe_completo)
        lay.addWidget(b5)
        b6 = BotonAnimado("Limpiar", "suave")
        b6.clicked.connect(self._limpiable(self.limpiar_d))
        lay.addWidget(b6)
        lay.addStretch(1)
        self.inf_d = TarjetaInforme(self, "Errores numéricos", "informe_errores",
                                    T.NARANJA)
        return self._fila_tab(self._con_desplazo(izq), self.inf_d)

    def ver_punto_flotante(self):
        """Muestra el informe de representación en punto flotante."""
        self.ocultar_error()
        self.inf_d.poner(N.informe_punto_flotante(), "Punto flotante",
                         resumen=self._res_d("Punto flotante",
                                             "0.1 + 0.2 == 0.3  →  {}".format(
                                                 0.1 + 0.2 == 0.3),
                                             "ε = 2.22e−16"))

    def ver_tipos(self):
        """Muestra el informe de tipos de error."""
        self.ocultar_error()
        self.inf_d.poner(N.informe_tipos_error(), "Tipos de error",
                         resumen=self._res_d("Tipos de error",
                                             "6 tipos de error con ejemplo", ""))

    @staticmethod
    def _res_d(tipo, respuesta, insignia):
        """Arma el resumen de respuesta del visor para la pestaña D."""
        return {"tipo": tipo, "respuesta": respuesta, "estado": "ok",
                "insignia": insignia}

    def _errores(self):
        """Calcula error absoluto y relativo; devuelve (informe, respuesta) o None si hay error."""
        for c in (self.xv_d, self.xa_d):
            _marcar(c, False)
        r = N.calcular_errores(self.xv_d.text(), self.xa_d.text())
        if not r["valido"]:
            _marcar(self.xv_d if "xv" in r["mensaje"] else self.xa_d, True)
            self.error("Cálculo de errores", r["mensaje"])
            return None
        if r["Er"] is None:
            resp = "Eₐ = {}  ·  Eᵣ no definido (xᵥ = 0)".format(N.cif(r["Ea"]))
        else:
            resp = "Eₐ = {}  ·  Eᵣ = {} %".format(N.cif(r["Ea"]),
                                                  N.cif(r["Er"] * 100))
        return r["informe"], resp

    def ver_errores(self):
        """Muestra el informe de error absoluto y relativo."""
        self.ocultar_error()
        res = self._errores()
        if res:
            self.inf_d.poner(res[0], "Errores xᵥ/xₐ",
                             resumen=self._res_d("Error absoluto y relativo",
                                                 res[1], ""))

    def _propagacion(self):
        """Calcula la propagación del error; devuelve (informe, respuesta) o None si hay error."""
        for c in (self.x_d, self.dx_d):
            _marcar(c, False)
        r = N.propagacion_error(self.x_d.text(), self.dx_d.text())
        if not r["valido"]:
            _marcar(self.dx_d if "Δx" in r["mensaje"] else self.x_d, True)
            self.error("Propagación del error", r["mensaje"])
            return None
        resp = "Δy aprox. = {}  ·  Δy real = {}".format(N.cif(r["dy_aprox"]),
                                                        N.cif(r["dy_real"]))
        return r["informe"], resp

    def ver_propagacion(self):
        """Muestra el informe de propagación del error."""
        self.ocultar_error()
        res = self._propagacion()
        if res:
            self.inf_d.poner(res[0], "Propagación",
                             resumen=self._res_d("Propagación del error  ·  "
                                                 "f(x) = sen(x) + x²", res[1], ""))

    @_medido("Módulo D")
    def informe_completo(self):
        """Todo el módulo D; usa los valores de xv/xa y x/Δx si están escritos."""
        self.ocultar_error()
        partes = [N.informe_punto_flotante(), N.informe_tipos_error()]
        if self.xv_d.text().strip() or self.xa_d.text().strip():
            res = self._errores()
            if res is None:
                return
            partes.append(res[0])
        if self.x_d.text().strip() or self.dx_d.text().strip():
            res = self._propagacion()
            if res is None:
                return
            partes.append(res[0])
        self.inf_d.poner("\n\n".join(partes), "Módulo D completo",
                         resumen=self._res_d("Errores numéricos",
                                             "Informe completo del módulo D",
                                             "{} apartados".format(len(partes))))

    def limpiar_d(self):
        """Limpia los campos de la pestaña D."""
        for c in (self.xv_d, self.xa_d, self.x_d, self.dx_d):
            c.clear()
            _marcar(c, False)
        self.inf_d.poner("")
        self.ocultar_error()

    def estado(self):
        """Devuelve los campos de cada pestaña para guardar la sesión."""
        return {
            "pestana": self.tabs.currentIndex(),
            "a": [c.text() for c in (self.f_a, self.a_a, self.b_b, self.e_a, self.n_a)],
            "a_calculado": self._res_a is not None,
            "scipy": self.sw_scipy.isChecked(),
            "tabla_completa": self.sw_ext.isChecked(),
            "b": [c.text() for c in (self.f_b, self.xmin_b, self.xmax_b)],
            "b_hecho": self._grafica_hecha,
            "c": [self.num_c.text(), self.base_c.currentIndex()],
            "c_res": self.inf_c.texto,
            "d": [c.text() for c in (self.xv_d, self.xa_d, self.x_d, self.dx_d)],
            "d_res": self.inf_d.texto,
            "historiales": [self.inf_a.historial, self.inf_c.historial,
                            self.inf_d.historial],
        }

    def restaurar(self, d):
        """Restaura el estado guardado por 'estado'; ignora datos dañados."""
        try:
            for c, v in zip((self.f_a, self.a_a, self.b_b, self.e_a, self.n_a), d["a"]):
                c.setText(v)
            self.sw_scipy.setChecked(bool(d.get("scipy", True)))
            self.sw_ext.blockSignals(True)
            self.sw_ext.setChecked(bool(d.get("tabla_completa", False)))
            self.sw_ext.blockSignals(False)
            for c, v in zip((self.f_b, self.xmin_b, self.xmax_b), d["b"]):
                c.setText(v)
            self.num_c.setText(d["c"][0])
            self.base_c.setCurrentIndex(int(d["c"][1]))
            for c, v in zip((self.xv_d, self.xa_d, self.x_d, self.dx_d), d["d"]):
                c.setText(v)
            if d.get("c_res"):
                self.inf_c.poner(d["c_res"], registrar=False, pulso=False)
            if d.get("d_res"):
                self.inf_d.poner(d["d_res"], registrar=False, pulso=False)
            hs = d.get("historiales", [[], [], []])
            self.inf_a.historial, self.inf_c.historial, self.inf_d.historial = \
                [list(h)[:40] for h in hs]
            if d.get("a_calculado"):
                self._recalcular_silencioso()
            if d.get("b_hecho"):
                dd = N.preparar_grafica(self.f_b.text(), self.xmin_b.text(),
                                        self.xmax_b.text())
                if dd["valido"]:
                    self._datos_b = dd
                    self._grafica_hecha = True
                    self.grafica.dibujar(dd, animar=False)
                    self.lbl_resumen_b.setText(dd["resumen"])
            self.tabs.setCurrentIndex(int(d.get("pestana", 0)))
        except (KeyError, IndexError, TypeError, ValueError):
            pass

    def _recalcular_silencioso(self):
        """Recalcula la bisección con los campos restaurados sin mostrar avisos ni animar."""
        r = N.biseccion(self.f_a.text(), self.a_a.text(), self.b_b.text(),
                        self.e_a.text(), self.n_a.text(), self.sw_scipy.isChecked(),
                        self.sw_ext.isChecked())
        self._res_a = r
        self.btn_graf_raiz.setEnabled(r["valido"] and r["raiz"] is not None)
        self._llenar_tabla(r["filas"])
        self.inf_a.poner(r["informe"], registrar=False, pulso=False)
        self._resumen_a(r)

    def aplicar_escala(self):
        """Aplica el nuevo tamaño de letra a los informes y a la tabla."""
        for inf in (self.inf_a, self.inf_c, self.inf_d):
            inf.estilo()
        for teclado in (self.teclado_a, self.teclado_b):
            teclado.estilo()
        self._estilo_tabla()
        if self._res_a:
            self._llenar_tabla(self._res_a["filas"])


def _html(texto):
    """Escapa el texto para HTML y convierte los saltos de línea en <br>."""
    return (subindices_numericos(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br>"))


def _misma(a, b):
    """¿Son la misma función escrita de la misma forma (ignorando espacios)?"""
    try:
        return compilar(a).normalizado == compilar(b).normalizado
    except ErrorFuncion:
        return False
