import json
import time
import random
import math
from pi_regler import PIRegler
from visualisation import Visualisierung

with open("config.json") as f:
    config = json.load(f)


def enthalpie_luft_joule(temperatur, rel_feuchte=config["physik"]["rel_feuchte_default"],
                         druck=config["physik"]["luftdruck_hPa"]):
    es = 6.1078 * 10 ** ((7.5 * temperatur) / (temperatur + 237.3))
    e = es * rel_feuchte / 100.0
    x = 0.622 * e / (druck - e)
    h = (1.006 * temperatur + x * (2501 + 1.86 * temperatur)) * 1000
    return h


def absolute_to_relative_humidity(T, abs_humidity, pressure=config["physik"]["luftdruck_hPa"]):
    es = 6.112 * math.exp((17.62 * T) / (243.12 + T))
    abs_max = 216.7 * (es / (T + 273.15))
    rel_humidity = (abs_humidity / abs_max) * 100
    return rel_humidity


def relative_to_absolute_humidity(T, rel_humidity, pressure=config["physik"]["luftdruck_hPa"]):
    es = 6.112 * math.exp((17.62 * T) / (243.12 + T))
    abs_max = 216.7 * (es / (T + 273.15))
    abs_humidity = (rel_humidity / 100) * abs_max
    return abs_humidity


# Initialisierung
t_sp = config["simulation"]["t_sp"]
dt = 0.1 / t_sp
T_AUL = config["simulation"]["T_AUL"]
X_AUL = relative_to_absolute_humidity(T_AUL, config["simulation"]["X_AUL"])
T_SOL_R = config["simulation"]["T_SOL_R"]
X_SOL_R = relative_to_absolute_humidity(T_SOL_R, config["simulation"]["X_SOL_R"])
V_R = config["raum"]["V_R"]
T_R = config["raum"]["T_R_init"]
X_R = relative_to_absolute_humidity(T_R, config["raum"]["X_R_init"])
X_ABL = X_R
T_SOL_ZUL = T_ZUL = T_WRG = T_AUL
X_ZUL = X_WRG = X_AUL
T_ABL = T_R
m_LUF = config["ventilator"]["m_LUF_min"]
n_BFT = config["befeuchter"]["n_BFT"]
m_TEP = 0
dT_RA_w = 0  # Vor den if-Bedingungen hinzufügen
dX_RA_w = 0
i = 0

# Systemparameter
C_Raum = config["raum"]["faktor_waermekapazitaet"] * V_R
Q_IN = config["raum"]["Q_IN"]
TOTZEIT_SCHRITTE = config["totzeit"]["totzeit_schritte"]
TOTZONE = config["totzeit"]["totzone"]
m_TEP_puffer = [0.0] * TOTZEIT_SCHRITTE
m_HUM_puffer = [0.0] * TOTZEIT_SCHRITTE

# Reglerinitialisierung
regler_X_ZUL = PIRegler(
    config["regler"]["X_ZUL"]["kp"],
    config["regler"]["X_ZUL"]["ki"],
    dt
)
regler_HUM = PIRegler(
    config["regler"]["BFT"]["kp"],
    config["regler"]["BFT"]["ki"],
    dt
)
regler_T_ZUL = PIRegler(
    config["regler"]["T_ZUL"]["kp"],
    config["regler"]["T_ZUL"]["ki"],
    dt
)
regler_TEP = PIRegler(
    config["regler"]["TEP"]["kp"],
    config["regler"]["TEP"]["ki"],
    dt
)


# WRG-Logik
def berechne_WRG(T_AUL, T_ABL, T_SOL_R):
    return ((T_ABL > T_AUL and T_AUL < T_SOL_R) or
            (T_AUL > T_SOL_R and T_AUL > T_ABL))


vis = Visualisierung()

for t in range(0, config["simulation"]["schritte"]):

# Störgrößensimulation
    if i == config["simulation"]["stoerung_intervall"]:
        T_AUL = max(
            config["simulation"]["T_AUL_min"],
            min(T_AUL + random.uniform(
                config["simulation"]["stoerung_T_AUL_min"],
                config["simulation"]["stoerung_T_AUL_max"]
            ), config["simulation"]["T_AUL_max"])
        )
        X_AUL_AUL = max(
            relative_to_absolute_humidity(T_AUL,config["simulation"]["X_AUL_min"]),
            min(X_AUL + random.uniform(
                relative_to_absolute_humidity(T_AUL,config["simulation"]["stoerung_X_AUL_min"]),
                relative_to_absolute_humidity(T_AUL,config["simulation"]["stoerung_X_AUL_max"])
            ), relative_to_absolute_humidity(T_AUL,config["simulation"]["X_AUL_max"]))
        )
        Q_IN = max(
            config["simulation"]["Q_IN_min"],
            min(Q_IN + random.uniform(
                config["simulation"]["stoerung_Q_IN_min"],
                config["simulation"]["stoerung_Q_IN_max"]
            ), config["simulation"]["Q_IN_max"])
        )
        i = 0
    else:
        i = 1

# Wärmerückgewinnung
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
        X_WRG = X_AUL

