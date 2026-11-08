import time

class KWP2000IAW8FService:
    """
    Protocollo KWP2000 Fiat per centralina IAW 8F.5T
    """

    def __init__(self, obd_comm):
        self.obd = obd_comm

    # -------------------------
    # WAKEUP ECU
    # -------------------------
    def wakeup_ecu(self):
        # Start diagnostic session: 81
        frame = "8111F181"
        self.obd.send_command(frame)
        time.sleep(0.150)

        try:
            raw = self.obd.wait_for_response(1000)
            return raw
        except:
            return None

    # -------------------------
    # INVIO RICHIESTA PID
    # -------------------------
    def _send_pid(self, pid):
        # Richiesta dati: 21 XX
        frame = f"8011F121{pid:02X}"
        self.obd.send_command(frame)

    # -------------------------
    # LETTURA RISPOSTA
    # -------------------------
    def _read_response(self):
        raw = self.obd.wait_for_response(1000)
        raw = raw.replace(" ", "").replace("\r", "").replace("\n", "")
        return raw

    # -------------------------
    # PARSER RISPOSTA 8F.5T
    # -------------------------
    def _parse(self, raw, pid):
        # Esempio risposta: 06 11 F1 21 0C 35
        if len(raw) < 10:
            raise RuntimeError(f"Risposta troppo corta: {raw}")

        # Converti in byte
        data = [int(raw[i:i+2], 16) for i in range(0, len(raw), 2)]

        sid = data[3]
        rpid = data[4]

        if sid != 0x21 or rpid != pid:
            raise RuntimeError(f"Risposta inattesa: SID={sid:02X}, PID={rpid:02X}, raw={data}")

        return data[5:]  # dati veri

    # -------------------------
    # RPM
    # -------------------------
    def read_rpm(self):
        self._send_pid(0x0C)
        raw = self._read_response()
        data = self._parse(raw, 0x0C)

        A = data[0]
        rpm = A * 32

        return {"rpm": rpm, "raw": raw}

    # -------------------------
    # TEMP ACQUA
    # -------------------------
    def read_coolant_temp(self):
        self._send_pid(0x05)
        raw = self._read_response()
        data = self._parse(raw, 0x05)

        A = data[0]
        temp = A - 40

        return {"coolant_temp": temp, "raw": raw}

    # -------------------------
    # VELOCITÀ
    # -------------------------
    def read_speed(self):
        self._send_pid(0x0D)
        raw = self._read_response()
        data = self._parse(raw, 0x0D)

        speed = data[0]

        return {"speed": speed, "raw": raw}

    # -------------------------
    # BATTERIA
    # -------------------------
    def read_battery_voltage(self):
        self._send_pid(0x42)
        raw = self._read_response()
        data = self._parse(raw, 0x42)

        A = data[0]
        B = data[1]
        volt = (A * 256 + B) / 1000.0

        return {"battery_voltage": volt, "raw": raw}

