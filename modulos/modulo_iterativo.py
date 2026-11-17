# -*- coding: utf-8 -*-
"""
Módulo de métodos iterativos (Programa 8): Jacobi y Gauss-Seidel.

Lógica pura, sin interfaz. Ambos métodos se programan desde cero con ciclos por
componente; NumPy solo se usa para las matrices de iteración, el radio espectral
y la solución de referencia con la que se contrastan los resultados.
Notación: A = D + L + U, x(k) es la aproximación de la iteración k y
d = ‖x(k) − x(k−1)‖ es el error entre iteraciones.
Unidad: Programa 8: Métodos Numéricos Integrador (Jacobi y Gauss-Seidel).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""
import math

import numpy as np

from core.fraccion import desde_texto
from core.formato import subindice
from modulos.modulo_numerico import leer_numero, num

LIMITE_N = 20
LIMITE_ITER = 5000
DESBORDE = 1e100
ITERACIONES_DETALLADAS = 300
FILAS_INFORME = 300
FILAS_INICIO = 250
FILAS_FINAL = 25
RACHA_CRECIMIENTO = 10
_TOLERANCIA_DOMINANCIA = 1e-12
_MENOS = "−"

CRITERIOS = {
    "norma2": "Norma 2:  d = ‖x(k) − x(k−1)‖₂ < ε",
    "norma_inf": "Norma ∞:  d = ‖x(k) − x(k−1)‖∞ < ε",
    "ea_pct": "Error relativo porcentual:  máx εₐ,ᵢ (%) < εₛ",
}
_COLUMNA_ERROR = {"norma2": "‖Δx‖₂", "norma_inf": "‖Δx‖∞", "ea_pct": "máx εₐ (%)"}
_NOMBRES = {"jacobi": "Jacobi", "gauss_seidel": "Gauss-Seidel"}


class ErrorEntrada(ValueError):
    """Dato de entrada inválido; `campo` y `posicion` dicen dónde está para marcarlo en pantalla."""

    def __init__(self, mensaje, campo, posicion=None):
        """Guarda el mensaje, el campo culpable (A, b, x0, eps, nmax, lam) y la celda (fila, columna)."""
        super().__init__(mensaje)
        self.campo = campo
        self.posicion = posicion


def _celda(valor, nombre, campo, posicion):
    """Convierte una celda (texto o número) a float; lanza ErrorEntrada si no es un número finito."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        v = float(valor)
    else:
        try:
            v = float(desde_texto(str(valor)).a_decimal())
        except (ValueError, ZeroDivisionError):
            v = float("nan")
    if not math.isfinite(v):
        raise ErrorEntrada("«{}» no es un número válido en {} (fila {}, columna {})."
                           .format(valor, nombre, posicion[0] + 1, posicion[1] + 1),
                           campo, posicion)
    return v


def _escalar(valor, nombre, campo):
    """Lee tolerancia, iteraciones o λ; lanza ErrorEntrada con el motivo si no sirve."""
    try:
        return leer_numero(valor, nombre)
    except ValueError as ex:
        raise ErrorEntrada(str(ex), campo) from None


def validar_entradas(A, b, x0, tolerancia, max_iter, lam=1.0):
    """
    Valida dimensiones, tolerancia, máximo de iteraciones y λ.
    Devuelve (A, b, x0, eps, nmax, lam) numéricos o lanza ErrorEntrada.
    """
    n = len(A) if A else 0
    if n == 0:
        raise ErrorEntrada("Escribe la matriz de coeficientes A.", "A")
    if n > LIMITE_N:
        raise ErrorEntrada("A puede tener como máximo {} filas.".format(LIMITE_N), "A")
    for fila in A:
        if len(fila) != n:
            raise ErrorEntrada("A debe ser cuadrada (n × n): recibí {} filas y {} columnas."
                               .format(n, len(fila)), "A")
    if len(b) != n:
        raise ErrorEntrada("b debe tener {} componentes (una por fila de A); recibí {}."
                           .format(n, len(b)), "b")
    if len(x0) != n:
        raise ErrorEntrada("El vector inicial x(0) debe tener {} componentes; recibí {}."
                           .format(n, len(x0)), "x0")
    A = [[_celda(A[i][j], "A", "A", (i, j)) for j in range(n)] for i in range(n)]
    b = [_celda(b[i], "b", "b", (i, 0)) for i in range(n)]
    x0 = [_celda(x0[i], "x(0)", "x0", (i, 0)) for i in range(n)]
    eps = _escalar(tolerancia, "la tolerancia ε", "eps")
    if eps <= 0:
        raise ErrorEntrada("La tolerancia debe ser positiva (ε > 0).", "eps")
    nmax = _escalar(max_iter, "las iteraciones máximas", "nmax")
    if nmax != int(nmax) or nmax < 1:
        raise ErrorEntrada("Las iteraciones máximas deben ser un entero positivo.", "nmax")
    if nmax > LIMITE_ITER:
        raise ErrorEntrada("Las iteraciones máximas no pueden pasar de {}.".format(LIMITE_ITER),
                           "nmax")
    lam = _escalar(lam, "el factor de relajación λ", "lam")
    if not 0 < lam < 2:
        raise ErrorEntrada("El factor de relajación debe cumplir 0 < λ < 2.", "lam")
    return A, b, x0, eps, int(nmax), lam


def analizar_diagonal(A):
    """
    Índices con aᵢᵢ = 0 y, por fila, |aᵢᵢ|, Σ|aᵢⱼ| (j ≠ i) y si la fila domina de forma estricta.
    La dominancia estricta exige |aᵢᵢ| > Σ|aᵢⱼ|; la igualdad no cuenta.
    """
    n = len(A)
    ceros = [i for i in range(n) if A[i][i] == 0]
    filas = []
    for i in range(n):
        suma = sum(abs(A[i][j]) for j in range(n) if j != i)
        diag = abs(A[i][i])
        filas.append({"i": i, "diag": diag, "suma": suma,
                      "domina": diag - suma > _TOLERANCIA_DOMINANCIA * max(1.0, diag)})
    return ceros, filas


