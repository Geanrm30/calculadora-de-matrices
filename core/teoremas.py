# -*- coding: utf-8 -*-
"""
Catálogo de teoremas del Proyecto Integrador: Calculadora de Álgebra Lineal.
Contiene los teoremas de las Sesiones 1-11: sistemas lineales, independencia,
matrices, determinante e inversa. Cada entrada es (nombre, enunciado, dónde_se_usa).
MTM0120 Álgebra Lineal — Universidad Americana.
Elaborado por: Anthony Sying González Chow, Jose Maria Moncada Maya,
               Geanfranco Alexander Rodriguez Mendieta
"""

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
        "Sean A, B y C matrices del mismo tamano, y sean r y s escalares:\n"
        "   1. A + B = B + A\n"
        "   2. (A + B) + C = A + (B + C)\n"
        "   3. A + 0 = A\n"
        "   4. r(A + B) = r·A + r·B\n"
        "   5. (r + s)A = r·A + s·A\n"
        "   6. r(s·A) = (r·s)·A\n"
        "   Nota: A + (-A) = 0  (opuesto de A)",
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
        "Sea A una matriz de m×n, y sean B y C matrices de tamanos compatibles:\n"
        "   1. A·(B·C) = (A·B)·C            (ley asociativa)\n"
        "   2. A·(B + C) = A·B + A·C        (distributiva izquierda)\n"
        "   3. (B + C)·A = B·A + C·A        (distributiva derecha)\n"
        "   4. r·(A·B) = (r·A)·B = A·(r·B)  (escalar)\n"
        "   5. I_n·A = A = A·I_n            (identidad, neutro del producto)\n"
        "   Advertencia: en general A·B != B·A (no conmutativo).",
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

    # ── Sesion 10: Matriz inversa ──────────────────────────────────────
    (
        "Propiedades de la inversa",
        "Si A y B son matrices invertibles de orden n:\n"
        "   a. (A⁻¹)⁻¹ = A\n"
        "   b. (A·B)⁻¹ = B⁻¹·A⁻¹   (el orden se invierte)\n"
        "   c. (Aᵀ)⁻¹ = (A⁻¹)ᵀ     (transpuesta e inversa conmutan)",
        "Operaciones con matrices: 'Propiedades' (categoría Inversa).",
    ),
    (
        "Teorema de la matriz invertible (criterios equivalentes)",
        "Sea A una matriz n×n. Las siguientes afirmaciones son equivalentes:\n"
        "   c. A tiene n posiciones de pivote.\n"
        "   e. Las columnas de A son linealmente independientes.\n"
        "   h. Las columnas de A generan R^n.\n"
        "   (Equivalencia completa: ver libro Lay, sección 2.3)",
        "Solucionador: clasificación del sistema (rango, pivotes, independencia).",
    ),
    (
        "Inversa por Gauss-Jordan",
        "Para encontrar A⁻¹, se construye la matriz aumentada [A | I_n] y se\n"
        "aplica eliminación de Gauss-Jordan hasta obtener [I_n | A⁻¹].\n"
        "Si A es singular (det = 0), la parte izquierda no puede reducirse a I\n"
        "y la inversa no existe.",
        "Operaciones con matrices: botón 'A⁻¹  G-J'.",
    ),
    (
        "Inversa por la fórmula de la adjunta",
        "Si det(A) ≠ 0, la inversa puede calcularse con:\n"
        "   A⁻¹ = (1/det(A)) · adj(A)\n"
        "donde adj(A) es la transpuesta de la matriz de cofactores de A.\n"
        "El cofactor C_{ij} = (-1)^(i+j) · det(A_{ij}), siendo A_{ij} la\n"
        "submatriz resultante de eliminar la fila i y la columna j.",
        "Operaciones con matrices: botón 'A⁻¹  Adj'.",
    ),

    # ── Sesion 11: Determinante ────────────────────────────────────────
    (
        "Determinante de una matriz triangular",
        "Si A es triangular superior, inferior o diagonal, entonces:\n"
        "   det(A) = a_{11} · a_{22} · ... · a_{nn}\n"
        "(producto de las entradas de la diagonal principal).",
        "Operaciones con matrices: botón 'det(A)'.",
    ),
    (
        "Efecto de las operaciones de fila sobre el determinante",
        "   Intercambio: intercambiar dos filas multiplica det por -1.\n"
        "   Reemplazo: sumar k·(fila_i) a otra fila NO cambia el det.\n"
        "   Escalado: multiplicar una fila por k multiplica det por k.",
        "Operaciones con matrices: 'det(A)' (la reducción triangular aplica estos pasos).",
    ),
    (
        "Propiedades del determinante",
        "   det(Aᵀ) = det(A)\n"
        "   det(A·B) = det(A) · det(B)\n"
        "   A es invertible  ⟺  det(A) ≠ 0\n"
        "   Si A es invertible: det(A⁻¹) = 1/det(A)",
        "Operaciones con matrices: 'Propiedades' (categoría Determinante).",
    ),
]
