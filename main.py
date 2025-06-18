import json
import time
import random
import math
from pi_regler import PIRegler
from visualisation import Visualisierung
from scipy.optimize import fsolve
from psychrolib import GetSatHumRatio, SetUnitSystem, SI
with open("config.json") as f:
    config = json.load(f)



# Funktions definierung
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or (T_AUL > T_SOL_R and T_AUL > T_ABL))

def absolute_to_relative_humidity(T, abs_humidity, pressure=1013.25):
    es = 6.112 * math.exp((17.62 * T) / (243.12 + T)) # Sättigungsdampfdruck nach Sonntag-Formel (hPa)
    abs_max = 216.7 * (es / (T + 273.15)) # maximale absolute Feuchte (g/m³)
    rel_humidity = (abs_humidity / abs_max) * 100 # relative Feuchte (%)
    return rel_humidity

def relative_to_absolute_humidity(T, rel_humidity, pressure=1013.25):
    es = 6.112 * math.exp((17.62 * T) / (243.12 + T))  # Sättigungsdampfdruck nach Sonntag-Formel (hPa)
    abs_max = 216.7 * (es / (T + 273.15))              # maximale absolute Feuchte (g/m³)
    abs_humidity = (rel_humidity / 100) * abs_max      # absolute Feuchte (g/m³)
    return abs_humidity

def abs_feuchte_bei_temp(T, soll_x):
    # Sättigungsdampfdruck nach Magnus-Formel (hPa)
    e_s = 6.112 * math.exp((17.62 * T) / (243.12 + T))
    # absolute Feuchte (g/m³)
    x = 216.7 * e_s / (T + 273.15)
    return x - soll_x

def berechne_abkuehl_temp(aktuelle_temp, ziel_x):
    # Startwert: aktuelle Temperatur
    T_guess = aktuelle_temp
    # Finde die Temperatur, bei der die absolute Feuchte = ziel_x ist
    T_ziel = fsolve(abs_feuchte_bei_temp, T_guess, args=(ziel_x,))
    return T_ziel

def berechne_kuehltemperatur(x_ziel_g_per_kg, start_temp=20):
    """
    Berechnet die Temperatur, auf die Luft gekühlt werden muss,
    damit sie bei 100% relativer Feuchte die gegebene absolute Feuchte erreicht.

    :param x_ziel_g_per_kg: Ziel-Feuchte in g/kg
    :param start_temp: Startwert für die Näherung (default: 20 °C)
    :return: Temperatur in °C
    """
    x_ziel = x_ziel_g_per_kg / 1000  # g/kg → kg/kg

    def diff(t):
        return GetSatHumRatio(t, P_ATM) - x_ziel

    t_ziel = fsolve(diff, start_temp)[0]
    return t_ziel
def berechne_feuchte_nach_kuehler(T_kuehler, x_vor_g_per_kg):
    """
    Bestimmt die Feuchte nach einem Kühler (Entfeuchtung durch Kondensation).

    :param T_kuehler: Temperatur des Kühlers [°C]
    :param x_vor_g_per_kg: Absolute Feuchte vor dem Kühler [g/kg]
    :return: Absolute Feuchte nach dem Kühler [g/kg]
    """
    try:
        x_satt = GetSatHumRatio(T_kuehler, P_ATM) * 1000  # kg/kg → g/kg

        if x_vor_g_per_kg > x_satt:
            return x_satt  # Es kondensiert Wasser – Entfeuchtung
        else:
            return x_vor_g_per_kg  # Kein Taupunkt erreicht, keine Entfeuchtung

    except ValueError as e:
        print(f"❌ Fehler bei der Berechnung: {e}")
        return None
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
T_ZUL = T_ZUL_prev = T_WRG = T_ERH = T_KUL = T_AUL
X_ZUL = X_WRG = X_BFT = X_AUL
T_ABL = T_R  # Abluft = Raumtemperatur
m_LUF = config["ventilator"]["m_LUF_min"]
m_LUF_prev = m_LUF  # Initialisiert mit dem Startwert m_LUF_min
m_ERH = m_KUL = 0
n_WRG = config["waermetauscher"]["n_WRG"]
n_BFT = config["befeuchter"]["n_BFT"]
i = 0
print("X_AUL: ",X_AUL," X_R: ",X_R," X_SOL_R: ",X_SOL_R)
SetUnitSystem(SI)
P_ATM = 101325
# Berechnen der Wärmekapazität
rho = 1.2  # kg/m³
c_LUF = 1005  # Ws/(kg·K)
C_Raum = rho * V_R * c_LUF  # Ws/K
Q_IN = config["raum"]["Q_IN"]  # W

# Totzeit und Totzone Parameter
TOTZEIT_SCHRITTE = 0     # z.B. 5 Simulationsschritte Verzögerung
TOTZONE = 0.05           # z.B. 5% Totzone (anpassen je nach Reglerausgabe)
m_ERH_puffer = [0.0] * TOTZEIT_SCHRITTE # Puffer für Totzeit (FIFO-Listen)
m_KUL_puffer = [0.0] * TOTZEIT_SCHRITTE # Puffer für Totzeit (FIFO-Listen)

# Regler
regler_X_ZUL = PIRegler(0.001, 0.004, dt)
regler_BFT = PIRegler(0.001, 0.004, dt)
regler_T_ZUL = PIRegler(0.5, 0.3, dt)
regler_ERH = PIRegler(0.001, 0.004, dt)
regler_KUL = PIRegler(0.001, 0.004, dt)

