class PIRegler:
    def __init__(self, kp, ki, dt, integrator_min=None, integrator_max=None):
        self.kp = kp
        self.ki = ki
        self.dt = dt
        self.integral = 0.0
        self.integrator_min = integrator_min
        self.integrator_max = integrator_max

    def reset(self):
        self.integral = 0.0

    def update(self, soll, ist):
        fehler = soll - ist #=6
        self.integral += fehler  # =0,1
        #print('pro', self.kp * fehler, 'Int', self.ki * self.integral)
        return self.kp * fehler + self.ki * self.integral
