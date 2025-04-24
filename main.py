"""
main.py

Dies ist der Einstiegspunkt für das HVAC-Projekt.
Hier wird die Simulation gestartet und die Programmausführung gesteuert.
"""

import logging
import argparse
from simulation import run_simulation
from hvac_system import AirflowControlLoop
from config import HVACConfig

def main():
    # Argumentparser für Kommandozeilenoptionen
    parser = argparse.ArgumentParser(description='HVAC Control System Simulation')
    parser.add_argument('--duration', type=int, default=60, help='Simulation duration in minutes')
    parser.add_argument('--interval', type=int, default=60, help='Simulation interval in seconds')
    parser.add_argument('--no-plot', action='store_true', help='Disable plotting of results')
    args = parser.parse_args()
    # Simulation starten
    results = run_simulation(
        duration_minutes=args.duration,
        interval_seconds=args.interval,
        plot_results=not args.no_plot
    )
    print("Simulation completed successfully")

if __name__ == "__main__":
    main()
