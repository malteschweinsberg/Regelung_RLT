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
        self.m_LUF = []
        self.m_BFT = []
        self.m_ENF = []
        self.WRG_state = []
        self.X_R = []
        self.X_Sol_R = []
        self.X_ZUL_Soll = []
        self.X_ZUL = []

    def add_data(self, t, T_R_soll, T_R, T_ZUL, T_Sol_ZUL, T_WRG_,
                 m_ERH, m_KUL, m_LUF, X_R, X_Sol_R, X_ZUL_Soll, X_ZUL,
                 m_BFT, m_ENF, WRG_state):
        self.time.append(t)
        self.T_R_soll.append(T_R_soll)
        self.T_R.append(T_R)
        self.T_ZUL.append(T_ZUL)
        self.T_Sol_ZUL.append(T_Sol_ZUL)
        self.T_WRG_.append(T_WRG_)
        self.m_ERH_ist.append(m_ERH)
        self.m_KUL_ist.append(m_KUL)
        self.m_LUF.append(m_LUF)
        self.X_R.append(X_R)
        self.X_Sol_R.append(X_Sol_R)
        self.X_ZUL_Soll.append(X_ZUL_Soll)
        self.X_ZUL.append(X_ZUL)
        self.m_BFT.append(m_BFT)
        self.m_ENF.append(m_ENF)
        self.WRG_state.append(1 if WRG_state else 0)

    def plot_and_save(self, filename, file_format="png"):
        fig, axs = plt.subplots(
            6, 1,
            figsize=(16, 14),
            sharex=True,
            gridspec_kw={'height_ratios': [2, 2, 2, 1, 1, 0.8]}
        )

        axs[0].plot(self.time, self.T_R, label="Ist Raumtemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_WRG_, label="Temperatur nach WRG", linewidth=1.2)
        axs[0].plot(self.time, self.T_R_soll, label="Soll Raumtemperatur", linewidth=1.2, linestyle='--')
        axs[0].plot(self.time, self.T_ZUL, label="Zulufttemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_Sol_ZUL, label="Soll Zulufttemperatur", linewidth=1.2, linestyle='--')
        axs[0].set_ylabel("Temperatur\n[°C]", fontsize=12, rotation=90)
        axs[0].yaxis.set_label_coords(-0.05, 0.5)
        axs[0].legend(loc='upper right', fontsize=9)
        axs[0].grid(True, which='both', linestyle='--', alpha=0.5)

        axs[1].plot(self.time, self.m_ERH_ist, label="Massenstrom Erhitzer", linewidth=1.2)
        axs[1].plot(self.time, self.m_KUL_ist, label="Massenstrom Kühler", linewidth=1.2)
        axs[1].set_ylabel("Massenstrom\n[kg/s]", fontsize=12, rotation=90)
        axs[1].yaxis.set_label_coords(-0.05, 0.5)
        axs[1].legend(loc='upper right', fontsize=9)
        axs[1].grid(True, which='both', linestyle='--', alpha=0.5)

        axs[2].step(self.time, self.X_R, label="Raumluftfeuchte", where='post', linewidth=1.2)
        axs[2].step(self.time, self.X_Sol_R, label="Soll Raumluftfeuchte", where='post', linewidth=1.2, linestyle='--')
        axs[2].step(self.time, self.X_ZUL, label="Zuluftfeuchte", where='post', linewidth=1.2)
        axs[2].step(self.time, self.X_ZUL_Soll, label="Soll Zuluftfeuchte", where='post', linewidth=1.2, linestyle='--')
        axs[2].set_ylabel("Feuchte\n[g/kg]", fontsize=12, rotation=90)
        axs[2].yaxis.set_label_coords(-0.05, 0.5)
        axs[2].legend(loc='upper right', fontsize=9)
        axs[2].grid(True, which='both', linestyle='--', alpha=0.5)

        axs[3].plot(self.time, self.m_LUF, label="Luftvolumenstrom", linewidth=1.2)
        axs[3].set_ylabel("Volumenstrom\n[m³/s]", fontsize=12, rotation=90)
        axs[3].yaxis.set_label_coords(-0.05, 0.5)
        axs[3].set_ylim(1, 3)
        axs[3].legend(loc='upper right', fontsize=9)
        axs[3].grid(True, which='both', linestyle='--', alpha=0.5)

        axs[4].plot(self.time, self.m_BFT, label="Massenstrom BFT", linewidth=1.2)
        axs[4].plot(self.time, self.m_ENF, label="Massenstrom ENF", linewidth=1.2, linestyle='--')
        axs[4].set_ylabel("Massenstrom\n[kg/s]", fontsize=12, rotation=90)
        axs[4].yaxis.set_label_coords(-0.05, 0.5)
        axs[4].legend(loc='upper right', fontsize=9)
        axs[4].grid(True, which='both', linestyle='--', alpha=0.5)

        axs[5].step(self.time, self.WRG_state, label="WRG Zustand", where='post', linewidth=1.2)
        axs[5].set_ylabel("WRG\n(0=Aus,1=Ein)", fontsize=12, rotation=90)
        axs[5].yaxis.set_label_coords(-0.05, 0.5)
        axs[5].set_yticks([0, 1])
        axs[5].legend(loc='upper right', fontsize=9)
        axs[5].grid(True, which='both', linestyle='--', alpha=0.5)

        # X-Achse als Zeit hh:mm für Sachsen
        xticks = np.arange(0, max(self.time) + 1, 600)
        xtick_labels = [f"{int(x // 3600):02d}:{int((x % 3600) // 60):02d}" for x in xticks]
        for ax in axs:
            ax.set_xticks(xticks)
            ax.set_xticklabels(xtick_labels, rotation=45)
            ax.set_xlim(0, max(self.time))

        fig.suptitle('Übertragungsfunktion für beide Regler', fontsize=20, y=1.02)
        plt.tight_layout()
        plt.savefig(f"{filename}.{file_format}", dpi=300, bbox_inches='tight')
        plt.close(fig)