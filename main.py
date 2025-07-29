# ===================================================================
#                       RLT-SIMULATIONSHAUPTPROGRAMM
#          (Open Source Raumlufttechnik-Simulation mit PI-Reglern)
#
#  Dieses Programm simuliert das thermodynamische Verhalten eines
#  vereinfachten Raummodells mit vollständiger PI-Regelung der
#  Zulufttemperatur und -feuchte. Es dient der Demonstration der
#  physikalischen, regelungstechnischen und programmatischen
#  Zusammenhänge einer RLT-Anlage.
# ===================================================================

# ----------- IMPORTS UND MODULANBINDUNGEN -----------
# Basisbibliotheken
import json         # Einlesen der Konfigurationsdaten (z. B. Raumparameter)
import time         # Zeitverzögerung für realitätsnahe Simulationsverläufe
import random       # Zufallsgenerierung für Störgrößen
import math         # Mathematische Funktionen (Logarithmen, Exponentialfunktionen)

# Eigenentwickelte Module
from pi_regler import PIRegler                            # Standard-PI-Regler
from visualisation import Visualisierung                  # Modul zur Visualisierung der Zeitverläufe

# ----------- KONFIGURATIONSEINLESUNG -----------
# Konfigurationsparameter (z. B. Starttemperatur, Raumvolumen, Reglerparameter)
# werden zentral aus JSON-Datei geladen, um Simulation flexibel anpassbar zu gestalten
with open("config.json") as f:
    config = json.load(f)


# ----------- PHYSIKALISCHE HILFSFUNKTIONEN -----------
# Die nachfolgenden Funktionen dienen der thermodynamischen Berechnung
# von Luft- und Feuchtezuständen auf Basis realer Gleichungen.

# --- Funktion zur Berechnung der Enthalpie feuchter Luft ---
def enthalpie_luft_joule_volum_feuchte(temperatur_C, abs_feuchte_kgm3, druck_Pa=config["physik"]["luftdruck_Pa"]):
    '''
    Funktion zur Berechnung der Enthalpie feuchter Luft (J/kg trockene Luft).
    Die Enthalpie berücksichtigt:
      - sensible Energie (Temperatur der Luft)
      - latente Energie (Wasserdampfanteil)
    Eingabegrößen:
      - Temperatur in °C
      - absolute Feuchte in kg/m³ (Wasserdampf pro Luftvolumen)
      - Luftdruck (optional aus config)
    Rückgabewert:
      - spezifische Enthalpie in J/kg trockene Luft
    '''
    R_d = config["physik"]["R_d"]                                 # Gaskonstante trockene Luft
    T_K = temperatur_C + config["physik"]["C_to_K"]               # Umrechnung in Kelvin
    rho_dry_air = druck_Pa / (R_d * T_K)                          # Dichte trockener Luft (idealisiert)
    x = abs_feuchte_kgm3 / rho_dry_air                            # spezifische Feuchte (kg H2O / kg trockene Luft)
    h = (config["physik"]["c_LUF"] * temperatur_C +              # sensible Energie der Luft
         x * (config["physik"]["h_V_DAMPF_0C"] +                 # latente Energie des Wasserdampfs
              config["physik"]["c_WASSERDAMPF"] * temperatur_C))
    return h


# --- Umrechnungsfunktionen für Feuchtewerte ---

def absolute_to_relative_humidity(T, abs_humidity):
    """
    Wandelt absolute Feuchte (kg/m³) in relative Feuchte (%) um.
    Parameter:
        T: Temperatur in °C
        abs_humidity: absolute Feuchte in kg/m³
    Rückgabe:
        relative Feuchte in Prozent
    """
    # Berechne den Sättigungsdampfdruck (Pa) mit Magnus-Formel
    es = config["physik"]["P_WS_0C_PA"] * math.exp(
        (config["physik"]["MAGNUS_A"] * T) /
        (config["physik"]["MAGNUS_B_C"] + T)
    )

    # Berechne die maximal mögliche absolute Feuchte bei dieser Temperatur (kg/m³)
    abs_max = config["physik"]["FEUCHTEFAKTOR_KG_PA"] * (es / (T + config["physik"]["C_to_K"]))

    # Setze die aktuelle absolute Feuchte ins Verhältnis zur maximalen → relative Feuchte in %
    rel_humidity = (abs_humidity / abs_max) * 100

    return rel_humidity