def es_simetrica_definida_positiva(A):
    """Indica si A es simétrica y definida positiva (intenta la factorización de Cholesky)."""
    M = np.array(A, dtype=float)
    if not np.allclose(M, M.T, rtol=1e-12, atol=1e-12):
        return False
    try:
        np.linalg.cholesky(M)
    except np.linalg.LinAlgError:
        return False
    return True


def buscar_reordenamiento(A):
    """
    Busca una permutación de filas. Devuelve (tipo, p) o None, donde la fila nueva j es la
    original p[j]. 'dominante' deja la diagonal estrictamente dominante; 'sin_ceros' solo la
    deja sin ceros.
    """
    n = len(A)
    destino = []
    for fila in A:
        total = sum(abs(v) for v in fila)
        # |aᵢⱼ| > Σ_{k≠j}|aᵢₖ| equivale a 2|aᵢⱼ| > Σ|aᵢₖ|: a lo más una columna lo cumple.
        posibles = [j for j, v in enumerate(fila)
                    if 2 * abs(v) - total > _TOLERANCIA_DOMINANCIA * max(1.0, total)]
        destino.append(posibles[0] if posibles else None)
    if None not in destino and len(set(destino)) == n:
        permutacion = [0] * n
        for fila, columna in enumerate(destino):
            permutacion[columna] = fila
        return "dominante", permutacion

    candidatos = [sorted((j for j in range(n) if A[i][j] != 0), key=lambda j: -abs(A[i][j]))
                  for i in range(n)]
    asignada = [None] * n

    def acomodar(fila, vistas):
        """Camino de aumento: coloca la fila en alguna columna libre o desplaza a otra fila."""
        for j in candidatos[fila]:
            if j in vistas:
                continue
            vistas.add(j)
            if asignada[j] is None or acomodar(asignada[j], vistas):
                asignada[j] = fila
                return True
        return False

    if all(acomodar(i, set()) for i in range(n)):
        return "sin_ceros", asignada
    return None


def aplicar_permutacion(A, b, permutacion):
    """Reordena las filas de A y de b: la fila nueva j es la original permutacion[j]."""
    return [list(A[p]) for p in permutacion], [b[p] for p in permutacion]


def _proponer_reordenamiento(A, ceros, dominante):
    """Reordenamiento que mejora la diagonal (quita ceros o logra dominancia), o None."""
    if not ceros and dominante:
        return None
    hallado = buscar_reordenamiento(A)
    if hallado is None:
        return None
    tipo, permutacion = hallado
    if permutacion == list(range(len(A))) or (tipo == "sin_ceros" and not ceros):
        return None
    return {"tipo": tipo, "permutacion": permutacion}


def radio_espectral(T):
    """ρ(T) = máx |λᵢ| con NumPy; None si el cálculo de valores propios no converge."""
    try:
        return float(max(abs(np.linalg.eigvals(T))))
    except np.linalg.LinAlgError:
        return None


def matrices_iteracion(A, b, lam=1.0):
    """
    D, L, U y, para x(k+1) = T·x(k) + c, las matrices T y c de Jacobi y de Gauss-Seidel con
    relajación λ: T_GS = (D + λL)⁻¹[(1 − λ)D − λU] y c_GS = λ(D + λL)⁻¹b.
    """
    M = np.array(A, dtype=float)
    v = np.array(b, dtype=float)
    D = np.diag(np.diag(M))
    L = np.tril(M, -1)
    U = np.triu(M, 1)
    D_inv = np.diag(1.0 / np.diag(M))
    T_J = -D_inv @ (L + U)
    c_J = D_inv @ v
    izquierda = D + lam * L
    T_GS = np.linalg.solve(izquierda, (1 - lam) * D - lam * U)
    c_GS = lam * np.linalg.solve(izquierda, v)
    return {"D": D.tolist(), "L": L.tolist(), "U": U.tolist(),
            "TJ": T_J.tolist(), "cJ": c_J.tolist(), "TGS": T_GS.tolist(),
            "cGS": c_GS.tolist(), "rho_J": radio_espectral(T_J),
            "rho_GS": radio_espectral(T_GS)}


def solucion_referencia(A, b):
    """Solución de numpy.linalg.solve(A, b) para contrastar; None si A es singular."""
    try:
        x = np.linalg.solve(np.array(A, dtype=float), np.array(b, dtype=float))
    except np.linalg.LinAlgError:
        return None
    return x.tolist() if np.all(np.isfinite(x)) else None


def _paso_jacobi(A, b, x, lam):
    """Una iteración de Jacobi: todos los componentes nuevos usan solo el vector anterior."""
    n = len(A)
    nuevo = [0.0] * n
    for i in range(n):
        suma = 0.0
        for j in range(n):
            if j != i:
                suma += A[i][j] * x[j]
        nuevo[i] = (b[i] - suma) / A[i][i]
    return nuevo


def _paso_gauss_seidel(A, b, x, lam):
    """Una iteración de Gauss-Seidel: cada xᵢ nuevo se usa de inmediato; con λ pondera con xᵢ anterior."""
    n = len(A)
    nuevo = list(x)
    for i in range(n):
        suma = 0.0
        for j in range(n):
            if j != i:
                suma += A[i][j] * nuevo[j]
        gauss_seidel = (b[i] - suma) / A[i][i]
        nuevo[i] = lam * gauss_seidel + (1 - lam) * x[i]
    return nuevo


_PASOS = {"jacobi": _paso_jacobi, "gauss_seidel": _paso_gauss_seidel}


