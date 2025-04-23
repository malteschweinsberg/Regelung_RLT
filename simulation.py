import numpy as np
import matplotlib.pyplot as plt
import logging
from hvac_system import AirflowControlLoop
from config import HVACConfig

logger = logging.getLogger("HVAC_Control")

def run_simulation(duration_minutes=60, interval_seconds=60, plot_results=True):
    # Create the airflow control system
    airflow_control = AirflowControlLoop()
    
    # Load and apply configuration
    config = HVACConfig()
    config.apply_config(airflow_control)
    
    # Get target values from config
    target_temp = config.config["temperature"]["target"]
    target_humidity = config.config["humidity"]["target"]
    
    # Initial conditions: room slightly warmer than target
    room_temp = target_temp + 2  # °C
    room_humidity = target_humidity + 1  # g/kg
    
    # Supply air references
    supply_temp_ref = target_temp - 1  # °C (cooler than target to cool the room)
    supply_humidity_ref = target_humidity - 0.5  # g/kg (drier than target to dehumidify)
    
    logger.info(f"Starting simulation: duration={duration_minutes}min, interval={interval_seconds}s")
    logger.info(f"Initial conditions: T={room_temp}°C, RH={room_humidity}g/kg")
    
    # Simulation results
    times = []
    temps = []
    humidities = []
    fan_speeds = []
    
    # Simulate the system over time
    for t in range(0, duration_minutes * 60, interval_seconds):
        # Process the control loop
        outputs = airflow_control.process(room_temp, room_humidity, supply_temp_ref, supply_humidity_ref)
        
        # Get fan speeds
        supply_fan_speed = outputs["supply_air_flow"]
        exhaust_fan_speed = outputs["exhaust_air_flow"]
        
        # Simulate the effect on the room (simple model)
        cooling_factor = 0.01 * supply_fan_speed / 100.0
        temp_difference = room_temp - supply_temp_ref
        room_temp -= temp_difference * cooling_factor
        
        dehumidifying_factor = 0.008 * supply_fan_speed / 100.0
        humidity_difference = room_humidity - supply_humidity_ref
        room_humidity -= humidity_difference * dehumidifying_factor
        
        # Add some random variation
        room_temp += np.random.normal(0, 0.1)
        room_humidity += np.random.normal(0, 0.05)
        
        # Store results
        times.append(t / 60.0)  # convert to minutes
        temps.append(room_temp)
        humidities.append(room_humidity)
        fan_speeds.append(supply_fan_speed)
    
    logger.info(f"Simulation complete. Final T={room_temp:.2f}°C, RH={room_humidity:.2f}g/kg")
    
    # Plotting
    if plot_results:
        plt.figure(figsize=(12, 8))
        
        # Temperature subplot
        plt.subplot(3, 1, 1)
        plt.plot(times, temps, 'r-', label='Room Temperature')
        plt.axhline(y=target_temp, color='r', linestyle='--', label='Target Temperature')
        plt.ylabel('Temperature (°C)')
        plt.title('HVAC System Simulation Results')
        plt.legend()
        
        # Humidity subplot
        plt.subplot(3, 1, 2)
        plt.plot(times, humidities, 'b-', label='Room Humidity')
        plt.axhline(y=target_humidity, color='b', linestyle='--', label='Target Humidity')
        plt.ylabel('Humidity (g/kg)')
        plt.legend()
        
        # Fan speed subplot
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
