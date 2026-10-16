# -*- coding: utf-8 -*-
"""
Operaciones con matrices y vectores (versión PySide6): suma, resta, escalar,
producto, transpuesta, determinante, inversa, Cramer, propiedades y envío al
solucionador. Todo con aritmética exacta de fracciones.
"""
import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QScrollArea, QSpinBox,
                               QSplitter, QTabWidget, QVBoxLayout, QWidget)

from core.fraccion import desde_texto
import core.algebra as alg  
import core.procedimiento as proc
import core.propiedades as prop

from qt import tema as T
from qt import render
from qt.componentes import (BotonAnimado, CuadriculaMatriz, Interruptor,
                            Tarjeta, agregar_acciones_grid, aparecer,
                            mostrar_aviso)
from qt.ejemplos import MATRICES
from qt.exportar import escribir_pdf
from qt.imagen import imagen_de_matriz, imagen_de_texto
from qt.pagina_base import PaginaBase
from qt.visor import abrir_visor

LIMITE = 10

METODO_COFACTORES = "Cofactores"
METODO_TRIANGULAR = "Triangular (eliminación)"
METODO_SARRUS = "Sarrus (solo 3×3)"

OP_ETIQUETAS = {
    "suma": "A + B", "resta": "A − B", "multiplicacion": "A × B",
    "escalar": "r · A", "transpuesta": "Aᵀ", "det": "det(A)",
    "inversa_gj": "A⁻¹ (Gauss-Jordan)", "inversa_adj": "A⁻¹ (Adjunta)",
}
MAX_HISTORIAL = 40