def _residuo(A, b, x):
    """‖A·x − b‖∞ calculado con ciclos."""
    mayor = 0.0
    for i in range(len(A)):
        suma = 0.0
        for j in range(len(A)):
            suma += A[i][j] * x[j]
        mayor = max(mayor, abs(suma - b[i]))
    return mayor


def _norma2(vector):
    """Norma euclídea de un vector (sin elevar al cuadrado con **, que desborda con error)."""
    return math.sqrt(sum(v * v for v in vector))


def _criterio(criterio, nuevo, viejo, eps):
    """Valor del error entre iteraciones según el criterio y si cumple (valor < eps); None si no está definido."""
    dif = [a - c for a, c in zip(nuevo, viejo)]
    if criterio == "norma_inf":
        valor = max(abs(d) for d in dif)
    elif criterio == "ea_pct":
        porcentajes = []
        for a, c in zip(nuevo, viejo):
            if a != 0:
                porcentajes.append(abs((a - c) / a) * 100)
            elif c == 0:
                porcentajes.append(0.0)
            else:
                return None, False
        valor = max(porcentajes)
    else:
        valor = _norma2(dif)
    return valor, valor < eps


def _fila_tabla(k, x, A, b, x_ref, valor=None, d2=None, cumple=False):
    """Fila de la tabla: x(k), error entre iteraciones, error verdadero ‖x* − x(k)‖₂ y residuo."""
    finito = all(math.isfinite(v) for v in x)
    return {"k": k, "x": list(x), "delta": valor, "d2": d2, "cumple": cumple,
            "err_ver": (_norma2([a - c for a, c in zip(x_ref, x)])
                        if x_ref is not None and finito else None),
            "residuo": _residuo(A, b, x) if finito else None}


def iterar(clave, A, b, x0, eps, nmax, criterio, lam, x_ref, rho):
    """
    Ejecuta Jacobi ('jacobi') o Gauss-Seidel ('gauss_seidel') hasta ε, el máximo o la divergencia.
    Devuelve las filas de la tabla, la aproximación final y el motivo de parada.
    """
    paso = _PASOS[clave]
    x = list(x0)
    filas = [_fila_tabla(0, x, A, b, x_ref)]
    motivo = "maximo"
    previo, racha = None, 0
    for k in range(1, nmax + 1):
        nuevo = paso(A, b, x, lam if clave == "gauss_seidel" else 1.0)
        if any(not math.isfinite(v) or abs(v) > DESBORDE for v in nuevo):
            filas.append(_fila_tabla(k, nuevo, A, b, x_ref))
            motivo = "diverge"
            break
        valor, cumple = _criterio(criterio, nuevo, x, eps)
        d2 = _norma2([a - c for a, c in zip(nuevo, x)])
        filas.append(_fila_tabla(k, nuevo, A, b, x_ref, valor, d2, cumple))
        x = nuevo
        if cumple:
            motivo = "tolerancia"
            break
        racha = racha + 1 if previo is not None and d2 > previo else 0
        previo = d2
        # Con ρ(T) ≥ 1 el error no puede decrecer a largo plazo: se detiene el crecimiento sostenido.
        if racha >= RACHA_CRECIMIENTO and not (rho is not None and rho < 1):
            motivo = "crece"
            break
    final = filas[-1]
    return {"clave": clave, "nombre": _NOMBRES[clave], "filas": filas, "x": final["x"],
            "iteraciones": len(filas) - 1, "motivo": motivo,
            "convergio": motivo == "tolerancia", "delta_final": final["delta"],
            "residuo_final": final["residuo"], "rho": rho}


def comparar(jacobi, gauss_seidel, x_ref):
    """Qué método usó menos iteraciones, la diferencia entre soluciones y el contraste con la referencia."""
    ambos = jacobi["convergio"] and gauss_seidel["convergio"]
    if ambos:
        j, g = jacobi["iteraciones"], gauss_seidel["iteraciones"]
        mas_rapido = "gauss_seidel" if g < j else "jacobi" if j < g else "igual"
    elif gauss_seidel["convergio"]:
        mas_rapido = "gauss_seidel"
    elif jacobi["convergio"]:
        mas_rapido = "jacobi"
    else:
        mas_rapido = None
    finitos = all(math.isfinite(v) for v in jacobi["x"] + gauss_seidel["x"])
    dif = (max(abs(a - c) for a, c in zip(jacobi["x"], gauss_seidel["x"]))
           if finitos else None)
    validacion = {}
    for met in (jacobi, gauss_seidel):
        if met["convergio"] and x_ref is not None:
            resta = [a - c for a, c in zip(met["x"], x_ref)]
            validacion[met["clave"]] = {"dif_inf": max(abs(d) for d in resta),
                                        "dif_2": _norma2(resta),
                                        "residuo": met["residuo_final"]}
    return {"mas_rapido": mas_rapido, "ambos": ambos, "dif_soluciones": dif,
            "validacion": validacion}


def _resultado_vacio():
    """Diccionario de resultado con todas las claves en su valor inicial."""
    return {"valido": False, "mensaje": "", "campo": None, "posicion": None,
            "advertencias": [], "informe": "", "n": 0, "A": None, "b": None,
            "A_original": None, "b_original": None, "x0": None, "eps": None,
            "nmax": None, "criterio": "norma2", "lam": 1.0, "ceros": [],
            "dominancia": [], "es_dominante": False, "spd": None,
            "propuesta": None, "permutacion": None, "matrices": None, "forma_matricial": False,
            "x_ref": None, "jacobi": None, "gauss_seidel": None,
            "comparacion": None}


