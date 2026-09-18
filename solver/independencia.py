# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: solver/independencia.py
#  Dependencia e independencia lineal de un conjunto de vectores.
#
#  Definicion: v1, v2, ..., vk son linealmente DEPENDIENTES si existen
#  escalares c1, ..., ck NO TODOS CERO tales que
#
#        c1.v1 + c2.v2 + ... + ck.vk = 0
#
#  Si la unica manera de obtener el vector cero es con todos los escalares
#  iguales a cero (solucion trivial), el conjunto es INDEPENDIENTE.
#
#  Esa ecuacion es el sistema homogeneo A.c = 0 con los vk como columnas de
#  A, de modo que la respuesta sale de la misma eliminacion de Gauss que usa
#  el resto del programa:
#
#        solucion unica (la trivial)  ->  linealmente independiente
#        infinitas soluciones         ->  linealmente dependiente
#
#  Ademas de resolver, este modulo aplica los criterios que permiten
#  responder POR INSPECCION en algunos casos, y construye una relacion de
#  dependencia explicita cuando el conjunto resulta dependiente.
# =============================================================================

from core.fraccion import Fraccion, mcd
from core.formato import subindice, texto_coeficiente


# ---------------------------------------------------------------------------
# Construccion del sistema homogeneo
# ---------------------------------------------------------------------------

def sistema_homogeneo(vectores):
    """
    Devuelve la matriz aumentada [v1 v2 ... vk | 0] del sistema
    c1.v1 + ... + ck.vk = 0.

    Cada vector ocupa una COLUMNA y la columna de terminos independientes es
    de ceros, porque la combinacion debe dar el vector nulo.
    """
    from core.vector import matriz_de_vectores

    A = matriz_de_vectores(vectores)
    return [fila + [Fraccion(0)] for fila in A]


def nombre_vector(indice):
    """Nombre del vector en base 1: 0 -> v con subindice 1."""
    return "v" + subindice(indice + 1)


# ---------------------------------------------------------------------------
# Criterios por inspeccion
# ---------------------------------------------------------------------------

def _es_vector_cero(v):
    """Indica si todas las componentes del vector son cero."""
    for componente in v:
        if not componente.es_cero():
            return False
    return True


def _multiplo(u, v):
    """
    Si v = k.u para algun escalar k, devuelve k; si no, devuelve None.

    Se busca el factor en la primera componente no nula de u y luego se
    comprueba que ese mismo factor sirva para todas las demas.
    """
    factor = None
    for i in range(len(u)):
        if u[i].es_cero():
            if not v[i].es_cero():
                return None      # u tiene 0 donde v no: ningun factor sirve
            continue
        candidato = v[i] / u[i]
        if factor is None:
            factor = candidato
        elif not (factor == candidato):
            return None
    return factor


def criterios_por_inspeccion(vectores):
    """
    Aplica los criterios que resuelven el problema sin eliminar.

    Devuelve una lista de diccionarios con:
        "texto"      : explicacion del criterio
        "conclusion" : "dependiente", "independiente" o None si no decide

    Criterios aplicados:
      1. Un conjunto con mas vectores que componentes (k > n) es dependiente.
      2. Un conjunto que contiene al vector cero es dependiente.
      3. Un conjunto de un solo vector es independiente si el vector no es cero.
      4. Un conjunto de dos vectores es dependiente si uno es multiplo del otro.
    """
    hallazgos = []
    k = len(vectores)
    n = len(vectores[0]) if vectores else 0

    # 1. Mas vectores que entradas en cada vector
    if k > n:
        hallazgos.append({
            "conclusion": "dependiente",
            "texto": ("El conjunto tiene {} vectores en R^{}: son mas vectores que "
                      "componentes (k > n), asi que es linealmente dependiente.".format(k, n)),
        })

    # 2. Presencia del vector cero
    for indice in range(k):
        if _es_vector_cero(vectores[indice]):
            hallazgos.append({
                "conclusion": "dependiente",
                "texto": ("{} es el vector cero. Todo conjunto que contiene al vector "
                          "cero es linealmente dependiente.".format(nombre_vector(indice))),
            })
            break

    # 3. Conjunto de un solo vector
    if k == 1:
        if _es_vector_cero(vectores[0]):
            hallazgos.append({
                "conclusion": "dependiente",
                "texto": "El unico vector del conjunto es el vector cero.",
            })
        else:
            hallazgos.append({
                "conclusion": "independiente",
                "texto": ("Un conjunto de un solo vector es linealmente independiente "
                          "siempre que ese vector no sea el vector cero."),
            })

    # 4. Conjunto de dos vectores: uno multiplo del otro
    if k == 2:
        factor = _multiplo(vectores[0], vectores[1])
        if factor is not None:
            hallazgos.append({
                "conclusion": "dependiente",
                "texto": ("{v2} es multiplo de {v1}: {v2} = {f}·{v1}, de donde "
                          "-{f}·{v1} + {v2} = 0 con escalares no todos cero.".format(
                              v1=nombre_vector(0), v2=nombre_vector(1), f=factor)),
            })
        else:
            factor = _multiplo(vectores[1], vectores[0])
            if factor is not None:
                hallazgos.append({
                    "conclusion": "dependiente",
                    "texto": ("{v1} es multiplo de {v2}: {v1} = {f}·{v2}.".format(
                        v1=nombre_vector(0), v2=nombre_vector(1), f=factor)),
                })
            else:
                hallazgos.append({
                    "conclusion": "independiente",
                    "texto": ("Ninguno de los dos vectores es multiplo del otro, "
                              "por lo tanto el conjunto es linealmente independiente."),
                })

    return hallazgos


