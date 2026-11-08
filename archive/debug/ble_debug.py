import asyncio
from bleak import BleakScanner

SENSORS = {
    "FL": "4B:A2:00:00:01:58",
    "FR": "4B:99:00:00:62:70",
    "RL": "4B:AA:00:00:B6:72",
    "RR": "4B:9C:00:00:06:28"
}

def callback(device, adv_data):
    mac = device.address.upper()
    for label, sensor_mac in SENSORS.items():
        if mac == sensor_mac:
            if adv_data.manufacturer_data:
                for _, data in adv_data.manufacturer_data.items():
                    print(f"\n[{label}] RAW:", list(data))

async def main():
    print("SCAN DEBUG…")
    scanner = BleakScanner(callback)
    await scanner.start()
    while True:
        await asyncio.sleep(1)

asyncio.run(main())

