import json
import os


class ConfigLoader:
    def __init__(self, dateipfad):
        self.dateipfad = dateipfad
        self._last_modified = 0
        self.config = self._lade_config()

    def _lade_config(self):
        try:
            with open(self.dateipfad, 'r') as f:
                config = json.load(f)
                self._last_modified = os.path.getmtime(self.dateipfad)
                return config
        except Exception as e:
            print(f"FEHLER beim Laden: {str(e)}")
            return None

    def check_and_reload(self):
        try:
            mod_time = os.path.getmtime(self.dateipfad)
            if mod_time > self._last_modified:
                self.config = self._lade_config()
                print("🔄 Konfiguration aktualisiert!")
                return True
        except Exception as e:
            print(f"Fehler beim Neuladen: {str(e)}")
        return False