def relative_to_absolute_humidity(T, rel_humidity):
    """
    Wandelt relative Feuchte (%) in absolute Feuchte (kg/m³) um.
    Parameter:
        T: Temperatur in °C
        rel_humidity: relative Feuchte in Prozent
    Rückgabe:
        absolute Feuchte in kg/m³
    """
    # Berechne den Sättigungsdampfdruck (Pa) mit Magnus-Formel
    es = config["physik"]["P_WS_0C_PA"] * math.exp(
        (config["physik"]["MAGNUS_A"] * T) /
        (config["physik"]["MAGNUS_B_C"] + T)
    )

    # Berechne die maximal mögliche absolute Feuchte bei dieser Temperatur (kg/m³)
    abs_max = config["physik"]["FEUCHTEFAKTOR_KG_PA"] * (es / (T + config["physik"]["C_to_K"]))

    # Multipliziere relative Feuchte (in %) mit max. Feuchte → ergibt absolute Feuchte
    abs_humidity = (rel_humidity / 100) * abs_max

    return abs_humidity

# --- Wärmerückgewinnung aktivieren je nach Enthalpiedifferenz ---
def berechne_WRG(dh1, dh2):
    """
    Entscheidet, ob die Wärmerückgewinnung (WRG) aktiviert werden soll.

    Hintergrund:
    Die Funktion vergleicht zwei Enthalpiedifferenzen:
      - dh1 = Differenz zwischen Soll-Zuluft-Enthalpie und Außenluft-Enthalpie
      - dh2 = Differenz zwischen Soll-Zuluft-Enthalpie und Abluft-Enthalpie

    Idee:
    Wenn der Abstand der Soll-Enthalpie zur Außenluft größer ist als zur Abluft (dh1 > dh2),
    ist es energetisch sinnvoll, die Wärmerückgewinnung zu aktivieren.
    Die Abluft ist der bessere „Energielieferant“ in diesem Fall.

    Rückgabe:
        True  → WRG einschalten
        False → WRG ausgeschaltet lassen
    """
    return dh1 > dh2  # WRG nur aktivieren, wenn dadurch mehr Energie eingespart werden kann

# =============================
#       Initialisierung
# =============================

# --- GRUNDLEGENDES SETUP ---
t_sp = config["simulation"]["t_sp"]                       # Anzahl Zeitschritte pro Zeiteinheit (z.B. 60 Schritte pro Stunde)
dt = 0.1 / t_sp                                           # Zeitschrittweite (s) für die Simulation, abhängig von t_sp

# --- AUSSENLUFT UND SOLLWERTE ---
T_AUL = config["simulation"]["T_AUL"]                     # Außenlufttemperatur in °C
X_AUL = relative_to_absolute_humidity(                    # Umrechnung der relativen Außenluftfeuchte in absolute (kg/m³)
    T_AUL, config["simulation"]["X_AUL"]
)
T_SOL_R = config["simulation"]["T_SOL_R"]                 # Solltemperatur im Raum (z.B. 21°C)
X_SOL_R = relative_to_absolute_humidity(                  # Umrechnung der relativen Sollfeuchte in absolute (kg/m³)
    T_SOL_R, config["simulation"]["X_SOL_R"]
)

# --- RAUMZUSTÄNDE INITIIEREN ---
V_R = config["raum"]["V_R"]                               # Raumvolumen in m³
T_R = config["raum"]["T_R_init"]                          # Initiale Raumtemperatur in °C
X_R = relative_to_absolute_humidity(                      # Initiale Raumfeuchte als absolute Feuchte in kg/m³
    T_R, config["raum"]["X_R_init"]
)
X_ABL = X_R                                               # Anfangs: Abluftfeuchte entspricht Raumluftfeuchte

# --- ZULUFT & WRG STARTWERTE ---
T_SOL_ZUL = T_ZUL = T_WRG = T_AUL                         # Zuluft-, WRG-Temperatur starten mit Außenlufttemperatur
X_SOL_ZUL = X_ZUL = X_WRG = X_AUL                         # Zuluft-, WRG-Feuchte starten mit Außenluftfeuchte
T_ABL = T_R                                               # Ablufttemperatur entspricht zunächst der Raumtemperatur

