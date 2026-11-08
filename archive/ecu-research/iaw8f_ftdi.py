from pyftdi.ftdi import Ftdi
import time

class IAW8F_FTDI:
    """
    Driver K-Line per Fiat Panda 141 (IAW 8F.5T)
    usando FT232R in modalità BITBANG.
    """

    def __init__(self, url="ftdi://ftdi:232:A10OMMJD/1"):
        self.url = url
        self.ftdi = Ftdi()

    # -------------------------
    # CONNESSIONE
    # -------------------------
    def connect(self):
        # Apre FTDI
        self.ftdi.open_from_url(self.url)

        # BITBANG MODE tramite Enum corretto
        self.ftdi.set_bitmode(0x01, Ftdi.BitMode.BITBANG)

        # Baudrate per KWP2000
        self.ftdi.set_baudrate(10400)

        time.sleep(0.1)
        self.k_high()

    def disconnect(self):
        self.k_high()
        self.ftdi.close()

    # -------------------------
    # LOW LEVEL K-LINE
    # -------------------------
    def k_low(self):
        self.ftdi.write_data(bytes([0x00]))  # D0 = 0

    def k_high(self):
        self.ftdi.write_data(bytes([0x01]))  # D0 = 1

    def read_rx(self):
        pins = self.ftdi.read_pins()
        return (pins >> 1) & 1  # RX = D1

    # -------------------------
    # 5-BAUD INIT (0x33)
    # -------------------------
    def init_5baud(self):
        byte = 0x33

        # Start bit (0)
        self.k_low()
        time.sleep(0.200)

        # 8 bit dati
        for i in range(8):
            bit = (byte >> i) & 1
            if bit:
                self.k_high()
            else:
                self.k_low()
            time.sleep(0.200)

        # Stop bit (1)
        self.k_high()
        time.sleep(0.200)

    # -------------------------
    # LETTURA KEY BYTES
    # -------------------------
    def read_key_bytes(self, timeout=1.0):
        t0 = time.time()
        buf = b""
        while time.time() - t0 < timeout:
            chunk = self.ftdi.read_data(64)
            if chunk:
                buf += chunk
            else:
                time.sleep(0.05)
        return buf

    # -------------------------
    # INVIO FRAME KWP2000
    # -------------------------
    def send_kwp(self, payload):
        frame = [0x80, 0x11, 0xF1] + payload
        chk = sum(frame) & 0xFF
        frame.append(chk)
        self.ftdi.write_data(bytes(frame))

    def read_kwp(self, timeout=0.5):
        t0 = time.time()
        buf = b""
        while time.time() - t0 < timeout:
            chunk = self.ftdi.read_data(64)
            if chunk:
                buf += chunk
            else:
                time.sleep(0.05)
        return buf

    # -------------------------
    # WAKEUP ECU
    # -------------------------
    def wakeup(self):
        self.init_5baud()
        return self.read_key_bytes()

    # -------------------------
    # LETTURA PID
    # -------------------------
    def read_pid(self, pid):
        self.send_kwp([0x21, pid])
        return self.read_kwp()

    # -------------------------
    # DECODER PID
    # -------------------------
    def decode_rpm(self, raw):
        if len(raw) < 6:
            return None
        A = raw[5]
        return A * 32

    def decode_temp(self, raw):
        if len(raw) < 6:
            return None
        A = raw[5]
        return A - 40

    def decode_speed(self, raw):
        if len(raw) < 6:
            return None
        return raw[5]

    def decode_batt(self, raw):
        if len(raw) < 7:
            return None
        A = raw[5]
        B = raw[6]
        return (A * 256 + B) / 1000.0

