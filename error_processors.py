import logging

logger = logging.getLogger("HVAC_Control")

# Error processor for section II in the diagram
class ErrorProcessor:
    def __init__(self, name, weight_factor=1.0):
        self.name = name
        self.weight_factor = weight_factor
        logger.info(f"Initialized error processor: {name}")
    
    def process(self, error_signal):
        return error_signal * self.weight_factor
    
    def set_weight(self, weight):
        self.weight_factor = weight
        logger.info(f"Updated weight for {self.name}: {weight}")

# Specific processors
class TemperatureErrorProcessor(ErrorProcessor):
    def __init__(self, weight_factor=1.0):
        super().__init__("Temperature Error Processor", weight_factor)

class HumidityErrorProcessor(ErrorProcessor):
    def __init__(self, weight_factor=0.7):
        super().__init__("Humidity Error Processor", weight_factor)
