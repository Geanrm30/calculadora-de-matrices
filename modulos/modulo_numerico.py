# -*- coding: utf-8 -*-
"""
Módulo de Métodos Numéricos (Programa 7).

Lógica pura, sin interfaz. Aquí vive el Método de Bisección programado desde
cero (el módulo A del Programa 7). SciPy se usa SOLO para contrastar la raíz.
Notación: xl (límite inferior), xu (límite superior),
xr (punto medio = aproximación de la raíz).
Unidad: Programa 7: Métodos Numéricos.
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import math

from core.evaluador import ErrorFuncion, FueraDeDominio, compilar, usa_circunflejo

DECIMALES = 6
AVISO_POTENCIA = ("Escribiste ^ y se interpretó como potencia (**). En Python la "
                  "potencia se escribe con ** (por ejemplo x**3).")
_MENOS = "−"


def ajustar(texto, ancho=104):
    """Parte las líneas largas (prosa) con sangría; las tablas no se tocan."""
    import re
    import textwrap
    salida = []
    for ln in texto.split("\n"):
        es_tabla = re.search(r"\S {2,}\S.* {2,}\S.* {2,}\S", ln.strip()) is not None
        if len(ln) <= ancho or es_tabla:
            salida.append(ln)
            continue
        sangria = len(ln) - len(ln.lstrip())
        salida.extend(textwrap.wrap(
            ln, ancho, subsequent_indent=" " * (sangria + 2),
            break_long_words=False, break_on_hyphens=False) or [ln])
    return "\n".join(salida)


def num(v, dec=DECIMALES):
    """Número con `dec` decimales y signo menos tipográfico."""
    if v is None:
        return "—"
    s = "{:.{d}f}".format(v, d=dec)
    if float(s) == 0.0:
        s = s.lstrip("-")
    return s.replace("-", _MENOS)


def num_signo(v, dec=DECIMALES):
    """Igual que `num` pero con «+» explícito (como en las tablas de resultados)."""
    s = num(v, dec)
    return s if s.startswith(_MENOS) else "+" + s


def leer_numero(texto, nombre):
    """Convierte lo escrito a float controlando vacíos, letras, nan e inf."""
    if isinstance(texto, (int, float)) and not isinstance(texto, bool):
        v = float(texto)
    else:
        t = (texto or "").strip().replace(",", ".").replace(_MENOS, "-")
        if not t:
            raise ValueError("Falta el valor de {}.".format(nombre))
        try:
            if "/" in t:
                p, q = t.split("/", 1)
                v = float(p) / float(q)
            else:
                v = float(t)
        except (ValueError, ZeroDivisionError):
            raise ValueError("«{}» no es un número válido para {}."
                             .format(texto, nombre)) from None
    if not math.isfinite(v):
        raise ValueError("{} debe ser un número finito.".format(nombre))
    return v


def iteraciones_teoricas(a, b, E):
    """n mínimo = ⌈log2((b − a)/E)⌉ (cota |r − xr_n| ≤ (b − a)/2ⁿ)."""
    cociente = (b - a) / E
    if cociente <= 1:
        return 0
    return int(math.ceil(math.log2(cociente) - 1e-12))


def revisar_continuidad(f, a, b, puntos=2000):
    """
    Muestrea [a, b] buscando puntos donde f no esté definida o donde un cambio
    de signo venga de un polo (como 1/x en [−1, 1]) y no de una raíz.
    Devuelve (lista_de_problemas, sin_dominio, polos).
    """
    problemas, sin_dominio, polos = [], [], []
    h = (b - a) / puntos
    previo = None
    for i in range(puntos + 1):
        x = a + i * h if i < puntos else b
        try:
            y = f(x)
        except FueraDeDominio:
            sin_dominio.append(x)
            previo = None
            continue
        if previo is not None and previo[1] * y < 0:
            # Cambio de signo entre dos muestras: se estrecha y se mira si |f|
            # llega a ≈ 0 (raíz) o se dispara (polo / discontinuidad).
            lo, hi, flo = previo[0], x, previo[1]
            for _ in range(80):
                m = (lo + hi) / 2
                try:
                    fm = f(m)
                except FueraDeDominio:
                    polos.append(m)
                    break
                if fm == 0:
                    lo = hi = m
                    break
                if flo * fm < 0:
                    hi = m
                else:
                    lo, flo = m, fm
            else:
                try:
                    if abs(f((lo + hi) / 2)) > 1e-3:
                        polos.append((lo + hi) / 2)
                except FueraDeDominio:
                    polos.append((lo + hi) / 2)
        previo = (x, y)
    if sin_dominio:
        problemas.append("f no está definida en todo el intervalo (por ejemplo "
                         "en x ≈ {}: posible asíntota o discontinuidad, donde "
                         "el cambio de signo no garantiza una raíz)."
                         .format(num(sin_dominio[0])))
    if polos:
        problemas.append("f presenta una discontinuidad (asíntota o polo) cerca "
                         "de x ≈ {}: el cambio de signo proviene de ahí y no de "
                         "una raíz.".format(num(polos[0])))
    return problemas, sin_dominio, polos


def biseccion(texto_f, a, b, E, nmax, comparar_scipy=True, extendida=False):
    """Método de bisección desde cero sobre f(x) en [a, b] con tolerancia E y máximo nmax.
    Con extendida=True la tabla trae también f(xl), f(xu) y Eb (la tabla completa de la Tarea 7).
    Devuelve un dict con filas por iteración, raíz, motivo de parada, cotas, contraste con SciPy e informe.
    """
    r = {"valido": False, "mensaje": "", "advertencias": [], "filas": [],
         "raiz": None, "f_raiz": None, "motivo": None, "n_teorico": None,
         "n_real": 0, "cota": None, "scipy": None, "dif_scipy": None,
         "scipy_metodos": [], "extendida": bool(extendida),
         "funcion": (texto_f or "").strip(), "informe": "",
         "a0": None, "b0": None, "E": None, "nmax": None}

    try:
        f = compilar(texto_f)
        a = leer_numero(a, "el extremo inferior a")
        b = leer_numero(b, "el extremo superior b")
        E = leer_numero(E, "la tolerancia E")
        nmax_v = leer_numero(nmax, "las iteraciones máximas")
    except (ErrorFuncion, ValueError) as ex:
        r["mensaje"] = str(ex)
        return r
    if usa_circunflejo(texto_f):
        r["advertencias"].append(AVISO_POTENCIA)
    if nmax_v != int(nmax_v):
        r["mensaje"] = "Las iteraciones máximas deben ser un número entero."
        return r
    nmax = int(nmax_v)
    r.update(a0=a, b0=b, E=E, nmax=nmax, funcion=f.texto)
    if not a < b:
        r["mensaje"] = ("El extremo inferior debe ser menor que el superior "
                        "(a < b). Recibí a = {} y b = {}.".format(num(a), num(b)))
        return r
    if E <= 0:
        r["mensaje"] = "La tolerancia debe ser positiva (E > 0)."
        return r
    if nmax < 1:
        r["mensaje"] = "Las iteraciones máximas deben ser al menos 1."
        return r

    try:
        fa = f(a)
    except FueraDeDominio as ex:
        r["mensaje"] = "f(a) no está definida: {}.".format(ex)
        return r
    try:
        fb = f(b)
    except FueraDeDominio as ex:
        r["mensaje"] = "f(b) no está definida: {}.".format(ex)
        return r
    r["n_teorico"] = iteraciones_teoricas(a, b, E)

    if fa == 0 or fb == 0:
        r["valido"] = True
        r["raiz"] = a if fa == 0 else b
        r["f_raiz"] = 0.0
        r["motivo"] = "exacta"
        r["cota"] = 0.0
        r["mensaje"] = ("Se encontró una raíz exacta en el extremo "
                        "x = {}: f(x) = 0.".format(num(r["raiz"])))
        r["informe"] = _informe(r, f)
        return r

    if fa * fb > 0:
        r["mensaje"] = ("El intervalo no cumple la condición de cambio de signo: "
                        "f(a)·f(b) = {} > 0. Bisección no puede continuar con "
                        "este intervalo (no se afirma que la función no tenga "
                        "raíces en otros intervalos).".format(num(fa * fb)))
        r["informe"] = _informe(r, f, fa, fb)
        return r

    # 5) Continuidad (Bolzano la exige; el cambio de signo solo no basta)
    problemas, _, polos = revisar_continuidad(f, a, b)
    if problemas:
        r["advertencias"] = problemas
        r["mensaje"] = ("No se cumplen las condiciones del método: " +
                        " ".join(problemas) +
                        " Elige un intervalo donde f sea continua.")
        r["informe"] = _informe(r, f, fa, fb)
        return r

    # 6) Proceso iterativo (los extremos se guardan ANTES de actualizarlos)
    xl, xu = a, b
    anterior = None
    for k in range(1, nmax + 1):
        xr = (xl + xu) / 2
        Eb = (xu - xl) / 2
        try:
            fr = f(xr)
        except FueraDeDominio as ex:
            r["mensaje"] = ("f no está definida en el punto medio x = {}: {}."
                            .format(num(xr), ex))
            r["informe"] = _informe(r, f, fa, fb)
            return r
        if anterior is None:
            Ea = ea = None
        else:
            Ea = abs(xr - anterior)
            ea = abs((xr - anterior) / xr) if xr != 0 else "nd"
        fila = {"k": k, "xl": xl, "xu": xu, "xr": xr, "fxl": fa, "fxu": fb,
                "fxr": fr, "Eb": Eb, "Ea": Ea, "ea": ea,
                "ancho": xu - xl, "producto": fa * fr}
        r["filas"].append(fila)
        anterior = xr
        if fr == 0:
            fila["decision"] = "f(xr) = 0: raíz exacta"
            r["motivo"] = "exacta"
            break
        if Eb <= E:
            fila["decision"] = "Eb ≤ E: tolerancia alcanzada"
            r["motivo"] = "tolerancia"
            break
        if fa * fr < 0:
            fila["decision"] = "f(xl)·f(xr) < 0: la raíz está en [xl, xr]  →  xu = xr"
            xu, fb = xr, fr
        else:
            fila["decision"] = "f(xl)·f(xr) > 0: la raíz está en [xr, xu]  →  xl = xr"
            xl, fa = xr, fr
    else:
        r["motivo"] = "maximo"
        r["filas"][-1]["decision"] = "se alcanzó el máximo de iteraciones"

    ultima = r["filas"][-1]
    r["raiz"], r["f_raiz"] = ultima["xr"], ultima["fxr"]
    r["cota"] = ultima["Eb"]
    r["n_real"] = len(r["filas"])
    r["valido"] = True

    if comparar_scipy:
        try:
            from core import calentamiento
            calentamiento.esperar()
            from scipy.optimize import bisect, brentq
            for nombre, metodo in (("scipy.optimize.bisect", bisect),
                                   ("scipy.optimize.brentq", brentq)):
                raiz_ref, info = metodo(lambda t: f(t), a, b, xtol=1e-12,
                                        rtol=1e-12, full_output=True)
                r["scipy_metodos"].append({
                    "nombre": nombre, "raiz": float(raiz_ref),
                    "f_raiz": f(float(raiz_ref)),
                    "iteraciones": info.iterations,
                    "dif": abs(r["raiz"] - raiz_ref)})
            r["scipy"] = r["scipy_metodos"][0]["raiz"]
            r["dif_scipy"] = r["scipy_metodos"][0]["dif"]
        except ImportError:
            r["advertencias"].append("SciPy no está instalado: se omitió la "
                                     "comparación externa.")
        except Exception as ex:
            r["advertencias"].append("No se pudo contrastar con SciPy: {}"
                                     .format(ex))
    r["mensaje"] = _mensaje_final(r)
    r["informe"] = _informe(r, f)
    return r


def _mensaje_final(r):
    """Texto que explica por qué terminó la bisección (exacta, tolerancia o máximo)."""
    if r["motivo"] == "exacta":
        return "Raíz exacta encontrada (en aritmética de máquina)."
    if r["motivo"] == "tolerancia":
        return ("Tolerancia alcanzada: Eb = {} ≤ E = {}.".format(
            num(r["cota"]), _corto(r["E"])))
    return ("Se alcanzó el máximo de {} iteraciones SIN cumplir la tolerancia "
            "(Eb = {} > E = {}): el resultado es una aproximación sin garantía "
            "del criterio pedido. Se necesitaban al menos {} iteraciones."
            .format(r["nmax"], num(r["cota"]), _corto(r["E"]), r["n_teorico"]))


def _corto(v):
    """Tolerancia legible: 0.0001 → 0.0001, 1e-10 → 1e-10."""
    return "{:.10g}".format(v)


_COLS = [("i", 4), ("xₗ", 10), ("xᵤ", 10), ("xᵣ", 10), ("εₐ (%)", 11),
         ("f(xᵣ)", 11), ("xᵤ − xₗ", 10)]
_COLS_EXT = [("i", 4), ("xₗ", 10), ("xᵤ", 10), ("xᵣ", 10), ("f(xₗ)", 11),
             ("f(xᵤ)", 11), ("f(xᵣ)", 11), ("Eᵦ", 10), ("εₐ (%)", 11)]


def columnas(extendida=False):
    """Nombres de las columnas: la tabla básica o la completa de la Tarea 7 (f(xl), f(xu), Eb)."""
    return tuple(n for n, _ in (_COLS_EXT if extendida else _COLS))


def _ea_pct(fila):
    """Error aproximado relativo de la fila como porcentaje con 6 decimales ('—' en la primera)."""
    if fila["ea"] is None:
        return "—"
    if fila["ea"] == "nd":
        return "No definido"
    return num(fila["ea"] * 100)


def valores_fila(fi, extendida=False):
    """Celdas de una fila de la tabla, en el orden de `columnas(extendida)`."""
    if extendida:
        return [str(fi["k"]), num(fi["xl"]), num(fi["xu"]), num(fi["xr"]),
                num_signo(fi["fxl"]), num_signo(fi["fxu"]), num_signo(fi["fxr"]),
                num(fi["Eb"]), _ea_pct(fi)]
    return [str(fi["k"]), num(fi["xl"]), num(fi["xu"]), num(fi["xr"]),
            _ea_pct(fi), num_signo(fi["fxr"]), num(fi["ancho"])]


def tabla_txt(filas, sangria="  ", extendida=False):
    """Líneas de la tabla con las filas dadas (cabecera, regla y datos)."""
    cols = _COLS_EXT if extendida else _COLS
    lineas = [sangria + "  ".join(n.rjust(w) for n, w in cols),
              sangria + "  ".join("-" * w for _, w in cols)]
    for fi in filas:
        lineas.append(sangria + "  ".join(
            v.rjust(w) for v, (_, w) in zip(valores_fila(fi, extendida), cols)))
    return lineas


def _tabla_scipy(r):
    """Tabla que compara la bisección propia con los métodos de SciPy sobre el mismo intervalo."""
    filas = [("Bisección (este programa)", num(r["raiz"]), num_signo(r["f_raiz"]),
              str(r["n_real"]), "—")]
    for m in r["scipy_metodos"]:
        filas.append((m["nombre"], num(m["raiz"]), num_signo(m["f_raiz"]),
                      str(m["iteraciones"]), num(m["dif"])))
    cabecera = ("Método", "Raíz", "f(raíz)", "Iter.", "|xr − raíz|")
    anchos = [max(len(c[i]) for c in filas + [cabecera]) for i in range(5)]
    def linea(fila):
        """Escribe una fila de la tabla con el método a la izquierda y los números a la derecha."""
        return "  " + "  ".join(
            (c.ljust(anchos[i]) if i == 0 else c.rjust(anchos[i]))
            for i, c in enumerate(fila))
    return "\n".join([linea(cabecera)] + [linea(f) for f in filas])


def _informe(r, f, fa=None, fb=None):
    """Arma el informe completo de la bisección: condiciones, paso a paso, tabla y resultado."""
    lineas = []
    a, b, E = r["a0"], r["b0"], r["E"]
    lineas.append("=== Método de bisección ===")
    lineas.append("")
    lineas.append("f(x) = {}".format(r["funcion"]))
    if a is not None:
        lineas.append("Intervalo inicial: xl = {},  xu = {}".format(num(a), num(b)))
        lineas.append("Tolerancia (error de convergencia): E = {}".format(_corto(E)))
        lineas.append("Iteraciones máximas: {}".format(r["nmax"]))
    lineas.append("")
    if fa is None and r["filas"]:
        fa, fb = r["filas"][0]["fxl"], r["filas"][0]["fxu"]
    if fa is not None:
        lineas.append("--- Condición inicial (Teorema de Bolzano) ---")
        lineas.append("  f(xl) = f({}) = {}".format(num(a), num_signo(fa)))
        lineas.append("  f(xu) = f({}) = {}".format(num(b), num_signo(fb)))
        lineas.append("  f(xl)·f(xu) = {} {} 0".format(
            num(fa * fb), "<" if fa * fb < 0 else (">" if fa * fb > 0 else "=")))
    if r["motivo"] == "exacta" and not r["filas"]:
        lineas.append("")
        lineas.append(r["mensaje"])
        return "\n".join(lineas)
    if not r["filas"]:
        lineas.append("")
        lineas.append("No se pudo aplicar el método: " + r["mensaje"])
        return "\n".join(lineas)
    lineas.append("  Hay cambio de signo y f es continua en el intervalo muestreado: "
             "existe al menos una raíz en (xl, xu).")
    lineas.append("")
    lineas.append("--- Número teórico de iteraciones ---")
    lineas.append("  n ≥ log₂((xu − xl)/E) = log₂(({} − {})/{}) = log₂({}) ≈ {}"
             .format(num(b), num(a), _corto(E), _corto((b - a) / E),
                     num(math.log2((b - a) / E), 2) if (b - a) / E > 0 else "—"))
    lineas.append("  Se redondea siempre al entero superior: n = {} iteraciones."
             .format(r["n_teorico"]))
    lineas.append("")
    lineas.append("--- Criterio de parada ---")
    lineas.append("  Eb = (xu − xl)/2 ≤ E, raíz exacta f(xr) = 0, o i = iteraciones "
             "máximas.")
    lineas.append("  Cada fila registra los extremos vigentes ANTES de actualizar el "
                  "intervalo: son los que se usaron para calcular xr.")

    lineas.append("")
    lineas.append("=== Paso a paso ===")
    for fi in r["filas"]:
        lineas.append("")
        lineas.append("Iteración {}:".format(fi["k"]))
        lineas.append("  xl = {}   xu = {}".format(num(fi["xl"]), num(fi["xu"])))
        lineas.append("  xr = (xl + xu)/2 = ({} + {})/2 = {}".format(
            num(fi["xl"]), num(fi["xu"]), num(fi["xr"])))
        lineas.append("  f(xl) = {}".format(num_signo(fi["fxl"])))
        lineas.append("  f(xu) = {}".format(num_signo(fi["fxu"])))
        lineas.append("  f(xr) = f({}) = {}".format(num(fi["xr"]), num_signo(fi["fxr"])))
        lineas.append("  f(xl)·f(xr) = {} · {} = {}".format(
            num_signo(fi["fxl"]), num_signo(fi["fxr"]), num_signo(fi["producto"])))
        if fi["Ea"] is None:
            lineas.append("  Ea = —   εa = —   (primera iteración: no hay aproximación anterior)")
        elif fi["ea"] == "nd":
            lineas.append("  Ea = |xr − xr anterior| = {}   εa = No definido "
                          "(xr = 0)".format(num(fi["Ea"])))
        else:
            lineas.append("  Ea = |xr − xr anterior| = {}".format(num(fi["Ea"])))
            lineas.append("  εa = |(xr nuevo − xr anterior)/xr nuevo| = {} = {} %"
                          .format(num(fi["ea"]), num(fi["ea"] * 100)))
        lineas.append("  Eb = (xu − xl)/2 = {}".format(num(fi["Eb"])))
        lineas.append("  → " + fi["decision"])
        lineas.append("")
        lineas.append("  Tabla hasta la iteración {}:".format(fi["k"]))
        lineas += tabla_txt(r["filas"][:fi["k"]], "  ", r["extendida"])

    lineas.append("")
    lineas.append("=== Tabla de resultados ===")
    lineas.append("")
    lineas += tabla_txt(r["filas"], "", r["extendida"])
    lineas.append("")
    lineas.append("=== Resultado ===")
    lineas.append("  Raíz aproximada: xr = {}".format(num(r["raiz"])))
    lineas.append("  f(xr) = {}".format(num_signo(r["f_raiz"], 6)))
    lineas.append("  Cota del error: |r − xr| ≤ Eb = {}".format(num(r["cota"])))
    lineas.append("  Iteraciones: teóricas = {}, realizadas = {}".format(
        r["n_teorico"], r["n_real"]))
    lineas.append("  " + r["mensaje"])
    if r["motivo"] == "tolerancia" and r["n_real"] != r["n_teorico"]:
        lineas.append("  Nota: las iteraciones realizadas difieren de las teóricas "
                 "porque el método terminó antes (raíz exacta) o porque n "
                 "teórico se redondea.")
    if r["scipy"] is not None:
        lineas.append("")
        lineas.append("--- Validación externa (SciPy, solo para contrastar) ---")
        lineas.append(_tabla_scipy(r))
        coinciden = r["dif_scipy"] <= r["cota"] * (1 + 1e-9) + 1e-12
        lineas.append("")
        if coinciden:
            lineas.append("  Coinciden: |xr − raíz SciPy| = {} ≤ Eb = {}, así que la raíz "
                          "de la bisección es consistente con la de SciPy.".format(
                              num(r["dif_scipy"]), num(r["cota"])))
        else:
            lineas.append("  NO coinciden: |xr − raíz SciPy| = {} > Eb = {}. Puede haber "
                          "más de una raíz en [a, b] o una discontinuidad: SciPy pudo "
                          "converger a otra raíz.".format(num(r["dif_scipy"]),
                                                          num(r["cota"])))
        lineas.append("  SciPy se ejecutó con una tolerancia muy fina para usar sus raíces como "
                      "referencia; nunca es la solución del programa.")
    for adv in r["advertencias"]:
        lineas.append("")
        lineas.append("[INFO] " + adv)
    lineas.append("")
    lineas.append("Recuerda: el cambio de signo no garantiza por sí solo la "
             "continuidad; Bisección solo asegura la raíz si f es continua en "
             "[xl, xu].")
    return "\n".join(lineas)


PUNTOS_GRAFICA = 2000


def muestrear(f, xmin, xmax, n=PUNTOS_GRAFICA):
    """Evalúa f en n puntos igualmente espaciados de [xmin, xmax].
    Donde f no existe o hay una asíntota guarda nan para que la gráfica no una los trozos.
    """
    import numpy as np
    xs = np.linspace(xmin, xmax, n)
    ys = np.full(n, np.nan)
    omitidos = 0
    for i, x in enumerate(xs):
        try:
            ys[i] = f(float(x))
        except FueraDeDominio:
            omitidos += 1
    asintotas = []
    fin = np.isfinite(ys)
    saltos = np.abs(np.diff(ys))
    saltos = saltos[np.isfinite(saltos)]
    if saltos.size:
        tipico = float(np.median(saltos)) or float(np.mean(saltos))
        for i in range(n - 1):
            if fin[i] and fin[i + 1] and ys[i] * ys[i + 1] < 0:
                salto = abs(ys[i + 1] - ys[i])
                if salto > 1.0 and salto > 60 * max(tipico, 1e-12):
                    ys[i] = np.nan
                    asintotas.append(float((xs[i] + xs[i + 1]) / 2))
    return xs, ys, omitidos, asintotas


def preparar_grafica(texto, xmin, xmax):
    """
    Valida las entradas y muestrea una o varias funciones (separadas por «;»).
    Devuelve {valido, mensaje, curvas:[{texto, xs, ys, omitidos, asintotas}],
    xmin, xmax, resumen}.
    """
    import numpy as np
    r = {"valido": False, "mensaje": "", "curvas": [], "xmin": None,
         "xmax": None, "resumen": ""}
    try:
        xmin = leer_numero(xmin, "x mínimo")
        xmax = leer_numero(xmax, "x máximo")
        partes = [t.strip() for t in (texto or "").split(";") if t.strip()]
        if not partes:
            raise ErrorFuncion("Escribe una función, por ejemplo 1/x.")
        if len(partes) > 6:
            raise ErrorFuncion("Se admiten hasta 6 funciones a la vez.")
        funciones = [compilar(t) for t in partes]
    except (ErrorFuncion, ValueError) as ex:
        r["mensaje"] = str(ex)
        return r
    if not xmin < xmax:
        r["mensaje"] = ("x mínimo debe ser menor que x máximo. Recibí {} y {}."
                        .format(num(xmin), num(xmax)))
        return r
    if xmax - xmin > 1e9:
        r["mensaje"] = "El intervalo es demasiado grande para graficarlo."
        return r
    lineas = []
    for fn in funciones:
        xs, ys, omitidos, asint = muestrear(fn, xmin, xmax)
        if not np.isfinite(ys).any():
            r["mensaje"] = ("f(x) = {} no está definida (con valores reales) en "
                            "ningún punto de [{}, {}]."
                            .format(fn.texto, num(xmin), num(xmax)))
            return r
        r["curvas"].append({"texto": fn.texto, "xs": xs, "ys": ys,
                            "omitidos": omitidos, "asintotas": asint})
        linea = "f(x) = {}: {} puntos".format(fn.texto, len(xs))
        if omitidos:
            linea += ", {} sin valor real (no se grafican)".format(omitidos)
        if asint:
            linea += ", asíntota(s) cerca de x ≈ " + ", ".join(
                num(a, 4) for a in asint[:4])
        lineas.append(linea)
    if usa_circunflejo(texto):
        lineas.append("Aviso: " + AVISO_POTENCIA)
    r.update(valido=True, xmin=xmin, xmax=xmax, resumen="\n".join(lineas))
    return r


_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _sup(n):
    """Escribe el entero n con dígitos superíndice."""
    return str(n).translate(_SUP)


def _sub(n):
    """Escribe el entero n con dígitos subíndice."""
    return str(n).translate(_SUB)


def _descomposicion(digitos, base, signo):
    """Devuelve (línea con potencias, línea con la suma, valor absoluto)."""
    n = len(digitos)
    terminos = ["{} · {}{}".format(d, base, _sup(n - 1 - i))
                for i, d in enumerate(digitos)]
    valores = [int(d) * base ** (n - 1 - i) for i, d in enumerate(digitos)]
    total = sum(valores)
    pre = _MENOS if signo < 0 else ""
    cab = "{}({}){}".format(pre, "".join(digitos), _sub(base))
    suma_t = " + ".join(terminos)
    suma_v = " + ".join(str(v) for v in valores)
    if pre:
        suma_t, suma_v = "({})".format(suma_t), "({})".format(suma_v)
    l1 = "{} = {}{}".format(cab, pre, suma_t)
    l2 = "{} = {}{} = {}({}){}".format(cab, pre, suma_v, pre, total, _sub(10))
    return l1, l2, total


def _a_binario(valor, L):
    """Divisiones sucesivas entre 2; devuelve la cadena binaria."""
    if valor == 0:
        L.append("  0 ÷ 2 = 0, residuo 0")
        return "0"
    restos, q = [], valor
    while q > 0:
        L.append("  {} ÷ 2 = {}, residuo {}".format(q, q // 2, q % 2))
        restos.append(str(q % 2))
        q //= 2
    return "".join(reversed(restos))


def descomponer(texto, base_origen):
    """
    Descompone un entero en notación posicional (base 10 o base 2) y lo pasa a
    la otra base. Devuelve {valido, mensaje, informe, valor, binario}.
    """
    r = {"valido": False, "mensaje": "", "informe": "", "valor": None,
         "binario": None}
    if base_origen not in (2, 10):
        r["mensaje"] = "La base de origen debe ser 10 o 2."
        return r
    t = (texto or "").strip().replace(" ", "").replace("_", "")
    t = t.replace(_MENOS, "-")
    if not t:
        r["mensaje"] = "Escribe un número entero."
        return r
    signo = 1
    if t[0] in "+-":
        signo = -1 if t[0] == "-" else 1
        t = t[1:]
    if not t:
        r["mensaje"] = "Falta el número después del signo."
        return r
    if "." in t or "," in t:
        r["mensaje"] = "Solo se admiten números enteros (sin parte decimal)."
        return r
    validos = "01" if base_origen == 2 else "0123456789"
    malos = [c for c in t if c not in validos]
    if malos:
        r["mensaje"] = ("«{}» no es válido en base {}: {}."
                        .format(malos[0], base_origen,
                                "solo dígitos 0 y 1" if base_origen == 2
                                else "solo dígitos del 0 al 9"))
        return r
    if len(t) > (400 if base_origen == 2 else 120):
        r["mensaje"] = "El número es demasiado largo."
        return r

    digitos = list(t)
    destino = 2 if base_origen == 10 else 10
    pre = _MENOS if signo < 0 else ""
    lineas = ["=== Notación posicional ===", ""]
    lineas.append("Número: {}{}".format(pre, t))
    lineas.append("Base de origen: {}      Base del resultado: {}".format(
        base_origen, destino))
    if signo < 0:
        lineas.append("El signo (−) se conserva y la descomposición posicional se "
                 "realiza sobre el valor absoluto.")
    lineas.append("")
    lineas.append("--- 1) Descomposición en base {} (base de origen) ---".format(base_origen))
    l1, l2, valor = _descomposicion(digitos, base_origen, signo)
    lineas += [l1, l2]

    if base_origen == 10:
        lineas.append("")
        lineas.append("--- 2) Conversión a base 2: divisiones sucesivas entre 2 ---")
        binario = _a_binario(valor, lineas)
        lineas.append("  Los residuos, leídos de abajo hacia arriba, dan el número "
                 "en base 2.")
        lineas.append("  {}({}){} = {}({}){}".format(
            pre, valor, _sub(10), pre, binario, _sub(2)))
        lineas.append("")
        lineas.append("--- 3) Descomposición en base 2 (base del resultado) ---")
        b1, b2, valor_dest = _descomposicion(list(binario), 2, signo)
        lineas += [b1, b2]
        dec_valor, bin_valor = valor, valor_dest
    else:
        binario = t.lstrip("0") or "0"
        lineas.append("")
        lineas.append("--- 2) Equivalente en base 10 (base del resultado) ---")
        lineas.append("  {}({}){} = {}({}){}".format(
            pre, t, _sub(2), pre, valor, _sub(10)))
        lineas.append("")
        lineas.append("--- 3) Descomposición del resultado en base 10 ---")
        d1, d2, valor_dest = _descomposicion(list(str(valor)), 10, signo)
        lineas += [d1, d2]
        dec_valor, bin_valor = valor_dest, valor

    lineas.append("")
    lineas.append("--- Verificación de equivalencia ---")
    lineas.append("  Valor decimal: {}{}".format(pre, dec_valor))
    lineas.append("  Valor binario interpretado: {}{}".format(pre, bin_valor))
    ok = dec_valor == bin_valor == int(binario, 2)
    lineas.append("  " + ("Coinciden: el valor decimal y el binario son equivalentes."
                     if ok else "NO coinciden: revisar el cálculo."))
    r.update(valido=ok, valor=signo * dec_valor, binario=binario,
             informe="\n".join(lineas), mensaje="" if ok else "Verificación fallida")
    return r


def cif(v):
    """Número con cifras significativas, o notación científica si es extremo."""
    if v == 0:
        return "0"
    if 1e-4 <= abs(v) < 1e10:
        return "{:.10g}".format(v).replace("-", _MENOS)
    return "{:.6e}".format(v).replace("-", _MENOS)


def informe_punto_flotante():
    """0.1 + 0.2 == 0.3, épsilon de máquina, overflow y underflow."""
    import warnings
    from decimal import Decimal
    import numpy as np

    lineas = ["=== Representación en punto flotante ===", ""]
    suma = 0.1 + 0.2
    lineas.append("--- 1) ¿Por qué 0.1 + 0.2 == 0.3 puede dar False? ---")
    lineas.append("  0.1 + 0.2 == 0.3   →   {}".format(suma == 0.3))
    lineas.append("  0.1 + 0.2 = {!r}".format(suma))
    lineas.append("  0.3       = {!r}".format(0.3))
    lineas.append("  Valor exacto guardado para 0.1 = {}".format(Decimal(0.1)))
    lineas.append("  Valor exacto guardado para 0.2 = {}".format(Decimal(0.2)))
    lineas.append("  Valor exacto guardado para 0.3 = {}".format(Decimal(0.3)))
    lineas.append("  Explicación: la computadora guarda los números en binario (doble "
             "precisión, 53 bits de mantisa). 0.1, 0.2 y 0.3 no tienen una "
             "representación binaria finita, igual que 1/3 no la tiene en base "
             "10: se redondean al número representable más cercano. Al sumar "
             "0.1 y 0.2 los errores de redondeo se acumulan y el resultado no "
             "coincide con el redondeo de 0.3.")
    lineas.append("  |(0.1 + 0.2) − 0.3| = {}".format(cif(abs(suma - 0.3))))
    lineas.append("  Forma correcta de comparar: abs(a − b) ≤ tolerancia  →  {}"
             .format(abs(suma - 0.3) <= 1e-9))
    lineas.append("")

    eps = float(np.finfo(float).eps)
    lineas.append("--- 2) Épsilon de máquina (numpy.finfo(float).eps) ---")
    lineas.append("  eps = {!r} = 2⁻⁵²".format(eps))
    lineas.append("  Es la distancia entre 1.0 y el siguiente número representable "
             "mayor en doble precisión.")
    lineas.append("  1.0 + eps   == 1.0  →  {}".format(1.0 + eps == 1.0))
    lineas.append("  1.0 + eps/2 == 1.0  →  {}  (eps/2 queda por debajo de la "
             "resolución y se pierde)".format(1.0 + eps / 2 == 1.0))
    lineas.append("  Siguiente número tras 1.0 (nextafter) = {!r}"
             .format(float(np.nextafter(1.0, 2.0))))
    lineas.append("")

    lineas.append("--- 3) Overflow y underflow (ejemplos controlados) ---")
    lineas.append("  Resultados de este equipo con float de 64 bits; pueden variar "
             "según el tipo de dato y la operación, no son universales.")
    info = np.finfo(float)
    lineas.append("  Mayor float representable: {!r}".format(float(info.max)))
    lineas.append("  Menor float normal positivo: {!r}".format(float(info.tiny)))
    lineas.append("  Menor positivo (subnormal): {!r}".format(
        float(np.nextafter(0.0, 1.0))))
    lineas.append("")

    def ejecutar(etiqueta, fn, explicacion):
        """Corre fn() capturando avisos de NumPy y devuelve el bloque de texto con su explicación."""
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            with np.errstate(all="warn"):
                try:
                    res = fn()
                    texto = repr(res.item() if isinstance(res, np.generic)
                                 else res)
                except OverflowError as ex:
                    texto = "OverflowError: {}".format(ex)
        lineas.append("  {}".format(etiqueta))
        lineas.append("     resultado: {}".format(texto))
        if avisos:
            lineas.append("     advertencia capturada: {}: {}".format(
                avisos[0].category.__name__, avisos[0].message))
        lineas.append("     {}".format(explicacion))

    ejecutar("Overflow:  1e308 * 10  (float de Python)",
             lambda: 1e308 * 10,
             "Supera el mayor float: el resultado es inf (no es finito).")
    ejecutar("Overflow:  numpy.float64(1e308) * 10",
             lambda: np.float64(1e308) * np.float64(10),
             "NumPy devuelve inf y emite una advertencia de desbordamiento.")
    ejecutar("Overflow:  math.exp(1000)",
             lambda: math.exp(1000),
             "Aquí Python no devuelve inf: lanza OverflowError. El "
             "comportamiento depende de la operación.")
    ejecutar("Overflow:  numpy.float32(3e38) * 10  (precisión simple)",
             lambda: np.float32(3e38) * np.float32(10),
             "Con float32 el límite es mucho menor (≈ 3.4e38): depende del tipo.")
    ejecutar("Underflow: 5e-324 / 2",
             lambda: 5e-324 / 2,
             "Es menor que el menor positivo representable: se redondea a 0.0.")
    ejecutar("Underflow gradual: 1e-310 (subnormal)",
             lambda: 1e-310,
             "Entre 5e-324 y 2.2e-308 los números son subnormales: se "
             "representan con menos cifras significativas.")
    ejecutar("Underflow: numpy.float64(1e-200) * 1e-200",
             lambda: np.float64(1e-200) * np.float64(1e-200),
             "El producto exacto (1e-400) no es representable: resultado 0.0.")
    ejecutar("Desbordamiento de enteros fijos: numpy.int64 máximo + 1",
             lambda: np.int64(np.iinfo(np.int64).max) + np.int64(1),
             "Los enteros de ancho fijo «dan la vuelta» (negativo). Los int "
             "de Python no tienen este límite.")
    return "\n".join(lineas)


def informe_tipos_error():
    """Definición y un ejemplo calculado de cada tipo de error."""
    import numpy as np
    lineas = ["=== Tipos de error ===", ""]

    lineas.append("--- 1) Error inherente ---")
    lineas.append("  Definición: el que traen los datos de entrada (mediciones, "
             "constantes aproximadas), antes de calcular nada.")
    lineas.append("  Ejemplo: se mide el lado de un cuadrado y se lee 12.3 cm con una "
             "regla que apenas distingue ±0.05 cm.")
    area, area2 = 12.3 ** 2, 12.35 ** 2
    lineas.append("     Área con 12.3 cm   = {}".format(cif(area)))
    lineas.append("     Área con 12.35 cm  = {}".format(cif(area2)))
    lineas.append("     La incertidumbre de la medición ya cambia el resultado en "
             "{} cm² aunque el cálculo sea exacto.".format(cif(area2 - area)))
    lineas.append("")

    lineas.append("--- 2) Error de redondeo ---")
    lineas.append("  Definición: aparece al representar un número con un número "
             "finito de cifras.")
    lineas.append("  Ejemplo: 1/3 guardado con 6 decimales.")
    ea = abs(1 / 3 - 0.333333)
    lineas.append("     1/3 = {!r}  →  0.333333".format(1 / 3))
    lineas.append("     Error absoluto = |1/3 − 0.333333| = {}".format(cif(ea)))
    lineas.append("")

    lineas.append("--- 3) Error de truncamiento ---")
    lineas.append("  Definición: se comete al cortar un proceso infinito (serie, "
             "límite, iteración) después de un número finito de pasos. Es un "
             "error del MÉTODO numérico, no de la representación.")
    lineas.append("  Ejemplo: e = 1 + 1 + 1/2! + 1/3! + 1/4! + … cortada en 4 términos.")
    aprox = 1 + 1 + 1 / 2 + 1 / 6
    lineas.append("     e (valor de la máquina) = {!r}".format(math.e))
    lineas.append("     Aproximación con 4 términos = {}".format(cif(aprox)))
    lineas.append("     Error de truncamiento = {}".format(cif(abs(math.e - aprox))))
    lineas.append("")

    with np.errstate(all="ignore"):
        ov = np.float64(1e308) * np.float64(10)
        un = np.float64(5e-324) / np.float64(2)
    lineas.append("--- 4) Overflow (desbordamiento) ---")
    lineas.append("  Definición: el resultado es mayor que el mayor número "
             "representable.")
    lineas.append("  Ejemplo: 1e308 · 10 = {}".format(ov))
    lineas.append("")
    lineas.append("--- 5) Underflow ---")
    lineas.append("  Definición: el resultado es menor (en valor absoluto) que el "
             "menor número representable y se redondea a cero.")
    lineas.append("  Ejemplo: 5e-324 / 2 = {}".format(un))
    lineas.append("")

    lineas.append("--- 6) Error del modelo matemático ---")
    lineas.append("  Definición: la ecuación que describe el fenómeno ya es una "
             "simplificación de la realidad. Aunque se calcule SIN ningún error "
             "numérico, el resultado puede no coincidir con lo real.")
    lineas.append("  Ejemplo ilustrativo: tiempo de caída libre desde 100 m con "
             "t = √(2h/g), g = 9.81 m/s².")
    t = math.sqrt(2 * 100 / 9.81)
    lineas.append("     t = {} s".format(cif(t)))
    lineas.append("     Este modelo ignora la resistencia del aire: una caída real "
             "tardaría más. Esa diferencia es error del modelo y no se corrige "
             "usando más decimales ni más iteraciones.")
    lineas.append("")
    lineas.append("--- Truncamiento numérico frente a error de modelación ---")
    lineas.append("  • Truncamiento: el modelo es correcto, pero el método para "
             "resolverlo corta un proceso infinito (ejemplo 3).")
    lineas.append("  • Modelo: el método puede ser exacto, pero la ecuación no "
             "describe bien la realidad (ejemplo 6).")
    return "\n".join(lineas)


def calcular_errores(xv, xa):
    """Error absoluto, relativo y porcentual entre el valor verdadero y el aproximado."""
    r = {"valido": False, "mensaje": "", "informe": ""}
    try:
        xv = leer_numero(xv, "el valor verdadero xv")
        xa = leer_numero(xa, "el valor aproximado xa")
    except ValueError as ex:
        r["mensaje"] = str(ex)
        return r
    Ea = abs(xv - xa)
    lineas = ["=== Cálculo de errores ===", ""]
    lineas.append("Valor verdadero:   xv = {}".format(cif(xv)))
    lineas.append("Valor aproximado:  xa = {}".format(cif(xa)))
    lineas.append("")
    lineas.append("Error absoluto:  Ea = |xv − xa| = |{} − {}| = {}".format(
        cif(xv), cif(xa), cif(Ea)))
    if xv != 0:
        Er = Ea / abs(xv)
        lineas.append("Error relativo:  Er = |xv − xa| / |xv| = {} / {} = {}".format(
            cif(Ea), cif(abs(xv)), cif(Er)))
        lineas.append("Error relativo porcentual:  Er(%) = Er × 100 = {} %".format(
            cif(Er * 100)))
        r["Er"] = Er
    else:
        lineas.append("Error relativo:  no está definido porque xv = 0 (habría una "
                 "división entre cero).")
        lineas.append("Error relativo porcentual:  no está definido (no se muestra un "
                 "porcentaje ficticio). Solo se puede informar el error "
                 "absoluto.")
        r["Er"] = None
    r.update(valido=True, Ea=Ea, informe="\n".join(lineas))
    return r


def propagacion_error(x, dx):
    """Propagación con f(x) = sen(x) + x²: aproximación lineal frente al cambio real."""
    r = {"valido": False, "mensaje": "", "informe": ""}
    try:
        x = leer_numero(x, "x")
        dx = leer_numero(dx, "la perturbación Δx")
    except ValueError as ex:
        r["mensaje"] = str(ex)
        return r
    f = lambda t: math.sin(t) + t * t
    fp = lambda t: math.cos(t) + 2 * t
    try:
        fx, fx2, d = f(x), f(x + dx), fp(x)
    except (OverflowError, ValueError):
        r["mensaje"] = "Los valores son demasiado grandes para calcular."
        return r
    dy_ap = d * dx
    dy_real = fx2 - fx
    dif = abs(dy_ap - dy_real)
    lineas = ["=== Propagación del error ===", ""]
    lineas.append("f(x) = sen(x) + x²          f′(x) = cos(x) + 2x")
    lineas.append("x = {}      Δx = {}".format(cif(x), cif(dx)))
    lineas.append("")
    lineas.append("f(x)      = f({}) = {}".format(cif(x), cif(fx)))
    lineas.append("f(x + Δx) = f({}) = {}".format(cif(x + dx), cif(fx2)))
    lineas.append("f′(x)     = {}".format(cif(d)))
    lineas.append("")
    lineas.append("Δy aproximado = f′(x) · Δx = {} · {} = {}".format(
        cif(d), cif(dx), cif(dy_ap)))
    lineas.append("Δy real       = f(x + Δx) − f(x) = {} − {} = {}".format(
        cif(fx2), cif(fx), cif(dy_real)))
    lineas.append("Diferencia absoluta |Δy aproximado − Δy real| = {}".format(cif(dif)))
    if dy_real != 0:
        lineas.append("Diferencia relativa respecto al cambio real = {} %".format(
            cif(dif / abs(dy_real) * 100)))
    lineas.append("")
    lineas.append("--- Interpretación ---")
    lineas.append("  La aproximación mediante la derivada es de primer orden "
             "(recta tangente): el error que se comete es del orden de (Δx)². "
             "Funciona mejor cuando la perturbación es pequeña.")
    lineas.append("")
    lineas.append("--- Comprobación con perturbaciones cada vez menores ---")
    lineas.append("  {:>12}  {:>16}  {:>16}  {:>14}".format(
        "Δx", "Δy aproximado", "Δy real", "diferencia"))
    for k in (1, 10, 100, 1000):
        h = dx / k
        try:
            ap, re = d * h, f(x + h) - fx
        except (OverflowError, ValueError):
            continue
        lineas.append("  {:>12}  {:>16}  {:>16}  {:>14}".format(
            cif(h), cif(ap), cif(re), cif(abs(ap - re))))
    lineas.append("  Al dividir Δx entre 10, la diferencia baja aproximadamente "
             "100 veces (orden 2).")
    r.update(valido=True, informe="\n".join(lineas), dy_aprox=dy_ap, dy_real=dy_real,
             dif=dif)
    return r
