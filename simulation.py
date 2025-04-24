"""
Datei: main.py
Datum: 2025-05-03
Beschreibung:
    Startet und steuert die Simulation der RLT-Anlage.
    Initialisiert alle Module, liest die Konfiguration und verwaltet den Simulationsablauf.
"""


def berechne_zustand(prev, dt, config):
    """
    Berechnet den neuen Raumzustand mittels Euler-Integration
    Args:
        prev: Vorheriger Zustand (Temperatur, Feuchte)
        dt: Zeitschritt [s]
        config: Konfigurationsparameter

    Returns:
        new_temp: Neue Raumtemperatur [°C]
        new_feuchte: Neue Raumfeuchte [%rF]
    """

    # Wärmebilanzgleichung
    Q_heizung = ANLAGE['heizung_temp'] * massenstrom_heizung
    Q_kuehlung = ANLAGE['kuehler_temp'] * massenstrom_kuehler
    dT = ((Q_heizung - Q_kuehler + config.ANLAGE['waermelast'])
          / (m_luft * c_luft)) * dt  # Euler-Integration

    # Feuchtebilanz mit Rotorwirkung
    rotor_feuchte = berechne_rotorwirkung(...)  # Siehe unten
    dh = ((m_befeuchter + rotor_feuchte - m_entfeuchter)
          / V_raum) * dt

    return new_temp, new_feuchte


def enthalpie_berechnung(temp, feuchte):
    """
    Berechnet die spezifische Enthalpie nach:
    h = 1.006*T + x*(2501 + 1.86*T) [kJ/kg]
    mit x = absolute Feuchte [kg/kg]
    """
    x = feuchte_absolut(feuchte, temp)
    return 1.006 * temp + x * (2501 + 1.86 * temp)


def berechne_rotorwirkung(aussen, abluft, soll, effizienz):
    """
    Modelliert den Rotationswärmetauscher nach dem ε-NTU-Ansatz
    Returns:
        Feuchteänderung durch Rotor [kg/s]
    """
    h_aussen = enthalpie_berechnung(aussen.temp, aussen.feuchte)
    h_abluft = enthalpie_berechnung(abluft.temp, abluft.feuchte)
    h_soll = enthalpie_berechnung(soll.temp, soll.feuchte)

    # MIN-Logik aus Regelkreis 1.3
    h_diff = min(abs(h_aussen - h_soll), abs(h_abluft - h_soll))

    return effizienz * h_diff * massenstrom
