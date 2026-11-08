import serial
import json
import time

PORT = "/dev/arduino"
BAUD = 115200

latest_data = {}

def get_latest_data():
    return latest_data

def main():
    global latest_data

    while True:
        try:
            print(f"[ECU] Connessione su {PORT}...")
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print("[ECU] Porta aperta, in ascolto...")

            while True:
                line = ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        latest_data.update(data)
                        print("[ECU]", data)
                    except json.JSONDecodeError:
                        print("[ECU] JSON corrotto:", line)

        except serial.SerialException:
            print("[ECU] Arduino disconnesso, riconnessione...")
            time.sleep(1)
        except Exception as e:
            print("[ECU] Errore:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()