vis = Visualisierung()

for t in range(0, 2000):  # Simulationszeitraum

    # Simulation Außentemperatur/Raumlast (feuchte Fehlt)
    if i == 60:
        #Änderung Außentemperatur
        AE_AT = random.uniform(-0.5, 0.5)
        T_AUL = T_AUL + AE_AT
        if T_AUL < 10:
            T_AUL = 10
        elif T_AUL > 30:
            T_AUL = 30

        #Änderun Innerewärmelast
        AE_Q = random.uniform(50,50)
        Q_IN = Q_IN + AE_Q
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
        if T_AUL < T_ABL:
            T_WRG = T_AUL + n_WRG * (T_ABL - T_AUL)
        else:
            T_WRG = T_AUL - n_WRG * (T_AUL - T_ABL)
    else:
        T_WRG = T_AUL

    # Regelung T_ZUL
    dT_RA_SOL = abs(T_SOL_R - T_R)
    if dT_RA_SOL > 0.02 :
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

        # Heizen oder Kühlen mit Totzeit und Totzone
        if dTZUL > 0:
            m_ERH_roh = regler_ERH.update(T_SOL_ZUL, T_ZUL_prev)     #Heizen
            # Totzone anwenden
            if abs(m_ERH_roh) < TOTZONE:
                m_ERH_roh = 0.0
            # Totzeit-Puffer aktualisieren
            m_ERH_puffer.append(m_ERH_roh)
            m_ERH = m_ERH_puffer.pop(0)
            m_KUL = 0
        elif dTZUL < 0:
            m_KUL_roh = regler_KUL.update(T_ZUL_prev, T_SOL_ZUL)     #Kühlen
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
        if X_SOL_ZUL > 12:
            X_SOL_ZUL = 12
        elif X_SOL_ZUL < 6:
            X_SOL_ZUL = 6
        dX_ZUL = X_SOL_ZUL - X_ZUL
        if dX_ZUL > 0:
            m_BFT = regler_BFT.update(X_SOL_ZUL, X_AUL)
            X_ZUL = X_AUL + m_BFT * n_BFT
        elif dX_ZUL <0:
            T_SOL_ENF_KUL = berechne_kuehltemperatur(T_WRG, X_SOL_ZUL)
            # Kühlen und somit entfeuchten
            m_KUL = regler_ERH.update(T_SOL_ENF_KUL, T_ZUL_prev)
            if abs(m_KUL_roh) < TOTZONE:
                m_KUL_roh = 0.0
            # Totzeit-Puffer aktualisieren
            m_KUL_puffer.append(m_KUL_roh)
            m_KUL = m_KUL_puffer.pop(0)
            params = config["physik"]
            T_KUL = T_WRG - (m_KUL * params["c_WAS"] * config["kuehler"]["T_DIF_KUL"]) / (params["c_LUF"] * m_LUF)
            X_ZUL = berechne_feuchte_nach_kuehler(T_KUL, X_WRG)
            print(t, 'T_K:',T_KUL,'T_wrg:',T_WRG,'Zähler:',m_KUL * params["c_WAS"] * config["kuehler"]["T_DIF_KUL"],'Nenner:', params["c_LUF"] * m_LUF)
            T_ZUL = T_KUL
            # Erhitzen nach dem Entfeuchen
            m_ERH_roh = regler_ERH.update(T_SOL_ZUL, T_ZUL_prev)     #Heizen
            # Totzone anwenden
            if abs(m_ERH_roh) < TOTZONE:
                m_ERH_roh = 0.0
            # Totzeit-Puffer aktualisieren
            m_ERH_puffer.append(m_ERH_roh)
            m_ERH = m_ERH_puffer.pop(0)
            T_ERH = T_WRG + (m_ERH * params["c_WAS"] * config["erhitzer"]["T_DIF_ERH"]) / (params["c_LUF"] * m_LUF)
            T_ZUL = T_ERH



    m_LUF_prev = m_LUF  # Speichert den aktuellen Wert für den nächsten Durchlauf
    T_ZUL_prev = T_ZUL
    # Raumtemperatur aktualisieren
    E_QIN = Q_IN * dt  # Energie in Joule, die im Zeitschritt zugeführt wird
    delta_T_QIN = E_QIN / C_Raum  # Temperaturerhöhung in Kelvin (bzw. °C)
    T_R = (T_R * V_R + p_LUF * m_LUF * T_ZUL) / (V_R + p_LUF * m_LUF) + delta_T_QIN
    X_R = (V_R * X_R + p_LUF * m_LUF * X_ZUL) / (V_R + p_LUF * m_LUF)
    X_R_rel = absolute_to_relative_humidity(X_R,T_R)
    X_ZUL_rel = absolute_to_relative_humidity(X_ZUL,T_ZUL)
    X_SOL_ZUL_rel = absolute_to_relative_humidity(X_SOL_ZUL,T_SOL_ZUL)
    T_ABL = T_R

    #print(t," T_SOL_ZUL: ", round(T_SOL_ZUL,3), " T_ZUL: ", round(T_ZUL,3), " T_R: ", round(T_R,3), " T_ABL: ", round(T_ABL,3))
    vis.add_data(t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_ERH, m_KUL, m_LUF, X_R, X_SOL_R, X_SOL_ZUL, X_ZUL)
    time.sleep(dt)

vis.plot()
