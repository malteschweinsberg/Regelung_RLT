import json
import time
import random
import math
from pi_regler import PIRegler
from visualisation import Visualisierung

with open("config.json") as f:
    config = json.load(f)

def enthalpie_luft_joule(temperatur, rel_feuchte = 35, druck=1013.25):
    """
    Berechnet die spezifische Enthalpie der feuchten Luft (in J/kg).
    temperatur: Temperatur in °C
    rel_feuchte: Relative Feuchte in %
    druck: Luftdruck in hPa (Standard: 1013.25 hPa)
    """
    # Sättigungsdampfdruck nach Magnus-Formel
    es = 6.1078 * 10 ** ((7.5 * temperatur) / (temperatur + 237.3))  # hPa
    # Dampfdruck
    e = es * rel_feuchte / 100.0
    # Wasserdampfgehalt (Mischungsverhältnis, Näherung)
    x = 0.622 * e / (druck - e)
    # Spezifische Enthalpie (J/kg)
    h = (1.006 * temperatur + x * (2501 + 1.86 * temperatur)) * 1000  # Umrechnung in J/kg
    return h

def absolute_to_relative_humidity(T, abs_humidity, pressure=1013.25):
    es = 6.112 * math.exp((17.62 * T) / (243.12 + T)) # Sättigungsdampfdruck nach Sonntag-Formel (hPa)
    abs_max = 216.7 * (es / (T + 273.15)) # maximale absolute Feuchte (g/m³)
    rel_humidity = (abs_humidity / abs_max)*10 # relative Feuchte (%)
    return rel_humidity

def relative_to_absolute_humidity(T, rel_humidity, pressure=1013.25):
    es = 6.112 * math.exp((17.62 * T) / (243.12 + T))  # Sättigungsdampfdruck nach Sonntag-Formel (hPa)
    abs_max = 216.7 * (es / (T + 273.15))              # maximale absolute Feuchte (g/m³)
    abs_humidity = (rel_humidity / 100) * abs_max      # absolute Feuchte (g/m³)
    return abs_humidity

# Simulationseinstellungen
t_sp = config["simulation"]["t_sp"]             # Geschwindigkeit der Simulation
dt = 0.1 / t_sp                                 # Reale Zeit pro Simulationsschritt

# Initialwerte
T_AUL = config["simulation"]["T_AUL"]           # Außenlufttemperatur
X_AUL = relative_to_absolute_humidity(T_AUL,config["simulation"]["X_AUL"] ) # Außenluftfeuchte
T_SOL_R = config["simulation"]["T_SOL_R"]       # Ziel-Raumtemperatur
X_SOL_R = relative_to_absolute_humidity(T_SOL_R, config["simulation"]["X_SOL_R"] )      # Ziel-Raumfeuchte
V_R = config["raum"]["V_R"]                     # Raumvolumen
T_R = config["raum"]["T_R_init"]                # Anfangs-Raumtemperatur
X_R = relative_to_absolute_humidity(T_R, config["raum"]["X_R_init"] )               # Anfangs-Raumfeuchte
p_LUF = config["physik"]["p_LUF"]
T_ZUL = T_WRG = T_ERH = T_KUL = T_AUL
X_ZUL = X_WRG = X_BFT = X_AUL
T_ABL = T_R  # Abluft = Raumtemperatur
m_LUF = config["ventilator"]["m_LUF_min"]
m_LUF_prev = m_LUF  # Initialisiert mit dem Startwert m_LUF_min
n_WRG = config["waermetauscher"]["n_WRG"]
n_BFT = config["befeuchter"]["n_BFT"]
m_ERH = m_KUL = 0
i = 0
print("X_AUL: ",X_AUL," X_R: ",X_R," X_SOL_R: ",X_SOL_R)
# Berechnen der Wärmekapazität
C_Raum = 15*3600*V_R  # J/K
Q_IN = config["raum"]["Q_IN"]  # W

# Totzeit und Totzone Parameter
TOTZEIT_SCHRITTE = 0     # z.B. 5 Simulationsschritte Verzögerung
TOTZONE = 0.05           # z.B. 5% Totzone (anpassen je nach Reglerausgabe)
m_ERH_puffer = [0.0] * TOTZEIT_SCHRITTE # Puffer für Totzeit (FIFO-Listen)
m_KUL_puffer = [0.0] * TOTZEIT_SCHRITTE # Puffer für Totzeit (FIFO-Listen)

# Regler
regler_X_ZUL = PIRegler(0.001, 0.004, dt)
regler_BFT = PIRegler(0.001, 0.004, dt)
regler_T_ZUL = PIRegler(0.4, 0.2, dt)
regler_ERH = PIRegler(0.008, 0.003, dt)
regler_KUL = PIRegler(0.008, 0.003, dt)