def resolver(A, b, x0, tolerancia, max_iter, criterio="norma2", lam=1.0, reordenar=False,
             forma_matricial=False):
    """
    Valida los datos, diagnostica la diagonal y, si todo está bien, ejecuta Jacobi y Gauss-Seidel
    con el mismo criterio. Con `reordenar` aplica el reordenamiento de filas propuesto y con
    `forma_matricial` el informe incluye D, L, U, T y c.
    Si hay ceros en la diagonal no calcula y deja la propuesta en r['propuesta'].
    """
    r = _resultado_vacio()
    if criterio not in CRITERIOS:
        r["mensaje"] = "Criterio de parada desconocido."
        return r
    try:
        A, b, x0, eps, nmax, lam = validar_entradas(A, b, x0, tolerancia, max_iter, lam)
    except ErrorEntrada as ex:
        r.update(mensaje=str(ex), campo=ex.campo, posicion=ex.posicion)
        return r
    n = len(A)
    r.update(n=n, A=A, b=b, A_original=A, b_original=b, x0=x0, eps=eps, nmax=nmax,
             criterio=criterio, lam=lam, forma_matricial=forma_matricial)
    ceros, dominancia = analizar_diagonal(A)
    dominante = all(f["domina"] for f in dominancia)
    propuesta = _proponer_reordenamiento(A, ceros, dominante)
    r["propuesta"] = propuesta
    if reordenar and propuesta is not None:
        A, b = aplicar_permutacion(A, b, propuesta["permutacion"])
        r.update(A=A, b=b, permutacion=propuesta["permutacion"])
        ceros, dominancia = analizar_diagonal(A)
        dominante = all(f["domina"] for f in dominancia)
    r.update(ceros=ceros, dominancia=dominancia, es_dominante=dominante,
             spd=es_simetrica_definida_positiva(A))
    if ceros:
        r["mensaje"] = _mensaje_ceros(ceros, propuesta)
        r["informe"] = informe(r)
        return r

    r["matrices"] = matrices_iteracion(A, b, lam)
    r["x_ref"] = solucion_referencia(A, b)
    if r["x_ref"] is None:
        r["advertencias"].append(
            "A es singular (det(A) = 0): el sistema no tiene solución única, así que no hay "
            "solución de referencia y es de esperar que los métodos no converjan.")
    m = r["matrices"]
    r["jacobi"] = iterar("jacobi", A, b, x0, eps, nmax, criterio, lam, r["x_ref"], m["rho_J"])
    r["gauss_seidel"] = iterar("gauss_seidel", A, b, x0, eps, nmax, criterio, lam,
                               r["x_ref"], m["rho_GS"])
    r["comparacion"] = comparar(r["jacobi"], r["gauss_seidel"], r["x_ref"])
    r["valido"] = True
    r["mensaje"] = _mensaje_final(r)
    r["informe"] = informe(r)
    return r


def _mensaje_ceros(ceros, propuesta):
    """Mensaje de la validación de ceros en la diagonal, con o sin salida por reordenamiento."""
    donde = ", ".join("a{0}{0}".format(subindice(i + 1)) for i in ceros)
    texto = ("La diagonal principal tiene ceros ({} = 0): Jacobi y Gauss-Seidel dividen entre "
             "aᵢᵢ y no pueden iniciar.".format(donde))
    if propuesta is not None:
        return texto + " Existe un reordenamiento de filas que lo evita: confírmalo para continuar."
    return (texto + " No se encontró ningún ordenamiento de filas que deje la diagonal sin ceros; "
            "no se fuerza ninguno.")


def _mensaje_final(r):
    """Resumen de una línea del resultado: qué ocurrió con cada método."""
    partes = []
    for met in (r["jacobi"], r["gauss_seidel"]):
        if met["convergio"]:
            partes.append("{}: {} iteraciones".format(met["nombre"], met["iteraciones"]))
        else:
            partes.append("{}: {}".format(met["nombre"], _ESTADO_CORTO[met["motivo"]]))
    return "  ·  ".join(partes)


_ESTADO_CORTO = {"tolerancia": "tolerancia alcanzada",
                 "maximo": "máximo de iteraciones sin cumplir ε",
                 "diverge": "diverge", "crece": "el error crece (posible divergencia)"}


def nombre_metodo(clave, lam):
    """Nombre del método para los títulos; indica λ cuando Gauss-Seidel usa relajación."""
    if clave == "gauss_seidel" and lam != 1:
        return "Gauss-Seidel con relajación (λ = {})".format(_corto(lam))
    return _NOMBRES[clave]


def _corto(v):
    """Número con hasta 10 cifras significativas (tolerancias como 1e-10 o 0.0001)."""
    return "{:.10g}".format(v)


def _c(v):
    """Número compacto: 6 decimales sin ceros sobrantes, menos tipográfico, sin exponente."""
    if not math.isfinite(v):
        return "no finito"
    if abs(v) >= 1e10:
        return "{:.4e}".format(v).replace("-", _MENOS)
    texto = "{:.6f}".format(v).rstrip("0").rstrip(".")
    return "0" if texto in ("", "-0") else texto.replace("-", _MENOS)


def _p(v):
    """Número compacto, entre paréntesis si es negativo (para productos)."""
    texto = _c(v)
    return "({})".format(texto) if texto.startswith(_MENOS) else texto


def _f(v):
    """Componente de x con 6 decimales fijos (columnas de la tabla)."""
    if not math.isfinite(v):
        return "no finito"
    return num(v, 6) if abs(v) < 1e10 else "{:.4e}".format(v).replace("-", _MENOS)


def _fe(v):
    """Error o residuo: 6 decimales, notación científica si es muy pequeño o muy grande."""
    if v is None:
        return "—"
    if not math.isfinite(v):
        return "no finito"
    if v == 0:
        return "0"
    if abs(v) < 1e-5 or abs(v) >= 1e6:
        return "{:.3e}".format(v)
    return "{:.6f}".format(v)


