# -*- coding: utf-8 -*-
"""
Generación de HTML (subconjunto que entiende Qt) para dibujar matrices,
vectores y texto del informe con colores.
Unidad: Proyecto Integrador (interfaz gráfica).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import html
import re

from core.formato import subindice
from qt import tema as T

_E = html.escape

def _mezcla(c0, c1, t):
    """Mezcla dos colores #RRGGBB y devuelve #RRGGBB."""
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#{:02X}{:02X}{:02X}".format(
        *[int(x + (y - x) * t) for x, y in zip(a, b)])


def css(impreso=False, tam=None, ajustar=None):
    """Hoja de estilos del informe; en impreso ajusta las líneas largas al ancho de la página.
    'tam' (pt) y 'ajustar' permiten a la ventana de resultados elegir tamaño y ajuste.
    """
    if ajustar is None:
        ajustar = impreso
    ajuste = "white-space: pre-wrap;" if ajustar else ""
    if tam is not None:
        tam = "{}pt".format(tam)
    else:
        tam = "9pt" if impreso else "{}pt".format(T.tam(10.5))
    return """
<style>
body {{ background-color: {FONDO}; color: {TEXTO};
        font-family: '{MONO}'; font-size: {TAM}; }}
pre  {{ margin: 0; font-family: '{MONO}'; font-size: {TAM}; {AJUSTE} }}
h3   {{ color: {AZUL}; font-family: '{FUENTE}'; margin: 14px 0 4px 0; }}
</style>
""".format(FONDO=T.FONDO, TEXTO=T.TEXTO, MONO=T.MONO, AZUL=T.AZUL,
           FUENTE=T.FUENTE, TAM=tam, AJUSTE=ajuste)


def pagina(cuerpo, impreso=False, tam=None, ajustar=None):
    """Envuelve el cuerpo HTML con su hoja de estilos en un documento completo."""
    return "<html><head>{}</head><body>{}</body></html>".format(
        css(impreso, tam, ajustar), cuerpo)


def etiqueta(texto, color=None):
    """Párrafo HTML pequeño y en color que sirve de rótulo de sección."""
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


_CELDA = r"-?\d+(?:/\d+)?"
_FILA_MATRIZ = re.compile(
    r"^\s*\[\s*((?:{c}\s+)*{c})\s*(?:\|\s*((?:{c}\s+)*{c})\s*)?\]\s*$".format(c=_CELDA))
_PASO = re.compile(r"^\s*(Paso \d+:|── |Iteración \d+:)")
_ENCABEZADO = re.compile(
    r"^\s*(PASO A PASO|PROPIEDAD|RESUMEN DE|LADO |COMPARACI|Resultado final|Comprobación\s+(?:de|A)|"
    r"Matriz aumentada inicial|Matriz [LU] |Producto L|Regla de Cramer|Solución\s+x)")


def _estilo_de_linea(linea):
    """(color, negrita) de una línea del informe, o (None, False) si va sin resaltar."""
    s = linea.strip()
    if linea.startswith("---") or linea.startswith("==="):
        return T.AZUL, True
    if ">>" in linea:
        return (T.ROJO if "INCONSISTENTE" in linea else T.VERDE), True
    if ("FALLA" in linea or "[No se cumple]" in linea or "[ERROR]" in linea
            or "Atención" in linea or s.startswith("No se pudo")
            or "SIN cumplir" in linea or "NO coinciden" in linea):
        return T.ROJO, True
    if ("CUMPLE" in linea or "superada" in linea or "[Se cumple]" in linea
            or "es correcta" in linea or "exitosa" in linea
            or "verificación exacta" in linea or "es invertible" in linea
            or "olerancia alcanzada" in linea or "Coinciden:" in linea
            or s.startswith(("Raíz exacta", "Se encontró una raíz exacta",
                             "Raíz aproximada"))):
        return T.VERDE, True
    if s.startswith("[OMITIDA]"):
        return T.MUTED, False
    if s.startswith("[INFO]"):
        return T.NARANJA, False
    if _ENCABEZADO.match(linea) or (not linea[:1].isspace() and s.endswith("=")
                                    and len(s) < 40):
        return T.AZUL, True
    if _PASO.match(linea):
        return T.NARANJA, True
    if s.startswith("Regla:"):
        return T.MUTED, False
    if re.match(r"^det\(A\)\s+=", linea):
        return T.VERDE, True
    return None, False


def _html_filas_de_texto(lineas):
    """Convierte líneas de texto en filas HTML con el color que corresponde a cada una."""
    out = []
    for linea in lineas:
        color, negrita = _estilo_de_linea(linea)
        contenido = _E(linea) if linea else "&nbsp;"
        if color:
            contenido = "<span style='color:{}{}'>{}</span>".format(
                color, ";font-weight:bold" if negrita else "", contenido)
        out.append(contenido)
    return "<pre>{}</pre>".format("\n".join(out))


