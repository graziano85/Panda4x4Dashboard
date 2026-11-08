// ===============================
//   ANIMAZIONE DI AVVIO (FADE OUT)
// ===============================
window.addEventListener("load", () => {

    const overlay = document.getElementById("startup-overlay");

    // 1️⃣ Assicuriamoci che l'immagine sia visibile
    overlay.style.opacity = "1";
    overlay.style.display = "block";

    // 2️⃣ Tempo di permanenza (modifica qui)
    const displayTime = 4000;   // 4 secondi

    // 3️⃣ Fade-out
    setTimeout(() => {
        overlay.style.opacity = "0";

        // 4️⃣ Rimozione finale DOPO il fade-out
        setTimeout(() => {
            overlay.style.display = "none";
        }, 1200); // deve essere identico al CSS transition
    }, displayTime);
});



// ===============================
//   VARIABILI GLOBALI BUSSOLA INTELLIGENTE
// ===============================
let lastLat = null;
let lastLon = null;
let lastHeading = 0;


// ===============================
//   FUNZIONE CALCOLO HEADING INTELLIGENTE
// ===============================
function calculateHeading(lat1, lon1, lat2, lon2) {
    const toRad = deg => deg * Math.PI / 180;
    const toDeg = rad => rad * 180 / Math.PI;

    const dLon = toRad(lon2 - lon1);
    const y = Math.sin(dLon) * Math.cos(toRad(lat2));
    const x = Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
              Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(dLon);

    let brng = toDeg(Math.atan2(y, x));
    return (brng + 360) % 360;
}

async function updateClock() {
    try {
        const response = await fetch("/time");
        const data = await response.json();

        const datetimeElement = document.getElementById("datetime");

        // Mostra Data/Ora + sorgente (RTC o SYSTEM)
        datetimeElement.textContent = `${data.date} ${data.time} (${data.source})`;

    } catch (e) {
        // In caso di errore, mostra solo l'ora del sistema locale
        const now = new Date();
        const fallback = now.toLocaleString("it-IT");
        document.getElementById("datetime").textContent = `${fallback} (LOCAL)`;
    }
}

// Aggiorna ogni secondo
setInterval(updateClock, 1000);
updateClock();

// ===============================
//   AGGIORNA TPMS + TEMP ESTERNA
// ===============================
function updateTPMS() {
    fetch("/data")
        .then(r => r.json())
        .then(data => {

            // --- Temperatura esterna ---
            const tempElem = document.getElementById("ext-temp");
            const temp = Number(data.external_temperature);

            let icon = `<img src="/static/icons/thermo.png" class="icon-small">`;

            if (isNaN(temp)) {
                tempElem.innerHTML = `${icon} -- °C`;
            } else {
                tempElem.innerHTML = `${icon} ${temp} °C`;
            }

            tempElem.style.color = "#ffb347";
            tempElem.style.textShadow = "1px 1px 3px #000";

            if (!isNaN(temp)) {
                if (temp <= 5) {
                    tempElem.style.color = "#4db8ff";
                    tempElem.style.textShadow = "0 0 8px #4db8ff";
                } else if (temp >= 30) {
                    tempElem.style.color = "#ff5733";
                    tempElem.style.textShadow = "0 0 8px #ff5733";
                }
            }


            // --- TPMS ---
            ["FL", "FR", "RL", "RR"].forEach(s => {
                if (data[s]) {

                    const pElem = document.querySelector(`#${s} .tpms-pressure`);
                    const tElem = document.querySelector(`#${s} .tpms-temp`);
                    const bElem = document.querySelector(`#${s} .tpms-batt`);

                    const pressure = data[s].pressure ?? "--";
                    const tempTire = data[s].temperature ?? "--";
                    const battery = data[s].battery ?? "--";

                    pElem.textContent = pressure + " bar";
                    tElem.textContent = tempTire + " °C";
                    bElem.textContent = battery + " V";

                    if (pressure !== "--") {
                        const p = Number(pressure);
                        if (!Number.isNaN(p)) {
                            if (p < 1.8) {
                                pElem.style.color = "#ff3333";
                            } else if (p > 2.8) {
                                pElem.style.color = "#ffaa00";
                            } else {
                                pElem.style.color = "#00ff66";
                            }
                        }
                    }

                    if (tempTire !== "--") {
                        const tt = Number(tempTire);
                        if (!Number.isNaN(tt)) {
                            if (tt < 10) {
                                tElem.style.color = "#4db8ff";
                            } else if (tt > 50) {
                                tElem.style.color = "#ff3333";
                            } else {
                                tElem.style.color = "#ffb347";
                            }
                        }
                    }

                    if (battery !== "--") {
                        const b = Number(battery);
                        if (!Number.isNaN(b)) {
                            if (b < 2.5) {
                                bElem.style.color = "#ff3333";
                            } else if (b < 2.9) {
                                bElem.style.color = "#ffaa00";
                            } else {
                                bElem.style.color = "#00ff66";
                            }
                        }
                    }
                }
            });
        });
}