def _vector(x):
    """Vector fila con la t de transpuesta: (1.4, 0.5, 1.4)ᵗ."""
    return "(" + ", ".join(_c(v) for v in x) + ")ᵗ"


def columnas(n, criterio, con_referencia=True):
    """Nombres de las columnas de la tabla: k, x₁…xₙ, error entre iteraciones, error verdadero y residuo."""
    cab = ["k"] + ["x" + subindice(i + 1) for i in range(n)] + [_COLUMNA_ERROR[criterio]]
    if con_referencia:
        cab.append("‖x* − x(k)‖₂")
    return cab + ["‖b − Ax‖∞"]


def valores_fila(fila, criterio, con_referencia=True):
    """Celdas de una fila de la tabla en el orden de `columnas`."""
    celdas = [str(fila["k"])] + [_f(v) for v in fila["x"]] + [_fe(fila["delta"])]
    if con_referencia:
        celdas.append(_fe(fila["err_ver"]))
    return celdas + [_fe(fila["residuo"])]


def tabla_texto(cabecera, filas, sangria=""):
    """Tabla de texto con columnas alineadas a la derecha y separadas por dos espacios."""
    anchos = [max(len(cabecera[c]), *(len(f[c]) for f in filas)) if filas else len(cabecera[c])
              for c in range(len(cabecera))]
    lineas = [sangria + "  ".join(h.rjust(w) for h, w in zip(cabecera, anchos)),
              sangria + "  ".join("-" * w for w in anchos)]
    for fila in filas:
        lineas.append(sangria + "  ".join(v.rjust(w) for v, w in zip(fila, anchos)))
    return lineas


def _tabla_de_iteraciones(met, r):
    """Líneas de la tabla de iteraciones; con muchas filas deja las primeras y las últimas."""
    con_ref = r["x_ref"] is not None
    cab = columnas(r["n"], r["criterio"], con_ref)
    filas = met["filas"]
    if len(filas) <= FILAS_INFORME:
        return tabla_texto(cab, [valores_fila(f, r["criterio"], con_ref) for f in filas])
    inicio, final = filas[:FILAS_INICIO], filas[-FILAS_FINAL:]
    omitidas = len(filas) - FILAS_INICIO - FILAS_FINAL
    return (tabla_texto(cab, [valores_fila(f, r["criterio"], con_ref) for f in inicio])
            + ["", "  … {} iteraciones intermedias omitidas en este informe (la tabla de la "
               "pantalla las incluye todas) …".format(omitidas), ""]
            + tabla_texto(cab, [valores_fila(f, r["criterio"], con_ref) for f in final]))


def _lineas_matriz(M, derecha=None, sangria="  "):
    """Filas «[ a b | c ]» con las columnas alineadas, para que el visor las dibuje como matriz."""
    celdas = [[_c(v) for v in fila] for fila in M]
    ancho = max(len(c) for fila in celdas for c in fila)
    ancho_der = max(len(c) for c in derecha) if derecha else 0
    lineas = []
    for i, fila in enumerate(celdas):
        cuerpo = " ".join(c.rjust(ancho) for c in fila)
        if derecha:
            cuerpo += " | " + derecha[i].rjust(ancho_der)
        lineas.append("{}[ {} ]".format(sangria, cuerpo))
    return lineas


def _lineas_columna(x, sangria="  "):
    """Vector columna como matriz de una columna."""
    return _lineas_matriz([[v] for v in x], sangria=sangria)


def _lineas_validaciones(r):
    """Apartado 1: dimensiones, tolerancia, máximo de iteraciones y ceros en la diagonal."""
    n = r["n"]
    lineas = ["--- 1) Validaciones ---",
              "  [Se cumple] A es {0}×{0}; b y x(0) tienen {0} componentes; ε > 0 y las "
              "iteraciones máximas son un entero positivo.".format(n)]
    if r["permutacion"] is not None:
        lineas.append("  Reordenamiento de filas aplicado (fila nueva ← fila original): "
                      + ",  ".join("{} ← {}".format(j + 1, p + 1)
                                   for j, p in enumerate(r["permutacion"])))
    if r["ceros"]:
        lineas.append("  [No se cumple] Hay ceros en la diagonal principal: "
                      + ", ".join("a{0}{0} = 0".format(subindice(i + 1)) for i in r["ceros"]) + ".")
        lineas.append("  " + r["mensaje"])
    else:
        lineas.append("  [Se cumple] Ningún elemento de la diagonal principal es cero.")
    return lineas


def _lineas_diagonal(r):
    """Apartado 2: dominancia estricta por filas, definida positiva y propuesta de reordenamiento."""
    lineas = ["", "--- 2) Diagonal estrictamente dominante por filas ---"]
    filas = [[str(f["i"] + 1), _c(f["diag"]), _c(f["suma"]), "Sí" if f["domina"] else "No"]
             for f in r["dominancia"]]
    lineas += tabla_texto(["i", "|aᵢᵢ|", "Σ|aᵢⱼ|, j ≠ i", "¿Domina?"], filas, "  ")
    if r["es_dominante"]:
        lineas.append("  [Se cumple] |aᵢᵢ| > Σ|aᵢⱼ| en todas las filas: condición suficiente de "
                      "convergencia.")
    else:
        lineas.append("  [No se cumple] No domina en todas las filas. Es una condición suficiente, "
                      "no necesaria: decide ρ(T) < 1.")
    if r["spd"]:
        lineas.append("  A es simétrica y definida positiva: Gauss-Seidel converge.")
    p = r["propuesta"]
    if p is not None and r["permutacion"] is None:
        lineas.append("  Reordenamiento propuesto (fila nueva ← fila original): "
                      + ",  ".join("{} ← {}".format(j + 1, o + 1)
                                   for j, o in enumerate(p["permutacion"]))
                      + ("  (deja la diagonal dominante)" if p["tipo"] == "dominante"
                         else "  (solo quita los ceros; no garantiza convergencia)"))
    elif p is None and (r["ceros"] or not r["es_dominante"]):
        lineas.append("  Ninguna permutación de filas deja la diagonal "
                      + ("sin ceros." if r["ceros"] else "estrictamente dominante."))
    return lineas


