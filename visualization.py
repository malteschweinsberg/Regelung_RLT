"""
Datei: visualization.py
Datum: 2025-05-03
Beschreibung:
    Stellt die kontinuierliche Visualisierung der Simulationsergebnisse bereit.
    Unterstützt Zoomfunktion und Echtzeit-Updates aller relevanten Größen.
"""


def init_plots():
    """
    Initialisiert 4 interaktive Matplotlib-Subplots
    Layout:
    - Oben: Temperaturverlauf
    - Mitte: Feuchteverlauf
    - Unten: Massenströme und Enthalpie
    """
    fig, axs = plt.subplots(4, 1, figsize=(12, 16))
    plt.subplots_adjust(hspace=0.3)
    axs[0].set_title('Raumklima-Simulation')

    # Temperaturplot
    axs[0].grid(True)
    axs[0].set_ylabel('T [°C]')
    temp_line, = axs[0].plot([], [], 'b-', label='Ist-Temperatur')

    # ... Analog für Feuchte, Massenstrom, Enthalpie ...

    plt.ion()  # Interaktiver Modus für Zoom/Scrollen
    return fig, {'temp': temp_line, ...}


def update_plots(data, plots):
    """
    Aktualisiert die Graphen mit neuen Daten
    Wird in jedem Simulationsschritt aufgerufen
    """
    plots['temp'].set_data(data['zeit'], data['temp'])
    # ... Aktualisierung aller Plots ...
    plt.pause(0.001)  # Ermöglicht Interaktion während Simulation

