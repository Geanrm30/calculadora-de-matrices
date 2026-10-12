# -*- coding: utf-8 -*-
"""
Generación de HTML (subconjunto que entiende Qt) para dibujar matrices,
vectores y texto del informe con colores.
"""
import html

from core.formato import subindice
from qt import tema as T

_E = html.escape

def _mezcla(c0, c1, t):
    """Mezcla dos colores #RRGGBB y devuelve #RRGGBB."""
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#{:02X}{:02X}{:02X}".format(
        *[int(x + (y - x) * t) for x, y in zip(a, b)])


def css(impreso=False):
    # En el PDF las líneas largas deben ajustarse al ancho de la página.
    ajuste = "white-space: pre-wrap;" if impreso else ""
    tam = "9pt" if impreso else "10.5pt"
    return """
<style>
body {{ background-color: {FONDO}; color: {TEXTO};
        font-family: '{MONO}'; font-size: {TAM}; }}
pre  {{ margin: 0; font-family: '{MONO}'; font-size: {TAM}; {AJUSTE} }}
h3   {{ color: {AZUL}; font-family: '{FUENTE}'; margin: 14px 0 4px 0; }}
</style>
""".format(FONDO=T.FONDO, TEXTO=T.TEXTO, MONO=T.MONO, AZUL=T.AZUL,
           FUENTE=T.FUENTE, TAM=tam, AJUSTE=ajuste)


def pagina(cuerpo, impreso=False):
    return "<html><head>{}</head><body>{}</body></html>".format(
        css(impreso), cuerpo)


def etiqueta(texto, color=None):
    color = color or T.MUTED
    return ("<p style=\"margin:10px 0 4px 0; color:{}; "
            "font-family:'{}'; font-size:9.5pt;\">{}</p>"
            .format(color, T.FUENTE, _E(texto)))


def html_matriz(M, n_vars, pivotes=None, resaltar=None):
    """
    Matriz aumentada [A | b] con cabeceras xᵢ y columnas pivote resaltadas.
    `resaltar` es el conjunto de filas que cambiaron en el paso actual.
    """
    pivotes = pivotes or []
    resaltar = resaltar or ()
    fondo_cambio = _mezcla(T.SUPERF, T.NARANJA, 0.45)
    filas = []

    cab = []
    for j in range(n_vars):
        piv = j in pivotes
        cab.append(
            "<td align='center' style='background-color:{bg}; color:{fg};"
            " font-weight:bold; padding:5px 12px;'>x{s}</td>".format(
                bg=T.PIV_BG if piv else T.HDR_BG,
                fg=T.NARANJA if piv else T.AZUL, s=subindice(j + 1)))
    cab.append("<td align='center' style='color:{};'>│</td>".format(T.BORDE))
    cab.append(
        "<td align='center' style='background-color:{}; color:{};"
        " font-weight:bold; padding:5px 12px;'>b</td>".format(T.HDR_BG, T.AZUL))
    filas.append("<tr>{}</tr>".format("".join(cab)))

    for i, fila in enumerate(M):
        cambio = i in resaltar
        celdas = []
        for j in range(n_vars):
            piv = j in pivotes
            if cambio:
                bg, fg, peso = fondo_cambio, T.TEXTO, "font-weight:bold;"
            else:
                bg = T.PIV_BG if piv else T.SUPERF
                fg = T.NARANJA if piv else T.TEXTO
                peso = ""
            celdas.append(
                "<td align='center' style='background-color:{bg}; color:{fg};"
                " {peso} padding:6px 12px;'>{v}</td>".format(
                    bg=bg, fg=fg, peso=peso, v=_E(str(fila[j]))))
        celdas.append("<td align='center' style='color:{};'>│</td>".format(T.BORDE))
        celdas.append(
            "<td align='center' style='background-color:{}; color:{};"
            " {} padding:6px 12px;'>{}</td>".format(
                fondo_cambio if cambio else T.SUPERF, T.TEXTO,
                "font-weight:bold;" if cambio else "", _E(str(fila[n_vars]))))
        filas.append("<tr>{}</tr>".format("".join(celdas)))

    return "<table cellspacing='3' cellpadding='0'>{}</table>".format("".join(filas))


def html_vector(valores, color=None):
    """Vector columna entre corchetes (bordes laterales continuos)."""
    color = color or T.TEXTO
    filas = []
    for v in valores:
        filas.append(
            "<tr><td align='center' style='color:{c}; padding:3px 12px;"
            " border-left:2px solid {c}; border-right:2px solid {c};'>{v}</td></tr>"
            .format(c=color, v=_E(str(v))))
    return "<table cellspacing='0' cellpadding='0'>{}</table>".format("".join(filas))


def html_vector_solucion(resultado):
    """x = [constante] + t₁·[v₁] + …, dibujado como en pizarra."""
    from core.formato import nombre_variable
    expresiones = resultado["expresiones"]
    libres = resultado["libres"]
    n_vars = resultado["n_vars"]

    partes = [
        "<td valign='middle' style='color:{}; font-weight:bold;'>x&nbsp;=&nbsp;</td>"
        .format(T.TEXTO),
        "<td>{}</td>".format(
            html_vector([expresiones[j][0] for j in range(n_vars)], T.TEXTO)),
    ]
    for idx, columna in enumerate(libres):
        partes.append(
            "<td valign='middle' style='color:{}; font-weight:bold;'>"
            "&nbsp;&nbsp;+&nbsp;{}&nbsp;·&nbsp;</td>".format(
                T.NARANJA, _E(nombre_variable(columna))))
        partes.append("<td>{}</td>".format(
            html_vector([expresiones[j][idx + 1] for j in range(n_vars)],
                        T.NARANJA)))
    return "<table cellspacing='0' cellpadding='0'><tr>{}</tr></table>".format(
        "".join(partes))


def html_texto(texto):
    """Texto del informe con las mismas reglas de color que el de escritorio."""
    lineas = []
    for linea in texto.split("\n"):
        color, negrita = None, False
        if linea.startswith("---") or linea.startswith("==="):
            color, negrita = T.AZUL, True
        elif ">>" in linea:
            color = T.ROJO if "INCONSISTENTE" in linea else T.VERDE
            negrita = True
        elif "FALLA" in linea:
            color, negrita = T.ROJO, True
        elif "CUMPLE" in linea or "superada" in linea:
            color, negrita = T.VERDE, True

        contenido = _E(linea) if linea else "&nbsp;"
        if color:
            contenido = "<span style='color:{}{}'>{}</span>".format(
                color, ";font-weight:bold" if negrita else "", contenido)
        lineas.append(contenido)
    return "<pre>{}</pre>".format("\n".join(lineas))