# --- ANFANGSWERTE SYSTEM ---
m_LUF = config["ventilator"]["m_LUF_min"]                # Mindest-Luftmassenstrom durch Ventilator (kg/s)
n_BFT = config["Feuchte Behandlung"]["n_HUM"]             # Befeuchterkonstante: kg Wasser pro kg Luft
m_TEP_roh = m_TEP = 0                                     # Rohwert und gefilterter Wert des Heiz-/Kühlstroms (kg/s)
m_HUM_prev = m_TEP_prev = 0.00001                         # Initiale "Vorwerte" für Totzonen-Logik (kleiner Startwert)
dT_RA_w = 0                                               # Gewichtete Temperaturabweichung zw. Raum und Sollwert
dX_RA_w = 0                                               # Gewichtete Feuchteabweichung zw. Raum und Sollwert
i = 0                                                     # Zählvariable für Störungstiming

# --- THERMISCHE SYSTEMPARAMETER ---
C_Raum = config["raum"]["faktor_waermekapazitaet"] * V_R  # Wärmekapazität des Raums [J/K]
Q_IN = config["raum"]["Q_IN"]                             # Interne Wärmelast im Raum [W]
TOTZEIT_SCHRITTE = config["totzeit"]["totzeit_schritte"]  # Anzahl der Totzeitschritte (Verzögerung)
TOTZONE = config["totzeit"]["totzone"]                    # Toleranzzone, in der keine Änderung erfolgt
m_TEP_puffer = [0.0] * TOTZEIT_SCHRITTE                   # Puffer für Heiz-/Kühlstromregelung zur Totzeitabbildung
m_HUM_puffer = [0.0] * TOTZEIT_SCHRITTE                   # Puffer für Befeuchterregelung zur Totzeitabbildung


# --- Initialisierung der PI-Regler ---
# Temperaturregelung Zuluft
regler_T_ZUL = PIRegler(
    config["regler"]["T_ZUL"]["kp"],
    config["regler"]["T_ZUL"]["ki"],
    dt
)

# Temperaturregelung Heiz-/Kühlregister
regler_TEP = PIRegler(
    config["regler"]["TEP"]["kp"],
    config["regler"]["TEP"]["ki"],
    dt
)

# Feuchteregelung Zuluft
regler_X_ZUL = PIRegler(
    config["regler"]["X_ZUL"]["kp"],
    config["regler"]["X_ZUL"]["ki"],
    dt
)

# Befeuchterregelung
regler_HUM = PIRegler(
    config["regler"]["BFT"]["kp"],
    config["regler"]["BFT"]["ki"],
    dt
)
# --- VISUALISIERUNG INITIALISIEREN ---
vis = Visualisierung()  # Initialisiert das Visualisierungsobjekt für die spätere Ausgabe


for t in range(0, config["simulation"]["schritte"]):  # Haupt-Simulationsschleife über definierte Anzahl an Schritten

    # =============================
    #     Störgrößensimulation
    # =============================
    if i == config["simulation"][
        "stoerung_intervall"]:  # Wenn der Störintervall erreicht ist, dann wird eine neue Störung eingeleitet
        T_AUL = max(  # Neue Außenlufttemperatur bestimmen (mit Störung)
            config["simulation"]["T_AUL_min"],  # Untere Begrenzung
            min(  # Obere Begrenzung:
                T_AUL + random.uniform(  # Aktuelle Temperatur plus zufällige Störung innerhalb definierter Grenzen
                    config["simulation"]["stoerung_T_AUL_min"],
                    config["simulation"]["stoerung_T_AUL_max"]
                ),
                config["simulation"]["T_AUL_max"]
            )
        )

        X_AUL = max(  # Neue absolute Außenluftfeuchte bestimmen (mit Störung)
            relative_to_absolute_humidity(  # Untere Begrenzung in absoluter Feuchte
                T_AUL, config["simulation"]["X_AUL_min"]
            ),
            min(  # Obere Begrenzung:
                X_AUL + random.uniform(  # Aktuelle Feuchte plus zufällige Störung (in relativer Feuchte umgerechnet)
                    relative_to_absolute_humidity(T_AUL, config["simulation"]["stoerung_X_AUL_min"]),
                    relative_to_absolute_humidity(T_AUL, config["simulation"]["stoerung_X_AUL_max"])
                ),
                relative_to_absolute_humidity(T_AUL, config["simulation"]["X_AUL_max"])
            )
        )

        Q_IN = max(  # Neue interne Wärmelast Q_IN (z.B. durch Personen, Geräte)
            config["simulation"]["Q_IN_min"],  # Untere Begrenzung
            min(  # Obere Begrenzung:
                Q_IN + random.uniform(  # Aktueller Wert plus zufällige Störung
                    config["simulation"]["stoerung_Q_IN_min"],
                    config["simulation"]["stoerung_Q_IN_max"]
                ),
                config["simulation"]["Q_IN_max"]
            )
        )

        i = 0  # Zähler zurücksetzen nach Auslösen der Störung
    else:
        i = i + 1  # Zähler für nächsten Störungszeitpunkt hochzählen


