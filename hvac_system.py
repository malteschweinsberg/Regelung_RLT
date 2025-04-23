from datetime import datetime
import logging
import numpy as np
from control_loops import (RoomAirTemperatureLoop, RoomAirHumidityLoop, 
                        SupplyAirTemperatureLoop, SupplyAirHumidityLoop)
from error_processors import TemperatureErrorProcessor, HumidityErrorProcessor
from fan_controllers import SupplyFanController, ExhaustFanController

logger = logging.getLogger("HVAC_Control")

class AirflowControlLoop:
    def __init__(self):
        # Initialize sub-control loops
        self.room_temp_loop = RoomAirTemperatureLoop()
        self.room_humidity_loop = RoomAirHumidityLoop()
        self.supply_temp_loop = SupplyAirTemperatureLoop()
        self.supply_humidity_loop = SupplyAirHumidityLoop()
        
        # Initialize error processors
        self.temp_error_processor = TemperatureErrorProcessor()
        self.humidity_error_processor = HumidityErrorProcessor()
        
        # Initialize fan controllers
        self.supply_fan = SupplyFanController()
        self.exhaust_fan = ExhaustFanController()
        
        # Initialize outputs
        self.outputs = {
            "supply_air_flow": 0,
            "exhaust_air_flow": 0,
            "weighted_temp_error": 0,
            "weighted_humidity_error": 0,
            "max_error": 0
        }
        
        # Initialize history for tracking
        self.history = {
            "timestamp": [],
            "room_temp": [],
            "room_humidity": [],
            "supply_temp_ref": [],
            "supply_humidity_ref": [],
            "supply_air_flow": [],
            "exhaust_air_flow": [],
            "weighted_temp_error": [],
            "weighted_humidity_error": [],
            "max_error": []
        }
        
        logger.info("Initialized Airflow Control Loop (1.4)")
    
    def process(self, room_temp, room_humidity, supply_temp_ref, supply_humidity_ref):
        timestamp = datetime.now()
        
        # Set inputs for supply air temperature loop
        self.supply_temp_loop.set_input("temp_ref_sa", supply_temp_ref)
        self.supply_temp_loop.process()
        w_1_1_1 = self.supply_temp_loop.get_output("w_1_1_1")
        
        # Set inputs for supply air humidity loop
        self.supply_humidity_loop.set_input("humidity_ref_sa", supply_humidity_ref)
        self.supply_humidity_loop.process()
        w_1_2_1 = self.supply_humidity_loop.get_output("w_1_2_1")
        
        # Set inputs for room temperature loop
        self.room_temp_loop.set_input("current_temp", room_temp)
        self.room_temp_loop.set_input("w_1_1_1", w_1_1_1)
        self.room_temp_loop.process()
        e_1_1 = self.room_temp_loop.get_output("e_1_1")
        
        # Set inputs for room humidity loop
        self.room_humidity_loop.set_input("current_humidity", room_humidity)
        self.room_humidity_loop.set_input("w_1_2_1", w_1_2_1)
        self.room_humidity_loop.process()
        e_1_2 = self.room_humidity_loop.get_output("e_1_2")
        
        # Apply weight factors to error signals
        weighted_temp_error = self.temp_error_processor.process(e_1_1)
        weighted_humidity_error = self.humidity_error_processor.process(e_1_2)
        
        # Determine maximum error (as per the MAX in section II of the diagram)
        max_error = max(weighted_temp_error, weighted_humidity_error)
        
        # Calculate fan control outputs based on the error
        base_fan_speed = 60
        error_scaling = 3  # Scaling factor for error to fan speed
        
        supply_air_flow = base_fan_speed + max_error * error_scaling
        supply_air_flow = self.supply_fan.set_speed(supply_air_flow)
        
        # In this simple model, exhaust air flow matches supply air flow
        exhaust_air_flow = self.exhaust_fan.set_speed(supply_air_flow)
        
        # Set outputs
        self.outputs["supply_air_flow"] = supply_air_flow
        self.outputs["exhaust_air_flow"] = exhaust_air_flow
        self.outputs["weighted_temp_error"] = weighted_temp_error
        self.outputs["weighted_humidity_error"] = weighted_humidity_error
        self.outputs["max_error"] = max_error
        
        # Update history
        self.history["timestamp"].append(timestamp)
        self.history["room_temp"].append(room_temp)
        self.history["room_humidity"].append(room_humidity)
        self.history["supply_temp_ref"].append(supply_temp_ref)
        self.history["supply_humidity_ref"].append(supply_humidity_ref)
        self.history["supply_air_flow"].append(supply_air_flow)
        self.history["exhaust_air_flow"].append(exhaust_air_flow)
        self.history["weighted_temp_error"].append(weighted_temp_error)
        self.history["weighted_humidity_error"].append(weighted_humidity_error)
        self.history["max_error"].append(max_error)
        
        logger.info(f"Processed: Temp={room_temp:.1f}°C, Humidity={room_humidity:.1f}g/kg, Fan={supply_air_flow}%")
        
        return self.outputs
