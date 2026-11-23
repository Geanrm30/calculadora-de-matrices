# -*- coding: utf-8 -*-
"""
Vectores: suma, resta, múltiplo escalar y combinación lineal c₁u + c₂v en un solo paso
para vectores de cualquier Rⁿ, más los datos para graficar u, v, u+v, u−v, c·u y la regla del
paralelogramo cuando n = 2. Aritmética exacta con fracciones.
Unidad: Proyecto Integrador (Vectores).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
from core import vector as V
from core.fraccion import desde_texto

def leer_vector(texto, nombre):
    """Lee «1, 2, 3», «(1; 2)» o «1 2» como lista de Fraccion; ValueError con el motivo si falla."""
    t = (texto or "").strip().strip("()[]<>").strip()
    if not t:
        raise ValueError("Falta el vector {}.".format(nombre))
    if ";" in t:
        partes = [p.strip() for p in t.split(";") if p.strip()]
    elif "," in t:
        partes = [p.strip() for p in t.split(",") if p.strip()]
    else:
        partes = t.split()
    try:
        return [desde_texto(p) for p in partes]
    except (ValueError, ZeroDivisionError):
        raise ValueError("El vector {} tiene un valor no válido: «{}». Escribe números separados "
                         "por comas, por ejemplo 2, −1, 3.".format(nombre, texto)) from None


def _v(vec):
    """Vector como «(a, b, c)»."""
    return "(" + ", ".join(str(x) for x in vec) + ")"


def _f(x):
    """Fraccion → float."""
    return x.a_decimal()


def calcular(u_txt, v_txt, c_txt, c1_txt, c2_txt):
    """
    Calcula u+v, u−v, c·u y c₁u + c₂v (en un solo paso) y, si n = 2, prepara los datos de la
    gráfica. Devuelve {valido, mensaje, campo, informe, grafica}.
    """
    r = {"valido": False, "mensaje": "", "campo": None, "informe": "", "grafica": None}
    campo = "u"
    try:
        u = leer_vector(u_txt, "u")
        campo = "v"
        v = leer_vector(v_txt, "v")
        if len(u) != len(v):
            raise ValueError("u tiene {} componentes y v tiene {}: deben estar en el mismo Rⁿ."
                             .format(len(u), len(v)))
        campo = "c"
        c = desde_texto(c_txt)
        campo = "c1"
        c1 = desde_texto(c1_txt)
        campo = "c2"
        c2 = desde_texto(c2_txt)
    except (ValueError, ZeroDivisionError) as ex:
        texto = str(ex)
        if "Valor vacio" in texto or not texto:
            texto = "Falta un escalar: escribe un número o una fracción."
        r.update(mensaje=texto, campo=campo)
        return r
    n = len(u)
    suma = V.sumar_vectores(u, v)
    resta = V.sumar_vectores(u, V.escalar_por_vector(desde_texto("-1"), v))
    cu = V.escalar_por_vector(c, u)
    comb = V.combinacion_con_escalares([u, v], [c1, c2])

    L = ["=== Vectores en R{} ===".format(_sup(n)), "",
         "u = {}      v = {}".format(_v(u), _v(v)),
         "c = {}      c₁ = {}      c₂ = {}".format(c, c1, c2), "",
         "--- Suma: u + v (componente a componente) ---",
         "  u + v = ({})".format(", ".join("{} + {}".format(a, _par(b)) for a, b in zip(u, v))),
         "        = {}".format(_v(suma)), "",
         "--- Resta: u − v ---",
         "  u − v = ({})".format(", ".join("{} − {}".format(a, _par(b)) for a, b in zip(u, v))),
         "        = {}".format(_v(resta)), "",
         "--- Múltiplo escalar: c·u ---",
         "  c·u = ({})".format(", ".join("{}·{}".format(_par(c), _par(a)) for a in u)),
         "      = {}".format(_v(cu)), "",
         "--- Combinación lineal en un solo paso: c₁·u + c₂·v ---",
         "  Cada componente i es  c₁·uᵢ + c₂·vᵢ:"]
    for i in range(n):
        L.append("    componente {}:  {}·{} + {}·{} = {}".format(
            i + 1, _par(c1), _par(u[i]), _par(c2), _par(v[i]), comb[i]))
    L += ["  c₁·u + c₂·v = {}".format(_v(comb)), ""]
    # Comprobación: coincide con hacerlo en dos pasos.
    dos = V.sumar_vectores(V.escalar_por_vector(c1, u), V.escalar_por_vector(c2, v))
    L.append("  Comprobación en dos pasos (c₁·u, luego c₂·v y sumar): {}  [{}]".format(
        _v(dos), "Se cumple" if all(a == b for a, b in zip(dos, comb)) else "No se cumple"))
    if n == 2:
        L += ["", "--- Gráfica en R² ---",
              "  Se dibujan u, v, u+v (diagonal del paralelogramo con lados u y v), u−v, c·u y "
              "c₁u + c₂v. La regla del paralelogramo: u + v es la diagonal que sale del origen."]
        r["grafica"] = _grafica(u, v, suma, resta, cu, comb, c, c1, c2)
    else:
        L += ["", "[INFO] La gráfica solo se dibuja para vectores de R² (2 componentes); aquí n = {}."
              .format(n)]
    r.update(valido=True, informe="\n".join(L), u=u, v=v, suma=suma, resta=resta, cu=cu, comb=comb)
    return r


def _par(x):
    """Número entre paréntesis si es negativo o fracción."""
    t = str(x)
    return "(" + t + ")" if (t.startswith("-") or t.startswith("−") or "/" in t) else t


def _sup(n):
    """Entero con dígitos superíndice."""
    return str(n).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))


def _grafica(u, v, suma, resta, cu, comb, c, c1, c2):
    """Datos de la gráfica de R²: flechas desde el origen y líneas del paralelogramo."""
    p = lambda vec: (_f(vec[0]), _f(vec[1]))
    flechas = [("u", p(u), "azul"), ("v", p(v), "naranja"), ("u + v", p(suma), "verde"),
               ("u − v", p(resta), "rojo"), ("c·u  (c = {})".format(c), p(cu), "morado")]
    flechas.append(("c₁u + c₂v", p(comb), "texto"))
    puntos = [(0.0, 0.0)] + [f[1] for f in flechas]
    xs = [a for a, _ in puntos]
    ys = [b for _, b in puntos]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    lado = max(xmax - xmin, ymax - ymin, 1.0)
    pad = 0.12 * lado
    return {"valido": True, "mensaje": "", "flechas": flechas,
            "paralelogramo": [p(u), p(suma), p(v)],
            "limites": (xmin - pad, xmax + pad, ymin - pad, ymax + pad),
            "titulo": "Vectores en R²: u, v, u + v y u − v",
            "resumen": "Las líneas punteadas completan el paralelogramo de lados u y v: su diagonal "
                       "desde el origen es u + v."}
