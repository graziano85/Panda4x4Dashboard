import time
import serial


class IAW8F_KKL:
    """
    Comunicazione diretta K-Line con VAG KKL per IAW 8F.5T
    Nessun AT, nessun ELM: solo byte grezzi.
    """

    def __init__(self, port="/dev/ttyUSB0", baudrate=10400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.2
        )
        # piccolo delay per stabilizzare
        time.sleep(0.2)

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    # -------------------------
    # LOW LEVEL
    # -------------------------
    def _write_bytes(self, data: bytes):
        # debug opzionale
        # print("TX:", data.hex(" ").upper())
        self.ser.write(data)
        self.ser.flush()

    def _read_bytes(self, timeout=0.5):
        self.ser.timeout = timeout
        data = self.ser.read(64)
        # print("RX:", data.hex(" ").upper())
        return data

    # -------------------------
    # WAKEUP ECU (semplificato)
    # -------------------------
    def wakeup(self):
        """
        Wakeup semplificato: invia 0x81 0x11 0xF1 0x81
        (molte 8F rispondono già così, senza 5-baud init completo)
        """
        frame = bytes([0x81, 0x11, 0xF1, 0x81])
        self._write_bytes(frame)
        time.sleep(0.150)
        resp = self._read_bytes(0.5)
        return resp

    # -------------------------
    # INVIO RICHIESTA PID
    # -------------------------
    def _send_pid(self, pid: int):
        """
        Richiesta dati: 0x80 0x11 0xF1 0x21 PID CHK
        """
        header = [0x80, 0x11, 0xF1, 0x21, pid]
        chk = (sum(header) & 0xFF)
        frame = bytes(header + [chk])
        self._write_bytes(frame)

    def _read_frame(self):
        """
        Legge una risposta KWP2000 grezza.
        """
        data = self._read_bytes(0.5)
        if not data:
            raise RuntimeError("Nessuna risposta ECU")
        # print("RX frame:", data.hex(" ").upper())
        return data

    def _parse_pid_response(self, raw: bytes, pid: int):
        """
        Formato atteso (tipico 8F):
        LEN ECU TESTER 0x61 PID DATA... CHK
        oppure
        LEN ECU TESTER 0x21 PID DATA... CHK
        """
        if len(raw) < 6:
            raise RuntimeError(f"Risposta troppo corta: {raw.hex(' ').upper()}")

        b = list(raw)
        length = b[0]
        ecu = b[1]
        tester = b[2]
        sid = b[3]
        rpid = b[4]

        if rpid != pid:
            raise RuntimeError(f"PID inatteso: {rpid:02X} (atteso {pid:02X}), raw={raw.hex(' ').upper()}")

        data_bytes = b[5:-1]  # escludo checksum finale
        if not data_bytes:
            raise RuntimeError(f"Nessun dato per PID {pid:02X}, raw={raw.hex(' ').upper()}")

        return {
            "len": length,
            "ecu": ecu,
            "tester": tester,
            "sid": sid,
            "pid": rpid,
            "data": data_bytes,
            "raw": raw
        }

    # -------------------------
    # PID SPECIFICI
    # -------------------------
    def read_rpm(self):
        self._send_pid(0x0C)
        raw = self._read_frame()
        parsed = self._parse_pid_response(raw, 0x0C)

        # molte 8F usano A*32, altre A*50: partiamo da A*32
        A = parsed["data"][0]
        rpm = A * 32

        return {"rpm": rpm, "raw": parsed["raw"].hex(" ").upper()}

    def read_coolant_temp(self):
        self._send_pid(0x05)
        raw = self._read_frame()
        parsed = self._parse_pid_response(raw, 0x05)

        A = parsed["data"][0]
        temp = A - 40

        return {"coolant_temp": temp, "raw": parsed["raw"].hex(" ").upper()}

    def read_speed(self):
        self._send_pid(0x0D)
        raw = self._read_frame()
        parsed = self._parse_pid_response(raw, 0x0D)

        speed = parsed["data"][0]

        return {"speed": speed, "raw": parsed["raw"].hex(" ").upper()}

    def read_battery_voltage(self):
        self._send_pid(0x42)
        raw = self._read_frame()
        parsed = self._parse_pid_response(raw, 0x42)

        A = parsed["data"][0]
        B = parsed["data"][1]
        volt = (A * 256 + B) / 1000.0

        return {"battery_voltage": volt, "raw": parsed["raw"].hex(" ").upper()}