# Wärmerückgewinnung (WRG)
    h_SOl_ZUL = enthalpie_luft_joule_volum_feuchte(T_SOL_ZUL, X_SOL_ZUL)         # Enthalpie der Soll-Zuluft berechnen
    h_AUL = enthalpie_luft_joule_volum_feuchte(T_AUL, X_AUL)                      # Enthalpie der Außenluft berechnen
    h_ABL = enthalpie_luft_joule_volum_feuchte(T_ABL, X_ABL)                      # Enthalpie der Abluft (Raumluft) berechnen
    dh1 = h_SOl_ZUL - h_AUL                                                       # Differenz Soll-Zuluft zu Außenluft
    dh2 = h_SOl_ZUL - h_ABL                                                       # Differenz Soll-Zuluft zu Abluft
    wrg_on = berechne_WRG(dh1, dh2)                                               # Prüfen, ob WRG sinnvoll ist (dh1 > dh2)

    if wrg_on:                                                                    # Wenn WRG aktiviert werden soll
        nt_WRG = config["waermetauscher"]["nt_WRG"]                               # Temperatur-Wirkungsgrad auslesen
        nx_WRG = config["waermetauscher"]["nx_WRG"]                               # Feuchte-Wirkungsgrad auslesen

        if T_AUL < T_ABL:                                                         # Wenn Abluft wärmer als Außenluft ist
            T_WRG = T_AUL + nt_WRG * (T_ABL - T_AUL)                              # Erwärme Außenluft anteilig mit WRG
            X_WRG = X_AUL + nx_WRG * (X_ABL - X_AUL)                              # Erhöhe Außenluft-Feuchte anteilig
        else:                                                                     # Wenn Außenluft wärmer als Abluft ist
            T_WRG = T_AUL - nt_WRG * (T_AUL - T_ABL)                              # Kühle Außenluft anteilig mit WRG
            X_WRG = X_AUL + nx_WRG * (X_ABL - X_AUL)                              # Erhöhe Außenluft-Feuchte anteilig
    else:                                                                         # Wenn WRG nicht aktiviert ist
        T_WRG = T_AUL                                                             # Zulufttemperatur bleibt wie Außenluft
        X_WRG = X_AUL                                                             # Zuluftfeuchte bleibt wie Außenluft




