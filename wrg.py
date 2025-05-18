def wrg_ausgang_temp(theta_abl, theta_aussen, eta):
    return theta_aussen + eta * (theta_abl - theta_aussen)

def wrg_eta_von_drehzahl(n, n_max, eta_min, eta_max):
    return eta_min + (eta_max - eta_min) * n / n_max
