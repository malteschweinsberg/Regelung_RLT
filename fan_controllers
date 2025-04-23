import logging

logger = logging.getLogger("HVAC_Control")

# Fan controllers for section III
class FanController:
    def __init__(self, name, min_speed=0, max_speed=100):
        self.name = name
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.current_speed = 0
        logger.info(f"Initialized fan controller: {name}")
    
    def set_speed(self, speed_percent):
        constrained_speed = max(self.min_speed, min(self.max_speed, speed_percent))
        self.current_speed = constrained_speed
        logger.info(f"Set {self.name} speed to {constrained_speed}%")
        return constrained_speed
    
    def get_speed(self):
        return self.current_speed

# Specific fan controllers
class SupplyFanController(FanController):
    def __init__(self, min_speed=0, max_speed=100):
        super().__init__("Supply Fan Controller", min_speed, max_speed)

class ExhaustFanController(FanController):
    def __init__(self, min_speed=0, max_speed=100):
        super().__init__("Exhaust Fan Controller", min_speed, max_speed)
