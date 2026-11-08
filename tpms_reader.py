import asyncio
import time
import requests
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# Mapping MAC → sigle usate dal backend
SENSORS = {
    "4B:A2:00:00:01:58": "FL",
    "4B:99:00:00:62:70": "FR",
    "4B:AA:00:00:B6:72": "RL",
    "4B:9C:00:00:06:28": "RR"
}

# Cache per smoothing
cache = {
    pos: {"pressure": None, "temperature": None, "battery": None}
    for pos in SENSORS.values()
}

BACKEND_URL = "http://127.0.0.1:5000/update"


def decode_packet(mfid, payload):
    id_low = mfid & 0xFF
    id_high = (mfid >> 8) & 0xFF

    ldata = [id_low, id_high] + list(payload)

    batt = ldata[1] / 10.0
    temp = ldata[2]
    press = ((ldata[3] * 256 + ldata[4]) - 145) / 145

    return {
        "battery": round(batt, 1),
        "temperature": round(temp, 1),
        "pressure": round(press, 2)
    }


def smooth(old, new, factor=0.3):
    if old is None:
        return new
    return round(old * (1 - factor) + new * factor, 2)


def found(device: BLEDevice, adv: AdvertisementData):
    mac = device.address.upper()
    if mac not in SENSORS:
        return

    pos = SENSORS[mac]

    if not adv.manufacturer_data:
        return

    for mfid, payload in adv.manufacturer_data.items():
        decoded = decode_packet(mfid, payload)

        # Sleep mode (0.01 bar)
        if decoded["pressure"] < 0.1:
            decoded["pressure"] = cache[pos]["pressure"]

        # Smoothing
        decoded["pressure"] = smooth(cache[pos]["pressure"], decoded["pressure"])
        decoded["temperature"] = smooth(cache[pos]["temperature"], decoded["temperature"])
        decoded["battery"] = smooth(cache[pos]["battery"], decoded["battery"])

        # Aggiorna cache
        cache[pos] = decoded

        # Invia al backend nel formato richiesto
        try:
            requests.post(BACKEND_URL, json={pos: decoded}, timeout=0.5)
        except:
            pass

        print(f"[{pos}] → {decoded}")


async def main():
    print("TPMS Reader avviato...")
    scanner = BleakScanner(detection_callback=found)
    await scanner.start()
    await asyncio.sleep(999999)
    await scanner.stop()


if __name__ == "__main__":
    asyncio.run(main())