# Ventilatorsteuerung
    T_SOL_ZUL = regler_T_ZUL.update(T_SOL_R, T_R)
    X_SOL_ZUL = regler_X_ZUL.update(X_SOL_R, X_R)
    T_min = config["schwellenwerte"]["T_ZUL_min"]
    T_max = config["schwellenwerte"]["T_ZUL_max"]
    X_min = config["schwellenwerte"]["X_ZUL_min"]
    X_max = config["schwellenwerte"]["X_ZUL_max"]
    dT_RA_SOL = abs(T_SOL_R - T_R)
    dX_RA_SOL = abs(X_SOL_R - X_R)

    dT_RA_w = dX_RA_w = 0

    if dT_RA_SOL > config["schwellenwerte"]["dT_RA_SOL"] or dX_RA_SOL > config["schwellenwerte"]["dX_RA_SOL"]:

        if T_SOL_ZUL < T_min or T_SOL_ZUL > T_max:
            dT_RA = abs(T_SOL_R - T_R)
            dT_RA_w = dT_RA * config["ventilator"]["q_w_T"]
            T_SOL_ZUL = max(T_min, min(T_SOL_ZUL, T_max))

        if X_SOL_ZUL < X_min or X_SOL_ZUL > X_max:
            dX_RA = abs(X_SOL_R - X_R)
            dX_RA_w = dX_RA * config["ventilator"]["q_w_X"]
            X_SOL_ZUL = max(X_min, min(X_SOL_ZUL, X_max))

        # m_LUF berechnen
        d_max = max(dT_RA_w, dX_RA_w)
        d_max_min = config["schwellenwerte"]["d_max_min"]
        d_max_max = config["schwellenwerte"]["d_max_max"]

        if d_max <= d_max_min:
            m_LUF = config["ventilator"]["m_LUF_min"]
        elif d_max >= d_max_max:
            m_LUF = config["ventilator"]["m_LUF_max"]
        else:
            m_LUF = config["ventilator"]["m_LUF_min"] + (d_max - d_max_min) / (d_max_max - d_max_min) * (
                    config["ventilator"]["m_LUF_max"] - config["ventilator"]["m_LUF_min"]
            )
    else:
        m_LUF = config["ventilator"].get("m_LUF_default", config["ventilator"]["m_LUF_min"])

# Heizregistersteuerung
    if dT_RA_SOL > config["schwellenwerte"]["dT_RA_SOL"]:
        m_TEP_roh = regler_TEP.update(T_SOL_ZUL, T_ZUL)
        if abs(m_TEP_roh) < TOTZONE:
            m_TEP_roh = 0.0
        m_TEP_puffer.append(m_TEP_roh)
        m_TEP = m_TEP_puffer.pop(0)
        T_ZUL = T_WRG +  (m_TEP * config["physik"]["c_WAS"] * config["TEP"]["T_DIF_TEP"]) / (
                config["physik"]["c_LUF"] * m_LUF)
        if m_TEP <= 0:
            m_KUL = -m_TEP
            m_ERH = 0
        else:
            m_ERH = m_TEP
            m_KUL = 0

# Befeuchtersteuerung
    dX_RA_SOL = abs(X_SOL_R - X_R)
    if dX_RA_SOL > config["schwellenwerte"]["dX_RA_SOL"]:
        m_HUM_roh = regler_HUM.update(X_SOL_ZUL, X_ZUL)
        if abs(m_HUM_roh) < TOTZONE:
            m_HUM_roh = 0.0
        m_HUM_puffer.append(m_HUM_roh)
        m_HUM = m_HUM_puffer.pop(0)
        if m_HUM <= 0:
            m_ENF = -m_HUM
            m_BFT = 0
        else:
            m_BFT = m_HUM
            m_ENF = 0


        X_ZUL = X_AUL + (m_HUM * n_BFT) / m_LUF

# Raumdynamik
    h_ZUL = enthalpie_luft_joule(T_ZUL)
    h_R = enthalpie_luft_joule(T_R)
    T_R += dt / C_Raum * (Q_IN + m_LUF * h_ZUL - m_LUF * h_R)
    T_ABL = T_R
    rho_luft = config["physik"]["rho_luft"]
    X_R += (m_LUF * dt) / (V_R * rho_luft) * (X_ZUL - X_R)

# Update Soll_Feuchte
    X_SOL_R = relative_to_absolute_humidity(T_R, config["simulation"]["X_SOL_R"])

    if t % 10 == 0:  # Nur jede 10. Iteration, damit die Ausgabe übersichtlich bleibt
        print(
            f"t={t:04d} | "
            f"T_R={T_R:.2f} (Soll {T_SOL_R:.2f}) | "
            f"T_ZUL={T_ZUL:.2f} (Soll {T_SOL_ZUL:.2f}) | "
            f"m_TEP={m_TEP:.3f} | "
            f"X_R={X_R:.2f} (Soll {X_SOL_R:.2f}) | "
            f"X_ZUL={X_ZUL:.2f} (Soll {X_SOL_ZUL:.2f}) | "
            f"m_BFT={m_HUM:.3f} | "
            f"m_LUF={m_LUF:.2f}"
    )


# Visualisierung
    vis.add_data(t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_ERH, m_KUL, m_LUF, X_R, X_SOL_R, X_SOL_ZUL, X_ZUL, m_BFT, m_ENF, wrg_on)
    time.sleep(dt)

vis.plot()
