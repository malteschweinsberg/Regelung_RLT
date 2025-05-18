# PI-Regler nach deutscher Norm, diskretisiert (Vorwärts-Rechteck)
class PIRegler:
    def __init__(self, k_p, t_n, dt):
        self.k_p = k_p
        self.t_n = t_n
        self.dt = dt
        self.i_sum = 0.0

    def reset(self):
        self.i_sum = 0.0

    def step(self, e):
        self.i_sum += e * self.dt / self.t_n
        return self.k_p * (e + self.i_sum)
