class PIRegler:
    def __init__(self, kp, ki, dt):
        self.kp = kp
        self.ki = ki
        self.dt = dt
        self.integral = 0.0
    def update(self, soll, ist):
        fehler = soll - ist #=6
        self.integral += fehler  # =0,1
        return self.kp * fehler + self.ki * self.integral
