from flask import Flask, request, jsonify, render_template
from external_temp import read_external_temperature
import lgpio
from mpu6050_reader import MPU6050
imu = MPU6050()
import track_manager
# ============================
#   ECU READER (INTEGRATO)
# ============================
import ecu_reader
from ecu_reader import get_latest_data

# Avvia ECU reader in background
import threading
threading.Thread(target=ecu_reader.main, daemon=True).start()

import socket
import subprocess
import requests
import os
import cv2
from flask import Response
# ============================
#   ORARIO: SYSTEM TIME + RTC FALLBACK
# ============================
from datetime import datetime
import subprocess

def get_system_time():
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "SYSTEM"
    }

def get_rtc_time():
    try:
        rtc_time = subprocess.check_output(["cat", "/sys/class/rtc/rtc0/time"]).decode().strip()
        rtc_date = subprocess.check_output(["cat", "/sys/class/rtc/rtc0/date"]).decode().strip()
        return {
            "time": rtc_time,
            "date": rtc_date,
            "source": "RTC"
        }
    except:
        return None

def get_dashboard_time():
    # 1️⃣ Ora del sistema (sempre corretta)
    system_time = get_system_time()

    # 2️⃣ Prova a leggere l’RTC
    rtc = get_rtc_time()

    # 3️⃣ Se l’RTC risponde → fallback
    if rtc:
        return rtc

    # 4️⃣ Altrimenti → ora del sistema
    return system_time

app = Flask(__name__)

# ============================
#   GPIO SETUP RELÈ (ACTIVE LOW)
# ============================

relay_pins = {
    1: 17,
    2: 27,
    3: 22,
    4: 23
}

chip = lgpio.gpiochip_open(0)

# Inizializziamo i pin come output (ACTIVE LOW) con protezione totale
for pin in relay_pins.values():
    try:
        result = lgpio.gpio_claim_output(chip, pin)
        if result >= 0:
            lgpio.gpio_write(chip, pin, 1)  # HIGH = OFF
        else:
            print(f"[GPIO] Pin {pin} occupato, salto inizializzazione...")
    except lgpio.error:
        print(f"[GPIO] Errore su pin {pin}, salto...")

relay_state = {1: False, 2: False, 3: False, 4: False}

# ============================
#   HOME / DASHBOARD
# ============================
@app.route("/")
def dashboard():
    return render_template("index.html")

# ============================
#   TPMS STORAGE
# ============================
tpms_storage = {}

@app.route("/update", methods=["POST"])
def update():
    data = request.json
    if not isinstance(data, dict):
        return {"status": "error", "message": "json non valido"}, 400

    for sensor, values in data.items():
        tpms_storage[sensor] = values

    return {"status": "ok"}

@app.route("/data", methods=["GET"])
def get_data():
    data = tpms_storage.copy()
    try:
        data["external_temperature"] = read_external_temperature()
    except:
        data["external_temperature"] = None
    return jsonify(data)

# ============================
#   GPS STORAGE
# ============================

gps_data = {
    "lat": None,
    "lon": None,
    "speed_kmh": None,
    "alt": None,
    "satellites": None,
    "fix_quality": None
}

@app.route("/gps_data", methods=["POST"])
def gps_data_post():

    global gps_data

    data = request.json

    gps_data["lat"] = data.get("lat")
    gps_data["lon"] = data.get("lon")

    speed_knots = data.get("speed")

    gps_data["speed_kmh"] = (
        speed_knots * 1.852
        if speed_knots is not None
        else None
    )

    gps_data["alt"] = data.get("altitude")
    gps_data["satellites"] = data.get("satellites")
    gps_data["fix_quality"] = data.get("fix_quality")

    # TRACK RECORDER
    track_manager.add_point(
        gps_data["lat"],
        gps_data["lon"],
        gps_data["alt"],
        gps_data["speed_kmh"]
    )

    return jsonify({"status": "ok"})


@app.route("/gps_data", methods=["GET"])
def gps_get():

    return jsonify({
        "lat": round(gps_data["lat"], 6)
            if gps_data["lat"] is not None else None,

        "lon": round(gps_data["lon"], 6)
            if gps_data["lon"] is not None else None,

        "speed_kmh": gps_data["speed_kmh"],
        "alt": gps_data["alt"],
        "satellites": gps_data["satellites"],
        "fix_quality": gps_data["fix_quality"]
    })


# ============================
#   TRACK RECORDER
# ============================

@app.route("/track_points")
def track_points():

    return jsonify(
        track_manager.get_track()
    )

# ============================
#   ECU DATA ENDPOINT
# ============================
@app.route("/ecu_data")
def ecu_data():
    return jsonify(get_latest_data())

