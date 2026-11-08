function updateStatus(id, ok) {
    const el = document.getElementById(id);
    el.className = "status " + (ok ? "ok" : "fail");
    el.textContent = ok ? "OK" : "ERRORE";
}

function updateUI(data) {

    // --- Sensori ---
    updateStatus("temp_status", data.external_temp_ok);
    updateStatus("tpms_status", data.tpms_ok);
    updateStatus("gps_status", data.gps_ok);
    updateStatus("obd_status", data.obd_ok);

    // --- Rete (riassunto) ---
    updateStatus("net_status", data.network_ok);

    // --- Dettagli rete ---
    document.getElementById("ip_value").textContent = data.ip || "N/A";

    updateStatus("link_status", data.network_link_ok);
    updateStatus("gateway_status", data.gateway_ok);
    updateStatus("internet_status", data.internet_ok);
    updateStatus("dns_status", data.dns_ok);
    updateStatus("backend_status", data.backend_ok);

    // ============================
    //   GPS DETTAGLI (NUOVI)
    // ============================
    if (data.gps) {
        document.getElementById("gps_lat").textContent = data.gps.lat ?? "N/A";
        document.getElementById("gps_lon").textContent = data.gps.lon ?? "N/A";
        document.getElementById("gps_speed").textContent = data.gps.speed_kmh ?? "N/A";
        document.getElementById("gps_alt").textContent = data.gps.alt ?? "N/A";
        document.getElementById("gps_satellites").textContent = data.gps.satellites ?? "N/A";
        document.getElementById("gps_fix").textContent = data.gps.fix_quality ?? "N/A";
    }
}

setInterval(() => {
    fetch("/diagnostics")
        .then(r => r.json())
        .then(updateUI)
        .catch(() => console.log("Errore diagnostica"));
}, 1000);

