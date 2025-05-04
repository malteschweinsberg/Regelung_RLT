import matplotlib.pyplot as plt
import time
from config_loader import ConfigLoader
from pid_controller import PIController
from simulation import berechne_zustand, rel_feuchte_zu_abs
from visualization import init_plots, update_plots

def main():
    print("RLT-Simulation startet...")
    config_loader = ConfigLoader("config.json")
    config = config_loader.config

    state = {
        "temp_raum": config["SIMULATION"]["initial"]["temp_raum"],
        "rel_feuchte_raum": config["SIMULATION"]["initial"]["rel_feuchte_raum"],
        "temp_aussen": config["SIMULATION"]["initial"]["temp_aussen"],
        "rel_feuchte_aussen": config["SIMULATION"]["initial"]["rel_feuchte_aussen"]
    }

    temp_pid = PIController(
        config["REGELUNG"]["temp"]["Kp"],
        config["REGELUNG"]["temp"]["Ti"],
        config["REGELUNG"]["temp"]["Td"],
        0,
        config["ANLAGE"]["max_massenstrom"],
        config["REGELUNG"]["temp"]["deadband"]
    )
    feuchte_pid = PIController(
        config["REGELUNG"]["feuchte"]["Kp"],
        config["REGELUNG"]["feuchte"]["Ti"],
        config["REGELUNG"]["feuchte"]["Td"],
        0,
        config["ANLAGE"]["max_befeuchtung"],
        config["REGELUNG"]["feuchte"]["deadband"]
    )

    daten = {
        "zeit": [0],
        "temp": [state["temp_raum"]],
        "rel_feuchte_raum": [state["rel_feuchte_raum"]],
        "m_heiz": [0],
        "m_kuehl": [0],
        "m_befeucht": [0],
        "rotor": [0],
        "aussen_temp": [state["temp_aussen"]],
        "rel_feuchte_aussen": [state["rel_feuchte_aussen"]]
    }

    fig, lines = init_plots(config)

    try:
        simulations_zeit = 0
        print("Simulation läuft... (Strg+C zum Beenden)")
        while simulations_zeit < config["SIMULATION"]["dauer"]:
            if config_loader.check_and_reload():
                config = config_loader.config
                print(f"Neue Sollwerte: T={config['SIMULATION']['soll_temp']}°C, rF={config['SIMULATION']['soll_rel_feuchte']}%")
                temp_pid = PIController(
                    config["REGELUNG"]["temp"]["Kp"],
                    config["REGELUNG"]["temp"]["Ti"],
                    config["REGELUNG"]["temp"]["Td"],
                    0,
                    config["ANLAGE"]["max_massenstrom"],
                    config["REGELUNG"]["temp"]["deadband"]
                )
                feuchte_pid = PIController(
                    config["REGELUNG"]["feuchte"]["Kp"],
                    config["REGELUNG"]["feuchte"]["Ti"],
                    config["REGELUNG"]["feuchte"]["Td"],
                    0,
                    config["ANLAGE"]["max_befeuchtung"],
                    config["REGELUNG"]["feuchte"]["deadband"]
                )

            temp_diff = config["SIMULATION"]["soll_temp"] - state["temp_raum"]
            if temp_diff > 0:
                m_heiz = temp_pid.compute(
                    config["SIMULATION"]["soll_temp"],
                    state["temp_raum"],
                    config["SIMULATION"]["zeitschritt"]
                )
                m_kuehl = 0
            else:
                m_kuehl = temp_pid.compute(
                    state["temp_raum"],
                    config["SIMULATION"]["soll_temp"],
                    config["SIMULATION"]["zeitschritt"]
                )
                m_heiz = 0

            feuchte_diff = config["SIMULATION"]["soll_rel_feuchte"] - state["rel_feuchte_raum"]
            if abs(feuchte_diff) <= config["REGELUNG"]["feuchte"]["deadband"]:
                m_befeucht = 0
            elif feuchte_diff > 0:
                m_befeucht = feuchte_pid.compute(
                    config["SIMULATION"]["soll_rel_feuchte"],
                    state["rel_feuchte_raum"],
                    config["SIMULATION"]["zeitschritt"]
                )
            else:
                m_befeucht = 0
                if m_kuehl < 0.1 and temp_diff < 0:
                    m_kuehl = 0.2

            state = berechne_zustand(
                state,
                config["SIMULATION"]["zeitschritt"],
                config["ANLAGE"],
                m_heiz,
                m_kuehl,
                m_befeucht
            )

            simulations_zeit += config["SIMULATION"]["zeitschritt"]
            daten["zeit"].append(simulations_zeit)
            daten["temp"].append(state["temp_raum"])
            daten["rel_feuchte_raum"].append(state["rel_feuchte_raum"])
            daten["m_heiz"].append(m_heiz)
            daten["m_kuehl"].append(m_kuehl)
            daten["m_befeucht"].append(m_befeucht)
            daten["rotor"].append(state["rotor_drehzahl"])
            daten["aussen_temp"].append(state["temp_aussen"])
            daten["rel_feuchte_aussen"].append(state["rel_feuchte_aussen"])

            update_plots(daten, lines)
            plt.pause(config["SIMULATION"]["zeitschritt"]/config["SIMULATION"]["beschleunigungsfaktor"])

    except KeyboardInterrupt:
        print("\nSimulation manuell gestoppt")
    except Exception as e:
        print(f"\nKritischer Fehler: {str(e)}")

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()