def _html_matriz_de_texto(filas):
    """Filas «[ 1 2 | 3 ]» consecutivas dibujadas como una matriz con corchetes."""
    partes = [(m.group(1).split(), (m.group(2) or "").split()) for m in filas]
    hay_barra = any(b for _, b in partes)
    trs = []
    for i, (izq, der) in enumerate(partes):
        celdas = ["<td width='28'></td>"]
        borde_i = "border-left:2px solid {};".format(T.AZUL)
        for j, v in enumerate(izq):
            celdas.append(
                "<td align='center' style='{} color:{}; padding:2px 10px;'>{}</td>".format(
                    borde_i if j == 0 else "", T.TEXTO, _E(v)))
        if hay_barra:
            celdas.append("<td style='border-left:1px solid {};'></td>".format(T.MUTED))
        for j, v in enumerate(der):
            ultimo = j == len(der) - 1
            celdas.append(
                "<td align='center' style='{} color:{}; padding:2px 10px;'>{}</td>".format(
                    "border-right:2px solid {};".format(T.AZUL) if ultimo else "",
                    T.NARANJA, _E(v)))
        if not der:
            celdas[-1] = celdas[-1].replace("style='", "style='border-right:2px solid {};".format(T.AZUL), 1)
        trs.append("<tr>{}</tr>".format("".join(celdas)))
    return "<table cellspacing='0' cellpadding='0'>{}</table>".format("".join(trs))


_CAB_TABLA = re.compile(r"^\s*i\s{2,}xₗ\s{2,}xᵤ\s{2,}xᵣ\s{2,}")
_REGLA_TABLA = re.compile(r"^\s*-+(\s+-+)+\s*$")
_FILA_TABLA = re.compile(r"^\s*\d+\s{2,}")


def _html_tabla_de_texto(cab, filas):
    """
    Tabla de iteraciones de la bisección (columnas separadas por 2+ espacios):
    cabecera azul, filas alternadas, signos de f(xr) en verde/rojo y la última
    fila resaltada (la iteración que acaba de añadirse).
    """
    tenue = _mezcla(T.FONDO, T.SUPERF, 0.55)
    actual = _mezcla(T.SUPERF, T.NARANJA, 0.45)
    trs = ["<tr>{}</tr>".format("".join(
        "<td align='center' style='background-color:{}; color:{};"
        " font-weight:bold; padding:4px 12px;'>{}</td>".format(
            T.HDR_BG, T.AZUL, _E(c)) for c in cab))]
    for r, celdas in enumerate(filas):
        ultima = r == len(filas) - 1
        bg = actual if ultima else (T.SUPERF if r % 2 == 0 else tenue)
        tds = []
        for c, v in enumerate(celdas):
            color = T.TEXTO
            if cab[c].startswith("f(") and v.startswith("+"):
                color = T.VERDE
            elif cab[c].startswith("f(") and v.startswith("\u2212"):
                color = T.ROJO
            elif c == 3:
                color = T.NARANJA
            tds.append(
                "<td align='{}' style='background-color:{}; color:{};{}"
                " padding:3px 12px;'>{}</td>".format(
                    "center" if c == 0 else "right", bg, color,
                    " font-weight:bold;" if ultima or c == 3 else "", _E(v)))
        trs.append("<tr>{}</tr>".format("".join(tds)))
    return ("<table cellspacing='1' cellpadding='0' style='margin:4px 0 4px 18px;'>"
            "{}</table>".format("".join(trs)))


def html_texto(texto):
    """
    Informe en texto plano con color: títulos en azul, pasos en naranja, lo que se
    cumple en verde y lo que falla en rojo, y las matrices «[ 1 2 | 3 ]» dibujadas
    como matrices con corchetes.
    """
    lineas = texto.split("\n")
    piezas, tramo, matriz = [], [], []

    def cerrar_tramo():
        """Cierra el tramo de líneas corridas acumulado."""
        if tramo:
            piezas.append(_html_filas_de_texto(tramo))
            tramo.clear()

    def cerrar_matriz():
        """Cierra el bloque de matriz acumulado."""
        if matriz:
            piezas.append(_html_matriz_de_texto(matriz))
            matriz.clear()

    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if (_CAB_TABLA.match(linea) and i + 1 < len(lineas)
                and _REGLA_TABLA.match(lineas[i + 1])):
            j = i + 2
            filas = []
            while j < len(lineas) and _FILA_TABLA.match(lineas[j]):
                filas.append(re.split(r"\s{2,}", lineas[j].strip()))
                j += 1
            cerrar_tramo()
            cerrar_matriz()
            piezas.append(_html_tabla_de_texto(
                re.split(r"\s{2,}", linea.strip()), filas))
            i = j
            continue
        m = _FILA_MATRIZ.match(linea)
        if m:
            cerrar_tramo()
            matriz.append(m)
        else:
            cerrar_matriz()
            tramo.append(linea)
        i += 1
    cerrar_matriz()
    cerrar_tramo()
    return "".join(piezas)
