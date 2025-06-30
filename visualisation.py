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
        self.m_TEP_ist = []
        self.m_LUF = []
        self.X_R = []
        self.X_Sol_R = []
        self.X_ZUL_Soll = []
        self.X_ZUL = []

    def add_data(self, t, T_R_soll, T_R, T_ZUL, T_Sol_ZUL, T_WRG_, m_TEP , m_LUF, X_R, X_Sol_R, X_ZUL_Soll, X_ZUL):
        self.time.append(t)
        self.T_R_soll.append(T_R_soll)
        self.T_R.append(T_R)
        self.T_ZUL.append(T_ZUL)
        self.T_Sol_ZUL.append(T_Sol_ZUL)
        self.T_WRG_.append(T_WRG_)
        self.m_TEP_ist.append(m_TEP)
        self.m_LUF.append(m_LUF)
        self.X_R.append(X_R)
        self.X_Sol_R.append(X_Sol_R)
        self.X_ZUL_Soll.append(X_ZUL_Soll)
        self.X_ZUL.append(X_ZUL)

    def plot(self):
        fig, axs = plt.subplots(4, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [2, 2, 2, 1]})

        # Temperaturverlauf
        axs[0].plot(self.time, self.T_R, label="Ist Raumtemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_WRG_, label="Temperatur nach WRG", linewidth=1.2)
        axs[0].plot(self.time, self.T_R_soll, label="Soll Raumtemperatur", linewidth=1.2, linestyle='--')
        axs[0].plot(self.time, self.T_ZUL, label="Zulufttemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_Sol_ZUL, label="Soll Zulufttemperatur", linewidth=1.2, linestyle='--')
        axs[0].legend(loc='upper right', fontsize=9)
        axs[0].set_ylabel("Temperatur [°C]", fontsize=12)
        axs[0].grid(True, which='both', linestyle='--', alpha=0.5)

        # Massenströme ERH/KUL
        axs[1].plot(self.time, self.m_TEP_ist, label="Massenstrom Erhitzer", linewidth=1.2)
        axs[1].legend(loc='upper right', fontsize=9)
        axs[1].set_ylabel("Massenstrom [kg/s]", fontsize=12)
        axs[1].grid(True, which='both', linestyle='--', alpha=0.5)

        # Luftfeuchte
        axs[2].step(self.time, self.X_R, label="Absolute Raumluftfeuchte", linewidth=1.2, where='post')
        axs[2].step(self.time, self.X_Sol_R, label="Absolute Soll Raumluftfeuchte", linewidth=1.2, where='post',
                    linestyle='--')
        axs[2].step(self.time, self.X_ZUL, label="Absolute Zuluftfeuchte", linewidth=1.2, where='post')
        axs[2].step(self.time, self.X_ZUL_Soll, label="Absolute Soll Zuluftfeuchte", linewidth=1.2, where='post',
                    linestyle='--')
        axs[2].set_ylabel("Luftfeuchte [g/kg]", fontsize=12)
        axs[2].legend(loc='upper right', fontsize=9)
        axs[2].grid(True, which='both', linestyle='--', alpha=0.5)

        # NEU: Luftvolumenstrom m_LUF
        axs[3].plot(self.time, self.m_LUF, label="Luftvolumenstrom", linewidth=1.2, color='tab:blue')
        axs[3].set_ylabel("Volumenstrom [m³/s]", fontsize=12)
        axs[3].set_xlabel("Zeit [s]", fontsize=12)
        axs[3].legend(loc='upper right', fontsize=9)
        axs[3].grid(True, which='both', linestyle='--', alpha=0.5)

        # Einheitliche X-Achse
        xticks = np.arange(0, max(self.time) + 1, 300)
        for ax in axs:
            ax.set_xticks(xticks)
            ax.set_xlim(0, max(self.time))

        plt.tight_layout()
        plt.show()