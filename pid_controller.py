"""
Datei: pid_controller.py
Datum: 2025-05-03
Beschreibung:
    Implementiert PI-Regler mit Anti-Windup für Temperatur- und Feuchteregelung.
    Die Reglerparameter werden über die Konfigurationsdatei eingestellt.
"""
# ... (restlicher Code)


class PIController:
    """
    PI-Regler mit Anti-Windup und Ausgangsbegrenzung
    Implementiert die Formel:
    u(t) = Kp*e(t) + Ki*∫e(t)dt
    """

    def __init__(self, Kp, Tn, limit):
        self.Kp = Kp  # Proportionalverstärkung
        self.Ki = Kp / max(Tn, 1e-9)  # Integralverstärkung
        self.integral = 0.0  # Integratorspeicher
        self.limit = limit  # Maximaler Ausgangswert

    def compute(self, setpoint, measured, dt):
        error = setpoint - measured

        # Integralberechnung mit Anti-Windup
        self.integral += error * dt
        self.integral = np.clip(self.integral, -self.limit, self.limit)

        # Reglerausgang
        output = self.Kp * error + self.Ki * self.integral
        return np.clip(output, 0, self.limit)
