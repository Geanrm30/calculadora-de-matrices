# -*- coding: utf-8 -*-
"""
Solucionador de sistemas A·x = b por eliminación de Gauss y Gauss-Jordan con
aritmética exacta de fracciones (versión PySide6).
"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QSpinBox, QSplitter,
                               QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from core.fraccion import desde_texto
from core.formato import (subindice, nombre_variable, texto_ecuacion,
                          subtitulo, separador)
from solver.clasificacion import INCONSISTENTE, INDETERMINADO
from solver.solucion import texto_expresion
from solver.resolutor import resolver as _resolver
from output.reporte import (generar, seccion_clasificacion, seccion_solucion,
                            seccion_verificacion, secciones_en_rn)

from qt import tema as T
from qt import render
from qt.componentes import (BotonAnimado, CuadriculaMatriz, Interruptor,
                            Tarjeta, agregar_acciones_grid, aparecer,
                            mostrar_aviso)
from qt.ejemplos import SISTEMAS
from qt.exportar import escribir_pdf
from qt.pagina_base import PaginaBase
from qt.visor import abrir_visor

LIMITE = 20

MENSAJES_CONTEXTO = {
    "matricial": "Ecuación matricial A·x = b enviada desde Operaciones con matrices.",
    "combinacion": ("Combinación lineal: se pregunta si b es combinación de las "
                    "columnas de A. Las xᵢ son los escalares."),
    "independencia": ("Independencia lineal: sistema homogéneo A·x = 0 de las "
                      "columnas de A. Solución única = independientes."),
}


class PaginaSolucionador(PaginaBase):

    def __init__(self, ventana):
        super().__init__(ventana, "Sistemas de ecuaciones lineales",
                         "Método matricial · operaciones elementales por filas "
                         "· aritmética exacta")

        self._contexto = None
        self._resultado = None
        self._informe = ""
        self._pasos = []
        self._idx = 0
        self._r = None
        self._reproduciendo = False
        self._reloj = QTimer(self)
        self._reloj.timeout.connect(self._tick)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.addWidget(self._panel_izquierdo())
        split.addWidget(self._panel_derecho())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([450, 830])
        self.raiz.addWidget(split, 1)

        self.generar_casillas()
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.resolver,
                  context=Qt.WidgetWithChildrenShortcut)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.resolver,
                  context=Qt.WidgetWithChildrenShortcut)

    # ──────────────────────────────────────────────────────────
    # Construcción
    # ──────────────────────────────────────────────────────────

    def _panel_izquierdo(self):
        w = QWidget()
        w.setMinimumWidth(410)
        w.setMaximumWidth(540)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(12)

        b_ej = BotonAnimado("Probar un ejemplo", "azul")
        b_ej.con_menu([(nombre, lambda _=False, i=i: self.cargar_ejemplo(i))
                       for i, (nombre, *_r) in enumerate(SISTEMAS)])
        lay.addWidget(b_ej)

        # Tamaño
        t = Tarjeta("Tamaño del sistema")
        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.sp_m = self._spin(3)
        self.sp_n = self._spin(3)
        for texto, sp in (("Ecuaciones (m)", self.sp_m), ("Variables (n)", self.sp_n)):
            col = QVBoxLayout()
            col.setSpacing(4)
            l = QLabel(texto)
            l.setObjectName("nota")
            col.addWidget(l)
            col.addWidget(sp)
            fila.addLayout(col)
        t.agregar_layout(fila)
        b = BotonAnimado("Generar cuadrícula", "suave")
        b.clicked.connect(self.generar_casillas)
        t.agregar(b)
        lay.addWidget(t)

        # Matriz aumentada
        t2 = Tarjeta("Matriz [A | b]", T.AZUL)
        self.cuadricula = CuadriculaMatriz(corchetes=True, aumentada=True,
                                           max_filas=LIMITE, max_cols=LIMITE)
        self.cuadricula.forma_cambiada.connect(self._forma_cambiada)
        agregar_acciones_grid(t2, self.cuadricula)
        t2.agregar(self.cuadricula, 1)
        nota = QLabel("Enteros (-7), fracciones (3/4), decimales (2.5), raíces (√4).")
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        t2.agregar(nota)
        lay.addWidget(t2, 1)

        # Opciones y acciones
        self.sw_jordan = Interruptor("Incluir forma escalonada reducida (Gauss-Jordan)", True)
        self.sw_vectores = Interruptor("Incluir análisis en Rⁿ (comb. lineal e independencia)", False)
        lay.addWidget(self.sw_jordan)
        lay.addWidget(self.sw_vectores)

        self.btn_resolver = BotonAnimado("RESOLVER", "primario")
        self.btn_resolver.setMinimumHeight(46)
        self.btn_resolver.clicked.connect(self.resolver)
        lay.addWidget(self.btn_resolver)
        atajo = QLabel("Ctrl + Enter para resolver rápidamente")
        atajo.setObjectName("nota")
        atajo.setAlignment(Qt.AlignRight)
        lay.addWidget(atajo)

        bl = BotonAnimado("Limpiar", "suave")
        bl.clicked.connect(self.limpiar)
        lay.addWidget(bl)
        return w

    def _spin(self, valor):
        sp = QSpinBox()
        sp.setRange(1, LIMITE)
        sp.setValue(valor)
        sp.valueChanged.connect(lambda _: self.generar_casillas())
        return sp

    def _panel_derecho(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(10)

        # Barra de estado y acciones
        barra = QFrame()
        barra.setObjectName("barra")
        bv = QVBoxLayout(barra)
        bv.setContentsMargins(16, 12, 12, 10)
        bv.setSpacing(8)
        self.lbl_estado = QLabel("Ingrese el sistema y presione RESOLVER.")
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setStyleSheet(
            "color: {}; font-weight: 700; background: transparent;".format(T.MUTED))
        bv.addWidget(self.lbl_estado)

        bl = QHBoxLayout()
        bl.setSpacing(6)
        for texto, cmd in (("Enviar [A | b] a Operaciones", self.enviar_a_matrices),
                           ("Abrir en ventana", self.abrir_en_ventana),
                           ("Copiar informe", self.copiar_informe)):
            b = BotonAnimado(texto, "suave", pequeno=True)
            b.clicked.connect(cmd)
            bl.addWidget(b)
        b_guardar = BotonAnimado("Guardar informe", "suave", pequeno=True)
        b_guardar.con_menu([("Texto (.txt)", self.guardar_informe),
                            ("PDF (.pdf)", self.exportar_pdf)])
        bl.addWidget(b_guardar)
        bl.addStretch(1)
        bv.addLayout(bl)
        lay.addWidget(barra)

        self.lbl_contexto = QLabel("")
        self.lbl_contexto.setObjectName("contexto")
        self.lbl_contexto.setWordWrap(True)
        self.lbl_contexto.hide()
        lay.addWidget(self.lbl_contexto)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_proceso(), "Sistema y eliminación")
        self.tabs.addTab(self._tab_solucion(), "Solución y verificación")
        lay.addWidget(self.tabs, 1)
        return w

    def _tab_proceso(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(8)

        self.lbl_ptitulo = QLabel("Presione RESOLVER para comenzar.")
        self.lbl_ptitulo.setStyleSheet(
            "color: {}; font-weight: 700; font-size: 11pt;".format(T.MUTED))
        self.lbl_poper = QLabel("")
        self.lbl_poper.setStyleSheet(
            "font-family: '{}'; font-size: 12pt; font-weight: 700;".format(T.MONO))
        self.lbl_pcom = QLabel("")
        self.lbl_pcom.setStyleSheet(
            "color: {}; font-style: italic;".format(T.MUTED))
        self.lbl_pcom.setWordWrap(True)
        for l in (self.lbl_ptitulo, self.lbl_poper, self.lbl_pcom):
            lay.addWidget(l)

        self.vista = QTextBrowser()
        self.vista.setOpenLinks(False)
        lay.addWidget(self.vista, 1)

        nav = QHBoxLayout()
        nav.setSpacing(6)
        self.b_ini = BotonAnimado("⏮  Inicio", "suave", pequeno=True)
        self.b_prev = BotonAnimado("◀  Anterior", "suave", pequeno=True)
        self.b_next = BotonAnimado("Siguiente  ▶", "azul", pequeno=True)
        self.b_fin = BotonAnimado("Final  ⏭", "suave", pequeno=True)
        self.b_play = BotonAnimado("▶  Reproducir", "verde", pequeno=True)
        self.b_play.clicked.connect(self._alternar_reproduccion)
        self.combo_vel = QComboBox()
        for texto, ms in (("Lenta", 2200), ("Normal", 1300), ("Rápida", 600)):
            self.combo_vel.addItem(texto, ms)
        self.combo_vel.setCurrentIndex(1)
        self.combo_vel.setToolTip("Velocidad de la reproducción")
        self.combo_vel.currentIndexChanged.connect(self._cambio_velocidad)
        self.lbl_nav = QLabel("")
        self.lbl_nav.setStyleSheet("color: {}; font-weight: 600;".format(T.MUTED))
        self.b_ini.clicked.connect(lambda: self._ir(0))
        self.b_prev.clicked.connect(self._prev)
        self.b_next.clicked.connect(self._next)
        self.b_fin.clicked.connect(lambda: self._ir(-1))
        for b in (self.b_ini, self.b_prev, self.b_next, self.b_fin):
            b.setEnabled(False)
            nav.addWidget(b)
        self.b_play.setEnabled(False)
        nav.addSpacing(10)
        nav.addWidget(self.b_play)
        nav.addWidget(self.combo_vel)
        nav.addStretch(1)
        nav.addWidget(self.lbl_nav)
        lay.addLayout(nav)

        QShortcut(QKeySequence("Right"), w, activated=self._next,
                  context=Qt.WidgetWithChildrenShortcut)
        QShortcut(QKeySequence("Left"), w, activated=self._prev,
                  context=Qt.WidgetWithChildrenShortcut)
        return w

    def _tab_solucion(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        self.vista_sol = QTextBrowser()
        self.vista_sol.setOpenLinks(False)
        lay.addWidget(self.vista_sol)
        return w

    # ──────────────────────────────────────────────────────────
    # Cuadrícula
    # ──────────────────────────────────────────────────────────

    def generar_casillas(self):
        self.cuadricula.reconstruir(self.sp_m.value(), self.sp_n.value() + 1)

    def _forma_cambiada(self, filas, cols):
        """Deshacer / rehacer / pegar cambiaron el tamaño de la cuadrícula."""
        self.sp_m.blockSignals(True)
        self.sp_n.blockSignals(True)
        self.sp_m.setValue(filas)
        self.sp_n.setValue(cols - 1)
        self.sp_m.blockSignals(False)
        self.sp_n.blockSignals(False)

    def cargar_ejemplo(self, indice):
        nombre, detalle, m, n, celdas = SISTEMAS[indice]
        self._contexto = None
        self._mostrar_contexto()
        self._poner_sistema(m, n, celdas)
        self.resolver()
        mostrar_aviso(self, "Ejemplo: {}. {}".format(nombre, detalle), "info")

    def _poner_sistema(self, m, n, celdas):
        self.sp_m.blockSignals(True)
        self.sp_n.blockSignals(True)
        self.sp_m.setValue(m)
        self.sp_n.setValue(n)
        self.sp_m.blockSignals(False)
        self.sp_n.blockSignals(False)
        self.cuadricula.reconstruir(m, n + 1, celdas)

    def construir_matriz(self):
        matriz = []
        for i, fila_c in enumerate(self.cuadricula.celdas):
            fila = []
            n = len(fila_c) - 1
            for j, c in enumerate(fila_c):
                try:
                    fila.append(desde_texto(c.text()))
                except (ValueError, ZeroDivisionError):
                    etiq = ("b{}".format(i + 1) if j == n
                            else "x{} ec.{}".format(subindice(j + 1), i + 1))
                    self.cuadricula.marcar_error(i, j)
                    self.error("Dato inválido",
                               "El valor «{}» en {} no es válido.\n\n"
                               "Use entero (-7), fracción (3/4) o decimal (2.5)."
                               .format(c.text(), etiq))
                    return None
            matriz.append(fila)
        return matriz

    # ──────────────────────────────────────────────────────────
    # Acciones
    # ──────────────────────────────────────────────────────────

    def resolver(self):
        self._parar()
        matriz = self.construir_matriz()
        if matriz is None:
            return

        n_vars = self.sp_n.value()
        jordan = self.sw_jordan.isChecked()
        vectores = self.sw_vectores.isChecked()

        try:
            resultado = _resolver(matriz, n_vars, aplicar_jordan=jordan)
        except Exception as ex:                      # noqa: BLE001
            self.error("Error al resolver", "Ocurrió un problema: {}".format(ex))
            return

        self._resultado = resultado
        self._informe = generar(resultado, incluir_jordan=jordan,
                                incluir_vectores=vectores,
                                contexto=self._contexto)

        tipo = resultado["analisis"]["tipo"]
        nombre = resultado["analisis"]["nombre"]
        color = T.ROJO if tipo == INCONSISTENTE else T.VERDE
        self.lbl_estado.setText(nombre)
        self.lbl_estado.setStyleSheet(
            "color: {}; font-weight: 700; background: transparent;".format(color))

        self._poblar_proceso(resultado)
        self.vista_sol.setHtml(render.pagina(
            self._html_solucion(resultado, jordan, vectores)))
        self.tabs.setCurrentIndex(0)

    def limpiar(self):
        self._parar()
        self.cuadricula.limpiar()
        self._resultado = None
        self._informe = ""
        self._contexto = None
        self._mostrar_contexto()
        self.lbl_estado.setText("Ingrese el sistema y presione RESOLVER.")
        self.lbl_estado.setStyleSheet(
            "color: {}; font-weight: 700; background: transparent;".format(T.MUTED))
        self.lbl_ptitulo.setText("Presione RESOLVER para comenzar.")
        self.lbl_ptitulo.setStyleSheet(
            "color: {}; font-weight: 700; font-size: 11pt;".format(T.MUTED))
        self.lbl_poper.setText("")
        self.lbl_pcom.setText("")
        self.lbl_nav.setText("")
        self.vista.clear()
        self.vista_sol.clear()
        self._pasos = []
        for b in (self.b_ini, self.b_prev, self.b_next, self.b_fin, self.b_play):
            b.setEnabled(False)

    def cargar_sistema(self, celdas, filas, columnas, contexto):
        """Recibe [A | b] desde Operaciones y lo resuelve de inmediato."""
        self._poner_sistema(filas, columnas, celdas)
        self._contexto = contexto
        self._mostrar_contexto()
        self.resolver()

    def _mostrar_contexto(self):
        texto = MENSAJES_CONTEXTO.get(self._contexto)
        if texto:
            self.lbl_contexto.setText(texto)
            self.lbl_contexto.show()
            aparecer(self.lbl_contexto, 300)
        else:
            self.lbl_contexto.hide()

    def enviar_a_matrices(self):
        celdas = self.cuadricula.textos()
        if not celdas:
            return
        n = self.sp_n.value()
        texto_A = [fila[:n] for fila in celdas]
        texto_b = [[fila[n]] for fila in celdas]
        self.ventana.pagina_matrices.cargar_AB(texto_A, texto_b)
        self.ventana.ir_a("matrices")

    def copiar_informe(self):
        if not self._informe:
            return
        QApplication.clipboard().setText(self._informe)
        mostrar_aviso(self, "Informe copiado al portapapeles")

    def abrir_en_ventana(self):
        if not self._informe:
            self.info("Sin resultado", "Primero resuelva un sistema con RESOLVER.")
            return
        abrir_visor(self, "Solución y verificación", self._informe, "informe.txt")

    def guardar_informe(self):
        if not self._informe:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", "informe.txt",
            "Texto (*.txt);;Todos los archivos (*.*)")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._informe)
            mostrar_aviso(self, "Informe guardado")
        except OSError as ex:
            self.error("Error al guardar", str(ex))

    # ──────────────────────────────────────────────────────────
    # Pestaña 1 — proceso paso a paso
    # ──────────────────────────────────────────────────────────

    def _poblar_proceso(self, r):
        self._r = r
        self._pasos = []
        for p in r["pasos"]:
            self._pasos.append({"tipo": "Eliminación", "operacion": p["operacion"],
                                "comentario": p["comentario"], "matriz": p["matriz"]})
        jordan = r.get("pasos_jordan")
        if jordan is not None:
            for p in jordan:
                self._pasos.append({"tipo": "Gauss-Jordan", "operacion": p["operacion"],
                                    "comentario": p["comentario"], "matriz": p["matriz"]})
        self._idx = 0
        self._actualizar_proceso()

    def _titulo(self, texto, color):
        self.lbl_ptitulo.setText(texto)
        self.lbl_ptitulo.setStyleSheet(
            "color: {}; font-weight: 700; font-size: 11pt;".format(color))

    def _actualizar_proceso(self):
        r = self._r
        pasos = self._pasos
        idx = self._idx
        n_vars = r["n_vars"]
        pivotes = r["columnas_pivote"]
        total = len(pasos)
        n_elim = len(r["pasos"])
        jordan = r.get("pasos_jordan")
        n_jordan = len(jordan) if jordan else 0

        if idx == 0:
            partes = []
            if n_elim > 0:
                partes.append("{} paso{} de eliminación".format(
                    n_elim, "s" if n_elim != 1 else ""))
            if n_jordan > 0:
                partes.append("{} paso{} de Gauss-Jordan".format(
                    n_jordan, "s" if n_jordan != 1 else ""))
            resumen = " · ".join(partes) if partes else "matriz ya escalonada"
            self._titulo("Sistema original — {} × {}   ({})".format(
                r["n_ecuaciones"], n_vars, resumen), T.AZUL)
            self.lbl_poper.setText("")
            self.lbl_pcom.setText("")
            cuerpo = self._html_sistema_original(r, pivotes)
        elif idx <= total:
            p = pasos[idx - 1]
            if p["tipo"] == "Eliminación":
                num, tot, col = idx, n_elim, T.NARANJA
            else:
                num, tot, col = idx - n_elim, n_jordan, T.AZUL
            self._titulo("{} — Paso {} / {}".format(p["tipo"], num, tot), col)
            self.lbl_poper.setText(p["operacion"])
            self.lbl_pcom.setText(p["comentario"])
            anterior = r["original"] if idx == 1 else pasos[idx - 2]["matriz"]
            cambiadas = {i for i, fila in enumerate(p["matriz"])
                         if any(fila[j] != anterior[i][j]
                                for j in range(len(fila)))}
            cuerpo = render.html_matriz(p["matriz"], n_vars, pivotes, cambiadas)
        else:
            self._titulo("Proceso completo — todos los pasos", T.VERDE)
            self.lbl_poper.setText("")
            self.lbl_pcom.setText("")
            cuerpo = self._html_todos(r, pivotes)

        self.vista.setHtml(render.pagina(cuerpo))
        aparecer(self.vista, 180)

        self.lbl_nav.setText("Completo" if idx > total else "{} / {}".format(idx, total))
        self.b_ini.setEnabled(idx > 0)
        self.b_prev.setEnabled(idx > 0)
        self.b_next.setEnabled(idx <= total)
        self.b_fin.setEnabled(idx <= total)
        self.b_play.setEnabled(total > 0)

    def _html_sistema_original(self, r, pivotes):
        n_vars = r["n_vars"]
        ecs = "\n".join("  " + texto_ecuacion(f, n_vars) for f in r["original"])
        cuerpo = [render.etiqueta("Sistema ingresado:"),
                  render.html_texto(ecs),
                  render.etiqueta("Matriz aumentada [A | b]:"),
                  render.html_matriz(r["original"], n_vars, pivotes)]
        if r["analisis"]["homogeneo"]:
            cuerpo.append(render.etiqueta(
                "Sistema homogéneo — siempre consistente "
                "(admite al menos la solución trivial)."))
        return "".join(cuerpo)

    def _html_todos(self, r, pivotes):
        n_vars = r["n_vars"]
        n_elim = len(r["pasos"])
        j_pasos = r.get("pasos_jordan") or []
        ecs = "\n".join("  " + texto_ecuacion(f, n_vars) for f in r["original"])
        cuerpo = [render.etiqueta("Sistema ingresado:"),
                  render.html_texto(ecs),
                  render.etiqueta("Matriz aumentada [A | b]:"),
                  render.html_matriz(r["original"], n_vars, pivotes)]

        for i, p in enumerate(self._pasos):
            if p["tipo"] == "Eliminación":
                num, tot, col = i + 1, n_elim, T.NARANJA
            else:
                num, tot, col = i - n_elim + 1, len(j_pasos), T.AZUL
            cuerpo.append("<hr style='color:{}'>".format(T.SUPERF))
            cuerpo.append("<p style='color:{}; font-weight:bold; margin:6px 0 2px 0;"
                          " font-family:{};'>{} — Paso {} / {}</p>".format(
                              col, T.FUENTE, p["tipo"], num, tot))
            cuerpo.append(render.html_texto(p["operacion"]))
            if p.get("comentario"):
                cuerpo.append(render.etiqueta(p["comentario"]))
            cuerpo.append(render.html_matriz(p["matriz"], n_vars, pivotes))
        return "".join(cuerpo)

    def _ir(self, idx):
        self._parar()
        total = len(self._pasos)
        self._idx = (total + 1) if idx == -1 else max(0, min(idx, total + 1))
        self._actualizar_proceso()

    def _prev(self):
        self._parar()
        if self._pasos and self._idx > 0:
            self._idx -= 1
            self._actualizar_proceso()

    def _next(self):
        self._parar()
        if self._pasos and self._idx <= len(self._pasos):
            self._idx += 1
            self._actualizar_proceso()

    # ──────────────────────────────────────────────────────────
    # Pestaña 2 — solución y verificación
    # ──────────────────────────────────────────────────────────

    def _html_solucion(self, r, jordan, vectores):
        """HTML de la pestaña «Solución y verificación»."""
        h = []
        add = lambda s: h.append(render.html_texto(s))      # noqa: E731

        add(separador("="))
        add("  CLASIFICACIÓN · SOLUCIÓN · VERIFICACIÓN")
        add(separador("="))

        tiene_jordan = jordan and r.get("reducida") is not None
        matriz_final = r["reducida"] if tiene_jordan else r["escalonada"]
        titulo = ("Matriz en forma escalonada reducida (RREF):" if tiene_jordan
                  else "Matriz en forma escalonada:")
        h.append(render.etiqueta(titulo, T.TEXTO))
        h.append(render.html_matriz(matriz_final, r["n_vars"], r["columnas_pivote"]))

        numero = 4 if tiene_jordan else 3
        add(seccion_clasificacion(r, numero))
        numero += 1

        for seccion in secciones_en_rn(r, vectores, self._contexto):
            add(seccion(r, numero))
            numero += 1

        if r["analisis"]["tipo"] == INDETERMINADO:
            expresiones = r["expresiones"]
            libres = r["libres"]
            n_vars = r["n_vars"]

            add(subtitulo("{}. SOLUCIÓN".format(numero)))
            h.append(render.etiqueta("Solución general (forma vectorial):", T.TEXTO))
            h.append(render.html_vector_solucion(r))
            add("  donde {} ∈ ℝ (parámetro libre).".format(
                ", ".join(nombre_variable(c) for c in libres)))

            h.append(render.etiqueta("Solución general parametrizada:", T.TEXTO))
            lineas = []
            for j in range(n_vars):
                if j in libres:
                    lineas.append("  {} = {}   (parámetro libre)".format(
                        nombre_variable(j), nombre_variable(j)))
                else:
                    lineas.append("  {} = {}".format(
                        nombre_variable(j), texto_expresion(expresiones[j], libres)))
            add("\n".join(lineas))

            x = r["solucion"]
            valores = ", ".join("{} = {}".format(nombre_variable(j), x[j])
                                for j in range(n_vars))
            h.append(render.etiqueta(
                "Solución particular tomando todas las variables libres = 0:", T.TEXTO))
            add("  " + valores)
        else:
            add(seccion_solucion(r, numero))

        add(seccion_verificacion(r, numero + 1))
        add(separador("="))
        return "".join(h)

    # ──────────────────────────────────────────────────────────
    # Reproductor automático de los pasos
    # ──────────────────────────────────────────────────────────

    def _alternar_reproduccion(self):
        if self._reproduciendo:
            self._parar()
            return
        total = len(self._pasos)
        if not total:
            return
        if self._idx >= total:                # ya estaba al final: reinicia
            self._idx = 0
            self._actualizar_proceso()
        self._reproduciendo = True
        self.b_play.setText("⏸  Pausa")
        self._reloj.start(self.combo_vel.currentData())

    def _parar(self):
        self._reloj.stop()
        if self._reproduciendo:
            self._reproduciendo = False
        self.b_play.setText("▶  Reproducir")

    def _cambio_velocidad(self):
        if self._reproduciendo:
            self._reloj.start(self.combo_vel.currentData())

    def _tick(self):
        if self._idx < len(self._pasos):
            self._idx += 1
            self._actualizar_proceso()
        if self._idx >= len(self._pasos):
            self._parar()

    # ──────────────────────────────────────────────────────────
    # Exportar a PDF
    # ──────────────────────────────────────────────────────────

    def exportar_pdf(self):
        if self._resultado is None:
            self.info("Sin resultado", "Primero resuelva un sistema con RESOLVER.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", "informe.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        r = self._resultado
        try:
            with T.paleta_temporal("impreso"):
                cuerpo = "".join([
                    "<h3>{}</h3>".format(r["analisis"]["nombre"]),
                    self._html_todos(r, r["columnas_pivote"]),
                    "<hr style='color:{}'>".format(T.BORDE),
                    self._html_solucion(r, self.sw_jordan.isChecked(),
                                        self.sw_vectores.isChecked()),
                ])
            escribir_pdf(ruta, "Solución de un sistema de ecuaciones lineales",
                         cuerpo)
            mostrar_aviso(self, "PDF guardado")
        except OSError as ex:
            self.error("Error al guardar", str(ex))

    # ──────────────────────────────────────────────────────────
    # Estado guardable (se recupera al volver a abrir el programa)
    # ──────────────────────────────────────────────────────────

    def estado(self):
        return {
            "m": self.sp_m.value(),
            "n": self.sp_n.value(),
            "celdas": self.cuadricula.textos(),
            "jordan": self.sw_jordan.isChecked(),
            "vectores": self.sw_vectores.isChecked(),
            "contexto": self._contexto,
            "resuelto": self._resultado is not None,
        }

    def restaurar(self, d):
        try:
            self.sw_jordan.setChecked(bool(d.get("jordan", True)))
            self.sw_vectores.setChecked(bool(d.get("vectores", False)))
            self._poner_sistema(d["m"], d["n"], d["celdas"])
            self._contexto = d.get("contexto")
            self._mostrar_contexto()
            if d.get("resuelto"):
                self.resolver()
        except (KeyError, IndexError, TypeError, ValueError):
            pass                      # datos viejos o dañados: se ignoran
