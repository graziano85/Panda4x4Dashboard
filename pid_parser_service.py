class PIDParserService:
    def __init__(self):
        self.pid_defs = {
            # qui metteremo i PID reali Fiat/Panda quando li avremo
            # esempio:
            # "010C": {"name": "rpm", "unit": "rpm"},
            # "0105": {"name": "coolant_temp", "unit": "°C"},
        }

    def get_pid_definitions(self):
        return self.pid_defs

    def parse_response(self, pid: str, response: str, name: str):
        # Per ora restituiamo solo la risposta grezza
        return {
            "pid": pid,
            "name": name,
            "value": None,
            "unit": "",
            "raw": response,
            "success": True,
            "error": False
        }

