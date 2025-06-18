import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from psychrolib import GetHumRatioFromRelHum, GetSatHumRatio, SetUnitSystem, SI

# Psychrolib auf SI-Einheiten setzen
SetUnitSystem(SI)

# Standardatmosphärendruck
P_ATM = 101325  # Pa


def calculate_entfeuchtung(temp_vor, x_ziel):
    """
    Berechne absolute Feuchte vorher und Zieltemperatur bei gegebener Ziel-Feuchte (100% rel).
    :param temp_vor: Temperatur vor Entfeuchtung [°C]
    :param x_ziel: Ziel-Feuchte [g/kg]
    :return: Tuple (w_vor, temp_ziel)
    """
    def func(t):
        return GetSatHumRatio(t, P_ATM) * 1000 - x_ziel

    temp_ziel = fsolve(func, temp_vor - 10)[0]
    return temp_ziel


