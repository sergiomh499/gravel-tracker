#!/usr/bin/env python3
"""
gravel_tracker.py - Punto de Entrada Ejecutable Unificado para Gravel Tracker.
Delega directamente en el despachador centralizado gravel_bot.cli.main().
"""

import sys
from gravel_bot.cli import main

if __name__ == "__main__":
    main()
