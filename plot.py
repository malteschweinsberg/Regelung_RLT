import matplotlib.pyplot as plt

def plot_zeitreihen(zeit, daten, labels, titel):
    fig, axs = plt.subplots(len(daten), 1, figsize=(12, 2.5*len(daten)), sharex=True)
    for i, (reihe, label) in enumerate(zip(daten, labels)):
        axs[i].plot(zeit, reihe)
        axs[i].set_ylabel(label)
        axs[i].grid()
    axs[-1].set_xlabel("Zeit [min]")
    plt.suptitle(titel)
    plt.tight_layout()
    plt.show()
