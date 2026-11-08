import smbus
import math
import time

class MPU6050:
    def __init__(self, address=0x68):
        self.bus = smbus.SMBus(1)
        self.address = address

        # Wake up MPU6050
        self.bus.write_byte_data(self.address, 0x6B, 0)

    def read_word(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg + 1)
        val = (high << 8) + low
        if val >= 0x8000:
            val = -((65535 - val) + 1)
        return val

    def get_pitch_roll(self):
        acc_x = self.read_word(0x3B)
        acc_y = self.read_word(0x3D)
        acc_z = self.read_word(0x3F)

        ax = acc_x / 16384.0
        ay = acc_y / 16384.0
        az = acc_z / 16384.0

        pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
        roll  = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))

        return round(pitch, 2), round(roll, 2)

