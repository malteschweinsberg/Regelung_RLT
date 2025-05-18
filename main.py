import json
from pi_regler import PIRegler
from erhitzer import erhitzer_ausgang_temp
from kuehler import kuehler_ausgang_temp
from wrg import wrg_ausgang_temp, wrg_eta_von_drehzahl
from physik import volumenstrom_zu_massenstrom, kg_h_zu_kg_s
from plot import plot_zeitreihen

def lade_config():
    with open("config.json", "r") as f:
        return json.load(f)

config = lade_config()
dt = config["zeitschritt_min"] * 60 * config["simulationsfaktor"]

zeit = [0]
theta_raum = [config["raum_temp_C"]]
x_raum = [config["raum_feuchte_g_kg"]]
theta_zul = [config["raum_temp_C"]]
m_dot_erh = [0]
m_dot_kueh = [0]
n_wrg = [config["wrg_n_start"]]
theta_aussen = [config["aussen_temp_C"]]
x_aussen = [config["aussen_feuchte_g_kg"]]

regler_raum = PIRegler(3, 15*60, dt)
regler_zul = PIRegler(25, 2*60, dt)
regler_kueh = PIRegler(12, 2*60, dt)

for t in range(1, 201):  # 200 Schritte als Beispiel
    if t % 10 == 0:
        config = lade_config()

    e_raum = config["soll_raum_temp_C"] - theta_raum[-1]
    theta_zul_soll = theta_raum[-1] + regler_raum.step(e_raum)
    theta_zul_soll = max(min(theta_zul_soll, 30), 10)

    e_zul = theta_zul_soll - theta_zul[-1]
    m_erh = max(0, regler_zul.step(e_zul))
    m_kueh = max(0, -regler_kueh.step(e_zul))

    eta_wrg = wrg_eta_von_drehzahl(n_wrg[-1], config["wrg_n_max"], config["wrg_eta_min"], config["wrg_eta_max"])
    theta_wrg = wrg_ausgang_temp(theta_raum[-1], config["aussen_temp_C"], eta_wrg)

    m_dot = volumenstrom_zu_massenstrom(config["zuluft_volumenstrom_m3_h"], config["luft_dichte_kg_m3"])
    m_dot_s = kg_h_zu_kg_s(m_dot)
    theta_nach_erh = erhitzer_ausgang_temp(theta_wrg, m_erh, config["erhitzer_temp_C"], config["luft_cp_kj_kgK"])
    theta_nach_kueh = kuehler_ausgang_temp(theta_nach_erh, m_kueh, config["kuehler_temp_C"], config["luft_cp_kj_kgK"])

    cp = config["luft_cp_kj_kgK"] * 1000  # J/kgK
    V = config["raum_volumen_m3"]
    rho = config["luft_dichte_kg_m3"]
    theta_raum_neu = theta_raum[-1] + dt / (V * rho) * m_dot_s * (theta_nach_kueh - theta_raum[-1])

    zeit.append(t * config["zeitschritt_min"])
    theta_raum.append(theta_raum_neu)
    theta_zul.append(theta_nach_kueh)
    m_dot_erh.append(m_erh)
    m_dot_kueh.append(m_kueh)
    n_wrg.append(n_wrg[-1])
    theta_aussen.append(config["aussen_temp_C"])
    x_aussen.append(config["aussen_feuchte_g_kg"])
    x_raum.append(x_raum[-1])  # Feuchte noch nicht modelliert

plot_zeitreihen(
    zeit,
    [theta_aussen, x_aussen, n_wrg, theta_raum, x_raum, m_dot_erh, m_dot_kueh],
    ["Außentemperatur [°C]", "Außenfeuchte [g/kg]", "Drehzahl WRG [%]", "Raumtemperatur [°C]", "Raumfeuchte [g/kg]", "Massenstrom Erhitzer [kg/h]", "Massenstrom Kühler [kg/h]"],
    "Simulation Vollklimaanlage"
)
