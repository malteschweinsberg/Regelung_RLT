"""
simulation.py

Diese Datei enthält den Simulationscode, um das HVAC-Regelungssystem zu testen.
Es werden Temperatur, Feuchte und Lüftergeschwindigkeit über die Zeit simuliert und visualisiert.
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
from hvac_system import AirflowControlLoop
from config import HVACConfig

logger = logging.getLogger("HVAC_Control")

def run_simulation(duration_minutes=60, interval_seconds=60, plot_results=True):
    # Erzeuge das Steuerungssystem
    airflow_control = AirflowControlLoop()
    # Konfiguration laden und anwenden
    config = HVACConfig()
    config.apply_config(airflow_control)
    # Zielwerte aus Konfiguration holen
    target_temp = config.config["temperature"]["target"]
    target_humidity = config.config["humidity"]["target"]
    # Anfangswerte: Raum etwas wärmer und feuchter als Ziel
    room_temp = target_temp + 2  # °C
    room_humidity = target_humidity + 1  # g/kg
    supply_temp_ref = target_temp - 1  # °C
    supply_humidity_ref = target_humidity - 0.5  # g/kg
    logger.info(f"Starting simulation: duration={duration_minutes}min, interval={interval_seconds}s")
    logger.info(f"Initial conditions: T={room_temp}°C, RH={room_humidity}g/kg")
    # Ergebnisse speichern
    times = []
    temps = []
    humidities = []
    fan_speeds = []
    # Simulation über die Zeit
    for t in range(0, duration_minutes * 60, interval_seconds):
        outputs = airflow_control.process(room_temp, room_humidity, supply_temp_ref, supply_humidity_ref)
        supply_fan_speed = outputs["supply_air_flow"]
        exhaust_fan_speed = outputs["exhaust_air_flow"]
        # Einfache Modellierung des Einflusses der Lüfter auf Raumklima
        cooling_factor = 0.01 * supply_fan_speed / 100.0
        temp_difference = room_temp - supply_temp_ref
        room_temp -= temp_difference * cooling_factor
        dehumidifying_factor = 0.008 * supply_fan_speed / 100.0
        humidity_difference = room_humidity - supply_humidity_ref
        room_humidity -= humidity_difference * dehumidifying_factor
        # Zufällige Schwankungen hinzufügen
        room_temp += np.random.normal(0, 0.1)
        room_humidity += np.random.normal(0, 0.05)
        # Ergebnisse speichern
        times.append(t / 60.0)
        temps.append(room_temp)
        humidities.append(room_humidity)
        fan_speeds.append(supply_fan_speed)
    logger.info(f"Simulation complete. Final T={room_temp:.2f}°C, RH={room_humidity:.2f}g/kg")
    # Ergebnisse plotten
    if plot_results:
        plt.figure(figsize=(12, 8))
        plt.subplot(3, 1, 1)
        plt.plot(times, temps, 'r-', label='Room Temperature')
        plt.axhline(y=target_temp, color='r', linestyle='--', label='Target Temperature')
        plt.ylabel('Temperature (°C)')
        plt.title('HVAC System Simulation Results')
        plt.legend()
        plt.subplot(3, 1, 2)
        plt.plot(times, humidities, 'b-', label='Room Humidity')
        plt.axhline(y=target_humidity, color='b', linestyle='--', label='Target Humidity')
        plt.ylabel('Humidity (g/kg)')
        plt.legend()
        plt.subplot(3, 1, 3)
        plt.plot(times, fan_speeds, 'g-', label='Fan Speed')
        plt.xlabel('Time (minutes)')
        plt.ylabel('Fan Speed (%)')
        plt.legend()
        plt.tight_layout()
        plt.savefig('simulation_results.png')
        plt.show()
        logger.info("Simulation results plotted and saved to simulation_results.png")
    return {
        'times': times,
        'temperatures': temps,
        'humidities': humidities,
        'fan_speeds': fan_speeds
    }
