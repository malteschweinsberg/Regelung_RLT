import json
import time
from pi_regler import PIRegler
from visualisation import Visualisierung

with open("config.json") as f:
    config = json.load(f)

# Simulationseinstellungen
t_sp = config["simulation"]["t_sp"]             # Geschwindigkeit der Simulation
dt = 0.1 / t_sp                                 # Reale Zeit pro Simulationsschritt
T_AUL = config["simulation"]["T_AUL"]           # Außenlufttemperatur
T_SOL_R = config["simulation"]["T_SOL_R"]       # Ziel-Raumtemperatur
V_R = config["raum"]["V_R"]                     # Raumvolumen
T_R = config["raum"]["T_R_init"]                # Anfangs-Raumtemperatur
p_LUF = config["simulation"]["p_LUF"]
m_LUF = config["erhitzer"]["m_LUF"]
# Initialwerte
T_ZUL = T_WRG = T_ERH = T_KUL = T_AUL
T_ABL = T_R  # Abluft = Raumtemperatur

# Totzeit und Totzone Parameter
TOTZEIT_SCHRITTE = 5      # z.B. 5 Simulationsschritte Verzögerung
TOTZONE = 0.05           # z.B. 5% Totzone (anpassen je nach Reglerausgabe)

# Puffer für Totzeit (FIFO-Listen)
m_ERH_puffer = [0.0] * TOTZEIT_SCHRITTE
m_KUL_puffer = [0.0] * TOTZEIT_SCHRITTE

# WRG Logik
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or (T_ABL > T_SOL_R and T_AUL > T_ABL))

# Berechnen der Wärmekapazität
rho = 1.2  # kg/m³
c_LUF = 1005  # Ws/(kg·K)
V_R = config["raum"]["V_R"]
C_Raum = rho * V_R * c_LUF  # Ws/K
Q_IN = config["raum"]["Q_IN"]  # W

# Regler
regler_T_ZUL = PIRegler(0.5, 0.1, dt)
regler_ERH = PIRegler(0.5, 0.05, dt, 0 )
regler_KUL = PIRegler(0.5, 0.05, dt, 0 )

vis = Visualisierung()

for t in range(0, 3600):  # 1 Stunde simulieren
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
    print(t, 'Temp. nach WRG:', T_WRG, 'Temp. ABL:', T_ABL, 'Temp. AUL:', T_AUL)
    # Regelung T_ZUL

    T_SOL_ZUL =  regler_T_ZUL.update(T_SOL_R, T_R)
    dTZUL = T_SOL_ZUL - T_WRG

    # Heizen oder Kühlen mit Totzeit und Totzone
    if dTZUL > 0:
        m_ERH_roh = regler_ERH.update(T_SOL_ZUL, T_ZUL)
        # Totzone anwenden
        if abs(m_ERH_roh) < TOTZONE:
            m_ERH_roh = 0.0
        # Totzeit-Puffer aktualisieren
        m_ERH_puffer.append(m_ERH_roh)
        m_ERH = m_ERH_puffer.pop(0)
        m_KUL = 0
    elif dTZUL < 0:
        m_KUL_roh = regler_KUL.update(T_ZUL, T_SOL_ZUL)
        # Totzone anwenden
        if abs(m_KUL_roh) < TOTZONE:
            m_KUL_roh = 0.0
        # Totzeit-Puffer aktualisieren
        m_KUL_puffer.append(m_KUL_roh)
        m_KUL = m_KUL_puffer.pop(0)
        m_ERH = 0
    else:
        m_ERH = 0
        m_KUL = 0

    # Temperaturberechnung Erhitzer/Kühler
    if m_ERH > 0:
        params = config["erhitzer"]
        T_ERH = T_WRG + (m_ERH * params["c_WAS"] * params["T_DIF_ERH"]) / (params["c_LUF"] * params["c_LUF"])
        T_ZUL = T_ERH
    elif m_KUL > 0:
        params = config["kuehler"]
        T_KUL = T_WRG - (m_KUL * params["c_WAS"] * params["T_DIF_KUL"]) / (params["c_LUF"] * params["c_LUF"])
        T_ZUL = T_KUL
    else:
        T_ZUL = T_WRG

    # Raumtemperatur aktualisieren
    #dT_R = (T_ZUL - T_R) * 0.1  # einfache Wärmezufuhrformel
    T_R = (T_R * V_R + p_LUF * m_LUF * T_ZUL)/(V_R + p_LUF * m_LUF)
    T_ABL = T_R

    vis.add_data(t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_ERH, m_KUL, wrg_on)
    time.sleep(dt)

vis.plot()
