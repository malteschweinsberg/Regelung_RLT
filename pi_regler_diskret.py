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
        if self.kp == 0.03:
             print('arbeitspunkt:', round(arbeitspunkt,2), '+ kp:',round(self.kp,2), '*(e:',round(e,2), '-e_prev:', round(self.e_prev,2), '+dt:', round(self.dt,2), '/ti:', round(self.ti,2), '*e:', round(e,2))
            #print('arbeitspunkt:', arbeitspunkt, '+ kp:', self.kp, 'diff_fehler:', e - self.e_prev, 'dt/ti*e',(self.dt / self.ti) * e, 'kp*()', self.kp * (e - self.e_prev + (self.dt / self.ti) * e), 'u',arbeitspunkt + self.kp * (e - self.e_prev + (self.dt / self.ti) * e), 'ist:', ist, 'soll', soll)
        self.e_prev = e

        return u
