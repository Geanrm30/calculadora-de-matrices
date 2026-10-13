# -*- coding: utf-8 -*-
"""
Tema visual (paleta oscura tipo Catppuccin Mocha) y hoja de estilos Qt.
MTM0120 Álgebra Lineal — Universidad Americana.
"""
import os
import tempfile
from contextlib import contextmanager

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF

PALETAS = {
    # Catppuccin Mocha
    "oscuro": dict(
        FONDO="#1E1E2E", PANEL="#181825", CRUST="#11111B", SUPERF="#313244",
        SUPERF2="#3B3D52", BORDE="#45475A", TEXTO="#CDD6F4", MUTED="#7F849C",
        NARANJA="#FAB387", NAR_H="#E3A074", AZUL="#89B4FA", AZUL_H="#6C93D9",
        VERDE="#A6E3A1", VERDE_H="#85C27D", ROJO="#F38BA8", ROJO_H="#D06A86",
        MORADO="#CBA6F7", PIV_BG="#2D2410", HDR_BG="#1E2845",
        ERROR_BG="#4A2733", SELECCION="#2D3B5A", TEXTO_BOTON="#181825"),
    # Catppuccin Latte
    "claro": dict(
        FONDO="#EFF1F5", PANEL="#FFFFFF", CRUST="#E6E9EF", SUPERF="#E1E5EC",
        SUPERF2="#D3D8E2", BORDE="#BCC0CC", TEXTO="#4C4F69", MUTED="#7C7F93",
        NARANJA="#F2873A", NAR_H="#DC7424", AZUL="#3F7CF0", AZUL_H="#2F68D8",
        VERDE="#4CAF50", VERDE_H="#3E9642", ROJO="#D9304F", ROJO_H="#B8203D",
        MORADO="#8839EF", PIV_BG="#FCE8D6", HDR_BG="#DCE6FB",
        ERROR_BG="#F9D5DC", SELECCION="#C9D8F8", TEXTO_BOTON="#FFFFFF"),
    # Para exportar a PDF: fondo blanco, texto negro
    "impreso": dict(
        FONDO="#FFFFFF", PANEL="#FFFFFF", CRUST="#F4F4F4", SUPERF="#F1F3F6",
        SUPERF2="#E5E8EE", BORDE="#B8BDC8", TEXTO="#1B1D26", MUTED="#5E6272",
        NARANJA="#C25E10", NAR_H="#A64D0A", AZUL="#1F5FD1", AZUL_H="#174DB0",
        VERDE="#2E7D32", VERDE_H="#256628", ROJO="#C62828", ROJO_H="#A31F1F",
        MORADO="#6A2BC4", PIV_BG="#FDEBD9", HDR_BG="#E3ECFB",
        ERROR_BG="#F9D5DC", SELECCION="#C9D8F8", TEXTO_BOTON="#FFFFFF"),
}

NOMBRE_TEMA = "oscuro"

# Factor de tamaño de letra de cuadrículas y resultados (1.0 = 100 %).
ESCALAS = (0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0)
ESCALA = 1.0


def poner_escala(valor):
    """Fija el factor de escala (se ajusta al valor permitido más cercano)."""
    global ESCALA
    ESCALA = min(ESCALAS, key=lambda e: abs(e - float(valor)))


def tam(base):
    """Tamaño en puntos de una fuente base, multiplicado por la escala."""
    return round(base * ESCALA, 1)


def aplicar(nombre):
    """Cambia los colores de todo el programa (los módulos leen T.COLOR)."""
    global NOMBRE_TEMA
    if nombre not in PALETAS:
        nombre = "oscuro"
    NOMBRE_TEMA = nombre
    globals().update(PALETAS[nombre])


@contextmanager
def paleta_temporal(nombre):
    """Usa otra paleta dentro de un bloque `with` y luego restaura la actual."""
    anterior = NOMBRE_TEMA
    aplicar(nombre)
    try:
        yield
    finally:
        aplicar(anterior)


