import matplotlib.pyplot as plt
import numpy as np

class Visualisierung:
    def __init__(self):
        self.time = []
        self.T_R_soll = []
        self.T_R = []
        self.T_ZUL = []
        self.T_Sol_ZUL = []
        self.T_WRG_ = []
        self.m_ERH_ist = []
        self.m_KUL_ist = []
        self.wrg_status = []

    def add_data(self, t, T_R_soll, T_R, T_ZUL, T_Sol_ZUL, T_WRG_, m_ERH, m_KUL, wrg_on):
        self.time.append(t)
        self.T_R_soll.append(T_R_soll)
        self.T_R.append(T_R)
        self.T_ZUL.append(T_ZUL)
        self.T_Sol_ZUL.append(T_Sol_ZUL)
        self.T_WRG_.append(T_WRG_)
        self.m_ERH_ist.append(m_ERH)
        self.m_KUL_ist.append(m_KUL)
        self.wrg_status.append(int(wrg_on))

    def plot(self):
        fig, axs = plt.subplots(3, 1, figsize=(16, 10), sharex=True)

        # Temperaturplot
        axs[0].plot(self.time, self.T_R, label="Ist Raumtemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_WRG_, label="Temperatur nach WRG", linewidth=1.2)
        axs[0].plot(self.time, self.T_R_soll, label="Soll Raumtemperatur", linewidth=1.2, linestyle='--')
        axs[0].plot(self.time, self.T_ZUL, label="Zulufttemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_Sol_ZUL, label="Soll Zulufttemperatur", linewidth=1.2, linestyle='--')
        axs[0].legend(loc='upper right', fontsize=9)
        axs[0].set_ylabel("Temperatur [°C]", fontsize=12)
        axs[0].grid(True, which='both', linestyle='--', alpha=0.5)

        # Massenstromplot
        axs[1].plot(self.time, self.m_ERH_ist, label="Massenstrom Erhitzer", linewidth=1.2)
        axs[1].plot(self.time, self.m_KUL_ist, label="Massenstrom Kühler", linewidth=1.2)
        axs[1].legend(loc='upper right', fontsize=9)
        axs[1].set_ylabel("Massenstrom [kg/s]", fontsize=12)
        axs[1].grid(True, which='both', linestyle='--', alpha=0.5)

        # WRG-Statusplot
        axs[2].step(self.time, self.wrg_status, label="WRG aktiv (0/1)", linewidth=1.2, where='post')
        axs[2].set_ylabel("WRG", fontsize=12)
        axs[2].set_xlabel("Zeit [s]", fontsize=12)
        axs[2].set_yticks([0, 1])
        axs[2].set_ylim(-0.1, 1.1)
        axs[2].legend(loc='upper right', fontsize=9)
        axs[2].grid(True, which='both', linestyle='--', alpha=0.5)

        # X-Achse: Ticks alle 5 Minuten (300 Sekunden)
        xticks = np.arange(0, max(self.time)+1, 300)
        axs[2].set_xticks(xticks)
        axs[2].set_xlim(0, max(self.time))

        plt.tight_layout()
        plt.show()
