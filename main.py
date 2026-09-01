# -*- coding: utf-8 -*-
# =============================================================================
#  Punto de entrada principal.
#
#      python main.py
#
#  Lanza la interfaz grafica del solucionador de sistemas de ecuaciones
#  lineales.
# =============================================================================

import sys
import os

# Garantiza que el directorio raiz del proyecto este en sys.path para que
# los paquetes core/, solver/, output/ y ui/ sean importables sin importar
# desde que directorio se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import main

if __name__ == "__main__":
    main()
