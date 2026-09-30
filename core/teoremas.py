# -*- coding: utf-8 -*-
# =============================================================================
#  MODULO: core/teoremas.py
#  Catalogo de los teoremas y criterios que usa el programa.
#
#  Cada entrada es (nombre, enunciado, donde_se_usa). La ventana
#  ui/app_teoremas.py solo se encarga de mostrarlos.
# =============================================================================

TEOREMAS = [
    (
        "Equivalencia de las tres formas de un sistema",
        "La ecuacion matricial A·x = b, la ecuacion vectorial "
        "x1·a1 + x2·a2 + ... + xn·an = b (a1..an son las columnas de A) y el "
        "sistema con matriz aumentada [a1 a2 ... an | b] tienen exactamente "
        "el mismo conjunto solucion.",
        "Solucionador: seccion 'Ecuacion matricial A·x = b' del informe.",
    ),
    (
        "Combinacion lineal",
        "b es combinacion lineal de los vectores v1, ..., vk si y solo si el "
        "sistema [v1 ... vk | b] es consistente. Los escalares de la "
        "combinacion son la solucion del sistema.",
        "Operaciones con matrices: 'Enviar al solucionador' (combinacion).",
    ),
    (
        "Operaciones elementales por filas",
        "Si una matriz aumentada se transforma con operaciones elementales "
        "(intercambiar dos filas, multiplicar una fila por un escalar no nulo, "
        "sumar a una fila un multiplo de otra), el sistema resultante es "
        "equivalente: tiene las mismas soluciones.",
        "Solucionador: eliminacion de Gauss y Gauss-Jordan, paso a paso.",
    ),
    (
        "Rouche-Frobenius (clasificacion de sistemas)",
        "Sea n el numero de variables.\n"
        "   rango(A) < rango([A|b])        ->  inconsistente (sin solucion).\n"
        "   rango(A) = rango([A|b]) = n    ->  consistente determinado "
        "(solucion unica).\n"
        "   rango(A) = rango([A|b]) < n    ->  consistente indeterminado "
        "(infinitas soluciones, n - rango variables libres).",
        "Solucionador: clasificacion del sistema.",
    ),
    (
        "Unicidad de la forma escalonada reducida",
        "Cada matriz es equivalente por filas a una unica matriz escalonada "
        "reducida. Las posiciones de los pivotes quedan determinadas aunque "
        "la forma escalonada (no reducida) pueda variar.",
        "Solucionador: Gauss-Jordan.",
    ),
    (
        "Propiedades del producto matriz-vector",
        "Si A es una matriz m x n, u, v estan en R^n y r es un escalar:\n"
        "   A(u + v) = A·u + A·v\n"
        "   A(r·u)   = r·(A·u)",
        "Operaciones con matrices: 'Propiedades de A·x'.",
    ),
    (
        "Propiedades algebraicas de los vectores en Rn",
        "Para u, v en R^n y escalares r:\n"
        "   u + v = v + u\n"
        "   r(u + v) = r·u + r·v",
        "Operaciones con matrices: 'Propiedades' (seleccion o 'Verificar todas').",
    ),
    (
        "Propiedades de la suma y el escalar de matrices",
        "Para A, B del mismo tamano y un escalar r:\n"
        "   A + B = B + A\n"
        "   r(A + B) = r·A + r·B\n"
        "   A + (-A) = 0",
        "Operaciones con matrices: 'Propiedades'.",
    ),
    (
        "Propiedades de la transpuesta",
        "   (A^T)^T = A\n"
        "   (A + B)^T = A^T + B^T\n"
        "   (r·A)^T = r·A^T\n"
        "   (A·B)^T = B^T·A^T   (el orden de los factores se invierte)",
        "Operaciones con matrices: 'Propiedades'.",
    ),
    (
        "Propiedades del producto de matrices",
        "   A·I = A = I·A   (la identidad es el neutro)\n"
        "   En general A·B != B·A: el producto NO es conmutativo.",
        "Operaciones con matrices: 'Propiedades'.",
    ),
    (
        "Dependencia e independencia lineal",
        "v1, ..., vk son linealmente independientes si y solo si la ecuacion "
        "c1·v1 + ... + ck·vk = 0 tiene solo la solucion trivial. Equivale a "
        "que el sistema homogeneo A·c = 0 (vectores como columnas) tenga "
        "solucion unica, es decir, que toda columna de A sea pivote.",
        "Solucionador: contexto 'independencia'.",
    ),
    (
        "Criterios por inspeccion de independencia",
        "1. Si k > n (mas vectores que componentes) en R^n, el conjunto es "
        "dependiente.\n"
        "2. Si el conjunto contiene al vector cero, es dependiente.\n"
        "3. Un conjunto de un solo vector es independiente si y solo si ese "
        "vector no es el vector cero.",
        "Solucionador: seccion de criterios de independencia.",
    ),
    (
        "Sistema homogeneo",
        "A·x = 0 siempre es consistente (x = 0 es la solucion trivial). Tiene "
        "soluciones no triviales si y solo si hay al menos una variable libre.",
        "Solucionador: independencia lineal.",
    ),
]
