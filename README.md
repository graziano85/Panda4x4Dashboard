# Panda Off-Road Computer

Dashboard off-road sviluppata per Fiat Panda 4x4 basata su Raspberry Pi.

Il progetto integra navigazione GPS, TPMS, ECU, inclinometro, bussola digitale, controllo relè, diagnostica e retrocamera in un'unica interfaccia touchscreen.

---

# Stato Progetto

Versione: **2.1**

Stato attuale:

✅ Dashboard operativa

✅ ECU Reader

✅ TPMS

✅ MPU6050

✅ Retrocamera

✅ GPS NMEA

✅ Mappa Leaflet

✅ Track Recorder (prima implementazione)

🚧 TrackBack in sviluppo

---

# Funzioni Principali

## Dashboard

Visualizzazione in tempo reale di:

- Velocità GPS
- Temperatura esterna
- Coordinate GPS
- Altitudine
- RPM motore
- Tensione batteria
- Stato TPMS
- Pitch
- Roll
- Diagnostica sistema

---

## Navigazione

Tecnologie:

- Leaflet
- OpenStreetMap

Funzioni:

- Posizione GPS live
- Marker dinamico
- Traccia percorso
- Navigazione off-road

---

## ECU

Comunicazione tramite:

```text
/dev/arduino
115200 baud
```

Parametri attuali:

- RPM
- Tensione batteria

Architettura predisposta per ulteriori PID.

---

## TPMS

Monitoraggio di:

- FL
- FR
- RL
- RR

Per ogni ruota:

- Pressione
- Temperatura
- Batteria sensore

---

## Inclinometro

Sensore:

```text
MPU6050
```

Visualizzazione:

- Pitch
- Roll

---

## Relè Ausiliari

Controllo di:

1. Luci
2. Ventola
3. Compressore
4. Verricello

---

## Retrocamera

Streaming MJPEG tramite OpenCV.

---

# Track Recorder

Versione iniziale implementata.

Funzioni:

- Registrazione del percorso
- Memorizzazione coordinate GPS
- Endpoint dedicato

```text
/track_points
```

Storage:

```text
tracks/current_track.json
```

---

# Hardware

## Raspberry Pi

Sistema principale.

## GPS

Attuale:

```text
u-blox NEO-6M
```

Stato:

- Comunicazione funzionante
- Satelliti rilevati
- Fix GPS in verifica

Upgrade consigliato:

```text
u-blox NEO-M8N
```

oppure

```text
u-blox NEO-M10N
```

## IMU

```text
MPU6050
```

## ECU

Arduino seriale

```text
/dev/arduino
```

---

# API

Disponibili:

```text
/
/data
/update
/gps_data
/track_points
/ecu_data
/imu_data
/map
/diagnostics
/rearcam
/rearcam_stream
/time
/shutdown_pi
/exit_dashboard
/relay/<numero>/<stato>
```

---

# Struttura Progetto

```text
tpms_dashboard/

├── backend.py
├── gps_reader.py
├── ecu_reader.py
├── track_manager.py

├── templates/
│   ├── index.html
│   └── map.html

├── static/
│   ├── dashboard.css
│   ├── dashboard.js
│   ├── diagnostics.html
│   ├── rearcam.html
│   └── icons/

├── tracks/

├── requirements.txt

└── start_dashboard.sh
```

---

# Roadmap

## Versione 2.1

- Track Recorder
- Salvataggio percorso
- Visualizzazione traccia

## Versione 2.2

- Start Recording
- Stop Recording
- Clear Track
- TrackBack

## Versione 2.3

- Waypoint permanenti
- Import/Export GPX

## Versione 3.0

- Mappe offline
- Storico escursioni
- Navigazione off-road avanzata

---

# Repository

Progetto sviluppato e mantenuto da Graziano Larocca.

Fiat Panda 4x4 + Raspberry Pi + Open Source.
