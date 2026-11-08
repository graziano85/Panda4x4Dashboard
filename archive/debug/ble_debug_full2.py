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

    if mac in SENSORS.values():
        print("\n==============================")
        print(f"SENSOR {mac}")
        print("NAME:", device.name)
        print("RSSI:", adv_data.rssi)

        # Manufacturer data
        if adv_data.manufacturer_data:
            for cid, data in adv_data.manufacturer_data.items():
                print(f"MANU CID={cid} LEN={len(data)} RAW={list(data)}")

        # Service data
        if adv_data.service_data:
            for uuid, data in adv_data.service_data.items():
                print(f"SERVICE UUID={uuid} LEN={len(data)} RAW={list(data)}")

        # Service UUIDs
        if adv_data.service_uuids:
            print("SERVICE UUIDs:", adv_data.service_uuids)

async def main():
    print("FULL BLE DEBUG…")
    scanner = BleakScanner(callback)
    await scanner.start()

    while True:
        await asyncio.sleep(1)

asyncio.run(main())

