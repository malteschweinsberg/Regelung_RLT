import numpy as np
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hvac_control.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HVAC_Control")

# Base class for all control loops
class ControlLoop:
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.inputs = {}
        self.outputs = {}
        self.parameters = {}
        logger.info(f"Initialized control loop: {name}")
    
    def process(self):
        raise NotImplementedError("Subclasses must implement process()")
    
    def set_parameter(self, key, value):
        self.parameters[key] = value
        
    def get_parameter(self, key):
        return self.parameters.get(key)
    
    def set_input(self, key, value):
        self.inputs[key] = value
        
    def get_output(self, key):
        return self.outputs.get(key)
    
    def apply_constraints(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))

# Room Air Temperature Control Loop (1.1)
class RoomAirTemperatureLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.1", description="Room air temperature")
        # Initialize with default parameters
        self.parameters = {
            "temp_min": 15,  # °C
            "temp_max": 24,  # °C
            "temp_target": 21  # °C
        }
        self.inputs = {
            "current_temp": 21,  # °C
            "w_1_1_1": 0  # weight factor
        }
        self.outputs = {
            "e_1_1": 0  # error signal
        }
    
    def process(self):
        # Calculate error signal based on target temperature and current temperature
        target = self.parameters["temp_target"]
        current = self.inputs["current_temp"]
        weight = self.inputs["w_1_1_1"]
        
        # Constrain current temperature to valid range
        current = self.apply_constraints(current, 
                                        self.parameters["temp_min"], 
                                        self.parameters["temp_max"])
        
        # Error calculation
        error = (target - current) * weight
        
        # Set output
        self.outputs["e_1_1"] = error
        
        return self.outputs

# Room Air Humidity Control Loop (1.2)
class RoomAirHumidityLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.2", description="Room air humidity")
        # Initialize with default parameters
        self.parameters = {
            "humidity_min": 6,  # g/kg
            "humidity_max": 12,  # g/kg
            "humidity_target": 9  # g/kg
        }
        self.inputs = {
            "current_humidity": 9,  # g/kg
            "w_1_2_1": 0  # weight factor
        }
        self.outputs = {
            "e_1_2": 0  # error signal
        }
    
    def process(self):
        # Calculate error signal based on target humidity and current humidity
        target = self.parameters["humidity_target"]
        current = self.inputs["current_humidity"]
        weight = self.inputs["w_1_2_1"]
        
        # Constrain current humidity to valid range
        current = self.apply_constraints(current, 
                                        self.parameters["humidity_min"], 
                                        self.parameters["humidity_max"])
        
        # Error calculation
        error = (target - current) * weight
        
        # Set output
        self.outputs["e_1_2"] = error
        
        return self.outputs

# Supply Air Temperature Control Loop (1.1.1)
class SupplyAirTemperatureLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.1.1", description="Supply air temperature")
        # Initialize with default parameters
        self.parameters = {
            "temp_min": 15,  # °C
            "temp_max": 24,  # °C
        }
        self.inputs = {
            "temp_ref_sa": 21  # °C, reference temperature
        }
        self.outputs = {
            "temp_sa_ref": 0,  # Processed reference temperature
            "w_1_1_1": 0  # weight factor output
        }
    
    def process(self):
        # Process reference temperature and calculate weight factor
        temp_ref = self.inputs["temp_ref_sa"]
        
        # Apply constraints based on min/max parameters
        constrained_temp = self.apply_constraints(temp_ref,
                                              self.parameters["temp_min"],
                                              self.parameters["temp_max"])
        
        # Calculate weight factor
        # For temperatures in the valid range, use full weight (1.0)
        if temp_ref >= self.parameters["temp_min"] and temp_ref <= self.parameters["temp_max"]:
            weight = 1.0
        else:
            # Calculate a reduced weight based on how far outside the range
            temp_range = self.parameters["temp_max"] - self.parameters["temp_min"]
            if temp_ref < self.parameters["temp_min"]:
                weight = 1.0 - min(1.0, (self.parameters["temp_min"] - temp_ref) / temp_range)
            else:  # temp_ref > self.parameters["temp_max"]
                weight = 1.0 - min(1.0, (temp_ref - self.parameters["temp_max"]) / temp_range)
        
        # Set outputs
        self.outputs["temp_sa_ref"] = constrained_temp
        self.outputs["w_1_1_1"] = weight
        
        return self.outputs

# Supply Air Humidity Control Loop (1.2.1)
class SupplyAirHumidityLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.2.1", description="Supply air humidity")
        # Initialize with default parameters
        self.parameters = {
            "humidity_min": 6,  # g/kg
            "humidity_max": 12,  # g/kg
        }
        self.inputs = {
            "humidity_ref_sa": 9  # g/kg, reference humidity
        }
        self.outputs = {
            "humidity_sa_ref": 0,  # Processed reference humidity
            "w_1_2_1": 0  # weight factor output
        }
    
    def process(self):
        # Process reference humidity and calculate weight factor
        humidity_ref = self.inputs["humidity_ref_sa"]
        
        # Apply constraints based on min/max parameters
        constrained_humidity = self.apply_constraints(humidity_ref,
                                                 self.parameters["humidity_min"],
                                                 self.parameters["humidity_max"])
        
        # Calculate weight factor
        if humidity_ref >= self.parameters["humidity_min"] and humidity_ref <= self.parameters["humidity_max"]:
            weight = 1.0
        else:
            humidity_range = self.parameters["humidity_max"] - self.parameters["humidity_min"]
            if humidity_ref < self.parameters["humidity_min"]:
                weight = 1.0 - min(1.0, (self.parameters["humidity_min"] - humidity_ref) / humidity_range)
            else:  # humidity_ref > self.parameters["humidity_max"]
                weight = 1.0 - min(1.0, (humidity_ref - self.parameters["humidity_max"]) / humidity_range)
        
        # Set outputs
        self.outputs["humidity_sa_ref"] = constrained_humidity
        self.outputs["w_1_2_1"] = weight
        
        return self.outputs