# Ventilatorsteuerung
    T_SOL_ZUL = regler_T_ZUL.update(T_SOL_R, T_R)                                 # Berechne Soll-Zulufttemperatur mit PI-Regler
    X_SOL_ZUL = regler_X_ZUL.update(X_SOL_R, X_R)                                 # Berechne Soll-Zuluftfeuchte mit PI-Regler

    T_min = config["schwellenwerte"]["T_ZUL_min"]                                 # Minimal zulässige Zulufttemperatur
    T_max = config["schwellenwerte"]["T_ZUL_max"]                                 # Maximal zulässige Zulufttemperatur
    X_min = config["schwellenwerte"]["X_ZUL_min"]                                 # Minimal zulässige Zuluftfeuchte
    X_max = config["schwellenwerte"]["X_ZUL_max"]                                 # Maximal zulässige Zuluftfeuchte

    dT_RA_SOL = abs(T_SOL_R - T_R)                                                # Temperaturabweichung im Raum
    dX_RA_SOL = abs(X_SOL_R - X_R)                                                # Feuchteabweichung im Raum

    dT_RA_w = dX_RA_w = 0                                                         # Initialisiere gewichtete Abweichungen

    if dT_RA_SOL > config["schwellenwerte"]["dT_RA_SOL"] or dX_RA_SOL > config["schwellenwerte"]["dX_RA_SOL"]:  # Nur regeln, wenn Abweichung groß genug

        if T_SOL_ZUL < T_min or T_SOL_ZUL > T_max:                                # Wenn berechnete Zulufttemperatur unzulässig
            dT_RA = abs(T_SOL_R - T_R)                                            # Temperaturabweichung bestimmen
            dT_RA_w = dT_RA * config["ventilator"]["q_w_T"]                       # Gewichtung der Abweichung
            T_SOL_ZUL = max(T_min, min(T_SOL_ZUL, T_max))                         # Begrenzung der Soll-Zulufttemperatur

        if X_SOL_ZUL < X_min or X_SOL_ZUL > X_max:                                # Wenn berechnete Zuluftfeuchte unzulässig
            dX_RA = abs(X_SOL_R - X_R)                                            # Feuchteabweichung bestimmen
            dX_RA_w = dX_RA * config["ventilator"]["q_w_X"]                       # Gewichtung der Abweichung
            X_SOL_ZUL = max(X_min, min(X_SOL_ZUL, X_max))                         # Begrenzung der Soll-Zuluftfeuchte

        # m_LUF berechnen (Luftmassenstrom anhand größter gewichteter Abweichung)
        d_max = max(dT_RA_w, dX_RA_w)                                             # Max. gewichtete Abweichung wählen
        d_max_min = config["schwellenwerte"]["d_max_min"]                         # Untere Schwelle
        d_max_max = config["schwellenwerte"]["d_max_max"]                         # Obere Schwelle

        if d_max <= d_max_min:                                                    # Wenn Abweichung sehr klein
            m_LUF = config["ventilator"]["m_LUF_min"]                             # kleinster Luftmassenstrom
        elif d_max >= d_max_max:                                                  # Wenn Abweichung sehr groß
            m_LUF = config["ventilator"]["m_LUF_max"]                             # maximaler Luftmassenstrom
        else:                                                                      # Wenn Abweichung dazwischen liegt
            m_LUF = config["ventilator"]["m_LUF_min"] + (d_max - d_max_min) / (d_max_max - d_max_min) * (
                    config["ventilator"]["m_LUF_max"] - config["ventilator"]["m_LUF_min"]
            )                                                                      # lineare Interpolation des Volumenstroms
    else:
        m_LUF = config["ventilator"].get("m_LUF_default", config["ventilator"]["m_LUF_min"])  # Standardwert verwenden, falls keine Regelung nötig



