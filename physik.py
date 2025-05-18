def volumenstrom_zu_massenstrom(volumenstrom_m3h, dichte):
    return volumenstrom_m3h / 3.6 * dichte  # m³/h → kg/h

def kg_h_zu_kg_s(kg_h):
    return kg_h / 3600
