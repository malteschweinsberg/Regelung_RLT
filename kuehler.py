def kuehler_ausgang_temp(theta_ein, m_dot, theta_reg_oberflaeche, cp):
    if m_dot == 0:
        return theta_ein
    return theta_reg_oberflaeche + (theta_ein - theta_reg_oberflaeche) * 0.5  # Vereinfachtes Modell
