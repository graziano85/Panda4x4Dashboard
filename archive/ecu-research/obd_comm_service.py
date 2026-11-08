import time
import threading
import serial

from pid_parser_service import PIDParserService


class OBDCommunicationService:
    def __init__(self, port_path="/dev/ttyUSB0", baudrate=10400):
        self.port_path = port_path
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()

        self.responses = []
        self.is_connected = False
        self.last_activity_time = time.time()

        self.pid_parser = PIDParserService()

    # -------------------------
    # CONNESSIONE
    # -------------------------
    def connect(self):
        self._create_serial_port()

        # FIX: se la porta è già aperta, NON riaprirla
        if self.ser.is_open:
            print("⚠️ La porta era già aperta, procedo senza riaprirla.")
        else:
            try:
                self.ser.open()
            except serial.SerialException as e:
                raise RuntimeError(f"Errore apertura porta {self.port_path}: {e}")

        self.is_connected = True
        self._update_activity()

        t = threading.Thread(target=self._reader_loop, daemon=True)
        t.start()

    def _create_serial_port(self):
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass

        self.ser = serial.Serial(
            port=self.port_path,
            baudrate=self.baudrate,
            timeout=0.1,
            write_timeout=0.5
        )

    def _reader_loop(self):
        buffer = ""
        while True:
            if not self.is_connected or self.ser is None or not self.ser.is_open:
                break
            try:
                data = self.ser.read(128)
                if data:
                    text = data.decode(errors="ignore")
                    buffer += text
                    while "\r" in buffer:
                        line, buffer = buffer.split("\r", 1)
                        cleaned = line.strip()
                        if cleaned and cleaned != ">":
                            with self.lock:
                                self.responses.append(cleaned)
                            self._update_activity()
            except Exception:
                self.is_connected = False
import time
import threading
import serial

from pid_parser_service import PIDParserService


class OBDCommunicationService:
    def __init__(self, port_path="/dev/ttyUSB0", baudrate=10400):
        self.port_path = port_path
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()

        self.responses = []
        self.is_connected = False
        self.last_activity_time = time.time()

        self.pid_parser = PIDParserService()

    # -------------------------
    # CONNESSIONE
    # -------------------------
    def connect(self):
        self._create_serial_port()

        # FIX: se la porta è già aperta, NON riaprirla
        if self.ser.is_open:
            print("⚠️ La porta era già aperta, procedo senza riaprirla.")
        else:
            try:
                self.ser.open()
            except serial.SerialException as e:
                raise RuntimeError(f"Errore apertura porta {self.port_path}: {e}")

        self.is_connected = True
        self._update_activity()

        t = threading.Thread(target=self._reader_loop, daemon=True)
        t.start()

    def _create_serial_port(self):
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass

        self.ser = serial.Serial(
            port=self.port_path,
            baudrate=self.baudrate,
            timeout=0.1,
            write_timeout=0.5
        )

    def _reader_loop(self):
        buffer = ""
        while True:
            if not self.is_connected or self.ser is None or not self.ser.is_open:
                break
            try:
                data = self.ser.read(128)
                if data:
                    text = data.decode(errors="ignore")
                    buffer += text
                    while "\r" in buffer:
                        line, buffer = buffer.split("\r", 1)
                        cleaned = line.strip()
                        if cleaned and cleaned != ">":
                            with self.lock:
                                self.responses.append(cleaned)
                            self._update_activity()
            except Exception:
                self.is_connected = False
                break

    # -------------------------
    # INVIO COMANDI
    # -------------------------
    def send_command(self, cmd: str):
        if self.ser is None or not self.ser.is_open:
            raise RuntimeError("Porta seriale non aperta")

        with self.lock:
            self.responses = []

        to_send = (cmd + "\r").encode()
        self.ser.write(to_send)
        self._update_activity()

    def wait_for_response(self, timeout_ms=4000):
        start = time.time()
        timeout_s = timeout_ms / 1000.0
        last_line = None

        while (time.time() - start) < timeout_s:
            with self.lock:
                if self.responses:
                    last_line = self.responses[-1]

            if last_line:
                if "SEARCHING" not in last_line and last_line != ">":
                    self._update_activity()
                    return last_line

                if "SEARCHING" in last_line:
                    time.sleep(1.0)
                    last_line = None
                    continue

            if not self.is_connected:
                raise RuntimeError("Connessione persa durante attesa risposta")

            time.sleep(0.1)

        raise TimeoutError("Timeout - Nessuna risposta ricevuta")

    # -------------------------
    # INIZIALIZZAZIONE ELM327
    # -------------------------
    def initialize(self):
        print("Inizializzazione ELM327...")

        try:
            self.send_command("ATZ")
            _ = self.wait_for_response(4000)
            print("Reset ELM327 completato")
        except Exception as e:
            print(f"Reset ELM327 parziale: {e}")

        time.sleep(2.0)

        init_cmds = [
            ("ATE0", "Echo off"),
            ("ATL0", "Linefeeds off"),
            ("ATS0", "Spaces off"),
            ("ATSP0", "Auto protocol")
        ]

        for cmd, desc in init_cmds:
            try:
                self.send_command(cmd)
                _ = self.wait_for_response(2000)
                print(f"Comando inizializzazione eseguito: {desc}")
            except Exception as e:
                print(f"Timeout durante inizializzazione ({desc}): {e}")
            time.sleep(0.3)

        return True

    # -------------------------
    # LETTURA PID
    # -------------------------
    def read_pid(self, pid: str, name: str):
        try:
            if not self.is_connected:
                raise RuntimeError("Non connesso")

            self.send_command(pid)
            response = self.wait_for_response(5000)

            if "STOPPED" in response or "7F" in response:
                self.wakeup_ecu()
                self.send_command(pid)
                retry_response = self.wait_for_response(5000)
                return self.pid_parser.parse_response(pid, retry_response, name)

            return self.pid_parser.parse_response(pid, response, name)

        except Exception as e:
            print(f"Errore lettura PID {pid}: {e}")
            return {
                "pid": pid,
                "name": name,
                "value": None,
                "unit": "",
                "raw": str(e),
                "success": False,
                "error": True
            }

    # -------------------------
    # WAKEUP ECU
    # -------------------------
    def wakeup_ecu(self):
        try:
            self.send_command("0100")
            _ = self.wait_for_response(2000)
        except Exception:
            pass
        time.sleep(0.3)

    # -------------------------
    # INFO / UTIL
    # -------------------------
    def get_pid_definitions(self):
        return self.pid_parser.get_pid_definitions()

    def _update_activity(self):
        self.last_activity_time = time.time()

    def get_last_activity_time(self):
        return self.last_activity_time

    def disconnect(self):
        self.is_connected = False
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            except Exception as e:
                print(f"Errore chiusura porta: {e}")

