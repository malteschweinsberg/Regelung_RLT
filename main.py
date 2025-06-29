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
    rel_humidity = (abs_humidity / abs_max) * 10 # relative Feuchte (%)
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
X_ABL = X_R = relative_to_absolute_humidity(T_R, config["raum"]["X_R_init"] )               # Anfangs-Raumfeuchte
p_LUF = config["physik"]["p_LUF"]
T_ZUL = T_WRG = T_TEP = T_AUL
X_ZUL = X_WRG = X_BFT = X_AUL
T_ABL = T_R  # Abluft = Raumtemperatur
m_LUF = config["ventilator"]["m_LUF_min"]
m_LUF_prev = m_LUF  # Initialisiert mit dem Startwert m_LUF_min
n_BFT = config["befeuchter"]["n_BFT"]
m_TEP = 0
i = 0
print("X_AUL: ",X_AUL," X_R: ",X_R," X_SOL_R: ",X_SOL_R)
# Berechnen der Wärmekapazität
C_Raum = 15*V_R  # J/K
Q_IN = config["raum"]["Q_IN"]  # W

# Totzeit und Totzone Parameter
TOTZEIT_SCHRITTE = 0     # z.B. 5 Simulationsschritte Verzögerung
TOTZONE = 0.05           # z.B. 5% Totzone (anpassen je nach Reglerausgabe)
m_TEP_puffer = [0.0] * TOTZEIT_SCHRITTE # Puffer für Totzeit (FIFO-Listen)


# Regler
regler_X_ZUL = PIRegler(0.01, 0.04, dt)
regler_BFT = PIRegler(0.001, 0.004, dt)
regler_T_ZUL = PIRegler(0.4, 0.2, dt)
regler_TEP = PIRegler(0.005, 0.02, dt)


# WRG Logik
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or (T_AUL > T_SOL_R and T_AUL > T_ABL))

vis = Visualisierung()

for t in range(0, 25000):  # Simulationszeitraum

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
        nt_WRG = config["waermetauscher"]["nt_WRG"]
        nx_WRG = config["waermetauscher"]["nx_WRG"]
        if T_AUL < T_ABL:
            T_WRG = T_AUL + nt_WRG * (T_ABL - T_AUL)
            X_WRG = X_AUL + nx_WRG * (X_ABL - X_AUL)
        else:
            T_WRG = T_AUL - nt_WRG * (T_AUL - T_ABL)
            X_WRG = X_AUL + nx_WRG * (X_ABL - X_AUL)
    else:
        T_WRG = T_AUL

    # Regelung T_ZUL


    T_SOL_ZUL =  regler_T_ZUL.update(T_SOL_R, T_R)
    X_SOL_ZUL = regler_X_ZUL.update(X_SOL_R, X_R)

    # Steuerung Ventilator
    if (X_SOL_ZUL not in range(6,12)) or (T_SOL_ZUL not in range(15,24) )  :
        if T_SOL_ZUL not in range(15,24):
            dT_RA = abs(T_SOL_R - T_R)
            dT_RA_w = dT_RA * config["ventilator"]["q_w_T"]
            if T_SOL_ZUL < 15:
                T_SOL_ZUL = 15
            elif T_SOL_ZUL > 24:
                T_SOL_ZUL = 24
        else:
            dT_RA_w = 0
        if X_SOL_ZUL not in range(6, 12):
            dX_RA = abs(X_SOL_R - X_R)
            dX_RA_w = dX_RA * config["ventilator"]["q_w_X"]
            if X_SOL_ZUL < 6:
                X_SOL_ZUL = 6
            elif X_SOL_ZUL > 12:
                X_SOL_ZUL = 12
        else:
            dX_RA_w = 0
        d_max = max(dT_RA_w, dX_RA_w)
        if d_max <= 0.1:
            m_LUF = config["ventilator"]["m_LUF_min"]
        elif d_max >= 2:
            m_LUF = config["ventilator"]["m_LUF_max"]
        elif 0.1 < d_max < 2:
            m_LUF = config["ventilator"]["m_LUF_min"] + (dT_RA_w - 0.1) / (2-0.1) * (config["ventilator"]["m_LUF_max"] - config["ventilator"]["m_LUF_min"])
    dT_RA_SOL = abs(T_SOL_R - T_R)


    if dT_RA_SOL > 0.2:
        dTZUL = T_SOL_ZUL - T_ZUL
        # Heizen oder Kühlen mit Totzeit und Totzone
        m_TEP_roh = regler_TEP.update(T_SOL_ZUL, T_ZUL)
        # Totzone anwenden
        if abs(m_TEP_roh) < TOTZONE:
            m_TEP_roh = 0.0
        # Totzeit-Puffer aktualisieren
        m_TEP_puffer.append(m_TEP_roh)
        m_TEP = m_TEP_puffer.pop(0)
        params = config["physik"]
        T_ZUL = T_WRG + (m_TEP * params["c_WAS"] * config["erhitzer"]["T_DIF_ERH"]) / (params["c_LUF"] * m_LUF)

    dX_R = abs(X_SOL_R - X_R)

    # Feuchte Regelung
    if dX_R >0.1:

        #print(t, " X_SOL_R: ", round(X_SOL_R, 3), " X_R: ", round(X_R, 3), " X_SOl_ZUL: ", round(X_SOL_ZUL, 3))
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
    X_R = X_R + ((m_LUF * 1.2 * dt)/(V_R * 1.2))*(X_ZUL - X_R)
    print(t, 'X_R', round(X_R,3), 'm_Luf', round(m_LUF,3),'dt', round(dt,3) , 'x_r', round(X_R,3), 'v_r', V_R ,'x_r*v_R', round(X_R * V_R,3),'X_ZUL',round(X_ZUL,3), 'X_R',round(X_R,3))
    print(t, 'X_R', round(X_R, 3), 'm_Luf *dt ', round(m_LUF *dt, 3),'x_r*v_R', round(X_R * V_R, 3), 'X_ZUL-x_R', round(X_ZUL-X_R, 3))
    #print(t," T_SOL_ZUL: ", round(T_SOL_ZUL,3), " T_ZUL: ", round(T_ZUL,3), " T_R: ", round(T_R,3), " T_ABL: ", round(T_ABL,3))
    vis.add_data(t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_TEP, m_LUF, X_R,  X_SOL_R, X_SOL_ZUL, X_ZUL)
    time.sleep(dt)

vis.plot()
