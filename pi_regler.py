# ===================================================================
#                            PI-REGELKLASSE
#      (Einfacher diskreter Proportional-Integral-Regler in Python)
#
#  Diese Klasse stellt einen kontinuierlich arbeitenden PI-Regler dar,
#  wie er zur Regelung von Temperatur oder Feuchte in RLT-Anlagen
#  eingesetzt wird. Der Regler berechnet das Ausgangssignal basierend
#  auf dem aktuellen Regelfehler (Soll - Ist) sowie der aufsummierten
#  Regelabweichung (Integral). Dies ist eine Kernkomponente der
#  RLT-Simulation zur dynamischen Regelung der Zuluftbedingungen.
# ===================================================================
class PIRegler:  # Definition der PIRegler-Klasse

    def __init__(self, kp, ki, dt):  # Konstruktor: erhält Regelparameter
        self.kp = kp                # Proportionalverstärkung speichern
        self.ki = ki                # Integralverstärkung speichern
        self.dt = dt                # Zeitintervall (Abtastzeit) speichern
        self.integral = 0.0         # Initialisierung des Integralanteils (Startwert 0)

    def update(self, soll, ist):    # Methode zur Berechnung des Regelsignals
        fehler = soll - ist         # Differenz zwischen Soll- und Istwert berechnen (Regelabweichung)
        self.integral += fehler     # Fehler aufsummieren → Integration über die Zeit
        return self.kp * fehler + self.ki * self.integral  # PI-Regelgesetz: P-Anteil + I-Anteil