def _lineas_radios(r):
    """Radios espectrales ρ(T_J) y ρ(T_GS) con su veredicto de convergencia."""
    m = r["matrices"]
    lineas = []
    for etiqueta, rho in (("ρ(T_J) ", m["rho_J"]), ("ρ(T_GS)", m["rho_GS"])):
        if rho is None:
            lineas.append("  {} = no se pudo calcular".format(etiqueta))
        else:
            lineas.append("  {} = {}   →   {}".format(etiqueta, _c(rho), (
                "< 1: converge" if rho < 1 else "≥ 1: no converge con cualquier x(0)")))
    return lineas


def _lineas_forma_matricial(r):
    """Apartado 3: convergencia por ρ(T) y, si se pidió, D, L, U, T y c de cada método."""
    if not r["forma_matricial"]:
        return (["", "--- 3) Convergencia: radio espectral de T (converge si ρ(T) < 1) ---"]
                + _lineas_radios(r))
    m, lam = r["matrices"], r["lam"]
    lineas = ["", "--- 3) Forma matricial A = D + L + U ---", "D (diagonal) ="]
    lineas += _lineas_matriz(m["D"])
    lineas += ["L (parte estrictamente inferior) ="] + _lineas_matriz(m["L"])
    lineas += ["U (parte estrictamente superior) ="] + _lineas_matriz(m["U"])
    lineas += ["", "Forma común:  x(k+1) = T·x(k) + c", "",
               "Jacobi:  T_J = −D⁻¹(L + U),   c_J = D⁻¹·b", "T_J ="]
    lineas += _lineas_matriz(m["TJ"]) + ["c_J ="] + _lineas_columna(m["cJ"])
    if lam == 1:
        lineas += ["", "Gauss-Seidel:  T_GS = −(D + L)⁻¹·U,   c_GS = (D + L)⁻¹·b", "T_GS ="]
    else:
        lineas += ["", "Gauss-Seidel con λ = {}:  T_GS = (D + λL)⁻¹[(1 − λ)D − λU],   "
                       "c_GS = λ(D + λL)⁻¹·b".format(_corto(lam)), "T_GS ="]
    lineas += _lineas_matriz(m["TGS"]) + ["c_GS ="] + _lineas_columna(m["cGS"])
    return (lineas + ["", "Radio espectral ρ(T) = máx |λᵢ|; converge con cualquier x(0) si ρ(T) < 1:"]
            + _lineas_radios(r))


def _termino(a, factor, separador):
    """Término « − a·x» de un despeje (« + |a|·x» si a < 0); vacío si a = 0 y sin el 1 si |a| = 1."""
    if a == 0:
        return ""
    c = abs(a)
    return (" − " if a > 0 else " + ") + (factor if c == 1 else _c(c) + separador + factor)


def _lineas_despeje(r):
    """Apartado 4: despeje de cada incógnita, con una línea por incógnita."""
    A, b, n = r["A"], r["b"], r["n"]
    lineas = ["", "--- 4) Despeje de cada incógnita ---"]
    for i in range(n):
        terminos = "".join(_termino(A[i][j], "x" + subindice(j + 1), "")
                           for j in range(n) if j != i)
        lineas.append("  x{} = ( {}{} ) / {}".format(subindice(i + 1), _c(b[i]), terminos,
                                                    _p(A[i][i])))
    lineas.append("  Jacobi usa solo la iteración anterior; Gauss-Seidel usa de inmediato lo "
                  "recién calculado.")
    if r["lam"] != 1:
        lineas.append("  Relajación: xᵢ(nuevo) = λ·xᵢ(GS) + (1 − λ)·xᵢ(anterior),  λ = {}"
                      .format(_corto(r["lam"])))
    return lineas


def _sustitucion(clave, A, b, anterior, actual, i):
    """Despeje de xᵢ con los valores numéricos que usa el método: devuelve (texto, valor)."""
    suma, terminos = 0.0, ""
    for j in range(len(A)):
        if j == i:
            continue
        xj = actual[j] if (clave == "gauss_seidel" and j < i) else anterior[j]
        suma += A[i][j] * xj
        terminos += _termino(A[i][j], _p(xj), "·")
    return "( {}{} ) / {}".format(_c(b[i]), terminos, _p(A[i][i])), (b[i] - suma) / A[i][i]


def _lineas_error(r, anterior, actual):
    """Líneas del error entre iteraciones dₖ con su sustitución y la comparación con ε."""
    k, n, crit = actual["k"], r["n"], r["criterio"]
    nuevo, viejo = actual["x"], anterior["x"]
    nombre = "d" + subindice(k)
    eps = "εₛ" if crit == "ea_pct" else "ε"
    cierre = "< {}   [Se cumple]".format(eps) if actual["cumple"] else "> {}".format(eps)
    if crit == "ea_pct":
        valores = []
        for a, c in zip(nuevo, viejo):
            if a != 0:
                valores.append(_c(abs((a - c) / a) * 100) + " %")
            else:
                valores.append("0 %" if c == 0 else "no definido")
        lineas = ["  εₐ = |(xᵢ({}) − xᵢ({})) / xᵢ({})|·100 = ( {} )".format(
            k, k - 1, k, ",  ".join(valores))]
        if actual["delta"] is None:
            return lineas + ["  máx εₐ no está definido (algún xᵢ = 0): se sigue iterando"]
        if actual["cumple"]:
            return lineas + ["  máx εₐ = {} % < εₛ = {} %   [Se cumple]".format(
                _c(actual["delta"]), _corto(r["eps"]))]
        return lineas + ["  máx εₐ = {} % {}".format(_c(actual["delta"]), cierre)]
    if crit == "norma_inf":
        cuerpo = ("máx( " + ", ".join("|{} − {}|".format(_c(a), _p(c))
                                      for a, c in zip(nuevo, viejo)) + " )"
                  if n <= 6 else "‖x({}) − x({})‖∞".format(k, k - 1))
    else:
        cuerpo = ("√( " + " + ".join("({} − {})²".format(_c(a), _p(c))
                                     for a, c in zip(nuevo, viejo)) + " )"
                  if n <= 6 else "‖x({}) − x({})‖₂".format(k, k - 1))
    if actual["cumple"]:
        return ["  {} = {} = {}".format(nombre, cuerpo, _fe(actual["delta"])),
                "  {} = {} < ε = {}   [Se cumple]".format(nombre, _fe(actual["delta"]),
                                                         _corto(r["eps"]))]
    return ["  {} = {} = {} {}".format(nombre, cuerpo, _fe(actual["delta"]), cierre)]