# ============================
#   RELÈ CONTROL
# ============================
@app.route("/relay/<int:num>/<state>", methods=["GET"])
def relay_control(num, state):
    if num not in relay_pins:
        return {"status": "error", "message": "Relè inesistente"}, 400

    pin = relay_pins[num]

    try:
        if state == "on":
            lgpio.gpio_write(chip, pin, 0)
            relay_state[num] = True
            return {"status": "ok", "relay": num, "state": "on"}

        elif state == "off":
            lgpio.gpio_write(chip, pin, 1)
            relay_state[num] = False
            return {"status": "ok", "relay": num, "state": "off"}

    except lgpio.error:
        return {"status": "error", "message": "GPIO occupato"}, 500

    return {"status": "error", "message": "Stato non valido"}, 400

# ============================
#   IMU
# ============================
@app.route("/imu_data", methods=["GET"])
def imu_data():
    try:
        pitch, roll = imu.get_pitch_roll()
        return jsonify({"pitch": pitch, "roll": roll})
    except Exception as e:
        return jsonify({"error": str(e)})

# ============================
#   MAP PAGE
# ============================
@app.route("/map")
def map_page():
    return render_template("map.html")

# ============================
#   DIAGNOSTICA
# ============================
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None

def ping(host, count=1, timeout=1):
    try:
        subprocess.check_output(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False

@app.route('/diagnostics')
def diagnostics():

    # TPMS
    try:
        data = requests.get("http://localhost:5000/data", timeout=1).json()
        temp = data.get("external_temperature")
        temp_ok = temp is not None

        tpms_data = {
            "FL": data.get("FL"),
            "FR": data.get("FR"),
            "RL": data.get("RL"),
            "RR": data.get("RR")
        }
        tpms_ok = all(v is not None for v in tpms_data.values())
    except:
        temp = None
        temp_ok = False
        tpms_data = None
        tpms_ok = False

    # GPS
    try:
        gps = requests.get("http://localhost:5000/gps_data", timeout=1).json()
        gps_ok = gps.get("lat") is not None
    except:
        gps = None
        gps_ok = False

    # ECU
    try:
        ecu = requests.get("http://localhost:5000/ecu_data", timeout=1).json()
        obd_ok = ecu.get("rpm") is not None
    except:
        ecu = None
        obd_ok = False

    # RETE
    ip = get_ip_address()
    network_link_ok = ip is not None

    gateway_ip = None
    gateway_ok = False
    try:
        out = subprocess.check_output(
            "ip route | grep default | awk '{print $3}'",
            shell=True
        ).decode().strip()
        if out:
            gateway_ip = out
            gateway_ok = ping(gateway_ip)
    except:
        pass

    internet_ok = ping("8.8.8.8")

    try:
        socket.gethostbyname("www.google.com")
        dns_ok = True
    except:
        dns_ok = False

    try:
        r = requests.get("http://localhost:5000", timeout=1)
        backend_ok = (r.status_code == 200)
    except:
        backend_ok = False

    network_ok = network_link_ok and gateway_ok and internet_ok and dns_ok

    return jsonify({
        "external_temp_ok": temp_ok,
        "external_temp": temp,

        "tpms_ok": tpms_ok,
        "tpms": tpms_data,

        "gps_ok": gps_ok,
        "gps": gps,

        "obd_ok": obd_ok,
        "obd": ecu,

        "network_ok": network_ok,
        "ip": ip,

        "network_link_ok": network_link_ok,
        "gateway_ok": gateway_ok,
        "gateway_ip": gateway_ip,
        "internet_ok": internet_ok,
        "dns_ok": dns_ok,
        "backend_ok": backend_ok
    })

@app.route('/exit_dashboard')
def exit_dashboard():
    try:
        subprocess.run(["pkill", "-f", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "OK", 200
    except Exception as e:
        print("Errore exit_dashboard:", e)
        return "Errore", 500

@app.route('/shutdown_pi')
def shutdown_pi():
    os.system("sudo shutdown -h now")
    return "Spegnimento in corso..."

# ============================
#   RETROCAMERA
# ============================
@app.route('/rearcam')
def rearcam_page():
    return app.send_static_file('rearcam.html')

camera = cv2.VideoCapture(0)

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/rearcam_stream')
def rearcam_stream():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
# ============================
#   TIME ENDPOINT (SYSTEM + RTC)
# ============================
@app.route("/time")
def time_endpoint():
    return jsonify(get_dashboard_time())

# ============================
#   AVVIO SERVER
# ============================
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        lgpio.gpiochip_close(chip)

