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
p_LUF = config["physik"]["p_LUF"]

# Initialwerte
T_ZUL = T_WRG = T_ERH = T_KUL = T_AUL
T_ABL = T_R  # Abluft = Raumtemperatur
m_LUF = config["ventilator"]["m_LUF_min"]
m_ERH = m_KUL = 0
# Totzeit und Totzone Parameter
TOTZEIT_SCHRITTE = 0      # z.B. 5 Simulationsschritte Verzögerung
TOTZONE = 0.05           # z.B. 5% Totzone (anpassen je nach Reglerausgabe)

# Puffer für Totzeit (FIFO-Listen)
m_ERH_puffer = [0.0] * TOTZEIT_SCHRITTE
m_KUL_puffer = [0.0] * TOTZEIT_SCHRITTE

# WRG Logik
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or (T_AUL > T_SOL_R and T_AUL > T_ABL))

# Berechnen der Wärmekapazität
rho = 1.2  # kg/m³
c_LUF = 1005  # Ws/(kg·K)
V_R = config["raum"]["V_R"]
C_Raum = rho * V_R * c_LUF  # Ws/K
Q_IN = config["raum"]["Q_IN"]  # W

# Regler
regler_T_ZUL = PIRegler(0.5, 0.3, dt)
regler_ERH = PIRegler(0.001, 0.004, dt, 0 )
regler_KUL = PIRegler(0.001, 0.004, dt, 0 )

vis = Visualisierung()

for t in range(0, 1000):  # 1 Stunde simulieren
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
    dT_RA_SOL = abs(T_SOL_R - T_R)
    if dT_RA_SOL > 0.2:

        T_SOL_ZUL =  regler_T_ZUL.update(T_SOL_R, T_R)
        dTZUL = T_SOL_ZUL - T_WRG

        # Steuerung Ventilator
        if 15 <= T_SOL_ZUL <= 24:
            T_SOL_ZUL = T_SOL_ZUL
        else:
            dT_RA = abs(T_SOL_R - T_R)
            dT_RA_w = dT_RA * config["ventilator"]["q_w_T"]
            if dT_RA_w <= 0.1:
                m_LUF = config["ventilator"]["m_LUF_min"]
            elif dT_RA_w >= 2:
                m_LUF = config["ventilator"]["m_LUF_max"]
            elif 0.1 < dT_RA_w < 2:
                m_LUF = config["ventilator"]["m_LUF_min"] + (dT_RA_w - 0.1) / (2-0.1) * (config["ventilator"]["m_LUF_max"] - config["ventilator"]["m_LUF_min"])
            if T_SOL_ZUL < 15:
                T_SOL_ZUL = 15
            elif T_SOL_ZUL > 24:
                T_SOL_ZUL = 24
        # berechnung der potentiellen zuluft temperatur
        if dTZUL > 0:
            params = config["physik"]
            T_ERH_pot = T_WRG + (m_ERH * params["c_WAS"] * config["erhitzer"]["T_DIF_ERH"]) / (params["c_LUF"] * m_LUF)
            T_ZUL_pot = T_ERH_pot
        elif dTZUL > 0:
            params = config["physik"]
            T_KUL_pot = T_WRG - (m_KUL * params["c_WAS"] * config["kuehler"]["T_DIF_KUL"]) / (params["c_LUF"] * m_LUF)
            T_ZUL_pot = T_KUL_pot
        else:
            T_ZUL_pot = T_WRG

        dTZUL_pot=T_SOL_ZUL-T_ZUL_pot

        # Heizen oder Kühlen mit Totzeit und Totzone
        if dTZUL > 0:
            m_ERH_roh = regler_ERH.update(T_SOL_ZUL, T_ZUL)     #Heizen
            # Totzone anwenden
            if abs(m_ERH_roh) < TOTZONE:
                m_ERH_roh = 0.0
            # Totzeit-Puffer aktualisieren
            m_ERH_puffer.append(m_ERH_roh)
            m_ERH = m_ERH_puffer.pop(0)
            m_KUL = 0
        elif dTZUL < 0:
            m_KUL_roh = regler_KUL.update(T_ZUL, T_SOL_ZUL)     #Kühlen
            # Totzone anwenden
            if abs(m_KUL_roh) < TOTZONE:
                m_KUL_roh = 0.0
            # Totzeit-Puffer aktualisieren
            m_KUL_puffer.append(m_KUL_roh)
            m_KUL = m_KUL_puffer.pop(0)
            m_ERH = 0
        else:
            m_ERH = m_ERH
            m_KUL = m_KUL

        # Temperaturberechnung Erhitzer/Kühler
        if m_ERH > 0:
            params = config["physik"]
            T_ERH = T_WRG + (m_ERH * params["c_WAS"] * config["erhitzer"]["T_DIF_ERH"]) / (params["c_LUF"] * m_LUF)
            T_ZUL = T_ERH
            print(T_SOL_ZUL, T_ZUL,t, 'T_WRG:', T_WRG,'zähler:', m_ERH ,'nenner:', m_LUF)
        elif m_KUL > 0:
            params = config["physik"]
            T_KUL = T_WRG - (m_KUL * params["c_WAS"] * config["kuehler"]["T_DIF_KUL"]) / (params["c_LUF"] * m_LUF)
            T_ZUL = T_KUL
        else:
            T_ZUL = T_WRG




      # Raumtemperatur aktualisieren
    T_R = (T_R * V_R + p_LUF * m_LUF * T_ZUL)/(V_R + p_LUF * m_LUF)
    T_ABL = T_R

    vis.add_data(t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_ERH, m_KUL, m_LUF)
    time.sleep(dt)

vis.plot()
