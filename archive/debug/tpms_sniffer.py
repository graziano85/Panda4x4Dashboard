import asyncio
from bleak import BleakScanner

TARGET_MACS = {
    "FL": "4B:A2:00:00:01:58",
    "FR": "4B:99:00:00:62:70",
    "RL": "4B:AA:00:00:B6:72",
    "RR": "4B:9C:00:00:06:28"
}

def dump_packet(name, mac, advertisement_data):
    print(f"\n[{name}] Packet from {mac}")

    # Stampa TUTTI i manufacturer data
    for m_id, m_data in advertisement_data.manufacturer_data.items():
        print(f"  Manufacturer ID: {hex(m_id)}")
        print(f"  RAW HEX: {m_data.hex().upper()}")
        print(f"  RAW BYTES: {list(m_data)}")

async def scan():
    print("Scanning BLE packets...\n")

    def callback(device, advertisement_data):
        mac = device.address.upper()

        for name, target_mac in TARGET_MACS.items():
            if mac == target_mac:
                dump_packet(name, mac, advertisement_data)

    scanner = BleakScanner(callback)
    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()

asyncio.run(scan())

