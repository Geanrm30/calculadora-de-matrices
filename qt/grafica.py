# -*- coding: utf-8 -*-
"""
Gráfica de funciones con Matplotlib incrustada en la ventana (módulo B del
Programa 7). Sigue el tema claro/oscuro de la aplicación, con título, ejes
identificados, cuadrícula y leyenda. La curva se va trazando con una animación
y después aparecen, con un fundido, la raíz y el intervalo de la bisección.
Unidad: Programa 7: Métodos Numéricos.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import os

os.environ.setdefault("QT_API", "pyside6")

import numpy as np

from core import calentamiento

calentamiento.esperar()
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg,
                                               NavigationToolbar2QT)
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PySide6.QtCore import (QElapsedTimer, QEasingCurve, QTimer, QVariantAnimation,
                            Qt)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QVBoxLayout,
                               QWidget)

from qt import tema as T

_MS_CURVA = 800
_MS_EXTRAS = 350


class _BarraGrafica(NavigationToolbar2QT):
    """Barra reducida a lo útil, con ayuda en español: inicio, mover, zoom y guardar."""

    toolitems = [
        ("Inicio", "Volver a la vista completa de la gráfica", "home", "home"),
        ("Mover", "Mover: arrastra la gráfica con el botón izquierdo", "move", "pan"),
        ("Zoom", "Zoom: arrastra un rectángulo sobre la zona que quieres ampliar",
         "zoom_to_rect", "zoom"),
        ("Guardar", "Guardar la gráfica como imagen", "filesave", "save_figure"),
    ]


class Grafica(QWidget):

    """Gráfica de Matplotlib con barra de navegación, animada y con el tema de la aplicación."""
    MENSAJE_VACIO = "Escribe una función y pulsa «Graficar»"

    def __init__(self, parent=None):
        """Crea la figura, su lienzo, la barra de navegación y el temporizador de la animación."""
        super().__init__(parent)
        self.figura = Figure(figsize=(6.4, 4.4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figura)
        self.barra = _BarraGrafica(self.canvas, self)
        self.barra.setStyleSheet("QToolBar { background: transparent; border: 0; }"
                                 "QToolButton { background: transparent; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self.barra)
        lay.addWidget(self.canvas, 1)
        self._ultima = None
        self._timer = QTimer(self)
        self._fondo = None
        self.canvas.mpl_connect("draw_event", self._guardar_fondo)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._cuadro)
        self._reloj = QElapsedTimer()
        self._anim = None
        self.vaciar()

    def _ejes(self):
        """Limpia la figura y devuelve unos ejes con los colores del tema."""
        self.figura.clear()
        self.figura.set_facecolor(T.PANEL)
        ax = self.figura.add_subplot(111)
        ax.set_facecolor(T.PANEL)
        for borde in ax.spines.values():
            borde.set_color(T.BORDE)
        ax.tick_params(colors=T.MUTED)
        ax.xaxis.label.set_color(T.TEXTO)
        ax.yaxis.label.set_color(T.TEXTO)
        ax.title.set_color(T.TEXTO)
        ax.grid(True, color=T.BORDE, alpha=0.55, linewidth=0.7)
        return ax

    def vaciar(self):
        """Deja la gráfica vacía con la indicación de que se escriba una función."""
        self._parar()
        ax = self._ejes()
        ax.text(0.5, 0.5, self.MENSAJE_VACIO,
                transform=ax.transAxes, ha="center", va="center",
                color=T.MUTED, fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        self._ultima = None
        self.canvas.draw_idle()

    def _colores(self):
        """Lista de colores del tema para las curvas."""
        return [T.AZUL, T.NARANJA, T.VERDE, T.MORADO, T.ROJO, T.TEXTO]

    def _leyenda(self, ax):
        """Dibuja la leyenda sobre los ejes con los colores del tema."""
        leyenda = ax.legend(loc="best", facecolor=T.FONDO, edgecolor=T.BORDE,
                            fontsize=9)
        for t in leyenda.get_texts():
            t.set_color(T.TEXTO)

    def dibujar(self, datos, raiz=None, intervalo=None, animar=True):
        """
        `datos`: resultado de `preparar_grafica`. `raiz`: (x, f(x)) opcional.
        `intervalo`: (a, b, "inicial" | "final") opcional.
        """
        self._parar()
        self._ultima = (datos, raiz, intervalo)
        ax = self._ejes()
        colores = self._colores()
        self._curvas = []
        self._extras = []
        todos = []
        for i, c in enumerate(datos["curvas"]):
            etiqueta = "f(x) = {}".format(c["texto"])
            if animar:
                (linea,) = ax.plot([], [], color=colores[i % len(colores)],
                                   linewidth=2.0, label=etiqueta)
            else:
                (linea,) = ax.plot(c["xs"], c["ys"], linewidth=2.0,
                                   color=colores[i % len(colores)], label=etiqueta)
            self._curvas.append((linea, c["xs"], c["ys"]))
            todos.append(c["ys"][np.isfinite(c["ys"])])
        ys = np.concatenate(todos) if todos else np.array([0.0])
        lo, hi = float(ys.min()), float(ys.max())
        if len(ys) > 20:
            p2, p98 = np.percentile(ys, [2, 98])
            span = max(p98 - p2, 1e-9)
            lo = max(lo, p2 - 0.6 * span)
            hi = min(hi, p98 + 0.6 * span)
        if raiz is not None:
            lo, hi = min(lo, 0.0, raiz[1]), max(hi, 0.0, raiz[1])
        if hi - lo < 1e-9:
            lo, hi = lo - 1, hi + 1
        pad = 0.08 * (hi - lo)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_xlim(datos["xmin"], datos["xmax"])
        ax.axhline(0, color=T.TEXTO, linewidth=0.9, alpha=0.7)
        if datos["xmin"] < 0 < datos["xmax"]:
            ax.axvline(0, color=T.TEXTO, linewidth=0.9, alpha=0.7)

        ini = 0.0 if animar else 1.0
        if intervalo is not None:
            a, b, cual = intervalo
            span_ = ax.axvspan(a, b, color=T.MORADO, alpha=0.13 * ini,
                               label="Intervalo {} [{:.6g}, {:.6g}]".format(cual, a, b))
            self._extras.append((span_, 0.13))
            for x in (a, b):
                v = ax.axvline(x, color=T.MORADO, linestyle="--", linewidth=1.1,
                               alpha=ini)
                self._extras.append((v, 1.0))
        if raiz is not None:
            (punto,) = ax.plot([raiz[0]], [raiz[1]], "o", color=T.ROJO,
                               markersize=8, markeredgecolor=T.TEXTO, zorder=5,
                               alpha=ini,
                               label="Raíz aproximada x ≈ {:.6f}".format(raiz[0]))
            nota = ax.annotate("({:.6f}, {:.2g})".format(raiz[0], raiz[1]),
                               (raiz[0], raiz[1]), textcoords="offset points",
                               xytext=(10, 12), color=T.TEXTO, fontsize=9,
                               alpha=ini)
            self._extras += [(punto, 1.0), (nota, 1.0)]

        titulo = ("f(x) = {}".format(datos["curvas"][0]["texto"])
                  if len(datos["curvas"]) == 1 else "Gráfica de funciones")
        ax.set_title(titulo, fontsize=12)
        ax.set_xlabel("x")
        ax.set_ylabel("f(x)")
        self._ax = ax
        self.figura.tight_layout()
        self.barra.update()
        self._mostrar(ax, animar)

    def _mostrar(self, ax, animar):
        """Deja la figura lista: de una vez, o con la animación del trazado y de los extras."""
        if not animar:
            self._leyenda(ax)
            self.canvas.draw_idle()
            return
        for obj in self._animados():
            obj.set_animated(True)
        self.canvas.draw()
        self._reloj.start()
        self._timer.start()

    def _animados(self):
        """Artistas que cambian en cada cuadro (se redibujan solos, sobre el fondo guardado)."""
        return [linea for linea, _, _ in self._curvas] + [obj for obj, _ in self._extras]

    def _pintar_cuadro(self):
        """Repone el fondo guardado y dibuja solo lo animado: mucho más rápido que redibujar todo."""
        if self._fondo is None:
            return
        self.canvas.restore_region(self._fondo)
        for obj in sorted(self._animados(), key=lambda a: a.get_zorder()):
            self._ax.draw_artist(obj)
        self.canvas.blit(self.figura.bbox)

    def _guardar_fondo(self, _evento=None):
        """Tras cada dibujo completo (también al cambiar de tamaño) guarda el fondo de la animación."""
        self._fondo = self.canvas.copy_from_bbox(self.figura.bbox)

    def _terminar_animacion(self):
        """Deja la gráfica completa, con todos los artistas en su estado final y la leyenda."""
        self._timer.stop()
        for linea, xs, ys in self._curvas:
            linea.set_data(xs, ys)
        for obj, alfa in self._extras:
            obj.set_alpha(alfa)
        for obj in self._animados():
            obj.set_animated(False)
        self._leyenda(self._ax)
        self.canvas.draw_idle()

    def _cuadro(self):
        """Un cuadro de la animación: primero la curva, luego la raíz."""
        ms = self._reloj.elapsed()
        if not self.isVisible():
            ms = _MS_CURVA + _MS_EXTRAS
        if ms <= _MS_CURVA:
            t = 1.0 - (1.0 - ms / _MS_CURVA) ** 3
            for linea, xs, ys in self._curvas:
                k = min(len(xs), int(len(xs) * t) + 1)
                linea.set_data(xs[:k], ys[:k])
        else:
            t = min(1.0, (ms - _MS_CURVA) / _MS_EXTRAS)
            for linea, xs, ys in self._curvas:
                linea.set_data(xs, ys)
            for obj, alfa in self._extras:
                obj.set_alpha(alfa * t)
        if ms >= _MS_CURVA + _MS_EXTRAS:
            self._terminar_animacion()
        else:
            self._pintar_cuadro()

    def _parar(self):
        """Detiene la animación si está en marcha."""
        if self._timer.isActive():
            self._timer.stop()
            for obj in self._animados():
                obj.set_animated(False)

    def redibujar(self):
        """Vuelve a dibujar la última gráfica sin animación (por ejemplo al cambiar de tema)."""
        if self._ultima:
            self.dibujar(*self._ultima, animar=False)
        else:
            self.vaciar()

    def guardar(self, ruta):
        """Guarda la gráfica con fondo blanco (para informes impresos)."""
        self._parar()
        with T.paleta_temporal("impreso"):
            self.redibujar()
            self.figura.savefig(ruta, dpi=160, facecolor="white")
        self.redibujar()

    def imagen(self):
        """Devuelve la gráfica actual como imagen."""
        return self.canvas.grab().toImage()


class GraficaError(Grafica):
    """Error por iteración de Jacobi y Gauss-Seidel en escala logarítmica, con la tolerancia ε como referencia."""
    MENSAJE_VACIO = "Calcula Jacobi y Gauss-Seidel para ver el error por iteración"
    _pendiente = None

    def _sin_tamano(self):
        """Verdadero si el lienzo aún no tiene un tamaño útil (su pestaña no se ha mostrado)."""
        return self.canvas.width() < 80 or self.canvas.height() < 80

    def _dibujar_pendiente(self):
        """Dibuja lo que quedó esperando a que el lienzo tuviera tamaño."""
        if self._pendiente is not None and self._ultima and not self._sin_tamano():
            animar, self._pendiente = self._pendiente, None
            self.dibujar(self._ultima[0], animar=animar)

    def showEvent(self, e):
        """Al mostrarse la pestaña dibuja lo pendiente, ya con el tamaño real."""
        super().showEvent(e)
        QTimer.singleShot(30, self._dibujar_pendiente)

    def resizeEvent(self, e):
        """Si el lienzo acaba de recibir tamaño, dibuja lo pendiente."""
        super().resizeEvent(e)
        QTimer.singleShot(30, self._dibujar_pendiente)

    def dibujar(self, datos, raiz=None, intervalo=None, animar=True):
        """
        `datos`: resultado de `preparar_grafica_error`. `raiz` e `intervalo` no se usan: existen
        para que la ventana de gráfica llame igual a las dos clases. Con la pestaña aún oculta
        espera a tener tamaño: Matplotlib no puede trazar en un lienzo de altura cero.
        """
        self._parar()
        self._ultima = (datos,)
        if self._sin_tamano():
            self._pendiente = animar
            return
        self._pendiente = None
        ax = self._ejes()
        colores = [T.AZUL, T.NARANJA]
        self._curvas = []
        self._extras = []
        for i, c in enumerate(datos["curvas"]):
            xs, ys = (np.array([]), np.array([])) if animar else (c["xs"], c["ys"])
            (linea,) = ax.plot(xs, ys, color=colores[i % len(colores)], linewidth=2.0,
                               marker="o", markersize=4.5, label=c["etiqueta"])
            self._curvas.append((linea, c["xs"], c["ys"]))
        ax.set_yscale("log")
        errores = np.concatenate([c["ys"] for c in datos["curvas"]])
        eps = datos["tolerancia"]
        ax.set_ylim(min(errores.min(), eps) / 3, max(errores.max(), eps) * 3)
        ax.set_xlim(datos["xmin"], datos["xmax"])
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        linea_eps = ax.axhline(eps, color=T.ROJO, linestyle="--", linewidth=1.3,
                               alpha=0.0 if animar else 1.0,
                               label="Tolerancia ε = {:.6g}".format(eps))
        self._extras.append((linea_eps, 1.0))
        ax.set_title(datos["titulo"], fontsize=12)
        ax.set_xlabel("Iteración k")
        ax.set_ylabel(datos["etiqueta_y"])
        self._ax = ax
        self.figura.tight_layout()
        self.barra.update()
        self._mostrar(ax, animar)


class VentanaGrafica(QWidget):
    """La gráfica en una ventana propia, grande, con la misma animación."""
    CLASE_GRAFICA = Grafica

    def __init__(self, titulo, datos, raiz=None, intervalo=None, resumen=""):
        """Crea la ventana con la gráfica grande, sus botones y el resumen."""
        super().__init__(None)
        from qt.componentes import BotonAnimado, mostrar_aviso
        from qt import visor
        self._visor = visor
        self._aviso = mostrar_aviso
        self.setWindowTitle(titulo)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(1100, 760)
        self.setMinimumSize(700, 480)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)
        barra = QHBoxLayout()
        barra.addStretch(1)
        b_png = BotonAnimado("Guardar imagen", "suave", pequeno=True)
        b_png.clicked.connect(self._guardar)
        b_cop = BotonAnimado("Copiar imagen", "suave", pequeno=True)
        b_cop.clicked.connect(self._copiar)
        b_rep = BotonAnimado("Repetir animación", "suave", pequeno=True)
        b_rep.clicked.connect(lambda: self.grafica.dibujar(*self.grafica._ultima))
        for b in (b_rep, b_png, b_cop):
            barra.addWidget(b)
        lay.addLayout(barra)

        self.grafica = self.CLASE_GRAFICA()
        lay.addWidget(self.grafica, 1)
        self.lbl = QLabel(resumen)
        self.lbl.setObjectName("nota")
        self.lbl.setWordWrap(True)
        self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.lbl)
        self._datos = (datos, raiz, intervalo)

    def _guardar(self):
        """Pide una ruta y guarda la gráfica como PNG o PDF."""
        from PySide6.QtWidgets import QFileDialog
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfica", "grafica.png",
            "Imagen PNG (*.png);;PDF (*.pdf);;Todos los archivos (*.*)")
        if ruta:
            try:
                self.grafica.guardar(ruta)
                self._aviso(self, "Gráfica guardada")
            except (OSError, ValueError):
                pass

    def _copiar(self):
        """Copia la gráfica al portapapeles como imagen."""
        QApplication.clipboard().setImage(self.grafica.imagen())
        self._aviso(self, "Gráfica copiada como imagen")

    def showEvent(self, e):
        """Al mostrarse por primera vez hace un fundido y lanza la animación de la gráfica."""
        super().showEvent(e)
        if not getattr(self, "_ya", False):
            self._ya = True
            self.setWindowOpacity(0.0)
            anim = QVariantAnimation(self)
            anim.setDuration(280)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.valueChanged.connect(self.setWindowOpacity)
            anim.start()
            self._anim_ventana = anim
            QTimer.singleShot(120, lambda: self.grafica.dibujar(*self._datos))

    def closeEvent(self, e):
        """Quita la ventana de la lista de ventanas abiertas."""
        if self in self._visor._ABIERTAS:
            self._visor._ABIERTAS.remove(self)
        super().closeEvent(e)


class VentanaGraficaError(VentanaGrafica):
    """Ventana propia para la gráfica del error de Jacobi y Gauss-Seidel."""
    CLASE_GRAFICA = GraficaError


def abrir_ventana_grafica(titulo, datos, raiz=None, intervalo=None, resumen="",
                          clase=VentanaGrafica):
    """Abre la gráfica en una ventana propia, desplazada respecto a la ventana activa."""
    from qt import visor
    v = clase(titulo, datos, raiz, intervalo, resumen)
    activa = QApplication.activeWindow()
    if activa is not None:
        v.move(activa.x() + 40 + 28 * len(visor._ABIERTAS),
               activa.y() + 40 + 28 * len(visor._ABIERTAS))
    visor._ABIERTAS.append(v)
    v.show()
    return v
