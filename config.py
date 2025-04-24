"""
Datei: config.py
Datum: 2025-05-03
Beschreibung:
    Enthält alle einstellbaren Parameter und Startwerte für die Simulation.
    Hier werden Simulationsdauer, Zeitschritt, Regelparameter und technische Grenzwerte definiert.
"""
# SIMULATION: Steuerparameter für den Simulationslauf
SIMULATION = {
    "beschleunigungsfaktor": 10.0,  # 10-fache Echtzeitgeschwindigkeit
    "zeitschritt": 60,              # Physikalischer Berechnungsschritt [s]
    "dauer": 24*3600,               # Gesamtsimulationsdauer [s]
    "initial": {                    # Startbedingungen
        "temp_raum": 22.0,          # Anfangstemperatur Raum [°C]
        "feuchte_raum": 45.0        # Anfangsfeuchte Raum [%rF]
    }
}

# REGELUNG: Parameter für die PID-Regler
REGELUNG = {
    "temp": {
        "Kp": 3.0,                  # Verstärkung Temperaturregler
        "Tn": 900                   # Nachstellzeit [s] (15min)
    },
    "feuchte": {
        "Kp": 5.0,                  # Verstärkung Feuchteregler
        "Tn": 1200                  # Nachstellzeit [s] (20min)
    },
    "tote_zone": {                  # Hysterese-Bereiche
        "temp": 0.5,                # ±0.5°C Totzone
        "feuchte": 2.0              # ±2% rF Totzone
    }
}

# ANLAGE: Technische Parameter der RLT-Anlage
ANLAGE = {
    "rotor_effizienz": 0.75,        # Wirkungsgrad Wärmetauscher [0-1]
    "max_massenstrom": 2.5,         # Max. Luftdurchsatz [kg/s]
    "kuehler_temp": 7.0,            # Kühlregistertemperatur [°C]
    "heizung_temp": 45.0,           # Heizregistertemperatur [°C]
    "waermelast": 1500.0            # Interne Wärmelasten [W]
}

