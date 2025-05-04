import numpy as np

def rel_feuchte_zu_abs(rel_feuchte, temp):
    sättigungsdruck = 611.2 * np.exp(17.62 * temp / (243.12 + temp))  # [Pa]
    abs_feuchte = 0.622 * (rel_feuchte/100 * sättigungsdruck) / (101325 - rel_feuchte/100 * sättigungsdruck)
    return abs_feuchte

def abs_feuchte_zu_rel(abs_feuchte, temp):
    sättigungsdruck = 611.2 * np.exp(17.62 * temp / (243.12 + temp))
    partialdruck = (abs_feuchte * 101325) / (0.622 + abs_feuchte)
    return np.clip((partialdruck / sättigungsdruck) * 100, 0, 100)

def berechne_zustand(state, dt, config, m_heiz, m_kuehl, m_befeucht):
    x_raum = rel_feuchte_zu_abs(state["rel_feuchte_raum"], state["temp_raum"])
    x_aussen = rel_feuchte_zu_abs(state["rel_feuchte_aussen"], state["temp_aussen"])

    gesamtstrom = m_heiz + m_kuehl
    dT_intern = (config["waermelast"] * dt) / (config["raumvolumen"] * config["luftdichte"] * config["c_luft"])
    if gesamtstrom < 0.01:
        return {
            "temp_raum": state["temp_raum"] + dT_intern,
            "rel_feuchte_raum": state["rel_feuchte_raum"],
            "temp_aussen": state["temp_aussen"],
            "rel_feuchte_aussen": state["rel_feuchte_aussen"],
            "massenstrom_heizung": m_heiz,
            "massenstrom_kuehler": m_kuehl,
            "massenstrom_befeuchter": m_befeucht,
            "rotor_drehzahl": 0
        }

    zuluft_temp = (m_heiz * config["heizung_temp"] + m_kuehl * config["kuehler_temp"]) / gesamtstrom

    if config["rotor_effizienz"] > 0:
        h_aussen = 1.006 * state["temp_aussen"] + x_aussen * (2501 + 1.86 * state["temp_aussen"])
        h_abluft = 1.006 * state["temp_raum"] + x_raum * (2501 + 1.86 * state["temp_raum"])
        delta_h = h_abluft - h_aussen
        if delta_h > 0:
            zuluft_temp = state["temp_aussen"] + delta_h * config["rotor_effizienz"] / 1.006
            rotor_leistung = config["rotor_effizienz"] * 100
        else:
            rotor_leistung = 0
    else:
        rotor_leistung = 0

    zuluft_feuchte = x_aussen
    if m_kuehl > 0 and config["kuehler_temp"] < 10:
        zuluft_feuchte = rel_feuchte_zu_abs(90, config["kuehler_temp"])
    if m_befeucht > 0:
        befeuchtung = m_befeucht * config["max_befeuchtung"] / 3600
        zuluft_feuchte += befeuchtung / gesamtstrom

    Q_zu = gesamtstrom * config["c_luft"] * (zuluft_temp - state["temp_raum"])
    dT = (Q_zu + config["waermelast"]) * dt / (config["raumvolumen"] * config["luftdichte"] * config["c_luft"])
    dX = gesamtstrom * (zuluft_feuchte - x_raum) * dt / (config["raumvolumen"] * config["luftdichte"])

    neue_temp = state["temp_raum"] + dT
    neues_x = x_raum + dX
    neue_rel_feuchte = abs_feuchte_zu_rel(neues_x, neue_temp)

    return {
        "temp_raum": neue_temp,
        "rel_feuchte_raum": neue_rel_feuchte,
        "temp_aussen": state["temp_aussen"],
        "rel_feuchte_aussen": state["rel_feuchte_aussen"],
        "massenstrom_heizung": m_heiz,
        "massenstrom_kuehler": m_kuehl,
        "massenstrom_befeuchter": m_befeucht,
        "rotor_drehzahl": rotor_leistung
    }