class PaginaMatrices(PaginaBase):

    def __init__(self, ventana):
        super().__init__(ventana, "Operaciones con matrices y vectores",
                         "Suma · resta · escalar · producto · transpuesta · "
                         "determinante · inversa · Cramer · propiedades")
        self.resultado_actual = None      # última matriz calculada (Fraccion)
        self._texto_res = ""
        self._etiqueta_res = ""
        self._historial = []          # resultados anteriores
        self.usa_B = True
        self.usa_C = True

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.addWidget(self._panel_izquierdo())
        split.addWidget(self._panel_centro())
        split.addWidget(self._panel_derecho())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 2)
        split.setStretchFactor(2, 3)
        split.setSizes([240, 400, 560])
        self.raiz.addWidget(split, 1)

        self.generar_cuadriculas()
        # El panel del centro (las matrices) no puede ser más estrecho que el
        # encabezado de sus tarjetas; los demás, que su propio contenido.
        self._area_centro.setMinimumWidth(
            self.tarjetas["A"].minimumSizeHint().width() + 40)
        self.respetar_minimos(split)
        self.atajo("Ctrl+D", lambda: self.ejecutar_operacion("det"))
        self.atajo("Ctrl+I", lambda: self.ejecutar_operacion("inversa_gj"))
        self.atajo("Ctrl+M", lambda: self.ejecutar_operacion("multiplicacion"))
        self.atajo("Ctrl+L", self.limpiar)
        self.atajo("Ctrl+S", self.guardar_informe)
        self.atajo("Ctrl+P", self.exportar_pdf)

    # ──────────────────────────────────────────────────────────
    # Construcción
    # ──────────────────────────────────────────────────────────

    def _spin(self, valor=2):
        sp = QSpinBox()
        sp.setRange(1, LIMITE)
        sp.setValue(valor)
        sp.valueChanged.connect(lambda _: self.generar_cuadriculas())
        return sp

    def _panel_izquierdo(self):
        w = QWidget()
        w.setMinimumWidth(230)
        w.setMaximumWidth(360)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(10)

        b_ej = BotonAnimado("Probar un ejemplo", "azul")
        b_ej.con_menu([(m["nombre"], lambda _=False, i=i: self.cargar_ejemplo(i))
                       for i, m in enumerate(MATRICES)])
        lay.addWidget(b_ej)

        self.sp = {}
        for nombre, e_f, e_c in (("A", "Filas (m)", "Cols (n)"),
                                 ("B", "Filas (n)", "Cols (p)"),
                                 ("C", "Filas (m)", "Cols (n)")):
            t = Tarjeta("Tamaño de " + nombre)
            fila = QHBoxLayout()
            fila.setSpacing(8)
            filas, cols = self._spin(), self._spin()
            self.sp[nombre] = (filas, cols)
            for texto, sp in ((e_f, filas), (e_c, cols)):
                col = QVBoxLayout()
                col.setSpacing(3)
                l = QLabel(texto)
                l.setObjectName("nota")
                col.addWidget(l)
                col.addWidget(sp)
                fila.addLayout(col)
            t.agregar_layout(fila)
            lay.addWidget(t)

        nota = QLabel("Pon 1 columna para trabajar con vectores de Rⁿ.")
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        lay.addWidget(nota)

        for texto, cmd in (("Generar cuadrículas", self.generar_cuadriculas),
                           ("Intercambiar A ↔ B", self.intercambiar),
                           ("Limpiar", self.limpiar)):
            b = BotonAnimado(texto, "suave")
            b.clicked.connect(cmd)
            lay.addWidget(b)

        self.btn_toggle_B = BotonAnimado("Quitar matriz B", "suave")
        self.btn_toggle_B.clicked.connect(lambda: self.alternar_matriz("B"))
        self.btn_toggle_C = BotonAnimado("Quitar matriz C", "suave")
        self.btn_toggle_C.clicked.connect(lambda: self.alternar_matriz("C"))
        lay.addWidget(self.btn_toggle_B)
        lay.addWidget(self.btn_toggle_C)

        ayuda = QLabel("Enteros (-7), fracciones (3/4),\ndecimales (2.5), raíces (√4).")
        ayuda.setObjectName("nota")
        lay.addWidget(ayuda)
        lay.addStretch(1)
        return w

    def _panel_centro(self):
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(10)

        self.tarjetas = {}
        self.grids = {}
        for nombre in ("A", "B", "C"):
            t = Tarjeta("Matriz " + nombre, T.AZUL)
            g = CuadriculaMatriz(corchetes=True, max_filas=LIMITE, max_cols=LIMITE)
            g.forma_cambiada.connect(
                lambda f, c, n=nombre: self._forma_cambiada(n, f, c))
            g.cambiado.connect(self.ocultar_error)
            agregar_acciones_grid(t, g)
            t.agregar(g, 1)
            lay.addWidget(t, 1)
            self.tarjetas[nombre] = t
            self.grids[nombre] = g
        self.grid_A, self.grid_B, self.grid_C = (self.grids[k] for k in "ABC")
        lay.addStretch(0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(cont)
        self._area_centro = area
        return area

    def _panel_derecho(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_operaciones(), "Operaciones")
        self.tabs.addTab(self._tab_propiedades(), "Propiedades")
        self.tabs.addTab(self._tab_solucionador(), "Solucionador")
        marco = self.marco_tabs = QFrame()
        marco.setObjectName("tarjeta")
        ml = QVBoxLayout(marco)
        ml.setContentsMargins(12, 6, 12, 12)
        ml.addWidget(self.tabs)
        lay.addWidget(marco)

        lay.addWidget(self._tarjeta_resultado(), 1)
        return w

    def _tab_operaciones(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)

        rej = QGridLayout()
        rej.setSpacing(6)
        for i, (texto, op) in enumerate((("A + B", "suma"), ("A − B", "resta"),
                                         ("A × B", "multiplicacion"),
                                         ("Aᵀ", "transpuesta"))):
            b = BotonAnimado(texto, "primario")
            b.clicked.connect(lambda _=False, o=op: self.ejecutar_operacion(o))
            rej.addWidget(b, i // 2, i % 2)
        lay.addLayout(rej)

        fe = QHBoxLayout()
        be = BotonAnimado("r · A   (escalar)", "primario")
        be.clicked.connect(lambda: self.ejecutar_operacion("escalar"))
        self.ed_escalar = QLineEdit("2")
        self.ed_escalar.setFixedWidth(70)
        self.ed_escalar.setAlignment(Qt.AlignCenter)
        fe.addWidget(be, 1)
        fe.addWidget(self.ed_escalar)
        lay.addLayout(fe)

        self.sw_pasos = Interruptor("Mostrar el paso a paso del cálculo", True)
        lay.addWidget(self.sw_pasos)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: {};".format(T.SUPERF))
        lay.addWidget(sep)
        l = QLabel("Operaciones sobre A cuadrada:")
        l.setObjectName("nota")
        lay.addWidget(l)

        fd = QGridLayout()
        fd.setSpacing(6)
        for i, (texto, op) in enumerate((("det(A)", "det"),
                                         ("A⁻¹  Gauss-Jordan", "inversa_gj"),
                                         ("A⁻¹  Adjunta", "inversa_adj"))):
            b = BotonAnimado(texto, "primario")
            b.clicked.connect(lambda _=False, o=op: self.ejecutar_operacion(o))
            fd.addWidget(b, 0, i)
        lay.addLayout(fd)

        fm = QHBoxLayout()
        fm.addWidget(QLabel("Método del determinante:"))
        self.combo_det = QComboBox()
        fm.addWidget(self.combo_det, 1)
        lay.addLayout(fm)

        bc = BotonAnimado("Resolver A · x = b   (Regla de Cramer)", "verde")
        bc.clicked.connect(self._mostrar_cramer)
        lay.addWidget(bc)
        n = QLabel("B debe ser el vector b (1 columna); A cuadrada n×n con det(A) ≠ 0.")
        n.setObjectName("nota")
        n.setWordWrap(True)
        lay.addWidget(n)

        bc_lu = BotonAnimado("Factorización LU (A = L·U) y Ax = b", "verde")
        bc_lu.clicked.connect(self._ejecutar_factorizacion_lu)
        lay.addWidget(bc_lu)
        n_lu = QLabel("Factoriza cualquier A (m×n). Si A es cuadrada y B es el vector b "
                      "(1 columna), también resuelve A · x = b.")
        n_lu.setObjectName("nota")
        n_lu.setWordWrap(True)
        lay.addWidget(n_lu)

        return w

    def _tab_propiedades(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)

        n = QLabel("u, v = col 1 y 2 de B  ·  r = escalar  ·  C = tercera matriz  ·  s = 2º escalar")
        n.setObjectName("nota")
        n.setWordWrap(True)
        lay.addWidget(n)

        fs = QHBoxLayout()
        fs.addWidget(QLabel("s ="))
        self.ed_s = QLineEdit("3")
        self.ed_s.setFixedWidth(70)
        self.ed_s.setAlignment(Qt.AlignCenter)
        fs.addWidget(self.ed_s)
        l = QLabel("(2º escalar, para propiedades que lo necesiten)")
        l.setObjectName("nota")
        fs.addWidget(l, 1)
        lay.addLayout(fs)

        self.combo_prop = QComboBox()
        for c, _n, _k, _f in prop.PROPIEDADES:
            self.combo_prop.addItem(prop.etiqueta(c))
        lay.addWidget(self.combo_prop)

        fb = QHBoxLayout()
        b1 = BotonAnimado("Verificar la elegida", "azul")
        b1.clicked.connect(lambda: self.ejecutar_operacion("prop"))
        b2 = BotonAnimado("Verificar todas", "suave")
        b2.clicked.connect(lambda: self.ejecutar_operacion("prop_todas"))
        fb.addWidget(b1)
        fb.addWidget(b2)
        lay.addLayout(fb)
        lay.addStretch(1)
        return w

    def _tab_solucionador(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)
        n = QLabel("B debe tener una sola columna: es el vector b.")
        n.setObjectName("nota")
        lay.addWidget(n)
        for texto, modo in (("Resolver la ecuación  A · x = b", "matricial"),
                            ("¿Es b combinación lineal de las columnas de A?", "combinacion"),
                            ("¿Son las columnas de A linealmente independientes?", "independencia")):
            b = BotonAnimado(texto, "azul")
            b.clicked.connect(lambda _=False, m=modo: self.enviar_al_solucionador(m))
            lay.addWidget(b)
        lay.addStretch(1)
        return w

    def _tarjeta_resultado(self):
        t = self.tarjeta_resultado = Tarjeta("Resultado")
        acc = QHBoxLayout()
        acc.setSpacing(5)
        l = QLabel("Usar como")
        l.setObjectName("nota")
        acc.addWidget(l)
        self.btn_res = {}
        for nombre in "ABC":
            b = BotonAnimado(nombre, "suave", pequeno=True)
            b.setEnabled(False)
            b.setMinimumWidth(34)
            b.clicked.connect(lambda _=False, n=nombre: self.usar_resultado(n))
            acc.addWidget(b)
            self.btn_res[nombre] = b
        acc.addStretch(1)
        self.btn_historial = BotonAnimado("Historial", "suave", pequeno=True)
        self.btn_historial.clicked.connect(self._menu_historial)
        acc.addWidget(self.btn_historial)
        t.agregar_layout(acc)

        acc2 = QHBoxLayout()
        acc2.setSpacing(5)
        b_guardar = BotonAnimado("Guardar informe", "suave", pequeno=True)
        b_guardar.con_menu([("Texto (.txt)", self.guardar_informe),
                            ("PDF (.pdf)", self.exportar_pdf)])
        acc2.addWidget(b_guardar)
        b_abrir = BotonAnimado("Abrir en ventana", "suave", pequeno=True)
        b_abrir.clicked.connect(self.abrir_en_ventana)
        acc2.addWidget(b_abrir)
        b_copiar = BotonAnimado("Copiar", "suave", pequeno=True)
        b_copiar.con_menu([
            ("Copiar como texto", self.copiar_resultado),
            ("Copiar como imagen", self.copiar_resultado_imagen),
            ("Copiar la matriz resultado como imagen",
             self.copiar_matriz_resultado_imagen)])
        acc2.addWidget(b_copiar)
        acc2.addStretch(1)
        t.agregar_layout(acc2)

        self.txt = QPlainTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._estilo_resultado()
        self.txt.setPlaceholderText("El resultado aparecerá aquí.")
        t.agregar(self.txt, 1)
        return t

    # ──────────────────────────────────────────────────────────
    # Cuadrículas
    # ──────────────────────────────────────────────────────────

    def generar_cuadriculas(self):
        for nombre in "ABC":
            f, c = self.sp[nombre]
            self.grids[nombre].reconstruir(f.value(), c.value())
        self._actualizar_titulos()
        self._actualizar_metodos_det()

    def _forma_cambiada(self, nombre, filas, cols):
        """Deshacer / rehacer / pegar cambiaron el tamaño de una cuadrícula."""
        f, c = self.sp[nombre]
        f.blockSignals(True)
        c.blockSignals(True)
        f.setValue(filas)
        c.setValue(cols)
        f.blockSignals(False)
        c.blockSignals(False)
        self._actualizar_titulos()
        self._actualizar_metodos_det()

    def cargar_ejemplo(self, indice):
        ej = MATRICES[indice]
        for nombre in "ABC":
            texto = ej[nombre]
            f, c = self.sp[nombre]
            f.blockSignals(True)
            c.blockSignals(True)
            f.setValue(len(texto))
            c.setValue(len(texto[0]))
            f.blockSignals(False)
            c.blockSignals(False)
            self.grids[nombre].reconstruir(len(texto), len(texto[0]), texto)
        self.ed_escalar.setText(ej["escalar"])
        self.ed_s.setText(ej["s"])
        self._actualizar_titulos()
        self._actualizar_metodos_det()
        self._sin_resultado()
        self.mostrar_resultado("")
        mostrar_aviso(self, "Ejemplo: {}. {}".format(ej["nombre"], ej["sugerencia"]),
                      "info")

    def _actualizar_titulos(self):
        for nombre in "ABC":
            f, c = self.sp[nombre]
            if c.value() == 1:
                txt = "Vector {} ({}×1)".format(nombre, f.value())
            else:
                txt = "Matriz {} ({}×{})".format(nombre, f.value(), c.value())
            self.tarjetas[nombre].poner_titulo(txt)

    def _metodos_det_disponibles(self):
        metodos = [METODO_COFACTORES, METODO_TRIANGULAR]
        f, c = self.sp["A"]
        if f.value() == 3 and c.value() == 3:
            metodos.append(METODO_SARRUS)
        return metodos

    def _actualizar_metodos_det(self):
        actual = self.combo_det.currentText()
        metodos = self._metodos_det_disponibles()
        self.combo_det.blockSignals(True)
        self.combo_det.clear()
        self.combo_det.addItems(metodos)
        self.combo_det.setCurrentText(actual if actual in metodos else METODO_COFACTORES)
        self.combo_det.blockSignals(False)

    def alternar_matriz(self, cual):
        if cual == "B":
            self.usa_B = not self.usa_B
            usa, boton = self.usa_B, self.btn_toggle_B
        else:
            self.usa_C = not self.usa_C
            usa, boton = self.usa_C, self.btn_toggle_C
        tarjeta = self.tarjetas[cual]
        tarjeta.setVisible(usa)
        if usa:
            aparecer(tarjeta, 260)
        boton.setText(("Quitar matriz " if usa else "Agregar matriz ") + cual)

    def _leer_B(self):
        if not self.usa_B:
            self.info("Matriz B quitada",
                      "Esta operación necesita B. Use «Agregar matriz B».")
            return None
        return self._leer_matriz(self.grid_B, "B")

    def limpiar(self):
        for g in self.grids.values():
            g.limpiar()
        self._sin_resultado()
        self.mostrar_resultado("")

    def intercambiar(self):
        tA, tB = self.grid_A.textos(), self.grid_B.textos()
        fa, ca = self.sp["A"]
        fb, cb = self.sp["B"]
        for sp in (fa, ca, fb, cb):
            sp.blockSignals(True)
        fa.setValue(len(tB)); ca.setValue(len(tB[0]))
        fb.setValue(len(tA)); cb.setValue(len(tA[0]))
        for sp in (fa, ca, fb, cb):
            sp.blockSignals(False)
        self.grid_A.reconstruir(len(tB), len(tB[0]), tB)
        self.grid_B.reconstruir(len(tA), len(tA[0]), tA)
        self._actualizar_titulos()
        self._actualizar_metodos_det()

    def cargar_AB(self, texto_A, texto_B):
        """Recibe A y b desde el solucionador."""
        for nombre, texto in (("A", texto_A), ("B", texto_B)):
            f, c = self.sp[nombre]
            f.blockSignals(True); c.blockSignals(True)
            f.setValue(len(texto)); c.setValue(len(texto[0]))
            f.blockSignals(False); c.blockSignals(False)
            self.grids[nombre].reconstruir(len(texto), len(texto[0]), texto)
        self._actualizar_titulos()
        self._actualizar_metodos_det()
        self._sin_resultado()
        self.mostrar_resultado("")

    def _sin_resultado(self):
        self.resultado_actual = None
        for b in self.btn_res.values():
            b.setEnabled(False)

    def _con_resultado(self, matriz):
        self.resultado_actual = matriz
        for b in self.btn_res.values():
            b.setEnabled(True)

    # ──────────────────────────────────────────────────────────
    # Lectura
    # ──────────────────────────────────────────────────────────

    def _leer_matriz(self, grid, nombre):
        matriz = []
        for i, fila_c in enumerate(grid.celdas):
            fila = []
            for j, c in enumerate(fila_c):
                try:
                    fila.append(desde_texto(c.text()))
                except (ValueError, ZeroDivisionError):
                    grid.marcar_error(i, j)
                    self.error(
                        "Dato inválido",
                        "El valor «{}» de {} (fila {}, columna {}) no es válido.\n\n"
                        "Use entero (-7), fracción (3/4), decimal (2.5) o raíz (√4)."
                        .format(c.text(), nombre, i + 1, j + 1))
                    return None
            matriz.append(fila)
        return matriz

    def _leer_escalar(self):
        try:
            return desde_texto(self.ed_escalar.text())
        except (ValueError, ZeroDivisionError):
            self.error("Escalar inválido",
                       "El escalar «{}» no es un número válido.".format(
                           self.ed_escalar.text()))
            return None

    def _leer_escalar_s(self):
        try:
            return desde_texto(self.ed_s.text())
        except (ValueError, ZeroDivisionError):
            self.error("Segundo escalar inválido",
                       "El valor «{}» no es un número válido para s.".format(
                           self.ed_s.text()))
            return None

    # ──────────────────────────────────────────────────────────
    # Operaciones
    # ──────────────────────────────────────────────────────────

    def ejecutar_operacion(self, operacion):
        self.ocultar_error()
        necesita_B = operacion in ("suma", "resta", "multiplicacion",
                                   "prop_suma", "prop_escalar",
                                   "prop", "prop_todas")

        A = self._leer_matriz(self.grid_A, "A")
        if A is None:
            return

        B = None
        if necesita_B:
            B = self._leer_B()
            if B is None:
                return

        try:
            if operacion in ("prop_suma", "prop_escalar", "prop", "prop_todas"):
                self._ejecutar_propiedad(operacion, A, B)
                return

            if operacion in ("inversa_gj", "inversa_adj"):
                self._mostrar_inversa(operacion, A)
                return

            resultado, titulo, pasos = self._calcular(operacion, A, B)
        except ValueError as ex:
            titulo_err = ("Matriz no invertible"
                          if operacion in ("det", "inversa_gj", "inversa_adj")
                          else "Dimensiones incompatibles")
            self.error(titulo_err, str(ex))
            return

        if resultado is None:
            return

        if operacion == "det":
            self._mostrar_determinante(A, resultado)
            return

        lineas = []
        if self.sw_pasos.isChecked() and pasos:
            lineas.extend(pasos)
            lineas.append("")
        lineas.extend(proc.texto_resultado(titulo, resultado))

        self._con_resultado(resultado)
        self.mostrar_resultado("\n".join(lineas), OP_ETIQUETAS.get(operacion, ""))

    def _mostrar_determinante(self, A, resultado):
        metodo = self.combo_det.currentText()
        es_3x3 = len(A) == 3 and len(A[0]) == 3
        if metodo == METODO_SARRUS and not es_3x3:
            metodo = METODO_COFACTORES
        val = resultado[0][0]
        if metodo == METODO_SARRUS:
            from modulos.modulo_matrices import determinante_sarrus
            val = determinante_sarrus(A)

        lineas = []
        if self.sw_pasos.isChecked():
            if metodo == METODO_SARRUS:
                lineas.extend(proc.pasos_determinante_sarrus(A))
            elif metodo == METODO_TRIANGULAR:
                lineas.extend(proc.pasos_determinante_triangular(A))
            else:
                lineas.extend(proc.pasos_determinante_cofactores(A))
            lineas.append("─" * 52)
            lineas.append("")
        lineas.append("det(A)  =  {}    (método: {})".format(val, metodo))
        lineas.append("")
        if val.es_cero():
            from modulos.modulo_matrices import rango
            r = rango(A)
            lineas.append(
                "La matriz A es SINGULAR: det(A) = 0,  "
                "tiene solo {} {} pivote (rango {}) y no tiene inversa.".format(
                    r, "posición" if r == 1 else "posiciones", r))
        else:
            lineas.append("La matriz A es invertible: det(A) ≠ 0.")
        self._sin_resultado()
        self.mostrar_resultado("\n".join(lineas), "det(A)")

    def _calcular(self, operacion, A, B):
        if operacion == "suma":
            return (alg.sumar_matrices(A, B), "A + B =", proc.pasos_suma(A, B))
        if operacion == "resta":
            return (alg.restar_matrices(A, B), "A − B =",
                    proc.pasos_suma(A, B, resta=True))
        if operacion == "multiplicacion":
            resultado = alg.multiplicar_matrices(A, B)
            titulo = "A × x =" if len(B[0]) == 1 else "A × B ="
            return resultado, titulo, proc.pasos_multiplicacion(A, B)
        if operacion == "escalar":
            r = self._leer_escalar()
            if r is None:
                return None, "", []
            return (alg.multiplicar_escalar(r, A), "{} · A =".format(r),
                    proc.pasos_escalar(r, A))
        if operacion == "transpuesta":
            return alg.transponer(A), "Aᵀ =", proc.pasos_transpuesta(A)
        if operacion == "det":
            from modulos.modulo_matrices import determinante
            return [[determinante(A)]], "det(A) =", []
        return None, "", []

    def _mostrar_cramer(self):
        self.ocultar_error()
        A = self._leer_matriz(self.grid_A, "A")
        if A is None:
            return
        B = self._leer_B()
        if B is None:
            return

        if len(B[0]) != 1:
            self.error("B no es un vector",
                       "B tiene {} columnas. Cramer necesita que B sea el vector b "
                       "(1 columna).".format(len(B[0])))
            return
        if len(A) != len(A[0]):
            self.error("A no es cuadrada",
                       "Cramer requiere A cuadrada (A es {}×{}).".format(
                           len(A), len(A[0])))
            return
        if len(B) != len(A):
            self.error("Dimensiones incompatibles",
                       "A tiene {} filas y b tiene {} componentes.".format(
                           len(A), len(B)))
            return

        from modulos.modulo_matrices import cramer, determinante

        b_vec = [B[i][0] for i in range(len(B))]
        n = len(A)
        try:
            det_A = determinante(A)
            sol = cramer(A, b_vec)
        except ValueError as ex:
            self.error("Regla de Cramer", str(ex))
            return

        lineas = []
        if self.sw_pasos.isChecked():
            lineas.extend(proc.pasos_cramer(A, b_vec))
            lineas.append("─" * 52)
            lineas.append("")
        lineas.extend(["Regla de Cramer:  A · x = b", "",
                       "det(A)  =  {}".format(det_A), ""])
        for i in range(n):
            Ai = [[A[fila][col] if col != i else b_vec[fila]
                   for col in range(n)] for fila in range(len(A))]
            det_Ai = determinante(Ai)
            lineas.append("  x{}  =  det(A{}) / det(A)  =  {}  /  {}  =  {}".format(
                i + 1, i + 1, det_Ai, det_A, sol[i]))
        lineas.append("")
        sol_mat = [[v] for v in sol]
        lineas.extend(proc.texto_resultado("x =", sol_mat))

        self._con_resultado(sol_mat)
        self.mostrar_resultado("\n".join(lineas), "Regla de Cramer")

    def _ejecutar_factorizacion_lu(self):
        """Factoriza A = L·U (A de cualquier tamaño) y, si se puede, resuelve A·x = b."""
        self.ocultar_error()
        A = self._leer_matriz(self.grid_A, "A")
        if A is None:
            return

        vector_b, nota = None, ""
        if len(A) != len(A[0]):
            nota = ("A no es cuadrada ({}×{}): se factorizó, pero no se resuelve "
                    "A · x = b.".format(len(A), len(A[0])))
        elif self.usa_B:
            B = self._leer_matriz(self.grid_B, "B")
            if B is None:
                return
            if len(B[0]) == 1 and len(B) == len(A):
                vector_b = [fila[0] for fila in B]
            else:
                nota = ("B no es un vector b de {} componentes (1 columna): se "
                        "factorizó, pero no se resuelve A · x = b.".format(len(A)))
        else:
            nota = "B está quitada: se factorizó, pero no se resuelve A · x = b."

        from modulos.modulo_lu import ejecutar_modulo_lu
        try:
            res = ejecutar_modulo_lu(A, vector_b, self.sw_pasos.isChecked())
        except ValueError as ex:
            self.error("Factorización LU", str(ex))
            return

        informe = res["informe"]
        if nota:
            informe += "\n" + nota

        # El resultado reutilizable es x si se resolvió; si no, la matriz U
        self._con_resultado([[v] for v in res["x"]] if res["x"] is not None
                            else res["U"])
        self.mostrar_resultado(informe, "Factorización LU")

    def _mostrar_inversa(self, operacion, A):
        from modulos.modulo_matrices import (determinante, inversa_gauss_jordan,
                                              inversa_adjunta, es_identidad)
        det = determinante(A)
        n = len(A)
        if det.es_cero():
            raise ValueError("La matriz A es singular: det(A) = 0. No tiene inversa.")

        if operacion == "inversa_gj":
            inv, metodo = inversa_gauss_jordan(A), "Gauss-Jordan"
        else:
            inv, metodo = inversa_adjunta(A), "Adjunta"

        producto = alg.multiplicar_matrices(A, inv)
        ok = es_identidad(producto)

        lineas = []
        if self.sw_pasos.isChecked():
            if operacion == "inversa_gj":
                lineas.extend(proc.pasos_inversa_gauss_jordan(A))
            else:
                lineas.extend(proc.pasos_inversa_adjunta(A))
            lineas.append("─" * 52)
            lineas.append("")
        lineas.extend(["det(A)  =  {}".format(det), ""])
        lineas.extend(proc.texto_resultado("A⁻¹  ({}) =".format(metodo), inv))
        lineas.append("")
        lineas.extend(proc.texto_resultado("Comprobación  A · A⁻¹ =", producto))
        lineas.append("")
        if ok:
            lineas.append("A · A⁻¹ = I  (verificación exacta con aritmética de fracciones).")
        else:
            lineas.append("[ERROR] La verificación A · A⁻¹ = I falló.")
        lineas.append("")
        lineas.append(
            "La matriz A es invertible: det(A) ≠ 0, tiene {} posiciones pivote, "
            "sus columnas son L.I. y generan ℝ{}.".format(n, n))

        self._con_resultado(inv)
        self.mostrar_resultado("\n".join(lineas), OP_ETIQUETAS[operacion])

    def _ejecutar_propiedad(self, operacion, A, B):
        r = self._leer_escalar()
        if r is None:
            return
        s = self._leer_escalar_s()
        if s is None:
            return

        C = None
        if self.usa_C:
            C = self._leer_matriz(self.grid_C, "C")
            if C is None:
                return

        try:
            if operacion == "prop_todas":
                lineas = prop.verificar_todas(A, B, r, C, s)
            else:
                if operacion in ("prop_suma", "prop_escalar"):
                    clave = "mv_suma" if operacion == "prop_suma" else "mv_escalar"
                else:
                    clave = prop.clave_de_etiqueta(self.combo_prop.currentText())
                    if clave is None:
                        self.error("Error", "Propiedad no reconocida.")
                        return
                lineas, _ = prop.verificar(clave, A, B, r, C, s)
        except (ValueError, ZeroDivisionError) as ex:
            self.error("No se puede verificar", str(ex))
            return

        self._sin_resultado()
        self.mostrar_resultado(
            "\n".join(lineas),
            "Todas las propiedades" if operacion == "prop_todas"
            else "Propiedad: " + self.combo_prop.currentText())

    def usar_resultado(self, destino):
        if self.resultado_actual is None:
            return
        texto = [[str(v) for v in fila] for fila in self.resultado_actual]
        f, c = self.sp[destino]
        f.blockSignals(True); c.blockSignals(True)
        f.setValue(len(texto)); c.setValue(len(texto[0]))
        f.blockSignals(False); c.blockSignals(False)
        self.grids[destino].reconstruir(len(texto), len(texto[0]), texto)
        self._actualizar_titulos()
        self._actualizar_metodos_det()
        mostrar_aviso(self, "Resultado copiado en {}".format(destino), "info")

    # ──────────────────────────────────────────────────────────
    # Salida
    # ──────────────────────────────────────────────────────────

    def mostrar_resultado(self, texto, etiqueta="", registrar=True):
        self._texto_res = texto.strip()
        self._etiqueta_res = etiqueta
        self.txt.setPlainText(("\n" + texto + "\n") if texto else "")
        if texto:
            aparecer(self.txt, 200, color=T.PANEL)
        if texto and etiqueta and registrar:
            matriz = None
            if self.resultado_actual is not None:
                matriz = [[str(v) for v in fila] for fila in self.resultado_actual]
            self._historial.insert(0, {
                "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                "etiqueta": etiqueta, "texto": texto, "matriz": matriz})
            del self._historial[MAX_HISTORIAL:]

    # ── Historial de resultados ───────────────────────────────

    def _menu_historial(self):
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        if not self._historial:
            accion = menu.addAction("Todavía no hay resultados")
            accion.setEnabled(False)
        else:
            for i, e in enumerate(self._historial):
                menu.addAction("{}  ·  {}".format(e["hora"], e["etiqueta"]),
                               lambda _=False, k=i: self._cargar_historial(k))
            menu.addSeparator()
            menu.addAction("Borrar historial", self._borrar_historial)
        b = self.btn_historial
        menu.exec(b.mapToGlobal(QPoint(0, b.height() + 4)))

    def _cargar_historial(self, indice):
        e = self._historial[indice]
        matriz = None
        if e["matriz"]:
            try:
                matriz = [[desde_texto(v) for v in fila] for fila in e["matriz"]]
            except (ValueError, ZeroDivisionError):
                matriz = None
        if matriz is not None:
            self._con_resultado(matriz)
        else:
            self._sin_resultado()
        self.mostrar_resultado(e["texto"], e["etiqueta"], registrar=False)

    def _borrar_historial(self):
        self._historial.clear()
        mostrar_aviso(self, "Historial borrado", "info")

    def copiar_resultado(self):
        if not self._texto_res:
            return
        QApplication.clipboard().setText(self._texto_res)
        mostrar_aviso(self, "Resultado copiado al portapapeles")

    def copiar_resultado_imagen(self):
        """Copia todo el resultado (con sus pasos) como imagen."""
        if not self._texto_res:
            return
        QApplication.clipboard().setImage(imagen_de_texto(self._texto_res))
        mostrar_aviso(self, "Resultado copiado como imagen")

    def copiar_matriz_resultado_imagen(self):
        """Copia solo la matriz resultado, limpia y entre corchetes, como imagen."""
        if self.resultado_actual is None:
            mostrar_aviso(self, "Este resultado no es una matriz", "info")
            return
        textos = [[str(v) for v in fila] for fila in self.resultado_actual]
        QApplication.clipboard().setImage(imagen_de_matriz(textos))
        mostrar_aviso(self, "Matriz resultado copiada como imagen")

    def abrir_en_ventana(self):
        if not self._texto_res:
            self.info("Sin resultado", "Todavía no hay nada que mostrar.")
            return
        abrir_visor("Resultado", self._texto_res, "informe_matrices")

    def guardar_informe(self):
        if not self._texto_res:
            self.info("Sin resultado", "Todavía no hay nada que guardar.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", "informe_matrices.txt",
            "Texto (*.txt);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._texto_res + "\n")
            mostrar_aviso(self, "Informe guardado")
        except OSError as ex:
            self.error("Error al guardar", str(ex))

    # ──────────────────────────────────────────────────────────
    # Envío al solucionador
    # ──────────────────────────────────────────────────────────

    def enviar_al_solucionador(self, modo):
        self.ocultar_error()
        """
        "matricial"     -> [A | b], el sistema A·x = b
        "combinacion"   -> [A | b], leído como «¿es b combinación lineal de A?»
        "independencia" -> [A | 0], sistema homogéneo de independencia
        """
        A = self._leer_matriz(self.grid_A, "A")
        if A is None:
            return

        filas, columnas = len(A), len(A[0])
        textos_A = self.grid_A.textos()

        if modo == "independencia":
            celdas = [fila + ["0"] for fila in textos_A]
        else:
            B = self._leer_B()
            if B is None:
                return
            if len(B[0]) != 1:
                self.error("B no es un vector",
                           "B tiene {} columnas. Para enviar el sistema, B debe ser "
                           "el vector b: pon 1 en «Cols (p)».".format(len(B[0])))
                return
            if len(B) != filas:
                self.error("Dimensiones incompatibles",
                           "A tiene {} filas y b tiene {} componentes.\n\n"
                           "El vector b debe tener una componente por cada fila de A."
                           .format(filas, len(B)))
                return
            textos_B = self.grid_B.textos()
            celdas = [textos_A[i] + [textos_B[i][0]] for i in range(filas)]

        self.ventana.pagina_solucionador.cargar_sistema(celdas, filas, columnas, modo)
        self.ventana.ir_a("solucionador")

    # ──────────────────────────────────────────────────────────
    # Exportar a PDF
    # ──────────────────────────────────────────────────────────

    def exportar_pdf(self):
        if not self._texto_res:
            self.info("Sin resultado", "Todavía no hay nada que exportar.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", "informe_matrices.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        titulo = "Resultado" + (": " + self._etiqueta_res if self._etiqueta_res else "")
        try:
            with T.paleta_temporal("impreso"):
                cuerpo = render.html_texto(self._texto_res)
            escribir_pdf(ruta, titulo, cuerpo)
            mostrar_aviso(self, "PDF guardado")
        except OSError as ex:
            self.error("Error al guardar", str(ex))

    # ──────────────────────────────────────────────────────────
    # Estado guardable (se recupera al volver a abrir el programa)
    # ──────────────────────────────────────────────────────────

    def estado(self):
        return {
            "tamanos": {n: [self.sp[n][0].value(), self.sp[n][1].value()]
                        for n in "ABC"},
            "textos": {n: self.grids[n].textos() for n in "ABC"},
            "usa_B": self.usa_B,
            "usa_C": self.usa_C,
            "escalar": self.ed_escalar.text(),
            "s": self.ed_s.text(),
            "pasos": self.sw_pasos.isChecked(),
            "metodo": self.combo_det.currentText(),
            "propiedad": self.combo_prop.currentIndex(),
            "resultado": self._texto_res,
            "etiqueta": self._etiqueta_res,
            "matriz": ([[str(v) for v in fila] for fila in self.resultado_actual]
                       if self.resultado_actual is not None else None),
            "historial": self._historial,
        }

    def restaurar(self, d):
        try:
            for n in "ABC":
                texto = d["textos"][n]
                f, c = self.sp[n]
                f.blockSignals(True)
                c.blockSignals(True)
                f.setValue(len(texto))
                c.setValue(len(texto[0]))
                f.blockSignals(False)
                c.blockSignals(False)
                self.grids[n].reconstruir(len(texto), len(texto[0]), texto)
            self.ed_escalar.setText(d.get("escalar", "2"))
            self.ed_s.setText(d.get("s", "3"))
            self.sw_pasos.setChecked(bool(d.get("pasos", True)))
            self._actualizar_titulos()
            self._actualizar_metodos_det()
            if d.get("metodo") in self._metodos_det_disponibles():
                self.combo_det.setCurrentText(d["metodo"])
            self.combo_prop.setCurrentIndex(
                min(int(d.get("propiedad", 0)), self.combo_prop.count() - 1))
            for n in ("B", "C"):
                if not d.get("usa_" + n, True):
                    self.alternar_matriz(n)
            self._historial = list(d.get("historial", []))[:MAX_HISTORIAL]
            if d.get("resultado"):
                if d.get("matriz"):
                    self._con_resultado([[desde_texto(v) for v in fila]
                                         for fila in d["matriz"]])
                self.mostrar_resultado(d["resultado"], d.get("etiqueta", ""),
                                       registrar=False)
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
            pass                      # datos viejos o dañados: se ignoran

    # ──────────────────────────────────────────────────────────
    # Tamaño de letra
    # ──────────────────────────────────────────────────────────

    def _estilo_resultado(self):
        self.txt.setStyleSheet("font-family: '{}'; font-size: {}pt;".format(
            T.MONO, T.tam(11)))

    def aplicar_escala(self):
        """Redibuja las cuadrículas y el resultado con la letra actual."""
        for g in self.grids.values():
            g.reconstruir(g.filas(), g.columnas(), registrar=False)
        self._estilo_resultado()