# ===================================================================
#                        VISUALISIERUNGSKLASSE
#       (Grafische Darstellung der Zustände und Regelsignale)
#
#  Diese Klasse sammelt Zeitreihen-Daten während der Simulation und
#  erzeugt nach Abschluss der Simulation eine anschauliche
#  Mehrfachgrafik mit Temperatur-, Feuchte-, Massenstrom- und
#  WRG-Zuständen. Die Ausgabe erfolgt als PNG-Datei.
# ===================================================================

import matplotlib.pyplot as plt        # Import der Plot-Bibliothek matplotlib
import numpy as np                    # Import der numerischen Bibliothek NumPy

class Visualisierung:                 # Definition der Klasse zur Datensammlung und Visualisierung

    def __init__(self):               # Konstruktor: Initialisiert alle Listen zur Datenspeicherung
        self.time = []                # Zeitstempel [s]
        self.T_R_soll = []            # Soll-Raumtemperatur [°C]
        self.T_R = []                 # Ist-Raumtemperatur [°C]
        self.T_ZUL = []               # Zulufttemperatur [°C]
        self.T_Sol_ZUL = []           # Soll-Zulufttemperatur [°C]
        self.T_WRG_ = []              # Temperatur nach Wärmerückgewinnung [°C]
        self.m_ERH_ist = []           # Massenstrom Erhitzer [kg/s]
        self.m_KUL_ist = []           # Massenstrom Kühler [kg/s]
        self.m_LUF = []               # Luftvolumenstrom [m³/s]
        self.m_BFT = []               # Massenstrom Befeuchter [kg/s]
        self.m_ENF = []               # Massenstrom Entfeuchter [kg/s]
        self.WRG_state = []           # Zustand Wärmerückgewinnung (0 oder 1)
        self.X_R = []                 # Raumfeuchte (absolut) [kg/m³]
        self.X_Sol_R = []             # Soll-Raumfeuchte [kg/m³]
        self.X_ZUL_Soll = []          # Soll-Zuluftfeuchte [kg/m³]
        self.X_ZUL = []               # Ist-Zuluftfeuchte [kg/m³]

    def add_data(self, t, T_R_soll, T_R, T_ZUL, T_Sol_ZUL, T_WRG_,
                 m_ERH, m_KUL, m_LUF, X_R, X_Sol_R, X_ZUL_Soll, X_ZUL,
                 m_BFT, m_ENF, WRG_state):
        self.time.append(t)                              # Zeitwert hinzufügen
        self.T_R_soll.append(T_R_soll)                   # Soll-Raumtemperatur
        self.T_R.append(T_R)                             # Ist-Raumtemperatur
        self.T_ZUL.append(T_ZUL)                         # Zulufttemperatur
        self.T_Sol_ZUL.append(T_Sol_ZUL)                 # Soll-Zulufttemperatur
        self.T_WRG_.append(T_WRG_)                       # WRG-Temperatur
        self.m_ERH_ist.append(m_ERH)                     # Erhitzer-Massenstrom
        self.m_KUL_ist.append(m_KUL)                     # Kühler-Massenstrom
        self.m_LUF.append(m_LUF)                         # Luftstrom
        self.X_R.append(X_R)                             # Raumfeuchte
        self.X_Sol_R.append(X_Sol_R)                     # Soll-Raumfeuchte
        self.X_ZUL_Soll.append(X_ZUL_Soll)               # Soll-Zuluftfeuchte
        self.X_ZUL.append(X_ZUL)                         # Ist-Zuluftfeuchte
        self.m_BFT.append(m_BFT)                         # Befeuchterstrom
        self.m_ENF.append(m_ENF)                         # Entfeuchterstrom
        self.WRG_state.append(1 if WRG_state else 0)     # WRG-Zustand binär (True → 1, False → 0)

    def plot_and_save(self, filename, file_format="png"):   # Methode zur Erstellung und Speicherung des Plots
        fig, axs = plt.subplots(                           # 6 Unterdiagramme übereinander
            6, 1,
            figsize=(16, 12),
            sharex=True,
            gridspec_kw={'height_ratios': [2, 2, 2, 1, 1, 0.8]}
        )

        # --- Temperaturverlauf ---
        axs[0].plot(self.time, self.T_R, label="Ist Raumtemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_WRG_, label="Temperatur nach WRG", linewidth=1.2)
        axs[0].plot(self.time, self.T_R_soll, label="Soll Raumtemperatur", linewidth=1.2, linestyle='--')
        axs[0].plot(self.time, self.T_ZUL, label="Zulufttemperatur", linewidth=1.2)
        axs[0].plot(self.time, self.T_Sol_ZUL, label="Soll Zulufttemperatur", linewidth=1.2, linestyle='--')
        axs[0].set_ylabel("Temperatur\n[°C]", fontsize=12, rotation=90)
        axs[0].yaxis.set_label_coords(-0.05, 0.5)
        axs[0].legend(loc='upper right', fontsize=9)
        axs[0].grid(True, which='both', linestyle='--', alpha=0.5)

        # --- Heiz-/Kühlmassenströme ---
        axs[1].plot(self.time, self.m_ERH_ist, label="Massenstrom Erhitzer", linewidth=1.2)
        axs[1].plot(self.time, self.m_KUL_ist, label="Massenstrom Kühler", linewidth=1.2)
        axs[1].set_ylabel("Massenstrom\n[kg/s]", fontsize=12, rotation=90)
        axs[1].yaxis.set_label_coords(-0.05, 0.5)
        axs[1].legend(loc='upper right', fontsize=9)
        axs[1].grid(True, which='both', linestyle='--', alpha=0.5)

        # --- Feuchteverläufe ---
        axs[2].step(self.time, self.X_R, label="Raumluftfeuchte", where='post', linewidth=1.2)
        axs[2].step(self.time, self.X_Sol_R, label="Soll Raumluftfeuchte", where='post', linewidth=1.2, linestyle='--')
        axs[2].step(self.time, self.X_ZUL, label="Zuluftfeuchte", where='post', linewidth=1.2)
        axs[2].step(self.time, self.X_ZUL_Soll, label="Soll Zuluftfeuchte", where='post', linewidth=1.2, linestyle='--')
        axs[2].set_ylabel("Feuchte\n[kg/m³]", fontsize=12, rotation=90)
        axs[2].yaxis.set_label_coords(-0.05, 0.5)
        axs[2].legend(loc='upper right', fontsize=9)
        axs[2].grid(True, which='both', linestyle='--', alpha=0.5)

        # --- Luftvolumenstrom ---
        axs[3].plot(self.time, self.m_LUF, label="Luftvolumenstrom", linewidth=1.2)
        axs[3].set_ylabel("Volumenstrom\n[m³/s]", fontsize=12, rotation=90)
        axs[3].yaxis.set_label_coords(-0.05, 0.5)
        axs[3].set_ylim(0, 11)
        axs[3].legend(loc='upper right', fontsize=9)
        axs[3].grid(True, which='both', linestyle='--', alpha=0.5)

        # --- Befeuchtung & Entfeuchtung ---
        axs[4].plot(self.time, self.m_BFT, label="Massenstrom BFT", linewidth=1.2)
        axs[4].plot(self.time, self.m_ENF, label="Massenstrom ENF", linewidth=1.2, linestyle='--')
        axs[4].set_ylabel("Massenstrom\n[kg/s]", fontsize=12, rotation=90)
        axs[4].yaxis.set_label_coords(-0.05, 0.5)
        axs[4].legend(loc='upper right', fontsize=9)
        axs[4].grid(True, which='both', linestyle='--', alpha=0.5)

        # --- WRG-Zustand (0 = aus, 1 = ein) ---
        axs[5].step(self.time, self.WRG_state, label="WRG Zustand", where='post', linewidth=1.2)
        axs[5].set_ylabel("WRG\n(0=Aus,1=Ein)", fontsize=12, rotation=90)
        axs[5].yaxis.set_label_coords(-0.05, 0.5)
        axs[5].set_yticks([0, 1])
        axs[5].legend(loc='upper right', fontsize=9)
        axs[5].grid(True, which='both', linestyle='--', alpha=0.5)

        # --- Zeitbeschriftung auf X-Achse in Stunden:Minuten ---
        xticks = np.arange(0, max(self.time) + 1, 600)  # alle 10 Minuten
        xtick_labels = [f"{int(x // 3600):02d}:{int((x % 3600) // 60):02d}" for x in xticks]
        for ax in axs:
            ax.set_xticks(xticks)
            ax.set_xticklabels(xtick_labels, rotation=45)
            ax.set_xlim(0, max(self.time))

        fig.suptitle('PI-Regler', fontsize=20, y=0.98)           # Haupttitel
        plt.tight_layout()                                       # Layout-Anpassung
        plt.savefig(f"{filename}.{file_format}", dpi=300, bbox_inches='tight')  # Speichern der Grafik
        plt.close(fig)                                           # Fenster schließen