aplicar("oscuro")

FUENTE = "Segoe UI"
MONO   = "Consolas"


def _icono_flecha(nombre, color, hacia_arriba):
    """Genera un PNG de flecha pequeña para spinbox y combobox."""
    ruta = os.path.join(tempfile.gettempdir(), "calc_matrices_" + nombre + ".png")
    pm = QPixmap(12, 12)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    if hacia_arriba:
        pts = [QPointF(2, 8), QPointF(10, 8), QPointF(6, 3.5)]
    else:
        pts = [QPointF(2, 4), QPointF(10, 4), QPointF(6, 8.5)]
    p.drawPolygon(QPolygonF(pts))
    p.end()
    pm.save(ruta, "PNG")
    return ruta.replace("\\", "/")


def hoja_de_estilos():
    """Devuelve el QSS global. Requiere QApplication ya creada."""
    arriba = _icono_flecha("arriba", MUTED, True)
    abajo = _icono_flecha("abajo", MUTED, False)

    return """
* {{ outline: 0; }}
QWidget {{
    background-color: {FONDO};
    color: {TEXTO};
    font-family: "{FUENTE}";
    font-size: 10pt;
}}
QMainWindow, QDialog {{ background-color: {FONDO}; }}
QLabel {{ background: transparent; }}
QToolTip {{
    background-color: {CRUST}; color: {TEXTO};
    border: 1px solid {BORDE}; padding: 5px 8px; border-radius: 6px;
}}

/* ── Tarjetas ─────────────────────────────────────────── */
QFrame#tarjeta {{
    background-color: {PANEL};
    border: 1px solid {SUPERF};
    border-radius: 12px;
}}
QFrame#tarjeta QLabel {{ background: transparent; }}
QLabel#tarjetaTitulo {{
    color: {MUTED}; font-weight: 600; font-size: 9pt;
    letter-spacing: 1px;
}}
QLabel#titulo {{ font-size: 20pt; font-weight: 700; color: {TEXTO}; }}
QLabel#subtitulo {{ color: {MUTED}; font-size: 9.5pt; }}
QLabel#nota {{ color: {MUTED}; font-size: 8.5pt; }}
QLabel#contexto {{
    background-color: {HDR_BG}; color: {AZUL};
    border-left: 3px solid {AZUL}; border-radius: 6px;
    padding: 8px 12px; font-weight: 600;
}}
QLabel#errorBanner {{
    background-color: {ERROR_BG}; color: {TEXTO};
    border: 1px solid {ROJO}; border-left: 4px solid {ROJO};
    border-radius: 8px; padding: 9px 14px; font-weight: 600;
}}
QFrame#barra {{
    background-color: {PANEL}; border: 1px solid {SUPERF};
    border-radius: 12px;
}}
QFrame#barra QLabel {{ background: transparent; }}

/* ── Campos de texto ──────────────────────────────────── */
QLineEdit {{
    background-color: {SUPERF}; color: {TEXTO};
    border: 1px solid {BORDE}; border-radius: 8px;
    padding: 4px 8px; selection-background-color: {NARANJA};
    selection-color: {PANEL};
}}
QLineEdit:hover {{ border-color: {MUTED}; }}
QLineEdit:focus {{ border: 1px solid {NARANJA}; background-color: {SUPERF2}; }}
QLineEdit[error="true"] {{ border: 1px solid {ROJO}; background-color: {ERROR_BG}; }}
QLineEdit#celda {{
    font-family: "{MONO}"; font-size: {CELDA}pt; padding: 2px 4px;
}}

QSpinBox {{
    background-color: {SUPERF}; color: {TEXTO};
    border: 1px solid {BORDE}; border-radius: 8px;
    padding: 4px 6px; padding-right: 22px; min-height: 22px;
    font-family: "{MONO}";
}}
QSpinBox:hover {{ border-color: {MUTED}; }}
QSpinBox:focus {{ border-color: {NARANJA}; }}
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border; width: 20px;
    background: transparent; border: none;
}}
QSpinBox::up-button {{ subcontrol-position: top right; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {BORDE}; border-radius: 4px;
}}
QSpinBox::up-arrow {{ image: url({arriba}); width: 10px; height: 10px; }}
QSpinBox::down-arrow {{ image: url({abajo}); width: 10px; height: 10px; }}

QComboBox {{
    background-color: {SUPERF}; color: {TEXTO};
    border: 1px solid {BORDE}; border-radius: 8px;
    padding: 6px 10px; min-height: 22px;
}}
QComboBox:hover {{ border-color: {MUTED}; }}
QComboBox:focus, QComboBox:on {{ border-color: {NARANJA}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right;
    width: 24px; border: none; background: transparent;
}}
QComboBox::down-arrow {{ image: url({abajo}); width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background-color: {PANEL}; color: {TEXTO};
    border: 1px solid {BORDE}; border-radius: 8px; padding: 4px;
    selection-background-color: {SUPERF2}; selection-color: {NARANJA};
    outline: 0;
}}

/* ── Texto largo ──────────────────────────────────────── */
QPlainTextEdit, QTextBrowser, QTextEdit {{
    background-color: {FONDO}; color: {TEXTO};
    border: none; border-radius: 10px; padding: 8px;
    selection-background-color: {SELECCION}; selection-color: {AZUL};
}}

/* ── Pestañas ─────────────────────────────────────────── */
QTabWidget::pane {{
    border: none; background: transparent; top: -1px;
}}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: transparent; color: {MUTED};
    padding: 9px 18px; margin-right: 4px;
    border: none; border-bottom: 2px solid transparent;
    font-weight: 600;
}}
QTabBar::tab:hover {{ color: {TEXTO}; }}
QTabBar::tab:selected {{
    color: {NARANJA}; border-bottom: 2px solid {NARANJA};
}}

/* ── Barras de desplazamiento ─────────────────────────── */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 12px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDE}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {MUTED}; }}
QScrollBar:horizontal {{
    background: transparent; height: 12px; margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDE}; border-radius: 4px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{ background: transparent; }}
QSplitter::handle:horizontal {{ width: 8px; }}

/* ── Cuadros de mensaje ───────────────────────────────── */
QMessageBox {{ background-color: {PANEL}; }}
QMessageBox QLabel {{ color: {TEXTO}; }}
QDialogButtonBox QPushButton, QMessageBox QPushButton {{
    background-color: {SUPERF}; color: {TEXTO}; border: none;
    border-radius: 8px; padding: 7px 18px; min-width: 70px;
}}
QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover {{ background-color: {BORDE}; }}
QDialogButtonBox QPushButton:default, QMessageBox QPushButton:default {{ background-color: {NARANJA}; color: {TEXTO_BOTON}; }}
QMenu {{
    background-color: {PANEL}; color: {TEXTO}; border: 1px solid {BORDE};
    border-radius: 10px; padding: 6px;
}}
QMenu::item {{ padding: 8px 22px 8px 14px; border-radius: 6px; }}
QMenu::item:selected {{ background-color: {SUPERF2}; color: {NARANJA}; }}
QMenu::separator {{ height: 1px; background: {SUPERF}; margin: 5px 8px; }}
QFileDialog QWidget {{ background-color: {FONDO}; }}
""".format(FONDO=FONDO, PANEL=PANEL, CRUST=CRUST, SUPERF=SUPERF,
           SUPERF2=SUPERF2, BORDE=BORDE, TEXTO=TEXTO, MUTED=MUTED,
           NARANJA=NARANJA, AZUL=AZUL, ROJO=ROJO, HDR_BG=HDR_BG,
           ERROR_BG=ERROR_BG, SELECCION=SELECCION, TEXTO_BOTON=TEXTO_BOTON,
           FUENTE=FUENTE, MONO=MONO, arriba=arriba, abajo=abajo,
           CELDA=tam(11))
