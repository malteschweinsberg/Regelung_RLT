# ===================================================================
#                       DISKRETER PI-REGELER
#      (Zur Regelung von Temperatur und Feuchte in der RLT-Simulation)
#
#  Diese Klasse implementiert einen einfach diskretisierten PI-Regler
#  auf Basis der Tustin-Methode. Sie eignet sich für zeitdiskrete
#  Simulationen, bei denen der Regler in festen Zeitschritten arbeitet.
#  Eingesetzt wird er u.a. für die Regelung von Zulufttemperatur und
#  -feuchte, wobei sich das Regelsignal dynamisch an Raumzustände anpasst.
# ===================================================================

class DiskreterPIRegler:
    def __init__(self, kp, ti, dt):
        # self.arbeitspunkt = arbeitspunkt           # (Optional) Arbeitspunkt kann genutzt werden für statische Basisregelgröße
        self.kp = kp                                 # Proportionalverstärkung (Kp) aus config
        self.ti = ti                                 # Integrationszeit (Ti) für den I-Anteil des Reglers
        self.dt = dt                                 # Abtastzeit (Zeitschrittweite dt) der Simulation
        self.e_prev = 0.0                            # Fehlerwert aus vorherigem Zeitschritt (für Differenzbildung nötig)

    def update(self, arbeitspunkt, soll, ist):
        e = soll - ist                               # Aktueller Regelfehler berechnen (Sollwert - Istwert)
        u = arbeitspunkt + self.kp * (               # Berechnung der Stellgröße u (neuer Ausgangswert):
            e - self.e_prev +                        #   Differenz zum vorherigen Fehler (Differenzanteil)
            (self.dt / self.ti) * e                  #   plus Anteil für die Integration über die Zeit (I-Anteil)
        )
        self.e_prev = e                              # Speichern des aktuellen Fehlers für den nächsten Schritt
        return u                                      # Rückgabe der berechneten Stellgröße (z.B. neue Solltemperatur)
