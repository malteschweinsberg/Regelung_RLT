"""
Datei: main.py
Datum: 2025-05-03
Beschreibung:
    Startet und steuert die Simulation der RLT-Anlage.
    Initialisiert alle Module, liest die Konfiguration und verwaltet den Simulationsablauf.
"""


def main():
    # Lädt alle Konfigurationsparameter
    from config import SIMULATION, REGELUNG, ANLAGE

    # Initialisiert Regler
    pid_temp = PIController(
        Kp=REGELUNG['temp']['Kp'],
        Tn=REGELUNG['temp']['Tn'],
        limit=ANLAGE['max_massenstrom']
    )

    # Simulationsschleife
    startzeit = time.time()
    for step in range(int(SIMULATION['dauer'] / SIMULATION['zeitschritt'])):
        # Regelungsberechnung
        massenstrom = pid_temp.compute(
            setpoint=22.0,
            measured=state['temp'],
            dt=SIMULATION['zeitschritt']
        )

        # Physikalische Simulation
        state = simulation_step(state, SIMULATION['zeitschritt'])

        # Echtzeitvisualisierung
        if step % 10 == 0:  # Reduzierte Plot-Updates für Performance
            update_plots(state)

        # Beschleunigungssteuerung
        sleep_time = (SIMULATION['zeitschritt'] /
                      SIMULATION['beschleunigungsfaktor'])
        time.sleep(max(0, sleep_time - (time.time() - startzeit)))
