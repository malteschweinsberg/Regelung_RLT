import json
import time
from pi_regler import PIRegler
from visualisation import Visualisierung

with open("config.json") as f:
    config = json.load(f)

# Simulationseinstellungen
t_sp = config["simulation"]["t_sp"]             #Geschwindigkeit der Simulation (z. B. 60-fach schneller als Echtzeit)
dt = 1 / t_sp                                   #Reale Zeit pro Simulationsschritt
T_AUL = config["simulation"]["T_AUL"]           #Außenlufttemperatur
T_SOL_R = config["simulation"]["T_SOL_R"]       #Ziel-Raumtemperatur
V_R = config["raum"]["V_R"]                     #Aktuelle Raumtemperatur
T_R = config["raum"]["T_R_init"]                #Raumvolumen (könnte für Wärmekapazität wichtig sein)

# Initialwerte
T_ZUL = T_WRG = T_ERH = T_KUL = T_AUL
T_ABL = T_R  # Abluft = Raumtemperatur

# WRG Logik
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or (T_ABL > T_SOL_R and T_AUL > T_ABL))

# Regler
regler_T_ZUL = PIRegler(3, 15*60, dt)
regler_ERH = PIRegler(25, 2*60, dt)
regler_KUL = PIRegler(12, 2*60, dt)

vis = Visualisierung()

for t in range(0, 60):  # 1 Stunde simulieren
    # WRG aktiv?
    wrg_on = berechne_WRG(T_AUL, T_ABL, T_SOL_R)
    if wrg_on:
        n_WRG = config["waermetauscher"]["n_WRG"]
        if T_AUL < T_ABL:
            T_WRG = T_AUL + n_WRG * (T_ABL - T_AUL)
        else:
            T_WRG = T_AUL - n_WRG * (T_AUL - T_ABL)
    else:
        T_WRG = T_AUL

    # Regelung T_ZUL
    T_SOL_ZUL = regler_T_ZUL.update(T_SOL_R, T_R)
    dTZUL = T_SOL_ZUL - T_WRG

    # Heizen oder Kühlen
    if dTZUL > 0:
        m_ERH = regler_ERH.update(T_SOL_ZUL, T_WRG)
        params = config["erhitzer"]
        #T_ERH = T_WRG + (params["A_ERH"] * params["k_ERH"] * (params["T_O_ERH"] - T_WRG)) / (m_ERH * params["c_ERH"] + 1e-6)
        #T_ERH = -1 * m_ERH * params["c_ERH"] * params["T_DIF_ERH"] / (params["A_ERH"] * params["k_ERH"]) + params["T_O_ERH"]
        #T_ERH = (params["k_ERH"] * params["A_ERH"] * params["T_O_ERH"] + (m_ERH * params["c_ERH"] - (params["k_ERH"] * params["A_ERH"]) / 2) * T_WRG) / (m_ERH * params["c_ERH"] + params["k_ERH"] * params["A_ERH"] * 2)
        T_ERH = T_WRG + (m_ERH * params["c_WAS"] * params["T_DIF_ERH"]) / (params["c_LUF"] * params["c_LUF"])
        T_ZUL = T_ERH
        m_KUL = 0
        print('T_WRG:', T_WRG, 'T_ERH:', T_ERH)
    else:
        m_KUL = regler_KUL.update(T_SOL_ZUL, T_WRG)
        params = config["kuehler"]
        T_KUL = T_WRG + (params["A_KUL"] * params["k_KUL"] * (params["T_O_KUL"] - T_WRG)) / (m_KUL * params["c_KUL"] + 1e-6)
        T_ZUL = T_KUL
        m_ERH = 0

    # Raumtemperatur aktualisieren
    dT_R = (T_ZUL - T_R) * 0.1  # einfache Wärmezufuhrformel
    T_R += dT_R

    vis.add_data(t, T_SOL_R, T_R, m_ERH, m_KUL, wrg_on)
    time.sleep(dt)

vis.plot()
