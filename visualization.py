import matplotlib.pyplot as plt

def init_plots(config):
    plt.ion()
    fig, axs = plt.subplots(5, 1, figsize=(12, 16), sharex=True)

    axs[0].set_title('Raumtemperatur')
    temp_line, = axs[0].plot([], [], 'b-', lw=2, label='Ist-Temperatur')
    axs[0].axhline(y=config["SIMULATION"]["soll_temp"], color='r', ls='--', lw=2, label='Soll-Temperatur')
    axs[0].set_ylabel('°C')
    axs[0].set_ylim(10, 30)
    axs[0].grid(True)
    axs[0].legend(loc='upper right')

    axs[1].set_title('Relative Luftfeuchte')
    feuchte_line, = axs[1].plot([], [], 'g-', lw=2, label='Ist-Feuchte')
    axs[1].axhline(y=config["SIMULATION"]["soll_rel_feuchte"], color='m', ls='--', lw=2, label='Soll-Feuchte')
    axs[1].set_ylabel('%')
    axs[1].set_ylim(20, 80)
    axs[1].grid(True)
    axs[1].legend(loc='upper right')

    axs[2].set_title('Massenströme')
    heiz_line, = axs[2].plot([], [], 'r-', lw=2, label='Heizung')
    kuehl_line, = axs[2].plot([], [], 'b-', lw=2, label='Kühlung')
    befeucht_line, = axs[2].plot([], [], 'y-', lw=2, label='Befeuchtung')
    axs[2].set_ylabel('kg/s')
    axs[2].set_ylim(-1, 3)
    axs[2].grid(True)
    axs[2].legend(loc='upper right')

    axs[3].set_title('Rotordrehzahl')
    rotor_line, = axs[3].plot([], [], 'm-', lw=2)
    axs[3].set_ylabel('%')
    axs[3].set_ylim(-10, 110)
    axs[3].grid(True)

    axs[4].set_title('Außenbedingungen')
    aussen_temp_line, = axs[4].plot([], [], 'c-', lw=2, label='Temperatur')
    aussen_feuchte_line, = axs[4].plot([], [], 'k-', lw=2, label='Feuchte')
    axs[4].set_xlabel('Zeit [s]')
    axs[4].set_ylabel('Wert')
    axs[4].set_ylim(0, 100)
    axs[4].grid(True)
    axs[4].legend(loc='upper right')

    for ax in axs:
        ax.set_xlim(0, config["SIMULATION"]["dauer"])

    plt.tight_layout()
    plt.show(block=False)
    return fig, (temp_line, feuchte_line, heiz_line, kuehl_line, befeucht_line, rotor_line, aussen_temp_line, aussen_feuchte_line)

def update_plots(daten, lines):
    lines[0].set_data(daten["zeit"], daten["temp"])
    lines[1].set_data(daten["zeit"], daten["rel_feuchte_raum"])
    lines[2].set_data(daten["zeit"], daten["m_heiz"])
    lines[3].set_data(daten["zeit"], daten["m_kuehl"])
    lines[4].set_data(daten["zeit"], daten["m_befeucht"])
    lines[5].set_data(daten["zeit"], daten["rotor"])
    lines[6].set_data(daten["zeit"], daten["aussen_temp"])
    lines[7].set_data(daten["zeit"], daten["rel_feuchte_aussen"])

    for line in lines:
        ax = line.axes
        ax.relim()
        ax.autoscale_view(scalex=True, scaley=False)

    plt.draw()
    plt.pause(0.01)
