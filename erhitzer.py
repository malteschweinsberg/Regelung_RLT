def erhitzer_ausgang_temp(theta_ein, m_dot, theta_reg_oberflaeche, cp):
    # Temperatur nach Erhitzer, einfache Energiebilanz
    if m_dot == 0:
        return theta_ein
    return theta_reg_oberflaeche - (theta_reg_oberflaeche - theta_ein) * 0.5  # Vereinfachtes Modell
