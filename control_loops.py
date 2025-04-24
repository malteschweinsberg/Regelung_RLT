"""
control_loops.py

Diese Datei enthält die grundlegenden Regelkreise für das HVAC-System:
- Raumlufttemperaturregelung (1.1)
- Raumluftfeuchteregelung (1.2)
- Zulufttemperaturregelung (1.1.1)
- Zuluftfeuchteregelung (1.2.1)
Jede Klasse bildet einen Regelkreis ab und verarbeitet die entsprechenden Eingangs- und Ausgangsgrößen.
"""

import numpy as np
import logging
from datetime import datetime

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hvac_control.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HVAC_Control")

# Basisklasse für alle Regelkreise
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
        # Begrenzung des Werts auf den erlaubten Bereich
        return max(min_val, min(value, max_val))

# Regelkreis für Raumlufttemperatur (1.1)
class RoomAirTemperatureLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.1", description="Room air temperature")
        self.parameters = {
            "temp_min": 15,  # °C
            "temp_max": 24,  # °C
            "temp_target": 21  # °C
        }
        self.inputs = {
            "current_temp": 21,  # °C
            "w_1_1_1": 0  # Gewichtungsfaktor
        }
        self.outputs = {
            "e_1_1": 0  # Fehlersignal
        }
    
    def process(self):
        # Fehlerberechnung basierend auf Soll- und Ist-Temperatur
        target = self.parameters["temp_target"]
        current = self.inputs["current_temp"]
        weight = self.inputs["w_1_1_1"]
        current = self.apply_constraints(current, self.parameters["temp_min"], self.parameters["temp_max"])
        error = (target - current) * weight
        self.outputs["e_1_1"] = error
        return self.outputs

# Regelkreis für Raumluftfeuchte (1.2)
class RoomAirHumidityLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.2", description="Room air humidity")
        self.parameters = {
            "humidity_min": 6,  # g/kg
            "humidity_max": 12,  # g/kg
            "humidity_target": 9  # g/kg
        }
        self.inputs = {
            "current_humidity": 9,  # g/kg
            "w_1_2_1": 0  # Gewichtungsfaktor
        }
        self.outputs = {
            "e_1_2": 0  # Fehlersignal
        }
    
    def process(self):
        # Fehlerberechnung basierend auf Soll- und Ist-Feuchte
        target = self.parameters["humidity_target"]
        current = self.inputs["current_humidity"]
        weight = self.inputs["w_1_2_1"]
        current = self.apply_constraints(current, self.parameters["humidity_min"], self.parameters["humidity_max"])
        error = (target - current) * weight
        self.outputs["e_1_2"] = error
        return self.outputs

# Regelkreis für Zulufttemperatur (1.1.1)
class SupplyAirTemperatureLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.1.1", description="Supply air temperature")
        self.parameters = {
            "temp_min": 15,  # °C
            "temp_max": 24,  # °C
        }
        self.inputs = {
            "temp_ref_sa": 21  # °C, Referenztemperatur
        }
        self.outputs = {
            "temp_sa_ref": 0,  # Verarbeitete Referenztemperatur
            "w_1_1_1": 0  # Gewichtungsfaktor-Ausgang
        }
    
    def process(self):
        # Verarbeitung der Referenztemperatur und Berechnung des Gewichtungsfaktors
        temp_ref = self.inputs["temp_ref_sa"]
        constrained_temp = self.apply_constraints(temp_ref, self.parameters["temp_min"], self.parameters["temp_max"])
        # Gewichtungsfaktor berechnen
        if temp_ref >= self.parameters["temp_min"] and temp_ref <= self.parameters["temp_max"]:
            weight = 1.0
        else:
            temp_range = self.parameters["temp_max"] - self.parameters["temp_min"]
            if temp_ref < self.parameters["temp_min"]:
                weight = 1.0 - min(1.0, (self.parameters["temp_min"] - temp_ref) / temp_range)
            else:
                weight = 1.0 - min(1.0, (temp_ref - self.parameters["temp_max"]) / temp_range)
        self.outputs["temp_sa_ref"] = constrained_temp
        self.outputs["w_1_1_1"] = weight
        return self.outputs

# Regelkreis für Zuluftfeuchte (1.2.1)
class SupplyAirHumidityLoop(ControlLoop):
    def __init__(self):
        super().__init__(name="Control Loop 1.2.1", description="Supply air humidity")
        self.parameters = {
            "humidity_min": 6,  # g/kg
            "humidity_max": 12,  # g/kg
        }
        self.inputs = {
            "humidity_ref_sa": 9  # g/kg, Referenzfeuchte
        }
        self.outputs = {
            "humidity_sa_ref": 0,  # Verarbeitete Referenzfeuchte
            "w_1_2_1": 0  # Gewichtungsfaktor-Ausgang
        }
    
    def process(self):
        # Verarbeitung der Referenzfeuchte und Berechnung des Gewichtungsfaktors
        humidity_ref = self.inputs["humidity_ref_sa"]
        constrained_humidity = self.apply_constraints(humidity_ref, self.parameters["humidity_min"], self.parameters["humidity_max"])
        if humidity_ref >= self.parameters["humidity_min"] and humidity_ref <= self.parameters["humidity_max"]:
            weight = 1.0
        else:
            humidity_range = self.parameters["humidity_max"] - self.parameters["humidity_min"]
            if humidity_ref < self.parameters["humidity_min"]:
                weight = 1.0 - min(1.0, (self.parameters["humidity_min"] - humidity_ref) / humidity_range)
            else:
                weight = 1.0 - min(1.0, (humidity_ref - self.parameters["humidity_max"]) / humidity_range)
        self.outputs["humidity_sa_ref"] = constrained_humidity
        self.outputs["w_1_2_1"] = weight
        return self.outputs