// ===============================
//   AGGIORNA GPS + BUSSOLA + ALTIMETRO
// ===============================
function updateGPS() {
    fetch("/gps_data")
        .then(r => r.json())
        .then(gps => {

            const speedElem = document.getElementById("speed");
            const speed = gps.speed_kmh ?? "--";

            speedElem.textContent = speed + " km/h";

            if (speed !== "--" && Number(speed) > 100) {
                speedElem.style.color = "#ff3333";
                speedElem.style.textShadow = "0 0 10px #ff3333";
            } else {
                speedElem.style.color = "#ffffff";
                speedElem.style.textShadow = "1px 1px 3px #000";
            }

            document.getElementById("gps-lat").textContent = gps.lat ?? "--";
            document.getElementById("gps-lon").textContent = gps.lon ?? "--";

            const altElem = document.getElementById("gps-alt");
            const alt = gps.alt ?? "--";

            if (alt !== "--") {
                altElem.textContent = ` ${alt} m`;
            } else {
                altElem.textContent = " -- m";
            }


            // ===============================
            //   BUSSOLA INTELLIGENTE
            // ===============================
            const needle = document.getElementById("compass-needle");

            const lat = gps.lat;
            const lon = gps.lon;

            if (lastLat !== null && lastLon !== null) {

                const distanceMoved = Math.sqrt(
                    Math.pow(lat - lastLat, 2) + Math.pow(lon - lastLon, 2)
                );

                if (distanceMoved > 0.00001) {
                    lastHeading = calculateHeading(lastLat, lastLon, lat, lon);
                }
            }

            needle.style.transform = `rotate(${lastHeading}deg)`;

            lastLat = lat;
            lastLon = lon;
        });
}


// ===============================
//   AGGIORNA DATA/ORA
// ===============================
function updateClock() {
    const now = new Date();
    document.getElementById("datetime").textContent =
        now.toLocaleString("it-IT");
}


// ===============================
//   RELÈ
// ===============================
function toggleRelay(num) {
    const btn = document.getElementById("relay" + num);

    const isActive = btn.classList.contains("active");
    const newState = isActive ? "off" : "on";

    fetch(`/relay/${num}/${newState}`)
        .then(r => r.json())
        .then(res => {
            if (res.status === "ok") {

                if (newState === "on") {
                    btn.classList.add("active");
                } else {
                    btn.classList.remove("active");
                }
            }
        })
        .catch(err => console.error("Errore relè:", err));
}


// ===============================
//   ECU
// ===============================
function updateECU() {
    fetch("/ecu_data")
        .then(r => r.json())
        .then(ecu => {

            document.getElementById("ecu-rpm").textContent = ecu.rpm ?? "--";
           // document.getElementById("ecu-temp").textContent = ecu.tw ?? "--";
            document.getElementById("ecu-batt").textContent = ecu.vbatt ?? "--";

            if (document.getElementById("ecu-map")) {
                document.getElementById("ecu-map").textContent = ecu.pa ?? "--";
            }
        })
        .catch(err => console.error("ECU error:", err));
}


document.getElementById("btn-rearcam").addEventListener("click", () => {
    window.location.href = "/rearcam";
});

// ===============================
//   MPU6050
// ===============================
function updateIMU() {
    fetch("/imu_data")
        .then(r => r.json())
        .then(imu => {

            if (imu.error) return;

            let pitchRaw = imu.pitch ?? 0;
            let rollRaw  = imu.roll ?? 0;

            const smoothFactor = 0.65;

            window.pitchSmooth = window.pitchSmooth ?? pitchRaw;
            window.rollSmooth  = window.rollSmooth  ?? rollRaw;

            window.pitchSmooth = window.pitchSmooth * smoothFactor + pitchRaw * (1 - smoothFactor);
            window.rollSmooth  = window.rollSmooth  * smoothFactor + rollRaw  * (1 - smoothFactor);

            let pitch = window.pitchSmooth;
            let roll  = window.rollSmooth;

            if (Math.abs(pitch) < 1) pitch = 0;
            if (Math.abs(roll)  < 1) roll  = 0;

            pitch = parseFloat(pitch.toFixed(1));
            roll  = parseFloat(roll.toFixed(1));

            const pitchText = document.getElementById("pitch-text");
            const rollText  = document.getElementById("roll-text");

            if (pitchText) pitchText.textContent = `${pitch}°`;
            if (rollText)  rollText.textContent  = `${roll}°`;

        })
        .catch(err => console.error("IMU error:", err));
}



// ===============================
//   DIAGNOSTICA
// ===============================
document.getElementById("btn_diagnostics").addEventListener("click", () => {
    window.location.href = "/static/diagnostics.html";
});


// ===============================
//   INTERVALLI
// ===============================
setInterval(updateTPMS, 5000);
setInterval(updateGPS, 1500);
setInterval(updateClock, 1000);
setInterval(updateECU, 500);
setInterval(updateIMU, 150);