def _lineas_iteracion(r, clave, anterior, actual):
    """Paso a paso de una iteración, cada xᵢ con su sustitución y el error d."""
    A, b, n, lam = r["A"], r["b"], r["n"], r["lam"]
    k = actual["k"]
    lineas = ["Iteración {}:   x({}) = {}".format(k, k - 1, _vector(anterior["x"]))]
    for i in range(n):
        base = "x" + subindice(i + 1)
        expresion, valor = _sustitucion(clave, A, b, anterior["x"], actual["x"], i)
        if clave == "gauss_seidel" and lam != 1:
            lineas.append("  {}(GS) = {} = {}".format(base, expresion, _c(valor)))
            lineas.append("  {0}({1}) = {2}·{3} + {4}·{5} = {6}".format(
                base, k, _c(lam), _p(valor), _p(1 - lam), _p(anterior["x"][i]),
                _c(actual["x"][i])))
        else:
            lineas.append("  {}({}) = {} = {}".format(base, k, expresion, _c(actual["x"][i])))
    return lineas + _lineas_error(r, anterior, actual)


def _comprobacion_matricial(r, met):
    """Comprueba que la primera iteración coincide con x(1) = T·x(0) + c; devuelve la línea o None."""
    if len(met["filas"]) < 2:
        return None
    sufijo = "J" if met["clave"] == "jacobi" else "GS"
    esperado = (np.array(r["matrices"]["T" + sufijo]) @ np.array(r["x0"])
                + np.array(r["matrices"]["c" + sufijo]))
    real = np.array(met["filas"][1]["x"])
    if not np.all(np.isfinite(real)):
        return None
    coincide = bool(np.allclose(esperado, real, rtol=1e-9, atol=1e-9))
    return "Comprobación matricial: x(1) = T_{0}·x(0) + c_{0} coincide con la iteración 1   {1}".format(
        sufijo, "[Se cumple]" if coincide else "[No se cumple]")


def _lineas_estado(r, met):
    """Estado final de un método, con las frases que el visor colorea (verde si converge, rojo si no)."""
    ultima = met["filas"][-1]
    d = _fe(ultima["delta"]) if ultima["delta"] is not None else "—"
    eps = _corto(r["eps"])
    if met["motivo"] == "tolerancia":
        return ["  Estado: Tolerancia alcanzada: d = {} < ε = {}.".format(d, eps)]
    if met["motivo"] == "maximo":
        return ["  Estado: Se alcanzó el máximo de {} iteraciones SIN cumplir la tolerancia "
                "(d = {} ≥ ε = {}): el resultado es solo una aproximación.".format(
                    r["nmax"], d, eps)]
    if met["motivo"] == "crece":
        return ["  Atención: el error crece {} iteraciones seguidas y ρ(T) ≥ 1: el método "
                "diverge con estos datos.".format(RACHA_CRECIMIENTO)]
    return ["  Atención: los valores se vuelven no finitos o superan 1e100 en la iteración {}: "
            "el método diverge con estos datos.".format(ultima["k"])]


def _lineas_metodo(r, clave):
    """Bloque de un método: iteraciones detalladas, tabla de iteraciones y resultado final."""
    met = r[clave]
    titulo = nombre_metodo(clave, r["lam"])
    lineas = ["", "=== Método de {} ===".format(titulo), ""]
    detalladas = min(ITERACIONES_DETALLADAS, met["iteraciones"])
    for k in range(1, detalladas + 1):
        lineas += _lineas_iteracion(r, clave, met["filas"][k - 1], met["filas"][k]) + [""]
    if met["iteraciones"] > detalladas:
        lineas += ["Las iteraciones {} a {} se calculan igual y están en la tabla.".format(
            detalladas + 1, met["iteraciones"]), ""]
    if r["forma_matricial"]:
        comprobacion = _comprobacion_matricial(r, met)
        if comprobacion:
            lineas += [comprobacion, ""]
    lineas += ["--- Tabla de iteraciones ---", ""] + _tabla_de_iteraciones(met, r) + [""]
    lineas.append("Resultado final de {}:".format(titulo))
    solucion = (_vector(met["x"]) if all(math.isfinite(v) for v in met["x"])
                else "valores no finitos")
    lineas.append("  x ≈ {}    Iteraciones: {}    Residuo ‖A·x − b‖∞ = {}".format(
        solucion, met["iteraciones"], _fe(met["residuo_final"])))
    return lineas + _lineas_estado(r, met)


_ESTADO_TABLA = {"tolerancia": "Convergencia alcanzada", "maximo": "Máximo de iteraciones",
                 "diverge": "Diverge", "crece": "El error crece"}


