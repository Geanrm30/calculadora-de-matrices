# -*- coding: utf-8 -*-
"""
Pestaña F de Métodos Numéricos (Programa 9): método abierto de Newton-Raphson.
f(x) escrita por el usuario, derivada simbólica con SymPy, tabla de iteraciones animada, gráfica
con las rectas tangentes e informe paso a paso.
Unidad: Programa 9: Método abierto de Newton-Raphson.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel,
                               QMenu, QTabWidget, QVBoxLayout, QWidget)

from core.formato import subindices_numericos
from modulos import modulo_newton as M

from qt import tema as T
from qt.componentes import BotonAnimado, Interruptor, Tarjeta, mostrar_aviso
from qt.ejemplos import EJEMPLOS_NEWTON
from qt.grafica import GraficaNewton, VentanaGraficaNewton, abrir_ventana_grafica
from qt.pagina_iterativos import TablaIteraciones
from qt.teclado import TecladoFunciones

_CRITERIOS = ("abs", "pct", "abs_res")
_NOMBRES_CRITERIO = ("Error absoluto εₐ = |xᵢ₊₁ − xᵢ| (por defecto)",
                     "Error relativo porcentual εₐ(%)",
                     "εₐ absoluto y residuo |f(xᵢ₊₁)|")
_TOLERANCIA_DEFECTO = {"abs": "0.0001", "pct": "0.01", "abs_res": "0.0001"}
_VACIO = "Escribe f(x), x₀ y pulsa «Calcular Newton-Raphson»."
_SIN_DERIVADA = "f′(x) se calcula con SymPy al pulsar «Calcular»."


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


class PaginaNewton(QWidget):
    """Contenido de la pestaña F: datos, tabla, gráfica e informe de Newton-Raphson."""

    def __init__(self, pagina, tarjeta_informe, fila_tab, panel_izq, con_desplazo):
        """
        `pagina` es la página de Métodos Numéricos (avisos y errores). El resto son las piezas de
        interfaz que esa página comparte con las demás pestañas.
        """
        super().__init__()
        self._pagina = pagina
        self._res = None
        self._grafica_hecha = False
        self._datos_grafica = None
        self._construir(tarjeta_informe, fila_tab, panel_izq, con_desplazo)
        self.cargar_ejemplo(0, avisar=False, calcular=False)

    @staticmethod
    def _campo(texto, marcador, ancho=None):
        """Campo de texto que se desmarca al editarlo."""
        from qt.pagina_numerica import _campo
        return _campo(texto, marcador, ancho)

    @staticmethod
    def _con_etiqueta(texto, campo):
        """Columna con una etiqueta sobre el campo."""
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(_nota(texto))
        col.addWidget(campo)
        return col

    # ------------------------------------------------------------ interfaz ----

    def _construir(self, tarjeta_informe, fila_tab, panel_izq, con_desplazo):
        """Arma el panel izquierdo (datos) y el derecho (resumen, tabla, gráfica e informe)."""
        izq, lay = panel_izq(ancho_max=440)
        self.b_ejemplos = BotonAnimado("Probar un ejemplo", "azul")
        self.b_ejemplos.con_menu([(e["nombre"], lambda _=False, i=i: self.cargar_ejemplo(i))
                                  for i, e in enumerate(EJEMPLOS_NEWTON)])
        lay.addWidget(self.b_ejemplos)
        lay.addWidget(self._tarjeta_datos())
        lay.addWidget(self._tarjeta_opciones())

        self.btn_calcular = BotonAnimado("Calcular Newton-Raphson", "verde")
        self.btn_calcular.clicked.connect(lambda: self.calcular())
        lay.addWidget(self.btn_calcular)
        b_limpiar = BotonAnimado("Limpiar", "suave")
        b_limpiar.clicked.connect(self._pagina._limpiable(self.limpiar))
        lay.addWidget(b_limpiar)
        lay.addWidget(_nota("Newton-Raphson es un método abierto: no necesita un intervalo, pero "
                            "puede diverger, oscilar o ir a otra raíz según x₀. Con Enter en un "
                            "campo se calcula."))
        lay.addStretch(1)

        der = QWidget()
        dl = QVBoxLayout(der)
        dl.setContentsMargins(8, 0, 0, 0)
        dl.setSpacing(10)
        dl.addWidget(self._tarjeta_resumen())
        self.sub = QTabWidget()
        self.tabla = TablaIteraciones()
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._menu_tabla)
        self.inf = tarjeta_informe(pagina=self._pagina, titulo="Newton-Raphson",
                                   nombre_base="informe_newton_raphson", color=T.VERDE)
        self.sub.addTab(self.tabla, "Tabla de iteraciones")
        self.sub.addTab(self._panel_grafica(), "Gráfica y tangentes")
        self.sub.addTab(self.inf, "Informe paso a paso")
        dl.addWidget(self.sub, 1)
        self.contenido = fila_tab(con_desplazo(izq), der)
        lay_raiz = QVBoxLayout(self)
        lay_raiz.setContentsMargins(0, 0, 0, 0)
        lay_raiz.addWidget(self.contenido)

    def _tarjeta_datos(self):
        """Tarjeta con f(x), el teclado de funciones, x₀, la tolerancia y las iteraciones máximas."""
        t = self.tarjeta_datos = Tarjeta("Datos del método")
        self.f_campo = self._campo("exp(-x) - x", "f(x), por ejemplo x**3 - 2*x - 5")
        t.agregar_layout(self._con_etiqueta("Función f(x)", self.f_campo))
        self.teclado = TecladoFunciones(self.f_campo)
        t.agregar(self.teclado)
        self.lbl_derivada = _nota(_SIN_DERIVADA)
        self.lbl_derivada.setTextInteractionFlags(Qt.TextSelectableByMouse)
        t.agregar(self.lbl_derivada)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.f_x0, self.f_eps = self._campo("0", "0"), self._campo("0.0001", "0.0001")
        fila.addLayout(self._con_etiqueta("Valor inicial x₀", self.f_x0))
        fila.addLayout(self._con_etiqueta("Tolerancia ε > 0", self.f_eps))
        t.agregar_layout(fila)
        fila2 = QHBoxLayout()
        fila2.setSpacing(8)
        self.f_nmax, self.f_res = self._campo("50", "50"), self._campo("0.0001", "0.0001")
        fila2.addLayout(self._con_etiqueta("Iteraciones máx.", self.f_nmax))
        fila2.addLayout(self._con_etiqueta("Tolerancia del residuo", self.f_res))
        t.agregar_layout(fila2)
        t.agregar(_nota("Valores por defecto: ε = 0.0001, máximo 50 iteraciones y residuo "
                        "0.0001. Potencia: ** o ^. Constantes: pi, e."))
        return t

    def _tarjeta_opciones(self):
        """Tarjeta con el criterio de parada y el contraste opcional con SciPy."""
        t = Tarjeta("Criterio y opciones")
        t.agregar(_nota("Criterio de parada"))
        self.combo_criterio = QComboBox()
        self.combo_criterio.addItems(_NOMBRES_CRITERIO)
        self.combo_criterio.currentIndexChanged.connect(self._cambio_criterio)
        t.agregar(self.combo_criterio)
        self.nota_criterio = _nota("")
        t.agregar(self.nota_criterio)
        self.sw_scipy = Interruptor("Contrastar con SciPy", True)
        self.sw_scipy.setToolTip("Solo contrasta: la solución sale del método programado aquí.")
        t.agregar(self.sw_scipy)
        self._cambio_criterio(0)
        return t

    def _tarjeta_resumen(self):
        """Tarjeta de resumen: aproximación, iteraciones, error, residuo y estado."""
        t = self.tarjeta_resumen = Tarjeta("Resumen")
        self.lbl_resumen = QLabel(_VACIO)
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setTextFormat(Qt.RichText)
        self.lbl_resumen.setTextInteractionFlags(Qt.TextSelectableByMouse)
        t.agregar(self.lbl_resumen)
        return t

    def _panel_grafica(self):
        """Panel de la gráfica con sus botones de ventana, guardar y copiar."""
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
        self.grafica = GraficaNewton()
        lay.addWidget(self.grafica, 1)
        self.lbl_grafica = _nota("")
        lay.addWidget(self.lbl_grafica)
        return w

    # ------------------------------------------------------------- lectura ----

    def _criterio(self):
        """Clave del criterio de parada elegido."""
        return _CRITERIOS[self.combo_criterio.currentIndex()]

    def _cambio_criterio(self, indice):
        """Muestra qué mide el criterio y ajusta la tolerancia si seguía siendo la de otro criterio."""
        clave = _CRITERIOS[indice]
        self.nota_criterio.setText(M.CRITERIOS[clave])
        if self.f_eps.text() in _TOLERANCIA_DEFECTO.values():
            self.f_eps.setText(_TOLERANCIA_DEFECTO[clave])

    def _campos(self):
        """Campos de la pestaña asociados al nombre de campo que usa el módulo en sus errores."""
        return {"f": self.f_campo, "x0": self.f_x0, "eps": self.f_eps, "nmax": self.f_nmax,
                "tol_res": self.f_res}

    def _desmarcar(self):
        """Quita las marcas de error de los campos."""
        from qt.pagina_numerica import _marcar
        for c in self._campos().values():
            _marcar(c, False)

    def _marcar_error(self, campo):
        """Pinta de rojo el campo que causó el error de validación."""
        from qt.pagina_numerica import _marcar
        widget = self._campos().get(campo)
        if widget is not None:
            _marcar(widget, True)

    # ------------------------------------------------------------- cálculo ----

    def calcular(self, avisar=True, animar=True):
        """Valida, ejecuta Newton-Raphson y muestra tabla, gráfica e informe."""
        pagina = self._pagina
        pagina.ocultar_error()
        self._desmarcar()
        r = M.resolver(self.f_campo.text(), self.f_x0.text(), self.f_eps.text(),
                       self.f_nmax.text(), self._criterio(), self.f_res.text(),
                       self.sw_scipy.isChecked())
        self._res = r
        if not r["valido"]:
            self.tabla.vaciar()
            self._vaciar_grafica()
            self.inf.poner("")
            self.lbl_derivada.setText(_SIN_DERIVADA)
            self.lbl_resumen.setText("<span style='color:{}'><b>No se pudo calcular.</b></span>"
                                     "<br>{}".format(T.ROJO, _html(r["mensaje"])))
            self._marcar_error(r["campo"])
            if avisar:
                pagina.error("Newton-Raphson", r["mensaje"])
            return r
        self.inf.poner(r["informe"], "Newton-Raphson", pulso=True, resumen=self._resumen_ventana(r))
        self.lbl_derivada.setText("f′(x) = " + r["texto_df"])
        self._llenar_tabla(r, animar)
        self._dibujar_grafica(r, animar)
        self._resumen(r)
        if avisar:
            self.sub.setCurrentIndex(0)
            self.tarjeta_resumen.pulso(T.VERDE if r["newton"]["convergio"] else T.NARANJA)
            pagina.estado_barra(r["mensaje"])
        return r

    def _llenar_tabla(self, r, animar):
        """Llena la tabla de iteraciones."""
        it = r["newton"]
        self.tabla.poner(M.columnas(), [M.valores_fila(f) for f in it["filas"]],
                         it["convergio"], animar)

    def _dibujar_grafica(self, r, animar):
        """Dibuja la curva y las tangentes; si no se puede, explica por qué."""
        datos = M.preparar_grafica_newton(r)
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

    def _resumen(self, r):
        """Resumen: aproximación, error, residuo, estado y avisos."""
        it = r["newton"]
        ultima = it["filas"][-1]
        color = T.VERDE if it["convergio"] else T.ROJO
        if it["convergio"]:
            titulo = "Raíz aproximada: x ≈ {}".format(M._n(r["x_aprox"]))
        else:
            titulo = "{} — última aproximación x ≈ {} (no es una raíz confirmada)".format(
                M._ESTADO[it["motivo"]], M._n(r["x_aprox"]))
        partes = ["<span style='color:{}'><b>{}</b></span>".format(color, _html(titulo)),
                  "{} iteraciones &nbsp;·&nbsp; εₐ = {} &nbsp;·&nbsp; εₐ(%) = {} &nbsp;·&nbsp; "
                  "|f(x)| = {}".format(it["iteraciones"], M._n(ultima["ea"]),
                                       "—" if ultima["ea"] is None else M._pct(ultima["ea_pct"]),
                                       M._n(r["residuo"]))]
        for aviso in r["advertencias"]:
            partes.append("<span style='color:{}'>Aviso: {}</span>".format(T.NARANJA, _html(aviso)))
        self.lbl_resumen.setText("<br>".join(partes))

    def _resumen_ventana(self, r):
        """Respuesta destacada de la ventana de resultado (Abrir en ventana)."""
        it = r["newton"]
        if it["convergio"]:
            return {"tipo": "Newton-Raphson  ·  f(x) = {}".format(r["texto_f"]),
                    "respuesta": "x ≈ {}".format(M._n(r["x_aprox"])), "estado": "ok",
                    "insignia": "✓ {} iteraciones · |f(x)| = {}".format(
                        it["iteraciones"], M._n(r["residuo"]))}
        return {"tipo": "Newton-Raphson  ·  f(x) = {}".format(r["texto_f"]),
                "respuesta": M.ESTADO_CORTO[it["motivo"]].capitalize(), "estado": "error",
                "insignia": "⚠ Sin raíz confirmada"}

    # ------------------------------------------------------------- acciones ----

    def _menu_tabla(self, pos):
        """Menú de clic derecho de la tabla: copiar la fila o toda la tabla."""
        fila = self.tabla.rowAt(pos.y())
        menu = QMenu(self)
        if fila >= 0:
            menu.addAction("Copiar fila", lambda: self._copiar_tabla(fila))
        if self.tabla.rowCount():
            menu.addAction("Copiar toda la tabla", lambda: self._copiar_tabla(-1))
        if not menu.isEmpty():
            menu.exec(self.tabla.viewport().mapToGlobal(pos))

    def _copiar_tabla(self, fila):
        """Copia al portapapeles una fila o toda la tabla."""
        if self.tabla.copiar(fila):
            mostrar_aviso(self._pagina, "Copiado: pégalo en Excel o Word")

    def abrir_ventana_grafica(self):
        """Abre la gráfica en una ventana grande."""
        if not self._grafica_hecha:
            self._pagina.info("Sin gráfica", self.lbl_grafica.text() or
                              "Primero calcula Newton-Raphson.")
            return
        d = self._datos_grafica
        abrir_ventana_grafica("Gráfica — Newton-Raphson", d, None, None, d["resumen"],
                              clase=VentanaGraficaNewton)

    def guardar_grafica(self):
        """Pide una ruta y guarda la gráfica como imagen."""
        if not self._grafica_hecha:
            self._pagina.info("Sin gráfica", "Primero calcula Newton-Raphson.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfica", "newton_raphson.png",
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
            self._pagina.info("Sin gráfica", "Primero calcula Newton-Raphson.")
            return
        QApplication.clipboard().setImage(self.grafica.imagen())
        mostrar_aviso(self._pagina, "Gráfica copiada como imagen")

    def cargar_ejemplo(self, i, avisar=True, calcular=True):
        """Carga el ejemplo con el índice dado y, si se pide, lo calcula."""
        e = EJEMPLOS_NEWTON[i]
        self.combo_criterio.blockSignals(True)
        self.combo_criterio.setCurrentIndex(_CRITERIOS.index(e["criterio"]))
        self.combo_criterio.blockSignals(False)
        self.nota_criterio.setText(M.CRITERIOS[e["criterio"]])
        self.f_campo.setText(e["f"])
        self.f_x0.setText(e["x0"])
        self.f_eps.setText(e["eps"])
        self.f_nmax.setText(e["nmax"])
        self.f_res.setText(e["tol_res"])
        if calcular:
            self.calcular()
        if avisar:
            mostrar_aviso(self._pagina, "Ejemplo: {}. {}".format(e["nombre"], e["sugerencia"]),
                          "info")

    def limpiar(self):
        """Limpia la pestaña: campos por defecto y sin resultados."""
        self.combo_criterio.setCurrentIndex(0)
        self.f_campo.clear()
        for campo, valor in ((self.f_x0, "0"), (self.f_eps, "0.0001"), (self.f_nmax, "50"),
                             (self.f_res, "0.0001")):
            campo.setText(valor)
        self.sw_scipy.setChecked(True)
        self._desmarcar()
        self._res = None
        self.tabla.vaciar()
        self._vaciar_grafica()
        self.inf.poner("")
        self.lbl_derivada.setText(_SIN_DERIVADA)
        self.lbl_resumen.setText(_VACIO)
        self._pagina.ocultar_error()

    def estado(self):
        """Datos de la pestaña para guardar la sesión."""
        return {"f": self.f_campo.text(), "x0": self.f_x0.text(), "eps": self.f_eps.text(),
                "nmax": self.f_nmax.text(), "tol_res": self.f_res.text(),
                "criterio": self._criterio(), "scipy": self.sw_scipy.isChecked(),
                "calculado": self._res is not None and self._res["valido"],
                "informe": self.inf.texto, "historial": self.inf.historial}

    def restaurar(self, d):
        """Restaura lo guardado por `estado`; los datos dañados se ignoran sin romper la ventana."""
        criterio = d.get("criterio", "abs")
        self.combo_criterio.blockSignals(True)
        self.combo_criterio.setCurrentIndex(_CRITERIOS.index(criterio)
                                            if criterio in _CRITERIOS else 0)
        self.combo_criterio.blockSignals(False)
        self.nota_criterio.setText(M.CRITERIOS[self._criterio()])
        for campo, clave in ((self.f_campo, "f"), (self.f_x0, "x0"), (self.f_eps, "eps"),
                             (self.f_nmax, "nmax"), (self.f_res, "tol_res")):
            campo.setText(str(d.get(clave, campo.text())))
        self.sw_scipy.setChecked(bool(d.get("scipy", True)))
        self.inf.historial = list(d.get("historial", []))[:40]
        if d.get("calculado"):
            self.calcular(avisar=False, animar=False)
        elif d.get("informe"):
            self.inf.poner(d["informe"], registrar=False, pulso=False)

    def aplicar_escala(self):
        """Aplica el nuevo tamaño de letra a la tabla, el informe y el teclado."""
        self.tabla.estilo()
        self.inf.estilo()
        self.teclado.estilo()
        if self._res and self._res["valido"]:
            self._llenar_tabla(self._res, False)

    def informe_actual(self):
        """Tarjeta de informe de esta pestaña (para Ctrl+S y Ctrl+P)."""
        return self.inf

    def campos_enter(self):
        """Campos que calculan Newton-Raphson al pulsar Enter."""
        return (self.f_campo, self.f_x0, self.f_eps, self.f_nmax, self.f_res)
