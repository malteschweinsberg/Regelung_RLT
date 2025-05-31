class PIRegler:
    def __init__(self, kp, tn, dt):
        self.kp = kp
        self.tn = tn
        self.dt = dt
        self.integral = 0.0

    def reset(self):
        self.integral = 0.0

    def update(self, soll, ist):
        fehler = soll - ist
        self.integral += fehler * self.dt
        #if self.kp == 25:
         #   print('KP:',self.kp,'soll:',soll,'-ist:',ist,'Fehler:',fehler, 'Integral:', self.integral, 'tn:', self.tn)
        return self.kp * (fehler + self.integral / self.tn)