def _lineas_comparacion(r):
    """Bloque final: comparación de iteraciones y soluciones, y validación con la solución de referencia."""
    jac, gs, cmp_ = r["jacobi"], r["gauss_seidel"], r["comparacion"]
    lineas = ["", "=== Comparación y validación ===", "", "--- Comparación de resultados ---", ""]
    filas = [[nombre_metodo(met["clave"], r["lam"]), str(met["iteraciones"]),
              _fe(met["delta_final"]), _fe(met["residuo_final"]), _ESTADO_TABLA[met["motivo"]]]
             for met in (jac, gs)]
    lineas += tabla_texto(["Método", "Iteraciones", "Error final", "Residuo ‖A·x − b‖∞", "Estado"],
                          filas)
    lineas.append("")
    if cmp_["ambos"]:
        mejor = cmp_["mas_rapido"]
        if mejor == "igual":
            lineas.append("Ambos métodos necesitaron {} iteraciones.".format(jac["iteraciones"]))
        else:
            rapido, lento = (gs, jac) if mejor == "gauss_seidel" else (jac, gs)
            lineas.append("{} necesitó menos iteraciones ({} frente a {}).".format(
                nombre_metodo(rapido["clave"], r["lam"]), rapido["iteraciones"],
                lento["iteraciones"]))
    elif cmp_["mas_rapido"] is not None:
        solo = jac if cmp_["mas_rapido"] == "jacobi" else gs
        lineas.append("Solo {} alcanzó la tolerancia.".format(nombre_metodo(solo["clave"], r["lam"])))
    else:
        lineas.append("Atención: ningún método alcanzó la tolerancia con estos datos.")
    if cmp_["dif_soluciones"] is not None:
        lineas.append("Diferencia entre las soluciones: ‖x_J − x_GS‖∞ = {}".format(
            _fe(cmp_["dif_soluciones"])))
    lineas += ["", "--- Validación con la solución de referencia ---"]
    if r["x_ref"] is None:
        lineas.append("  No hay solución de referencia: A es singular.")
    else:
        lineas.append("  numpy.linalg.solve(A, b):  x* = {}   (solo comprueba; no sustituye a los "
                      "métodos)".format(_vector(r["x_ref"])))
        if cmp_["validacion"]:
            filas = [[nombre_metodo(c, r["lam"]), _fe(v["dif_inf"]), _fe(v["dif_2"]),
                      _fe(v["residuo"])] for c, v in cmp_["validacion"].items()]
            lineas.append("")
            lineas += tabla_texto(["Método", "‖x − x*‖∞", "‖x − x*‖₂", "Residuo ‖A·x − b‖∞"],
                                  filas, "  ")
        else:
            lineas.append("  Ningún método convergió: no se compara con x*.")
    for aviso in r["advertencias"]:
        lineas += ["", "[INFO] " + aviso]
    return lineas


def informe(r):
    """Informe completo de texto: validaciones, diagnóstico, despeje, cada método y comparación."""
    if r["A"] is None:
        return ""
    lineas = ["=== Métodos iterativos: Jacobi y Gauss-Seidel ===", "",
              "Sistema A·x = b   (matriz aumentada [A | b])"]
    lineas += _lineas_matriz(r["A"], [_c(v) for v in r["b"]])
    lineas += ["", "x(0) = {}    ε = {}    Iteraciones máximas: {}".format(
        _vector(r["x0"]), _corto(r["eps"]), r["nmax"]),
        "Criterio de parada:  {}".format(CRITERIOS[r["criterio"]])]
    if r["lam"] != 1:
        lineas.append("Relajación en Gauss-Seidel: λ = {}".format(_corto(r["lam"])))
    lineas.append("")
    lineas += _lineas_validaciones(r)
    lineas += _lineas_diagonal(r)
    if r["matrices"] is None:
        lineas += ["", "No se pudo iniciar el cálculo: " + r["mensaje"]]
        return "\n".join(lineas)
    lineas += _lineas_forma_matricial(r)
    lineas += _lineas_despeje(r)
    lineas += _lineas_metodo(r, "jacobi")
    lineas += _lineas_metodo(r, "gauss_seidel")
    lineas += _lineas_comparacion(r)
    return "\n".join(lineas)


def preparar_grafica_error(r):
    """
    Datos de la gráfica del error contra la iteración para ambos métodos.
    Devuelve {valido, mensaje, curvas, xmin, xmax, tolerancia, ...} o valido False si falta alguno.
    """
    salida = {"valido": False, "mensaje": "", "curvas": []}
    if not r.get("valido"):
        salida["mensaje"] = "Calcula primero los dos métodos."
        return salida
    for clave in ("jacobi", "gauss_seidel"):
        met = r[clave]
        puntos = [(f["k"], f["delta"]) for f in met["filas"][1:]
                  if f["delta"] is not None and math.isfinite(f["delta"]) and f["delta"] > 0]
        if not puntos:
            salida["mensaje"] = ("No hay datos válidos del error de {} para graficar (el error es "
                                 "cero o no es finito).".format(met["nombre"]))
            salida["curvas"] = []
            return salida
        salida["curvas"].append({
            "etiqueta": nombre_metodo(clave, r["lam"]),
            "xs": np.array([p[0] for p in puntos], dtype=float),
            "ys": np.array([p[1] for p in puntos], dtype=float)})
    mayor = max(int(c["xs"][-1]) for c in salida["curvas"])
    salida.update(valido=True, xmin=0.5, xmax=mayor + 0.5, tolerancia=r["eps"],
                  titulo="Error por iteración: Jacobi frente a Gauss-Seidel",
                  etiqueta_y=_COLUMNA_ERROR[r["criterio"]],
                  resumen="Error ({}) en cada iteración, escala logarítmica. La línea punteada es "
                          "la tolerancia ε = {}.".format(_COLUMNA_ERROR[r["criterio"]], _corto(r["eps"])))
    return salida