# Heizregistersteuerung
    if dT_RA_SOL > config["schwellenwerte"]["dT_RA_SOL"]:                         # Nur regeln, wenn Temperaturabweichung im Raum groß genug

        m_TEP_roh = regler_TEP.update(T_SOL_ZUL, T_ZUL)                           # PI-Regler berechnet Rohwert für Heiz-/Kühlleistung

        if abs(m_TEP_roh - m_TEP_prev) / abs(m_TEP_prev) < TOTZONE:              # Wenn Änderung innerhalb der Totzone liegt (Hysterese)
            m_TEP_roh = m_TEP_prev                                                # Dann alten Wert beibehalten

        m_TEP_prev = m_TEP_roh                                                    # Aktuellen Reglerwert speichern

        m_TEP_puffer.append(m_TEP_roh)                                            # Wert in den Verzögerungspuffer schreiben
        m_TEP = m_TEP_puffer.pop(0)                                               # Ältesten Wert aus Puffer entnehmen (Totzeitmodell)

        if m_TEP <= 0:                                                             # Bei negativem Reglerwert → Kühlen
            T_ZUL = T_WRG + (m_TEP * config["physik"]["c_WAS"] *                  # Berechne Zulufttemperatur nach Kühlung
                    config["Kuehler"]["T_DIF_KUH"]) /(config["physik"]["c_LUF"] * m_LUF)
            m_KUL = -m_TEP                                                        # Kühlleistung ist der negative Reglerwert
            m_ERH = 0                                                             # Keine Heizleistung

        else:                                                                      # Bei positivem Reglerwert → Heizen
            T_ZUL = T_WRG + (m_TEP * config["physik"]["c_WAS"] *                  # Berechne Zulufttemperatur nach Erwärmung
                    config["Erhitzer"]["T_DIF_ERH"]) /(config["physik"]["c_LUF"] * m_LUF)
            m_KUL = 0                                                             # Keine Kühlleistung
            m_ERH = m_TEP                                                         # Heizleistung entspricht Reglerwert




    # Befeuchtersteuerung
    dX_RA_SOL = abs(X_SOL_R - X_R)                                                # Berechne Abweichung zwischen Soll- und Ist-Raumfeuchte

    if dX_RA_SOL > config["schwellenwerte"]["dX_RA_SOL"]:                         # Nur regeln, wenn Abweichung groß genug

        m_HUM_roh = regler_HUM.update(X_SOL_ZUL, X_ZUL)                           # PI-Regler berechnet Rohwert für Feuchtezufuhr/-entzug

        if abs(m_HUM_roh - m_HUM_prev) / abs(m_HUM_prev) < TOTZONE:              # Wenn Änderung innerhalb Totzone (Hysterese)
            m_HUM_roh = m_HUM_prev                                                # Vorherigen Wert beibehalten

        m_HUM_prev = m_HUM_roh                                                    # Aktuellen Reglerwert speichern

        m_HUM_puffer.append(m_HUM_roh)                                            # Wert in Verzögerungspuffer schreiben
        m_HUM = m_HUM_puffer.pop(0)                                               # Verzögerten Reglerwert anwenden (Totzeit)

        if m_HUM <= 0:                                                            # Bei negativem Wert → Entfeuchtung
            m_ENF = -m_HUM                                                        # Entfeuchterleistung entspricht negativem Wert
            m_BFT = 0                                                             # Keine Befeuchtung
        else:                                                                     # Bei positivem Wert → Befeuchtung
            m_ENF = 0                                                             # Keine Entfeuchtung
            m_BFT = m_HUM                                                         # Befeuchterleistung = Reglerwert

        X_ZUL = X_WRG + (m_HUM * n_BFT) / m_LUF                                   # Neue Zuluft-Feuchte nach (Ent-/)Befeuchtung berechnen


# Raumdynamik
    h_ZUL = enthalpie_luft_joule_volum_feuchte(T_ZUL, X_ZUL)                     # Enthalpie der Zuluft berechnen
    h_R = enthalpie_luft_joule_volum_feuchte(T_R, X_ZUL)                         # Enthalpie im Raum (für spätere Verwendung)

    T_R += (dt / C_Raum) * (Q_IN +                                               # Temperaturänderung im Raum basierend auf:
            (m_LUF * config["physik"]["c_LUF"] * (T_ZUL - T_R)) +                #   - Wärmeeintrag durch Luftstrom
            (m_LUF * config["physik"]["r_WAS"] * (T_ZUL - T_R)))                 #   - zusätzlicher Einfluss durch Wasserdampf

    T_ABL = T_R                                                                  # Ablufttemperatur = aktuelle Raumtemperatur

    rho_luft = config["physik"]["rho_luft"]                                      # Luftdichte laden

    X_R += (m_LUF * dt) / (V_R * rho_luft) * (X_ZUL - X_R)                       # Änderung der absoluten Raumfeuchte

    X_SOL_R = relative_to_absolute_humidity(T_R, config["simulation"]["X_SOL_R"])   # Aktualisiere Soll-Feuchte basierend auf aktueller Raumtemperatur

    if t % 1 == 0:                                                                   # Ausgabe in jeder Iteration (kann z.B. auch % 10 sein)
        print(                                                                       # Konsolenausgabe der wichtigsten Zustände
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
    vis.add_data(                                                                     # Übergibt aktuelle Werte an das Visualisierungsobjekt
        t, T_SOL_R, T_R, T_ZUL, T_SOL_ZUL, T_WRG, m_ERH, m_KUL, m_LUF,
        X_R, X_SOL_R, X_SOL_ZUL, X_ZUL, m_BFT, m_ENF, wrg_on
    )
    time.sleep(dt)                                                                    # Warten um die Simulation zeitlich zu strecken

vis.plot_and_save('Ergebnis', file_format='png')                             # Abschließendes Speichern und Plotten der Ergebnisse

