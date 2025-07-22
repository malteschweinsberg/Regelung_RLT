class DiskreterPIRegler:
    def __init__(self, kp, ti, dt):
        #self.arbeitspunkt = arbeitspunkt  # Aktueller Arbeitspunkt (Raum- oder Zuluftwert vom letzten Schritt)
        self.kp = kp                     # Verstärkung aus config
        self.ti = ti                     # Nachstellzeit aus config
        self.dt = dt                     # Abtastzeit/Sampling aus config
        self.e_prev = 0.0                # Fehler beim letzten Schritt

    def update(self, arbeitspunkt, soll, ist):
        e = soll - ist
        faktor = 1 + (self.dt / self.ti)
        u = arbeitspunkt + self.kp * (e - self.e_prev+(self.dt/self.ti)*e)
        self.e_prev = e
        return u