# WRG Logik
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or (T_AUL > T_SOL_R and T_AUL > T_ABL))

vis = Visualisierung()

for t in range(0, 150):  # Simulationszeitraum

    # Simulation Außentemperatur/Raumlast
    if i == 60:
        AE_AT = random.uniform(-0.5, 0.5)
        T_AUL = T_AUL + AE_AT
        # Begrenzung der Temperatur im definierten Rahmen
        if T_AUL < 10:
            T_AUL = 10
        elif T_AUL > 30:
            T_AUL = 30

        AE_Q = random.uniform(50,50)
        Q_IN = Q_IN + AE_Q
        # Begrenzung der Temperatur im definierten Rahmen
        if Q_IN < 0:
            Q_IN = 0
        elif Q_IN > 1000:
            Q_IN = 1000
        i = 0
    else:
        i = i + 1


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
        dTZUL = T_SOL_ZUL - T_ZUL

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

        # Heizen oder Kühlen mit Totzeit und Totzone
        if dTZUL > 0:
            m_ERH_roh = regler_ERH.update(T_SOL_ZUL, T_ZUL)     #Heizen
            regler_KUL.reset()
            # Totzone anwenden
            if abs(m_ERH_roh) < TOTZONE:
                m_ERH_roh = 0.0
            # Totzeit-Puffer aktualisieren
            m_ERH_puffer.append(m_ERH_roh)
            m_ERH = m_ERH_puffer.pop(0)
            m_KUL = 0
        elif dTZUL < 0:
            m_KUL_roh = regler_KUL.update(T_ZUL, T_SOL_ZUL)     #Kühlen
            regler_ERH.reset()
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

        elif m_KUL > 0:
            params = config["physik"]
            T_KUL = T_WRG - (m_KUL * params["c_WAS"] * config["kuehler"]["T_DIF_KUL"]) / (params["c_LUF"] * m_LUF)
            T_ZUL = T_KUL
        else:
            T_ZUL = T_WRG

        #Kontrolle Volumenstrom Luft
        if 15 <= T_ZUL <= 24:
            T_ZUL = T_ZUL
        else:
            m_LUF = m_LUF_prev  # Nutzt den gespeicherten Wert des letzten Durchlaufs

            if m_ERH > 0:
                params = config["physik"]
                T_ERH = T_WRG + (m_ERH * params["c_WAS"] * config["erhitzer"]["T_DIF_ERH"]) / (params["c_LUF"] * m_LUF)
                T_ZUL = T_ERH

            elif m_KUL > 0:
                params = config["physik"]
                T_KUL = T_WRG - (m_KUL * params["c_WAS"] * config["kuehler"]["T_DIF_KUL"]) / (params["c_LUF"] * m_LUF)
                T_ZUL = T_KUL
            else:
                T_ZUL = T_WRG

    dX_R = abs(X_SOL_R - X_R)

    # Feuchte Regelung
    X_WRG = X_AUL
    if dX_R >0.1:
        X_SOL_ZUL =  regler_X_ZUL.update(X_SOL_R, X_R)
        dX_ZUL = X_SOL_ZUL - X_ZUL
        if dX_ZUL > 0:
            m_BFT = regler_BFT.update(X_SOL_ZUL, X_AUL)
            X_ZUL = X_AUL + m_BFT * n_BFT

    m_LUF_prev = m_LUF  # Speichert den aktuellen Wert für den nächsten Durchlauf

    # Raumtemperatur aktualisieren

    h_ZUL = enthalpie_luft_joule(T_ZUL)
    h_R = enthalpie_luft_joule(T_R)
    T_R = T_R + dt/C_Raum * (Q_IN + m_LUF * h_ZUL - m_LUF * h_R)
    T_ABL = T_R
    X_R = X_R + ((m_LUF * dt)/(X_R * V_R))*(X_ZUL - X_R)
    X_R_rel = absolute_to_relative_humidity(X_R,T_R)
    X_ZUL_rel = absolute_to_relative_humidity(X_ZUL,T_ZUL)
    X_SOL_ZUL_rel = absolute_to_relative_humidity(X_SOL_ZUL,T_SOL_ZUL)

    #print(t," T_SOL_ZUL: ", round(T_SOL_ZUL,3), " T_ZUL: ", round(T_ZUL,3), " T_R: ", round(T_R,3), " T_ABL: ", round(T_ABL,3))
    print( X_R_rel,  config["simulation"]["X_SOL_R"], X_SOL_ZUL_rel, X_ZUL_rel)
    vis.add_data(t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_ERH, m_KUL, m_LUF, X_R_rel,  config["simulation"]["X_SOL_R"], X_SOL_ZUL_rel, X_ZUL_rel)
    time.sleep(dt)

vis.plot()
