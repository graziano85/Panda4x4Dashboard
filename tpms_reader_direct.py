import asyncio
from bleak import BleakScanner
import aiohttp

# Mappatura sensori → ruote
SENSORS = {
    "4B:A2:00:00:01:58": "FL",
    "4B:99:00:00:62:70": "FR",
    "4B:AA:00:00:B6:72": "RL",
    "4B:9C:00:00:06:28": "RR",
}

# Service UUID dei sensori BR
TARGET_SERVICE = "000027a5-0000-1000-8000-00805f9b34fb"

# Endpoint backend
BACKEND_URL = "http://localhost:5000/update"


def decode_tpms(data: bytes):
    """
    Formato completo sensori BR (come da tua tabella):
    SS BB TT PPPP CC

    - SS = stato
    - BB = batteria (1/10 V)
    - TT = temperatura (°C)
    - PPPP = pressione assoluta (1/10 psi)
    - CC = checksum

    Formato ridotto (5 byte):
    SS FF PP TT CC
    """

    # PACCHETTO RIDOTTO (5 BYTE)
    if len(data) == 5:
        state = data[0]
        flags = data[1]
        raw_pressure = data[2]
        raw_temp = data[3]
        checksum = data[4]

        pressure_bar = raw_pressure / 50.0
        temperature_c = raw_temp / 10.0

        return {
            "pressure_bar": round(pressure_bar, 2),
            "temperature_c": round(temperature_c, 1),
            "battery": None,
            "state": state,
            "flags": flags,
            "checksum": checksum
        }

    # PACCHETTO COMPLETO (>=7 BYTE)
    if len(data) >= 7:
        state = data[0]
        raw_battery = data[1]          # 1/10 V
        raw_temp = data[2]             # °C
        raw_pressure = (data[3] << 8) | data[4]   # 1/10 psi
        checksum = data[5]

        battery_v = raw_battery / 10.0
        temperature_c = raw_temp
        pressure_psi = raw_pressure / 10.0
        pressure_bar = pressure_psi * 0.0689476

        return {
            "pressure_bar": round(pressure_bar, 2),
            "temperature_c": round(temperature_c, 1),
            "battery": round(battery_v, 1),
            "state": state,
            "flags": 0,
            "checksum": checksum
        }

    # Pacchetto sconosciuto
    return None


async def send_to_backend(sensor, decoded):
    async with aiohttp.ClientSession() as session:
        payload = {
            "sensor": sensor,
            "pressure": decoded["pressure_bar"],
            "temperature": decoded["temperature_c"],
            "battery": decoded["battery"],
            "state": decoded["state"],
            "flags": decoded["flags"]
        }
        try:
            await session.post(BACKEND_URL, json=payload)
        except Exception as e:
            print(f"[ERRORE BACKEND] {e}")


def detection_callback(device, advertisement_data):
    mac = device.address.upper()

    if mac not in SENSORS:
        return

    if TARGET_SERVICE not in advertisement_data.service_uuids:
        return

    mdata = advertisement_data.manufacturer_data
    if not mdata:
        return

    key = list(mdata.keys())[0]
    value = mdata[key]

    # DEBUG RAW
    print(f"[DEBUG] {SENSORS[mac]} RAW={value.hex()}  LEN={len(value)}")

    decoded = decode_tpms(value)
    if not decoded:
        return

    wheel = SENSORS[mac]

    # Pacchetto IDLE
    if decoded["flags"] == 1:
        print(f"[IDLE] {wheel} ignorato")
        return

    batt_str = f"{decoded['battery']}V" if decoded["battery"] is not None else "N/A"

    print(
        f"[ACTIVE] {wheel}  "
        f"P={decoded['pressure_bar']} bar  "
        f"T={decoded['temperature_c']}°C  "
        f"Batt={batt_str}"
    )

    asyncio.create_task(send_to_backend(wheel, decoded))


async def main():
    print("Scanning BLE TPMS e inviando al backend…")
    scanner = BleakScanner(detection_callback, scanning_mode="active")
    await scanner.start()
    await asyncio.sleep(999999)


if __name__ == "__main__":
    asyncio.run(main())

