import json
import os
import math
import time

TRACK_FILE = "/home/graziano/tpms_dashboard/tracks/current_track.json"

track_points = []

last_lat = None
last_lon = None


def distance_m(lat1, lon1, lat2, lon2):
    """
    distanza approssimata in metri
    """

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2 +
        math.cos(phi1) *
        math.cos(phi2) *
        math.sin(dlambda / 2) ** 2
    )

    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def add_point(lat, lon, alt=None, speed=None):

    global last_lat
    global last_lon

    if lat is None or lon is None:
        return

    if last_lat is not None:

        dist = distance_m(
            last_lat,
            last_lon,
            lat,
            lon
        )

        if dist < 5:
            return

    point = {
        "lat": lat,
        "lon": lon,
        "alt": alt,
        "speed": speed,
        "timestamp": int(time.time())
    }

    track_points.append(point)

    last_lat = lat
    last_lon = lon

    save_track()


def save_track():

    os.makedirs(
        "/home/graziano/tpms_dashboard/tracks",
        exist_ok=True
    )

    with open(TRACK_FILE, "w") as f:
        json.dump(track_points, f)


def get_track():
    return track_points


def clear_track():

    global track_points
    global last_lat
    global last_lon

    track_points = []

    last_lat = None
    last_lon = None

    save_track()
