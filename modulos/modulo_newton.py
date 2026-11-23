# -*- coding: utf-8 -*-
"""
Módulo del método abierto de Newton-Raphson (Programa 9).

Lógica pura, sin interfaz. El método se programa desde cero:
    xᵢ₊₁ = xᵢ − f(xᵢ) / f′(xᵢ)
con f′(x) obtenida simbólicamente con SymPy. Controla la
derivada nula o muy pequeña, los valores no finitos, los ciclos y el máximo de iteraciones, y
SIEMPRE informa el residuo |f(x)| de la aproximación final. SciPy solo contrasta
el resultado; nunca lo produce.
Notación: xᵢ es la aproximación de la iteración i (en i = 1 es el valor inicial x₀),
εₐ = |xᵢ₊₁ − xᵢ| y εₐ(%) = |(xᵢ₊₁ − xᵢ)/xᵢ₊₁|·100.
Unidad: Programa 9: Método abierto de Newton-Raphson.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import math

from core.evaluador import ErrorFuncion, FueraDeDominio, usa_circunflejo
from core.formato import subindice
from core.simbolico import ErrorDerivada, FuncionDerivable
from modulos.modulo_numerico import leer_numero, muestrear, num

LIMITE_ITER = 1000
UMBRAL_DERIVADA = 1e-12
DESBORDE = 1e100
ITERACIONES_DETALLADAS = 60
FILAS_INFORME = 120
MAX_TANGENTES = 10
TOL_RESIDUO_DEFECTO = 1e-4
_MENOS = "−"

CRITERIOS = {
    "abs": "εₐ = |xᵢ₊₁ − xᵢ| < ε   (error aproximado absoluto, como en las diapositivas)",
    "pct": "εₐ(%) = |(xᵢ₊₁ − xᵢ)/xᵢ₊₁|·100 < εₛ   (error relativo porcentual; tolerancia en %)",
    "abs_res": "εₐ = |xᵢ₊₁ − xᵢ| < ε  y  |f(xᵢ₊₁)| < tolerancia del residuo",
}
_ESTADO = {
    "tolerancia": "Convergencia alcanzada",
    "derivada": "Derivada nula o muy cercana a cero",
    "maximo": "Máximo de iteraciones sin cumplir la tolerancia",
    "ciclo": "Ciclo: el método oscila y no converge",
    "diverge": "Diverge: valores no finitos o enormes",
    "dominio": "f o f′ no están definidas en la aproximación",
}
ESTADO_CORTO = {
    "tolerancia": "convergencia alcanzada", "derivada": "derivada nula o casi nula",
    "maximo": "máximo de iteraciones sin cumplir ε", "ciclo": "el método oscila (ciclo)",
    "diverge": "diverge", "dominio": "fuera del dominio de f o f′",
}


class ErrorEntrada(ValueError):
    """Dato de entrada inválido; `campo` dice qué cuadro marcar en pantalla."""

    def __init__(self, mensaje, campo):
        """Guarda el mensaje y el campo culpable (f, x0, eps, nmax, tol_res, h, x1)."""
        super().__init__(mensaje)
        self.campo = campo


# ---------------------------------------------------------------- formato ----

def _corto(v):
    """Número con hasta 10 cifras significativas (tolerancias como 1e-10 o 0.0001)."""
    return "{:.10g}".format(v).replace("-", _MENOS)


def _n(v, dec=6):
    """Número de las tablas: 6 decimales, notación científica si es muy pequeño o enorme."""
    if v is None:
        return "—"
    if not math.isfinite(v):
        return "no finito"
    if v == 0:
        return num(0.0, dec)
    if abs(v) < 1e-5 or abs(v) >= 1e7:
        return "{:.2e}".format(v).replace("-", _MENOS)
    return num(v, dec)


def _p(v):
    """Número entre paréntesis si es negativo (para restas y productos)."""
    t = _n(v)
    return "({})".format(t) if t.startswith(_MENOS) else t


def _pct(v):
    """Error porcentual (o «no definido» cuando xᵢ₊₁ = 0)."""
    return "no definido" if v is None else _n(v)


# ------------------------------------------------------------- validación ----

def _leer(valor, nombre, campo):
    """Lee un número; lanza ErrorEntrada con el motivo y el campo si no sirve."""
    try:
        return leer_numero(valor, nombre)
    except ValueError as ex:
        raise ErrorEntrada(str(ex), campo) from None


def validar_entradas(x0, tolerancia, max_iter, criterio, tol_res):
    """Valida el valor inicial, la tolerancia, las iteraciones y el residuo; devuelve los números."""
    if criterio not in CRITERIOS:
        raise ErrorEntrada("Criterio de parada desconocido.", "eps")
    x0 = _leer(x0, "el valor inicial x₀", "x0")
    eps = _leer(tolerancia, "la tolerancia", "eps")
    if eps <= 0:
        raise ErrorEntrada("La tolerancia debe ser positiva (ε > 0).", "eps")
    nmax = _leer(max_iter, "las iteraciones máximas", "nmax")
    if nmax != int(nmax) or nmax < 1:
        raise ErrorEntrada("Las iteraciones máximas deben ser un entero positivo.", "nmax")
    if nmax > LIMITE_ITER:
        raise ErrorEntrada("Las iteraciones máximas no pueden pasar de {}.".format(LIMITE_ITER),
                           "nmax")
    if str(tol_res).strip():
        tol_res = _leer(tol_res, "la tolerancia del residuo", "tol_res")
        if tol_res <= 0:
            raise ErrorEntrada("La tolerancia del residuo debe ser positiva.", "tol_res")
    else:
        tol_res = TOL_RESIDUO_DEFECTO
    return x0, eps, int(nmax), tol_res


def preparar_funcion(texto):
    """
    Valida f(x) y obtiene f′(x) con SymPy. Devuelve (f, df, texto_df, derivable) donde `derivable`
    es la FuncionDerivable. Lanza ErrorEntrada si f no se puede interpretar o derivar.
    """
    try:
        deriv = FuncionDerivable(texto)
    except (ErrorFuncion, ErrorDerivada) as ex:
        raise ErrorEntrada(str(ex), "f") from None
    return deriv.valor, deriv.derivada_en, deriv.texto_derivada, deriv


# ------------------------------------------------------------------ Newton ----

def _error_pct(xn, ea):
    """εₐ(%) o None cuando xᵢ₊₁ = 0 (no se divide entre cero)."""
    return ea / abs(xn) * 100 if xn != 0 else None


def _cumple(criterio, ea, ea_pct, fxn, eps, tol_res):
    """¿Se cumple el criterio de parada elegido en esta iteración?"""
    if criterio == "pct":
        return ea_pct is not None and ea_pct < eps
    if criterio == "abs_res":
        return ea < eps and fxn is not None and abs(fxn) < tol_res
    return ea < eps


def iterar(f, df, x0, eps, nmax, criterio, tol_res):
    """
    Newton-Raphson. Devuelve {filas, x_aprox, iteraciones, motivo, convergio, detalle}.
    Cada fila: i, x, fx, dfx, xn, ea, ea_pct, fxn, cumple, salto.
    """
    filas, x, motivo, detalle = [], x0, "maximo", ""
    historial = [x0]
    for i in range(1, nmax + 1):
        fila = {"i": i, "x": x, "fx": None, "dfx": None, "xn": None, "ea": None,
                "ea_pct": None, "fxn": None, "cumple": False, "salto": False}
        filas.append(fila)
        try:
            fila["fx"] = f(x)
            fila["dfx"] = df(x)
        except FueraDeDominio as ex:
            motivo, detalle = "dominio", str(ex)
            break
        if abs(fila["dfx"]) < UMBRAL_DERIVADA:
            # Una tangente casi plana tras alejarse mucho de x₀ es divergencia (arctan x, x₀ = 2).
            lejos = abs(x) > 1e6 * max(1.0, abs(x0))
            motivo = "diverge" if lejos else "derivada"
            break
        xn = x - fila["fx"] / fila["dfx"]
        if not math.isfinite(xn) or abs(xn) > DESBORDE:
            fila["xn"] = xn if math.isfinite(xn) else None
            motivo = "diverge"
            break
        fila["xn"] = xn
        fila["ea"] = abs(xn - x)
        fila["ea_pct"] = _error_pct(xn, fila["ea"])
        fila["salto"] = fila["ea"] > 10 * max(1.0, abs(x))
        try:
            fila["fxn"] = f(xn)
        except FueraDeDominio:
            fila["fxn"] = None
        fila["cumple"] = _cumple(criterio, fila["ea"], fila["ea_pct"], fila["fxn"], eps, tol_res)
        # f(xᵢ₊₁) = 0: no hay nada que mejorar aunque el error relativo no esté definido.
        exacto = fila["fxn"] == 0 and not fila["cumple"]
        x = xn
        historial.append(xn)
        if fila["cumple"] or exacto:
            fila["cumple"] = True
            motivo = "tolerancia"
            break
        if len(historial) >= 4 and abs(historial[-1] - historial[-3]) <= 1e-12 * max(
                1.0, abs(historial[-1])) and abs(historial[-1] - historial[-2]) > 1e-9:
            motivo = "ciclo"
            break
    ultima = filas[-1]
    x_aprox = ultima["xn"] if ultima["xn"] is not None else ultima["x"]
    if motivo == "diverge" and ultima["xn"] is None:
        x_aprox = ultima["x"]
    return {"filas": filas, "x_aprox": x_aprox, "iteraciones": len(filas), "motivo": motivo,
            "convergio": motivo == "tolerancia", "detalle": detalle}


def residuo(f, x):
    """|f(x)| o None si f no está definida o x no es finito."""
    if x is None or not math.isfinite(x):
        return None
    try:
        return abs(f(x))
    except FueraDeDominio:
        return None


# ------------------------------------------------------------- contrastes ----

def contraste_scipy(f, df, x0, eps, nmax):
    """scipy.optimize.newton solo para CONTRASTAR (no produce la solución). None si no se puede."""
    try:
        import warnings
        from scipy import optimize
    except ImportError:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raiz, info = optimize.newton(f, x0, fprime=df, tol=min(eps, 1e-10), maxiter=nmax,
                                         full_output=True, disp=False)
    except (RuntimeError, FueraDeDominio, ValueError, ZeroDivisionError, OverflowError):
        return None
    return {"raiz": float(raiz), "iteraciones": int(getattr(info, "iterations", 0)),
            "convergio": bool(getattr(info, "converged", False))}


# -------------------------------------------------------------- resolución ----

def _resultado_vacio():
    """Diccionario de resultado con todas las claves en su valor inicial."""
    return {"valido": False, "mensaje": "", "campo": None, "advertencias": [], "informe": "",
            "texto_f": "", "texto_df": "", "x0": None, "eps": None, "nmax": None,
            "criterio": "abs", "tol_res": TOL_RESIDUO_DEFECTO, "newton": None, "x_aprox": None,
            "residuo": None, "scipy": None, "_f": None, "_df": None, "deriv": None}


def resolver(texto_f, x0, tolerancia, max_iter, criterio="abs", tol_res="", con_scipy=True):
    """
    Valida los datos, deriva f con SymPy y ejecuta Newton-Raphson. Devuelve el diccionario del
    resultado; si `valido` es False, `mensaje` y `campo` dicen por qué.
    """
    r = _resultado_vacio()
    try:
        x0, eps, nmax, tol_res = validar_entradas(x0, tolerancia, max_iter, criterio, tol_res)
        f, df, texto_df, deriv = preparar_funcion(texto_f)
    except ErrorEntrada as ex:
        r.update(mensaje=str(ex), campo=ex.campo)
        return r
    r.update(texto_f=str(texto_f).strip(), texto_df=texto_df, x0=x0, eps=eps, nmax=nmax,
             criterio=criterio, tol_res=tol_res, _f=f, _df=df, deriv=deriv)
    if usa_circunflejo(texto_f):
        r["advertencias"].append("Escribiste ^ y se interpretó como potencia (**).")
    r["newton"] = iterar(f, df, x0, eps, nmax, criterio, tol_res)
    it = r["newton"]
    r["x_aprox"] = it["x_aprox"]
    r["residuo"] = residuo(f, it["x_aprox"])
    _avisos(r)
    if con_scipy:
        r["scipy"] = contraste_scipy(f, df, x0, eps, nmax)
    r["valido"] = True
    r["mensaje"] = mensaje_final(r)
    r["informe"] = informe(r)
    return r


def _avisos(r):
    """Advertencias de lectura: salto grande, residuo no pequeño o resultado dudoso."""
    it = r["newton"]
    for fila in it["filas"]:
        if fila["salto"]:
            r["advertencias"].append(
                "En la iteración {} el paso es enorme (|xᵢ₊₁ − xᵢ| = {}): f′(xᵢ) = {} es casi "
                "cero y la tangente corta el eje x muy lejos. Con otro x₀ puede ir a otra raíz "
                "o no converger.".format(fila["i"], _n(fila["ea"]), _n(fila["dfx"])))
            break
    if it["convergio"] and r["residuo"] is not None and r["residuo"] > r["tol_res"]:
        r["advertencias"].append(
            "Se cumplió el criterio de εₐ, pero |f(x)| = {} es mayor que la tolerancia del "
            "residuo ({}): cumplir εₐ no garantiza una raíz. La convergencia es lenta o la "
            "tolerancia es poco exigente.".format(_n(r["residuo"]), _corto(r["tol_res"])))
    if it["motivo"] == "derivada":
        f0 = it["filas"][-1]
        if f0["fx"] == 0:
            r["advertencias"].append("f(x) = 0 y f′(x) ≈ 0 a la vez: puede ser una raíz múltiple.")


def mensaje_final(r):
    """Resumen de una línea de lo que ocurrió."""
    it = r["newton"]
    if it["convergio"]:
        base = "Newton-Raphson: {} iteraciones, raíz aproximada x ≈ {}  (residuo {})".format(
            it["iteraciones"], _n(r["x_aprox"]), _n(r["residuo"]))
    else:
        base = "Newton-Raphson: {}".format(ESTADO_CORTO[it["motivo"]])
    return base


# ----------------------------------------------------------------- informe ----

def columnas():
    """Cabecera de la tabla de Newton-Raphson."""
    return ["i", "xᵢ", "f(xᵢ)", "f′(xᵢ)", "xᵢ₊₁", "εₐ", "εₐ (%)", "|f(xᵢ₊₁)|"]


def valores_fila(fila):
    """Celdas de una fila de la tabla, en el orden de `columnas`."""
    return [str(fila["i"]), _n(fila["x"]), _n(fila["fx"]), _n(fila["dfx"]), _n(fila["xn"]),
            _n(fila["ea"]), "—" if fila["ea"] is None else _pct(fila["ea_pct"]), _n(fila["fxn"])]


def tabla_texto(cabecera, filas, sangria=""):
    """Tabla de texto con columnas alineadas a la derecha y separadas por dos espacios."""
    anchos = [max([len(cabecera[c])] + [len(f[c]) for f in filas]) for c in range(len(cabecera))]
    lineas = [sangria + "  ".join(h.rjust(w) for h, w in zip(cabecera, anchos)),
              sangria + "  ".join("-" * w for w in anchos)]
    for fila in filas:
        lineas.append(sangria + "  ".join(v.rjust(w) for v, w in zip(fila, anchos)))
    return lineas


def _umbral_texto(r):
    """Símbolo y valor de la tolerancia según el criterio (ε o εₛ en %)."""
    return ("εₛ" if r["criterio"] == "pct" else "ε"), _corto(r["eps"]) + (
        " %" if r["criterio"] == "pct" else "")


def _linea_parada(r, fila):
    """Línea «¿Detener?» de una iteración con la comparación que hace el criterio elegido."""
    simbolo, valor = _umbral_texto(r)
    crit = r["criterio"]
    if crit == "pct":
        if fila["ea_pct"] is None:
            return "  ¿Detener?  εₐ(%) no está definido (xᵢ₊₁ = 0): se sigue iterando."
        dato, cumple = "εₐ(%) = {} %".format(_n(fila["ea_pct"])), fila["cumple"]
    else:
        dato, cumple = "εₐ = {}".format(_n(fila["ea"])), fila["ea"] < r["eps"]
    texto = "  ¿Detener?  {} {} {} = {}".format(dato, "<" if cumple else "≥", simbolo, valor)
    if crit == "abs_res":
        ok_res = fila["fxn"] is not None and abs(fila["fxn"]) < r["tol_res"]
        texto += "  y  |f(xᵢ₊₁)| = {} {} {}".format(
            _n(fila["fxn"]), "<" if ok_res else "≥", _corto(r["tol_res"]))
    if fila["cumple"]:
        return texto + "   →   SÍ: [Se cumple]"
    return texto + "   →   NO, seguir"


def _lineas_iteracion(r, fila):
    """Paso a paso de una iteración: f, f′, fórmula, errores, residuo y decisión."""
    i = fila["i"]
    lineas = ["Iteración {}:   xᵢ = {}{}".format(
        i, _n(fila["x"]), "   (= x₀, el valor inicial)" if i == 1 else "")]
    lineas.append("  f(xᵢ)  = f({}) = {}".format(_n(fila["x"]), _n(fila["fx"])))
    if fila["fx"] is None:
        return lineas + ["  Atención: f no está definida en xᵢ = {}: el método se detiene.".format(
            _n(fila["x"]))]
    lineas.append("  f′(xᵢ) = f′({}) = {}".format(_n(fila["x"]), _n(fila["dfx"])))
    if fila["dfx"] is None:
        return lineas + ["  Atención: f′ no está definida en xᵢ: el método se detiene."]
    if fila["xn"] is None or (abs(fila["dfx"]) < UMBRAL_DERIVADA):
        if abs(fila["dfx"]) < UMBRAL_DERIVADA:
            return lineas + ["  Atención: |f′(xᵢ)| = {} < {}: la derivada es nula o demasiado "
                             "pequeña, no se divide (el paso no puede calcularse).".format(
                                 _n(abs(fila["dfx"])), _corto(UMBRAL_DERIVADA))]
        return lineas + ["  Atención: xᵢ₊₁ no es finito o supera {}: el método diverge.".format(
            _corto(DESBORDE))]
    lineas.append("  xᵢ₊₁ = xᵢ − f(xᵢ)/f′(xᵢ) = {} − {} / {} = {}".format(
        _n(fila["x"]), _p(fila["fx"]), _p(fila["dfx"]), _n(fila["xn"])))
    lineas.append("  εₐ = |xᵢ₊₁ − xᵢ| = |{} − {}| = {}".format(
        _n(fila["xn"]), _n(fila["x"]), _n(fila["ea"])))
    if fila["ea_pct"] is None:
        lineas.append("  εₐ(%) = no definido porque xᵢ₊₁ = 0 (no se divide entre cero; "
                      "se informa el error absoluto)")
    else:
        lineas.append("  εₐ(%) = |(xᵢ₊₁ − xᵢ)/xᵢ₊₁|·100 = {} %".format(_n(fila["ea_pct"])))
    lineas.append("  |f(xᵢ₊₁)| = {}".format(_n(fila["fxn"])))
    return lineas + [_linea_parada(r, fila)]


def _tabla_de_iteraciones(it):
    """Líneas de la tabla de Newton; con muchas filas deja las primeras y las últimas."""
    cab = columnas()
    filas = it["filas"]
    if len(filas) <= FILAS_INFORME:
        return tabla_texto(cab, [valores_fila(f) for f in filas])
    inicio, final = filas[:FILAS_INFORME - 20], filas[-20:]
    omitidas = len(filas) - len(inicio) - len(final)
    return (tabla_texto(cab, [valores_fila(f) for f in inicio])
            + ["", "  … {} iteraciones intermedias omitidas en este informe (la tabla de la "
               "pantalla las incluye todas) …".format(omitidas), ""]
            + tabla_texto(cab, [valores_fila(f) for f in final]))


def _lineas_estado(r):
    """Estado final con las frases que el visor colorea (verde si converge, rojo si no)."""
    it = r["newton"]
    ultima = it["filas"][-1]
    simbolo, valor = _umbral_texto(r)
    ea = _n(ultima["ea_pct"] if r["criterio"] == "pct" else ultima["ea"])
    if it["motivo"] == "tolerancia":
        return ["  Estado: Tolerancia alcanzada: {} = {} < {} = {}.".format(
            "εₐ(%)" if r["criterio"] == "pct" else "εₐ", ea, simbolo, valor)]
    if it["motivo"] == "maximo":
        return ["  Estado: Se alcanzó el máximo de {} iteraciones SIN cumplir la tolerancia "
                "({} = {} ≥ {} = {}): el resultado es solo una aproximación, no una raíz "
                "confirmada.".format(r["nmax"], "εₐ(%)" if r["criterio"] == "pct" else "εₐ",
                                     ea, simbolo, valor)]
    if it["motivo"] == "ciclo":
        return ["  Atención: las aproximaciones se repiten (x{} ≈ x{}): el método oscila entre "
                "valores y no converge con este x₀.".format(
                    subindice(it["iteraciones"] - 2), subindice(it["iteraciones"]))]
    if it["motivo"] == "derivada":
        return ["  Atención: f′(x) = {} es nula o demasiado cercana a cero (umbral {}): Newton "
                "no puede dividir y se detuvo de forma controlada. Prueba otro x₀.".format(
                    _n(ultima["dfx"]), _corto(UMBRAL_DERIVADA))]
    if it["motivo"] == "dominio":
        return ["  Atención: {} en xᵢ = {}: el método se detuvo.".format(
            it["detalle"] or "f o f′ no están definidas", _n(ultima["x"]))]
    if ultima["dfx"] is not None and abs(ultima["dfx"]) < UMBRAL_DERIVADA:
        return ["  Atención: el método diverge: las aproximaciones se alejaron mucho de x₀ "
                "(xᵢ = {}) y la tangente es casi horizontal (f′ ≈ 0).".format(_n(ultima["x"]))]
    return ["  Atención: los valores se vuelven no finitos o superan {}: el método diverge con "
            "estos datos.".format(_corto(DESBORDE))]


def _lineas_resultado(r):
    """Bloque «Resultado final» sin afirmar que la aproximación es una raíz exacta."""
    it, res = r["newton"], r["residuo"]
    lineas = ["Resultado final de Newton-Raphson:"]
    ultima = it["filas"][-1]
    if it["convergio"]:
        lineas.append("  Raíz aproximada:  x ≈ {}".format(_n(r["x_aprox"])))
    else:
        lineas.append("  Última aproximación calculada:  x ≈ {}   (no es una raíz confirmada)".format(
            _n(r["x_aprox"])))
    lineas.append("  Iteraciones: {}    Tolerancia: {} = {}    Máximo: {}".format(
        it["iteraciones"], *_umbral_texto(r), r["nmax"]))
    lineas.append("  Error alcanzado:  εₐ = {}   εₐ(%) = {}".format(
        _n(ultima["ea"]), "—" if ultima["ea"] is None else _pct(ultima["ea_pct"])))
    lineas.append("  Residuo:  |f(x ≈ {})| = {}".format(_n(r["x_aprox"]), _n(res)))
    return lineas + _lineas_estado(r)


def _lineas_verificacion(r):
    """Residuo y contraste con SciPy (solo comprueba; no sustituye el método)."""
    it = r["newton"]
    lineas = ["", "--- Verificación del resultado ---",
              "  Se sustituye la aproximación en la función ORIGINAL (cumplir εₐ no basta):",
              "  |f({})| = {}".format(_n(r["x_aprox"]), _n(r["residuo"]))]
    if r["residuo"] is not None:
        if r["residuo"] <= r["tol_res"]:
            lineas.append("  [Se cumple] |f(x)| ≤ {} (tolerancia del residuo): f vale casi 0 ahí."
                          .format(_corto(r["tol_res"])))
        else:
            lineas.append("  [No se cumple] |f(x)| > {}: la aproximación todavía no hace f ≈ 0."
                          .format(_corto(r["tol_res"])))
    if r["scipy"] is not None:
        s = r["scipy"]
        lineas.append("  Contraste con scipy.optimize.newton:  x = {}   (diferencia {})".format(
            _n(s["raiz"], 8), _n(abs(s["raiz"] - r["x_aprox"]))))
    if not it["convergio"]:
        lineas.append("  Como no convergió, esta aproximación NO debe presentarse como la raíz.")
    return lineas


def informe(r):
    """Informe completo de texto: datos, derivada, iteraciones, tabla, resultado y verificación."""
    it = r["newton"]
    simbolo, valor = _umbral_texto(r)
    lineas = ["=== Método abierto de Newton-Raphson ===", "",
              "Función ingresada:   f(x) = {}".format(r["texto_f"]),
              "Derivada:            f′(x) = {}".format(r["texto_df"]),
              "Fórmula iterativa:   xᵢ₊₁ = xᵢ − f(xᵢ) / f′(xᵢ)",
              "Valor inicial:       x₀ = {}".format(_n(r["x0"])),
              "Tolerancia:          {} = {}      Iteraciones máximas: {}".format(
                  simbolo, valor, r["nmax"]),
              "Criterio de parada:  {}".format(CRITERIOS[r["criterio"]])]
    if r["criterio"] != "abs_res":
        lineas.append("Residuo:             se informa siempre; tolerancia de referencia {}".format(
            _corto(r["tol_res"])))
    lineas += ["", "--- 1) Validaciones ---",
               "  [Se cumple] f(x) se interpretó correctamente y x₀, la tolerancia (ε > 0) y las "
               "iteraciones máximas son válidos.",
               "  Protecciones: |f′(xᵢ)| < {} detiene el método; también se vigilan los valores no "
               "finitos, los ciclos y el máximo de iteraciones.".format(_corto(UMBRAL_DERIVADA))]
    lineas += ["", "--- 2) Derivada simbólica (SymPy) ---",
               "  f(x)  = {}".format(r["deriv"].texto_sympy),
               "  f′(x) = {}".format(r["texto_df"])]
    lineas += ["", "=== Iteraciones de Newton-Raphson ===", "",
               "En la iteración i = 1 el valor de partida es x₀; xᵢ₊₁ pasa a ser xᵢ de la "
               "iteración siguiente.", ""]
    detalladas = min(ITERACIONES_DETALLADAS, it["iteraciones"])
    for fila in it["filas"][:detalladas]:
        lineas += _lineas_iteracion(r, fila) + [""]
    if it["iteraciones"] > detalladas:
        lineas += ["Las iteraciones {} a {} se calculan igual y están en la tabla.".format(
            detalladas + 1, it["iteraciones"]), ""]
    lineas += ["--- Tabla de iteraciones ---", ""] + _tabla_de_iteraciones(it) + [""]
    lineas += _lineas_resultado(r)
    lineas += _lineas_verificacion(r)
    for aviso in r["advertencias"]:
        lineas += ["", "[INFO] " + aviso]
    return "\n".join(lineas)


# ----------------------------------------------------------------- gráfica ----

def _ventana(r):
    """Intervalo de x que muestra el proceso: x₀ y la aproximación final (o las primeras iteraciones)."""
    it = r["newton"]
    xs = [f["x"] for f in it["filas"]]
    if it["filas"][-1]["xn"] is not None:
        xs.append(it["filas"][-1]["xn"])
    if it["convergio"]:
        base = [xs[0], xs[-1]]
    else:
        tope = 1e3 * max(1.0, abs(xs[0]))
        base = [x for x in xs[:7] if abs(x) <= tope] or [xs[0]]
    lo, hi = min(base), max(base)
    ancho = hi - lo
    if ancho < 1e-9:
        ancho = max(1.0, abs(lo)) * 0.5
        lo, hi = lo - ancho / 2, hi + ancho / 2
    margen = max(0.3 * ancho, 0.15)
    return lo - margen, hi + margen


def preparar_grafica_newton(r):
    """
    Datos de la gráfica: f(x) en la ventana, las rectas tangentes de las primeras iteraciones,
    los puntos xᵢ sobre el eje y la aproximación final. {valido, mensaje, xs, ys, pasos, ...}.
    """
    salida = {"valido": False, "mensaje": ""}
    if not r.get("valido"):
        salida["mensaje"] = "Calcula primero Newton-Raphson."
        return salida
    it = r["newton"]
    xmin, xmax = _ventana(r)
    xs, ys, _omitidos, _asint = muestrear(r["_f"], xmin, xmax, 900)
    import numpy as np
    if not np.isfinite(ys).any():
        salida["mensaje"] = "f(x) no está definida con valores reales en la zona de las iteraciones."
        return salida
    pasos = []
    for fila in it["filas"]:
        if fila["fx"] is None:
            continue
        pasos.append({"i": fila["i"], "x": fila["x"], "fx": fila["fx"], "xn": fila["xn"]})
    mostrados = pasos[:MAX_TANGENTES]
    raiz = None
    if r["x_aprox"] is not None and math.isfinite(r["x_aprox"]):
        raiz = {"x": r["x_aprox"], "fx": r["residuo"] if r["residuo"] is None else
                _valor_firmado(r), "convergio": it["convergio"]}
    resumen = ("Curva f(x), tangentes en cada xᵢ (la recta que corta el eje x en xᵢ₊₁) y las "
               "aproximaciones sobre el eje.")
    if len(pasos) > MAX_TANGENTES:
        resumen += " Se dibujan las primeras {} de {} iteraciones.".format(
            MAX_TANGENTES, len(pasos))
    fuera = [p for p in mostrados if p["xn"] is not None and not xmin <= p["xn"] <= xmax]
    if fuera:
        resumen += " Algunas tangentes cortan el eje fuera del cuadro (salto grande): usa el zoom."
    salida.update(valido=True, xs=xs, ys=ys, pasos=mostrados, raiz=raiz, xmin=xmin, xmax=xmax,
                  texto_f=r["texto_f"], titulo="Newton-Raphson: f(x) = {}".format(r["texto_f"]),
                  resumen=resumen)
    return salida


def _valor_firmado(r):
    """f(x ≈) con su signo (la gráfica pone el punto sobre la curva)."""
    try:
        return r["_f"](r["x_aprox"])
    except FueraDeDominio:
        return 0.0