# ---------------------------------------------------------------------------
# Relacion de dependencia explicita
# ---------------------------------------------------------------------------

def _mcm(a, b):
    """Minimo comun multiplo, calculado con el maximo comun divisor."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // mcd(a, b)


def relacion_de_dependencia(expresiones, libres, n_vars):
    """
    Construye una relacion de dependencia concreta a partir de la solucion
    general del sistema homogeneo.

    Se da valor a UNA variable libre (las demas quedan en cero) y con eso se
    obtiene un juego de escalares no todos cero. El valor elegido es el
    minimo comun multiplo de los denominadores que aparecen, para que los
    escalares salgan enteros siempre que sea posible.

    Devuelve (escalares, indice_libre, valor_asignado) o None si no hay
    variables libres (el conjunto seria independiente).
    """
    if not libres:
        return None

    indice_libre = libres[0]      # posicion de la variable libre en el sistema
    columna = 1                   # columna 0 = termino independiente

    # Denominador comun de los coeficientes que acompanan a esa variable
    comun = 1
    for j in range(n_vars):
        coeficiente = expresiones[j][columna]
        comun = _mcm(comun, coeficiente.den)

    valor = Fraccion(comun)

    escalares = []
    for j in range(n_vars):
        # Las demas variables libres valen cero, asi que solo interviene el
        # coeficiente de la variable libre elegida. El termino independiente
        # (columna 0) se descarta a proposito: pertenece a la solucion
        # particular y no forma parte de las soluciones de A.x = 0, que son
        # las unicas que dan una relacion de dependencia. En un sistema
        # homogeneo ese termino ya vale cero.
        escalares.append(expresiones[j][columna] * valor)

    return escalares, indice_libre, valor


def analizar(vectores):
    """
    Analisis completo de un conjunto de vectores.

    Resuelve SIEMPRE el sistema homogeneo A.c = 0 propio del conjunto, sin
    importar de que sistema venga la pregunta: la independencia lineal
    depende solo de los vectores, nunca del termino independiente b.

    Devuelve un diccionario con:
        "independiente" : True si la unica solucion es la trivial
        "libres"        : indices de las variables libres
        "relacion"      : (escalares, indice_libre, valor) o None
        "criterios"     : hallazgos por inspeccion
    """
    from solver.resolutor import resolver

    k = len(vectores)
    resultado = resolver(sistema_homogeneo(vectores), k, aplicar_jordan=False)

    libres = resultado["libres"]
    independiente = not libres

    relacion = None
    if not independiente:
        relacion = relacion_de_dependencia(resultado["expresiones"], libres, k)

    return {
        "independiente": independiente,
        "libres": libres,
        "relacion": relacion,
        "criterios": criterios_por_inspeccion(vectores),
        "resultado": resultado,
    }


def texto_relacion(escalares, nombre=nombre_vector, igual_a="0"):
    """
    Escribe la combinacion con sus escalares:

        10·v1 - 5·v2 + 5·v3 = 0

    Los terminos con escalar cero se omiten, salvo que todos lo sean.
    """
    partes = []
    for k in range(len(escalares)):
        c = escalares[k]
        if c.es_cero():
            continue

        magnitud = -c if c.es_negativo() else c
        # El coeficiente 1 se omite: se escribe v₂, no 1·v₂.
        factor = texto_coeficiente(magnitud)
        cuerpo = (factor + "·" + nombre(k)) if factor else nombre(k)

        if not partes:
            partes.append(("-" if c.es_negativo() else "") + cuerpo)
        else:
            partes.append((" - " if c.es_negativo() else " + ") + cuerpo)

    if not partes:
        return "0 = " + igual_a

    return "".join(partes) + " = " + igual_a


def comprobar_relacion(vectores, escalares):
    """
    Sustituye los escalares en la combinacion y devuelve el vector obtenido,
    que debe ser el vector cero. Sirve como verificacion del resultado.
    """
    from core.vector import combinacion_con_escalares

    return combinacion_con_escalares(vectores, escalares)
