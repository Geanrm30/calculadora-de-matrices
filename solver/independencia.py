# -*- coding: utf-8 -*-
"""
Analiza dependencia e independencia lineal de vectores resolviendo el sistema
homogéneo A·c = 0 con los vectores como columnas de A; incluye criterios
por inspección.
Unidad: Proyecto Integrador (Sesiones 1-11).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

from core.fraccion import Fraccion, mcd
from core.formato import subindice, texto_coeficiente


def sistema_homogeneo(vectores):
    """Devuelve la matriz aumentada [v1 ... vk | 0] del sistema c1·v1 + ... + ck·vk = 0.
    Cada vector ocupa una columna; los términos independientes son ceros.
    """
    from core.vector import matriz_de_vectores

    A = matriz_de_vectores(vectores)
    return [fila + [Fraccion(0)] for fila in A]


def nombre_vector(indice):
    """Nombre del vector en base 1: 0 -> v con subindice 1."""
    return "v" + subindice(indice + 1)


def _es_vector_cero(v):
    """Indica si todas las componentes del vector son cero."""
    for componente in v:
        if not componente.es_cero():
            return False
    return True


def _multiplo(u, v):
    """Si v = k·u para algún escalar k, devuelve k; si no, None.
    El factor se busca en la primera componente no nula de u y se comprueba en las demás.
    """
    factor = None
    for i in range(len(u)):
        if u[i].es_cero():
            if not v[i].es_cero():
                return None
            continue
        candidato = v[i] / u[i]
        if factor is None:
            factor = candidato
        elif not (factor == candidato):
            return None
    return factor


def criterios_por_inspeccion(vectores):
    """Aplica los criterios que deciden sin eliminar (k > n, vector cero, un vector, múltiplo).
    Devuelve una lista de dicts con 'texto' y 'conclusion' (dependiente, independiente o None).
    """
    hallazgos = []
    k = len(vectores)
    n = len(vectores[0]) if vectores else 0

    if k > n:
        hallazgos.append({
            "conclusion": "dependiente",
            "texto": ("El conjunto tiene {} vectores en R^{}: son mas vectores que "
                      "componentes (k > n), asi que es linealmente dependiente.".format(k, n)),
        })

    for indice in range(k):
        if _es_vector_cero(vectores[indice]):
            hallazgos.append({
                "conclusion": "dependiente",
                "texto": ("{} es el vector cero. Todo conjunto que contiene al vector "
                          "cero es linealmente dependiente.".format(nombre_vector(indice))),
            })
            break

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


def _mcm(a, b):
    """Minimo comun multiplo, calculado con el maximo comun divisor."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // mcd(a, b)


def relacion_de_dependencia(expresiones, libres, n_vars):
    """Construye una relación de dependencia concreta desde la solución general del sistema homogéneo.
    Da a una variable libre el mcm de los denominadores y a las demás libres el valor cero.
    """
    if not libres:
        return None

    indice_libre = libres[0]
    columna = 1

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
    """Análisis completo de un conjunto de vectores resolviendo siempre A·c = 0.
    Devuelve un dict con 'independiente', 'libres', 'relacion', 'criterios' y 'resultado'.
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
    """Escribe la combinación con sus escalares, por ejemplo 10·v1 - 5·v2 + 5·v3 = 0.
    Omite los términos con escalar cero, salvo que todos lo sean.
    """
    partes = []
    for k in range(len(escalares)):
        c = escalares[k]
        if c.es_cero():
            continue

        magnitud = -c if c.es_negativo() else c
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
