import asyncio
import aiohttp
import serial
import pynmea2

GPS_PORT = "/dev/serial0"
GPS_BAUD = 9600
SERVER_URL = "http://127.0.0.1:5000/gps_data"

# Variabili globali
satellites_visible = 0
fix_quality = 0
last_altitude = None

async def main():
    global satellites_visible, fix_quality, last_altitude

    ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=1)
    print("GPS reader avviato…")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                line = ser.readline().decode("ascii", errors="ignore").strip()

                # --- SATELLITI (GPGSV) ---
                if line.startswith("$GPGSV"):
                    try:
                        msg = pynmea2.parse(line)
                        satellites_visible = msg.num_sv_in_view
                        print(f"[SATELLITI] visibili: {satellites_visible}")
                    except:
                        pass

                # --- FIX + ALTITUDINE (GPGGA) ---
                if line.startswith("$GPGGA"):
                    try:
                        msg = pynmea2.parse(line)
                        fix_quality = msg.gps_qual
                        last_altitude = getattr(msg, "altitude", None)
                        print(f"[FIX] qualità: {fix_quality}  altitudine: {last_altitude}")
                    except:
                        pass

                # --- POSIZIONE + VELOCITÀ (GPRMC) ---
                if line.startswith("$GPRMC"):
                    msg = pynmea2.parse(line)

                    lat = getattr(msg, "latitude", None)
                    lon = getattr(msg, "longitude", None)
                    speed = getattr(msg, "spd_over_grnd", 0)

                    data = {
                        "lat": lat,
                        "lon": lon,
                        "speed": speed,
                        "altitude": last_altitude,
                        "satellites": satellites_visible,
                        "fix_quality": fix_quality
                    }

                    print("[GPS]", data)

                    await session.post(SERVER_URL, json=data)

            except Exception as e:
                print("[ERRORE GPS]", e)

            await asyncio.sleep(0.1)

asyncio.run(main())

