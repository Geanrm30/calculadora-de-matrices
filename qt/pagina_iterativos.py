# -*- coding: utf-8 -*-
"""
Pestaña E de Métodos Numéricos (Programa 8): Jacobi y Gauss-Seidel para A·x = b.
Datos en cuadrículas, tablas de iteraciones animadas, gráfica del error por iteración,
comparación entre métodos e informe paso a paso.
Unidad: Programa 8: Métodos Numéricos Integrador (Jacobi y Gauss-Seidel).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog,
                               QFrame, QHBoxLayout, QHeaderView, QLabel, QSpinBox,
                               QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget)

from core.formato import subindices_numericos
from modulos import modulo_iterativo as M

from qt import tema as T
from qt.componentes import (BotonAnimado, CuadriculaMatriz, Interruptor, Tarjeta,
                            agregar_acciones_grid, mostrar_aviso)
from qt.ejemplos import EJEMPLOS_ITERATIVOS
from qt.grafica import GraficaError, VentanaGraficaError, abrir_ventana_grafica

LIMITE = 10
_CRITERIOS = ("norma2", "norma_inf", "ea_pct")
_NOMBRES_CRITERIO = ("Norma 2 (por defecto)", "Norma ∞", "Error relativo porcentual εₐ (%)")
_TOLERANCIA_DEFECTO = {"norma2": "0.0001", "norma_inf": "0.0001", "ea_pct": "0.05"}


def _html(texto):
    """Escapa el texto para HTML y convierte los saltos de línea en <br>."""
    return (subindices_numericos(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br>"))


def _nota(texto):
    """Etiqueta pequeña de nota con ajuste de línea."""
    rotulo = QLabel(texto)
    rotulo.setObjectName("nota")
    rotulo.setWordWrap(True)
    return rotulo


class TablaIteraciones(QTableWidget):
    """Tabla de iteraciones de un método: las filas aparecen una a una y la última se resalta."""

    def __init__(self, parent=None):
        """Crea la tabla vacía, de solo lectura, con el estilo del tema."""
        super().__init__(0, 0, parent)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setFrameShape(QFrame.NoFrame)
        self._cabecera = []
        self._pendientes = []
        self._color_final = T.VERDE
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._siguiente)
        self.estilo()

    def estilo(self):
        """Aplica a la tabla los colores y el tamaño de letra actuales."""
        self.setStyleSheet(
            "QTableWidget {{ background: {p}; alternate-background-color: {f};"
            " color: {tx}; gridline-color: {b}; border: 0;"
            " font-family: '{mono}'; font-size: {tam}pt; }}"
            "QHeaderView::section {{ background: {s}; color: {tx}; border: 0;"
            " border-right: 1px solid {b}; padding: 6px; font-weight: 600; }}"
            .format(p=T.PANEL, f=T.FONDO, tx=T.TEXTO, b=T.BORDE, s=T.SUPERF,
                    mono=T.MONO, tam=T.tam(10)))
        self.verticalHeader().setDefaultSectionSize(int(T.tam(10) * 2.6))

    def poner(self, cabecera, filas, convergio, animar):
        """Muestra las filas (listas de texto); con `animar` se van añadiendo una a una."""
        self._timer.stop()
        self._cabecera = list(cabecera)
        self._color_final = T.VERDE if convergio else T.ROJO
        self.setRowCount(0)
        self.setColumnCount(len(cabecera))
        self.setHorizontalHeaderLabels(cabecera)
        self._pendientes = list(filas)
        if not animar:
            while self._pendientes:
                self._siguiente()
            return
        self._timer.start(max(40, min(160, int(1600 / max(1, len(filas))))))
        self._siguiente()

    def vaciar(self):
        """Quita todas las filas y detiene la animación."""
        self._timer.stop()
        self._pendientes = []
        self.setRowCount(0)

    def _siguiente(self):
        """Añade la siguiente fila pendiente o detiene la animación."""
        if not self._pendientes:
            self._timer.stop()
            return
        celdas = self._pendientes.pop(0)
        fila = self.rowCount()
        self.insertRow(fila)
        for c, valor in enumerate(celdas):
            item = QTableWidgetItem(valor)
            item.setTextAlignment(Qt.AlignCenter if c == 0 else Qt.AlignRight | Qt.AlignVCenter)
            nombre = self._cabecera[c]
            if nombre.startswith(("‖Δx", "máx", "εₐ", "Error")):
                item.setForeground(QColor(T.NARANJA))
            if not self._pendientes:
                tipo = item.font()
                tipo.setBold(True)
                item.setFont(tipo)
                if c == 0:
                    item.setForeground(QColor(self._color_final))
            self.setItem(fila, c, item)
        self.selectRow(fila)
        self.scrollToBottom()
        if not self._pendientes:
            self._timer.stop()

    def copiar(self, fila=-1):
        """Copia una fila (o toda la tabla con -1) separada por tabuladores."""
        if self.rowCount() == 0:
            return False
        filas = range(self.rowCount()) if fila < 0 else [fila]
        lineas = []
        if fila < 0:
            lineas.append("\t".join(self._cabecera))
        for f in filas:
            lineas.append("\t".join(self.item(f, c).text() for c in range(self.columnCount())
                                    if self.item(f, c)))
        QApplication.clipboard().setText("\n".join(lineas))
        return True


class PaginaIterativos(QWidget):
    """Contenido de la pestaña E: sistema, parámetros, tablas, gráfica e informe de Jacobi y Gauss-Seidel."""

    def __init__(self, pagina, tarjeta_informe, fila_tab, panel_izq, con_desplazo):
        """
        `pagina` es la página de Métodos Numéricos (avisos y errores). El resto son las piezas
        de interfaz que esa página comparte con las demás pestañas.
        """
        super().__init__()
        self._pagina = pagina
        self._res = None
        self._grafica_hecha = False
        self._datos_grafica = None
        self._construir(tarjeta_informe, fila_tab, panel_izq, con_desplazo)
        self._poner_n(3)
        self.cargar_ejemplo(0, avisar=False, calcular=False)

    def _construir(self, tarjeta_informe, fila_tab, panel_izq, con_desplazo):
        """Arma el panel izquierdo (datos) y el derecho (resumen, tablas, gráfica e informe)."""
        izq, lay = panel_izq(ancho_max=470)
        self.b_ejemplos = BotonAnimado("Probar un ejemplo", "azul")
        self.b_ejemplos.con_menu([(e["nombre"], lambda _=False, i=i: self.cargar_ejemplo(i))
                                  for i, e in enumerate(EJEMPLOS_ITERATIVOS)])
        lay.addWidget(self.b_ejemplos)
        lay.addWidget(self._tarjeta_sistema())
        lay.addWidget(self._tarjeta_parametros())

        self.btn_calcular = BotonAnimado("Calcular Jacobi y Gauss-Seidel", "verde")
        self.btn_calcular.clicked.connect(lambda: self.calcular())
        lay.addWidget(self.btn_calcular)
        b_limpiar = BotonAnimado("Limpiar", "suave")
        b_limpiar.clicked.connect(self._pagina._limpiable(self.limpiar))
        lay.addWidget(b_limpiar)
        lay.addWidget(_nota("Enteros (-7), fracciones (3/4), decimales (2.5) o raíces (√4). "
                            "Con Enter en un campo de parámetros se calcula."))
        lay.addStretch(1)

        der = QWidget()
        dl = QVBoxLayout(der)
        dl.setContentsMargins(8, 0, 0, 0)
        dl.setSpacing(10)
        dl.addWidget(self._tarjeta_resumen())
        self.sub = QTabWidget()
        self.tabla_j, self.tabla_g = TablaIteraciones(), TablaIteraciones()
        for tabla in (self.tabla_j, self.tabla_g):
            tabla.setContextMenuPolicy(Qt.CustomContextMenu)
            tabla.customContextMenuRequested.connect(
                lambda pos, t=tabla: self._menu_tabla(t, pos))
        self.inf = tarjeta_informe(pagina=self._pagina, titulo="Jacobi y Gauss-Seidel",
                                   nombre_base="informe_jacobi_gauss_seidel",
                                   color=T.VERDE)
        self.sub.addTab(self.tabla_j, "Jacobi")
        self.sub.addTab(self.tabla_g, "Gauss-Seidel")
        self.sub.addTab(self._panel_grafica(), "Gráfica del error")
        self.sub.addTab(self.inf, "Informe paso a paso")
        dl.addWidget(self.sub, 1)
        self.contenido = fila_tab(con_desplazo(izq), der)
        lay_raiz = QVBoxLayout(self)
        lay_raiz.setContentsMargins(0, 0, 0, 0)
        lay_raiz.addWidget(self.contenido)

    def _tarjeta_sistema(self):
        """Tarjeta con el tamaño n, la matriz aumentada [A | b] y el vector inicial x(0)."""
        t = self.tarjeta_sistema = Tarjeta("Sistema A·x = b")
        fila = QHBoxLayout()
        fila.setSpacing(8)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(_nota("Tamaño n (A es n × n)"))
        self.sp_n = QSpinBox()
        self.sp_n.setRange(1, LIMITE)
        self.sp_n.setValue(3)
        self.sp_n.valueChanged.connect(self._poner_n)
        col.addWidget(self.sp_n)
        fila.addLayout(col)
        fila.addStretch(1)
        t.agregar_layout(fila)

        self.grid_A = CuadriculaMatriz(corchetes=True, aumentada=True, max_filas=LIMITE,
                                       max_cols=LIMITE)
        self.grid_A.forma_cambiada.connect(self._forma_cambiada)
        self.grid_A.cambiado.connect(self._pagina.ocultar_error)
        agregar_acciones_grid(t, self.grid_A)
        self.grid_A.setMinimumHeight(190)
        t.agregar(_nota("Matriz aumentada [A | b]: las n primeras columnas son A y la última es b."))
        t.agregar(self.grid_A, 1)

        t.agregar(_nota("Vector inicial x(0)"))
        self.grid_x0 = CuadriculaMatriz(corchetes=True, max_filas=LIMITE, max_cols=1)
        self.grid_x0.cambiado.connect(self._pagina.ocultar_error)
        self.grid_x0.setMinimumHeight(110)
        t.agregar(self.grid_x0)
        return t

    def _tarjeta_parametros(self):
        """Tarjeta con tolerancia, iteraciones máximas, criterio de parada y relajación λ."""
        t = Tarjeta("Parámetros")
        self.f_eps = self._campo("0.0001", "0.0001")
        self.f_nmax = self._campo("100", "100")
        fila = QHBoxLayout()
        fila.setSpacing(8)
        for etiqueta, campo in (("Tolerancia ε > 0", self.f_eps),
                                ("Iteraciones máx.", self.f_nmax)):
            col = QVBoxLayout()
            col.setSpacing(3)
            col.addWidget(_nota(etiqueta))
            col.addWidget(campo)
            fila.addLayout(col)
        t.agregar_layout(fila)

        t.agregar(_nota("Criterio de parada"))
        self.combo_criterio = QComboBox()
        self.combo_criterio.addItems(_NOMBRES_CRITERIO)
        self.combo_criterio.currentIndexChanged.connect(self._cambio_criterio)
        t.agregar(self.combo_criterio)
        self.nota_criterio = _nota("")
        t.agregar(self.nota_criterio)

        self.btn_lam = BotonAnimado("Mostrar relajación λ", "fantasma", pequeno=True)
        self.btn_lam.setToolTip("Opción avanzada de Gauss-Seidel (sobrerrelajación). También "
                                "aparece sola al cargar un ejemplo con relajación.")
        self.btn_lam.clicked.connect(lambda: self.mostrar_lambda(self.caja_lam.isHidden()))
        t.agregar(self.btn_lam)
        self.caja_lam = QWidget()
        lay_lam = QVBoxLayout(self.caja_lam)
        lay_lam.setContentsMargins(0, 0, 0, 0)
        lay_lam.setSpacing(6)
        self.sw_lam = Interruptor("Relajación λ en Gauss-Seidel", False)
        self.sw_lam.setToolTip("Con λ = 1 es Gauss-Seidel clásico. Con 0 < λ < 2 se mezcla "
                               "el valor nuevo con el anterior (sobrerrelajación SOR).")
        self.sw_lam.toggled.connect(lambda marcado: self.f_lam.setEnabled(marcado))
        lay_lam.addWidget(self.sw_lam)
        self.f_lam = self._campo("1", "1", 90)
        self.f_lam.setEnabled(False)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(_nota("Factor λ, 0 < λ < 2"))
        col.addWidget(self.f_lam)
        lay_lam.addLayout(col)
        self.caja_lam.setVisible(False)
        t.agregar(self.caja_lam)
        self.sw_matrices = Interruptor("Mostrar D, L, U, T y c en el informe", False)
        self.sw_matrices.setToolTip("Añade al paso a paso la forma matricial A = D + L + U y las "
                                    "matrices de iteración T y c. Apagado, el informe es más corto.")
        t.agregar(self.sw_matrices)
        self._cambio_criterio(0)
        return t

    def mostrar_lambda(self, mostrar):
        """Muestra u oculta la opción de relajación; al ocultarla se apaga y vuelve a λ = 1."""
        if not mostrar:
            self.sw_lam.setChecked(False)
            self.f_lam.setText("1")
        self.caja_lam.setVisible(mostrar)
        self.btn_lam.setText("Ocultar relajación λ" if mostrar else "Mostrar relajación λ")

    @staticmethod
    def _campo(texto, marcador, ancho=None):
        """Campo de texto que se desmarca al editarlo."""
        from qt.pagina_numerica import _campo
        return _campo(texto, marcador, ancho)

    def _tarjeta_resumen(self):
        """Tarjeta de resumen con el resultado de cada método y el botón de reordenar filas."""
        t = self.tarjeta_resumen = Tarjeta("Resumen")
        self.lbl_resumen = QLabel("Introduce el sistema y pulsa «Calcular Jacobi y Gauss-Seidel».")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setTextFormat(Qt.RichText)
        self.lbl_resumen.setTextInteractionFlags(Qt.TextSelectableByMouse)
        t.agregar(self.lbl_resumen)
        self.btn_reordenar = BotonAnimado("Reordenar filas y recalcular", "azul", pequeno=True)
        self.btn_reordenar.setToolTip("Aplica la permutación de filas propuesta. Es una sugerencia: "
                                      "solo se hace si lo pides.")
        self.btn_reordenar.clicked.connect(self.reordenar)
        self.btn_reordenar.setVisible(False)
        t.agregar(self.btn_reordenar)
        return t

    def _panel_grafica(self):
        """Panel de la gráfica del error con sus botones de ventana, guardar y copiar."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(8)
        fila = QHBoxLayout()
        fila.setSpacing(6)
        for texto, accion in (("Abrir en ventana", self.abrir_ventana_grafica),
                              ("Guardar imagen", self.guardar_grafica),
                              ("Copiar imagen", self.copiar_grafica)):
            b = BotonAnimado(texto, "suave", pequeno=True)
            b.clicked.connect(accion)
            fila.addWidget(b)
        fila.addStretch(1)
        lay.addLayout(fila)
        self.grafica = GraficaError()
        lay.addWidget(self.grafica, 1)
        self.lbl_grafica = _nota("")
        lay.addWidget(self.lbl_grafica)
        return w

    def _cambio_criterio(self, indice):
        """Muestra qué mide el criterio elegido y ajusta la tolerancia si seguía siendo la de otro criterio."""
        clave = _CRITERIOS[indice]
        self.nota_criterio.setText(M.CRITERIOS[clave])
        if self.f_eps.text() in _TOLERANCIA_DEFECTO.values():
            self.f_eps.setText(_TOLERANCIA_DEFECTO[clave])

    def _poner_n(self, n):
        """Reconstruye [A | b] y x(0) con n filas conservando lo escrito; las celdas nuevas quedan en 0."""
        self.grid_A.reconstruir(n, n + 1)
        self.grid_x0.reconstruir(n, 1)

    def _forma_cambiada(self, filas, columnas):
        """Deshacer, rehacer o pegar cambiaron el tamaño de [A | b]: se sincronizan n y x(0)."""
        n = max(1, min(LIMITE, filas))
        self.sp_n.blockSignals(True)
        self.sp_n.setValue(n)
        self.sp_n.blockSignals(False)
        if self.grid_x0.filas() != filas:
            self.grid_x0.reconstruir(filas, 1, registrar=False)

    def _leer(self):
        """Lee la pantalla: (A, b, x0) como listas de texto."""
        celdas = self.grid_A.textos()
        A = [fila[:-1] for fila in celdas]
        b = [fila[-1] for fila in celdas]
        x0 = [fila[0] for fila in self.grid_x0.textos()]
        return A, b, x0

    def _criterio(self):
        """Clave del criterio de parada elegido."""
        return _CRITERIOS[self.combo_criterio.currentIndex()]

    def _lam(self):
        """Texto de λ: el campo si la relajación está activada, y 1 si no."""
        return self.f_lam.text() if self.sw_lam.isChecked() else "1"

    def _desmarcar(self):
        """Quita las marcas de error de campos y celdas."""
        from qt.pagina_numerica import _marcar
        for c in (self.f_eps, self.f_nmax, self.f_lam):
            _marcar(c, False)

    def _marcar_error(self, r):
        """Pinta de rojo el campo o la celda que causó el error de validación."""
        from qt.pagina_numerica import _marcar
        campo, pos = r["campo"], r["posicion"]
        if campo == "A" and pos:
            self.grid_A.marcar_error(pos[0], pos[1])
        elif campo == "b" and pos:
            self.grid_A.marcar_error(pos[0], self.grid_A.columnas() - 1)
        elif campo == "x0" and pos:
            self.grid_x0.marcar_error(pos[0], 0)
        else:
            widget = {"eps": self.f_eps, "nmax": self.f_nmax, "lam": self.f_lam}.get(campo)
            if widget is not None:
                _marcar(widget, True)

    def calcular(self, reordenar=False, avisar=True, animar=True):
        """Valida, ejecuta Jacobi y Gauss-Seidel con el mismo criterio y muestra tablas, gráfica e informe."""
        pagina = self._pagina
        pagina.ocultar_error()
        self._desmarcar()
        A, b, x0 = self._leer()
        r = M.resolver(A, b, x0, self.f_eps.text(), self.f_nmax.text(), self._criterio(),
                       self._lam(), reordenar, self.sw_matrices.isChecked())
        self._res = r
        self.inf.poner(r["informe"], "Jacobi y Gauss-Seidel", pulso=r["valido"],
                       resumen=self._resumen_ventana(r))
        self.btn_reordenar.setVisible(r["propuesta"] is not None and r["permutacion"] is None)
        if not r["valido"]:
            self.tabla_j.vaciar()
            self.tabla_g.vaciar()
            self._vaciar_grafica()
            self._marcar_error(r)
            self._resumen_error(r)
            if avisar:
                pagina.error("Jacobi y Gauss-Seidel", r["mensaje"])
            if r["informe"]:
                self.sub.setCurrentWidget(self.inf)
            return r
        self._llenar_tablas(r, animar)
        self._dibujar_grafica(r, animar)
        self._resumen(r)
        if avisar:
            self.sub.setCurrentIndex(0)
            self.tarjeta_resumen.pulso(
                T.VERDE if r["comparacion"]["ambos"] else T.NARANJA)
            pagina.estado_barra(r["mensaje"])
        return r

    def reordenar(self):
        """Aplica la permutación de filas propuesta: reordena la cuadrícula y recalcula."""
        r = self._res
        if not r or r["propuesta"] is None:
            return
        permutacion = r["propuesta"]["permutacion"]
        A, b, _ = self._leer()
        nueva = [A[p] + [b[p]] for p in permutacion]
        self.grid_A.reconstruir(len(nueva), len(nueva[0]), nueva, animar=True)
        self.calcular(reordenar=False)
        self._res["permutacion"] = permutacion
        self.btn_reordenar.setVisible(False)
        mostrar_aviso(self._pagina, "Filas reordenadas: " + ",  ".join(
            "{} ← {}".format(j + 1, p + 1) for j, p in enumerate(permutacion)), "info")

    def _llenar_tablas(self, r, animar):
        """Llena las dos tablas de iteraciones."""
        con_ref = r["x_ref"] is not None
        cab = M.columnas(r["n"], r["criterio"], con_ref)
        for tabla, clave in ((self.tabla_j, "jacobi"), (self.tabla_g, "gauss_seidel")):
            met = r[clave]
            filas = [M.valores_fila(f, r["criterio"], con_ref) for f in met["filas"]]
            tabla.poner(cab, filas, met["convergio"], animar)

    def _dibujar_grafica(self, r, animar):
        """Dibuja el error de ambos métodos si los dos tienen datos válidos; si no, explica por qué."""
        datos = M.preparar_grafica_error(r)
        if not datos["valido"]:
            self._vaciar_grafica(datos["mensaje"])
            return
        self._datos_grafica = datos
        self._grafica_hecha = True
        self.grafica.dibujar(datos, animar=animar)
        self.lbl_grafica.setText(datos["resumen"])

    def _vaciar_grafica(self, mensaje=""):
        """Deja la gráfica en blanco con un mensaje opcional del motivo."""
        self._datos_grafica = None
        self._grafica_hecha = False
        self.grafica.vaciar()
        self.lbl_grafica.setText(mensaje)

    def _resumen_error(self, r):
        """Resumen cuando no se pudo calcular: el motivo y, si existe, la propuesta de reordenar."""
        texto = ("<span style='color:{}'><b>No se pudo aplicar el método.</b></span><br>{}"
                 .format(T.ROJO, _html(r["mensaje"])))
        self.lbl_resumen.setText(texto)

    def _linea_metodo(self, r, met):
        """Línea de resumen de un método: solución, iteraciones y estado, en verde o rojo."""
        color = T.VERDE if met["convergio"] else T.ROJO
        nombre = M.nombre_metodo(met["clave"], r["lam"])
        if all(math.isfinite(v) for v in met["x"]) and max(abs(v) for v in met["x"]) < 1e8:
            solucion = M._vector(met["x"])
        else:
            solucion = "valores muy grandes (diverge)"
        estado = ("{} iteraciones".format(met["iteraciones"]) if met["convergio"]
                  else M._ESTADO_CORTO[met["motivo"]])
        return ("<span style='color:{c}'><b>{n}</b>: x ≈ {x} &nbsp;·&nbsp; {e}</span>"
                .format(c=color, n=_html(nombre), x=_html(solucion), e=_html(estado)))

    def _resumen(self, r):
        """Resumen: solución y estado de cada método, comparación y avisos."""
        partes = [self._linea_metodo(r, r["jacobi"]), self._linea_metodo(r, r["gauss_seidel"])]
        cmp_ = r["comparacion"]
        if cmp_["ambos"] and cmp_["mas_rapido"] not in (None, "igual"):
            rapido = r["gauss_seidel"] if cmp_["mas_rapido"] == "gauss_seidel" else r["jacobi"]
            partes.append("<span style='color:{}'>{} necesitó menos iteraciones.</span>".format(
                T.AZUL, _html(M.nombre_metodo(rapido["clave"], r["lam"]))))
        m = r["matrices"]
        if m["rho_J"] is not None and m["rho_GS"] is not None:
            partes.append("ρ(T_J) = {} &nbsp;·&nbsp; ρ(T_GS) = {} &nbsp;·&nbsp; diagonal {}".format(
                M._c(m["rho_J"]), M._c(m["rho_GS"]),
                "estrictamente dominante" if r["es_dominante"] else "no dominante"))
        if r["permutacion"] is not None:
            partes.append("<span style='color:{}'>Filas reordenadas (propuesta aceptada).</span>"
                          .format(T.AZUL))
        elif r["propuesta"] is not None:
            partes.append("<span style='color:{}'>Se propone reordenar las filas; solo se hace si "
                          "lo confirmas con el botón.</span>".format(T.NARANJA))
        for aviso in r["advertencias"]:
            partes.append("<span style='color:{}'>Aviso: {}</span>".format(T.NARANJA, _html(aviso)))
        self.lbl_resumen.setText("<br>".join(partes))

    def _resumen_ventana(self, r):
        """Respuesta destacada de la ventana de resultado (Abrir en ventana)."""
        if not r["valido"]:
            return {"tipo": "Jacobi y Gauss-Seidel", "respuesta": "No se pudo calcular",
                    "estado": "error", "insignia": ""}
        gs = r["gauss_seidel"]
        ambos = r["comparacion"]["ambos"]
        return {"tipo": "Jacobi y Gauss-Seidel  ·  {}×{}".format(r["n"], r["n"]),
                "respuesta": ("x ≈ " + M._vector(gs["x"])) if gs["convergio"]
                else "Sin convergencia en Gauss-Seidel",
                "estado": "ok" if ambos else None,
                "insignia": ("✓ Ambos convergen: J = {}, GS = {} iteraciones".format(
                    r["jacobi"]["iteraciones"], gs["iteraciones"]) if ambos
                    else "⚠ Al menos un método no converge")}

    def _menu_tabla(self, tabla, pos):
        """Menú de clic derecho de una tabla: copiar la fila o toda la tabla."""
        from PySide6.QtWidgets import QMenu
        fila = tabla.rowAt(pos.y())
        menu = QMenu(self)
        if fila >= 0:
            menu.addAction("Copiar fila", lambda: self._copiar_tabla(tabla, fila))
        if tabla.rowCount():
            menu.addAction("Copiar toda la tabla", lambda: self._copiar_tabla(tabla, -1))
        if not menu.isEmpty():
            menu.exec(tabla.viewport().mapToGlobal(pos))

    def _copiar_tabla(self, tabla, fila):
        """Copia al portapapeles una fila o toda la tabla."""
        if tabla.copiar(fila):
            mostrar_aviso(self._pagina, "Copiado: pégalo en Excel o Word")

    def abrir_ventana_grafica(self):
        """Abre la gráfica del error en una ventana grande."""
        if not self._grafica_hecha:
            self._pagina.info("Sin gráfica", self.lbl_grafica.text() or
                              "Primero calcula los dos métodos.")
            return
        d = self._datos_grafica
        abrir_ventana_grafica("Gráfica — error por iteración", d, None, None, d["resumen"],
                              clase=VentanaGraficaError)

    def guardar_grafica(self):
        """Pide una ruta y guarda la gráfica como imagen."""
        if not self._grafica_hecha:
            self._pagina.info("Sin gráfica", "Primero calcula los dos métodos.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfica", "error_por_iteracion.png",
            "Imagen PNG (*.png);;PDF (*.pdf);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            self.grafica.guardar(ruta)
            mostrar_aviso(self._pagina, "Gráfica guardada")
        except (OSError, ValueError) as ex:
            self._pagina.error("Error al guardar", str(ex))

    def copiar_grafica(self):
        """Copia la gráfica al portapapeles como imagen."""
        if not self._grafica_hecha:
            self._pagina.info("Sin gráfica", "Primero calcula los dos métodos.")
            return
        QApplication.clipboard().setImage(self.grafica.imagen())
        mostrar_aviso(self._pagina, "Gráfica copiada como imagen")

    def cargar_ejemplo(self, i, avisar=True, calcular=True):
        """Carga el ejemplo con el índice dado y, si se pide, lo calcula."""
        e = EJEMPLOS_ITERATIVOS[i]
        n = len(e["A"])
        self.sp_n.blockSignals(True)
        self.sp_n.setValue(n)
        self.sp_n.blockSignals(False)
        aumentada = [fila + [e["b"][k]] for k, fila in enumerate(e["A"])]
        self.grid_A.reconstruir(n, n + 1, aumentada)
        self.grid_x0.reconstruir(n, 1, [[v] for v in e["x0"]])
        self.combo_criterio.blockSignals(True)
        self.combo_criterio.setCurrentIndex(_CRITERIOS.index(e["criterio"]))
        self.combo_criterio.blockSignals(False)
        self.nota_criterio.setText(M.CRITERIOS[e["criterio"]])
        self.f_eps.setText(e["eps"])
        self.f_nmax.setText(e["nmax"])
        self.mostrar_lambda(e["lam"] != "1")
        self.sw_lam.setChecked(e["lam"] != "1")
        self.f_lam.setText(e["lam"])
        if calcular:
            self.calcular()
        if avisar:
            mostrar_aviso(self._pagina, "Ejemplo: {}. {}".format(e["nombre"], e["sugerencia"]),
                          "info")

    def limpiar(self):
        """Limpia la pestaña: pone el sistema en 0, los parámetros por defecto y borra resultados."""
        self.sp_n.blockSignals(True)
        self.sp_n.setValue(3)
        self.sp_n.blockSignals(False)
        self.grid_A.reconstruir(3, 4, [["0"] * 4 for _ in range(3)])
        self.grid_x0.reconstruir(3, 1, [["0"] for _ in range(3)])
        self.combo_criterio.setCurrentIndex(0)
        self.f_eps.setText("0.0001")
        self.f_nmax.setText("100")
        self.mostrar_lambda(False)
        self.sw_matrices.setChecked(False)
        self._desmarcar()
        self._res = None
        self.tabla_j.vaciar()
        self.tabla_g.vaciar()
        self._vaciar_grafica()
        self.inf.poner("")
        self.btn_reordenar.setVisible(False)
        self.lbl_resumen.setText("Introduce el sistema y pulsa «Calcular Jacobi y Gauss-Seidel».")
        self._pagina.ocultar_error()

    def estado(self):
        """Datos de la pestaña para guardar la sesión."""
        A, b, x0 = self._leer()
        return {"A": A, "b": b, "x0": x0, "eps": self.f_eps.text(),
                "nmax": self.f_nmax.text(), "criterio": self._criterio(),
                "lam_activa": self.sw_lam.isChecked(), "lam": self.f_lam.text(),
                "matrices": self.sw_matrices.isChecked(),
                "calculado": self._res is not None and self._res["valido"],
                "informe": self.inf.texto, "historial": self.inf.historial}

    def restaurar(self, d):
        """Restaura lo guardado por `estado`; los datos dañados se ignoran sin romper la ventana."""
        n = len(d["A"])
        if not 1 <= n <= LIMITE or len(d["b"]) != n or len(d["x0"]) != n:
            return
        self.sp_n.blockSignals(True)
        self.sp_n.setValue(n)
        self.sp_n.blockSignals(False)
        self.grid_A.reconstruir(n, n + 1, [list(map(str, fila)) + [str(d["b"][k])]
                                           for k, fila in enumerate(d["A"])], registrar=False,
                                animar=False)
        self.grid_x0.reconstruir(n, 1, [[str(v)] for v in d["x0"]], registrar=False, animar=False)
        criterio = d.get("criterio", "norma2")
        self.combo_criterio.blockSignals(True)
        self.combo_criterio.setCurrentIndex(_CRITERIOS.index(criterio)
                                            if criterio in _CRITERIOS else 0)
        self.combo_criterio.blockSignals(False)
        self.nota_criterio.setText(M.CRITERIOS[self._criterio()])
        self.f_eps.setText(str(d.get("eps", "0.0001")))
        self.f_nmax.setText(str(d.get("nmax", "100")))
        self.mostrar_lambda(bool(d.get("lam_activa", False)))
        self.sw_lam.setChecked(bool(d.get("lam_activa", False)))
        self.f_lam.setText(str(d.get("lam", "1")))
        self.sw_matrices.setChecked(bool(d.get("matrices", False)))
        self.inf.historial = list(d.get("historial", []))[:40]
        if d.get("calculado"):
            self.calcular(avisar=False, animar=False)
        elif d.get("informe"):
            self.inf.poner(d["informe"], registrar=False, pulso=False)

    def aplicar_escala(self):
        """Aplica el nuevo tamaño de letra a las tablas, al informe y a las cuadrículas."""
        self.tabla_j.estilo()
        self.tabla_g.estilo()
        self.inf.estilo()
        for g in (self.grid_A, self.grid_x0):
            g.reconstruir(g.filas(), g.columnas(), g.textos(), registrar=False, animar=False)
        if self._res and self._res["valido"]:
            self._llenar_tablas(self._res, False)

    def informe_actual(self):
        """Tarjeta de informe de esta pestaña (para Ctrl+S y Ctrl+P)."""
        return self.inf

    def campos_enter(self):
        """Campos que calculan al pulsar Enter."""
        return (self.f_eps, self.f_nmax, self.f_lam)
