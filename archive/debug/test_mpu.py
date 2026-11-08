from mpu6050_reader import MPU6050
import time

imu = MPU6050()

while True:
    pitch, roll = imu.get_pitch_roll()
    print("Pitch:", pitch, "Roll:", roll)
    time.sleep(0.2)

