import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt  # zwingt matplotlib, das richtige GUI-Backend zu benutzen

class Visualisierung:
    def __init__(self):
        self.time = []
        self.T_R_soll = []
        self.T_R = []
        self.T_ZUL = []
        self.m_ERH = []
        self.m_KUL = []
        self.wrg_status = []

    def add_data(self, t, T_R_soll, T_R, T_ZUL, m_ERH, m_KUL, wrg_on):
        self.time.append(t)
        self.T_R_soll.append(T_R_soll)
        self.T_R.append(T_R)
        self.T_ZUL.append(T_ZUL)
        self.m_ERH.append(m_ERH)
        self.m_KUL.append(m_KUL)
        self.wrg_status.append(int(wrg_on))

    def plot(self):
        fig, axs = plt.subplots(3, 1, figsize=(10, 10))

        axs[0].plot(self.time, self.T_R, label="Ist Raumtemperatur")
        axs[0].plot(self.time, self.T_R_soll, label="Soll Raumtemperatur")
        axs[0].plot(self.time, self.T_ZUL, label="Zulfuttemperatur")
        axs[0].legend()
        axs[0].set_ylabel("Temperatur [°C]")

        axs[1].plot(self.time, self.m_ERH, label="Massenstrom Erhitzer")
        axs[1].plot(self.time, self.m_KUL, label="Massenstrom Kühler")
        axs[1].legend()
        axs[1].set_ylabel("Massenstrom [kg/s]")

        axs[2].plot(self.time, self.wrg_status, label="WRG aktiv (0/1)")
        axs[2].set_ylabel("WRG")
        axs[2].set_xlabel("Zeit [s]")
        axs[2].legend()

        plt.tight_layout()
        plt.show()
