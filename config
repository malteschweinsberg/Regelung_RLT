import json
import os
import logging

logger = logging.getLogger("HVAC_Control")

class HVACConfig:
    def __init__(self, config_file="hvac_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                return self._get_default_config()
        else:
            logger.info(f"Configuration file {self.config_file} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self):
        return {
            "temperature": {
                "min": 15,
                "max": 24,
                "target": 21
            },
            "humidity": {
                "min": 6,
                "max": 12,
                "target": 9
            },
            "weights": {
                "temperature": 1.0,
                "humidity": 0.7
            },
            "fan_control": {
                "base_speed": 60,
                "error_scaling": 3
            }
        }
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def apply_config(self, airflow_control):
        # Apply temperature settings
        airflow_control.room_temp_loop.set_parameter("temp_min", self.config["temperature"]["min"])
        airflow_control.room_temp_loop.set_parameter("temp_max", self.config["temperature"]["max"])
        airflow_control.room_temp_loop.set_parameter("temp_target", self.config["temperature"]["target"])
        
        airflow_control.supply_temp_loop.set_parameter("temp_min", self.config["temperature"]["min"])
        airflow_control.supply_temp_loop.set_parameter("temp_max", self.config["temperature"]["max"])
        
        # Apply humidity settings
        airflow_control.room_humidity_loop.set_parameter("humidity_min", self.config["humidity"]["min"])
        airflow_control.room_humidity_loop.set_parameter("humidity_max", self.config["humidity"]["max"])
        airflow_control.room_humidity_loop.set_parameter("humidity_target", self.config["humidity"]["target"])
        
        airflow_control.supply_humidity_loop.set_parameter("humidity_min", self.config["humidity"]["min"])
        airflow_control.supply_humidity_loop.set_parameter("humidity_max", self.config["humidity"]["max"])
        
        # Apply weight factors
        airflow_control.temp_error_processor.set_weight(self.config["weights"]["temperature"])
        airflow_control.humidity_error_processor.set_weight(self.config["weights"]["humidity"])
        
        logger.info("Applied configuration to airflow control system")
