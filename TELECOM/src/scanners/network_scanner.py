#!/usr/bin/env python3
"""
Network audit scanner rápido y con visibilidad:
 - ping-scan por subnet para hosts activos
 - escaneo de puertos en lote por subnet
 - medición de latencia (ping) y pérdida
 - barra de progreso y logs
 - CSV por subnet + CSV consolidado
Ajusta EXPORT_FOLDER y ARCHIVO_REDES arriba.
"""
import os
import csv
import re
import subprocess
import socket
import time
from datetime import datetime
from tqdm import tqdm
import nmap

# ==============================
# CONFIG
# ==============================
EXPORT_FOLDER = r"C:\Users\kramos\Documents\TPC - TECNICO\ESTACIONES DE TRABAJAO"
ARCHIVO_REDES = r"C:\Git-Kevin\Personales\TELECOM\config\redes.txt"
PUERTOS_COMUNES = "22,80,443,445,3389,5900,8080,8443"
PING_INTENTOS = 3

CSV_FIELDS = [
    "red", "ip", "hostname", "mac", "vendor",
    "puertos", "lat_min_ms", "lat_max_ms",
    "lat_avg_ms", "loss_pct"
]

LOG_FILE = os.path.join(EXPORT_FOLDER, "network_audit_log.txt")


# ==============================
# UTIL
# ==============================
def ensure_dirs():
    os.makedirs(EXPORT_FOLDER, exist_ok=True)


def now_ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def safe_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""


# ==============================
# LATENCIA
# ==============================
def medir_latencia_win(ip, intentos=PING_INTENTOS):
    tiempos = []
    hechos = 0

    for _ in range(intentos):
        try:
            salida = subprocess.check_output(
                f"ping -n 1 -w 1000 {ip}",
                shell=True, encoding="utf-8",
                stderr=subprocess.DEVNULL
            )
            hechos += 1

            m = re.search(r"[Tt]iempo[=<]\s*([0-9]+)|time[=<]\s*([0-9]+)", salida)
            if m:
                val = next(g for g in m.groups() if g)
                tiempos.append(int(val))
        except:
            pass

    if hechos == 0:
        return {"min": None, "max": None, "avg": None, "loss": 100}

    if not tiempos:
        loss = round(100, 2)
        return {"min": None, "max": None, "avg": None, "loss": loss}

    loss = round((1 - len(tiempos) / hechos) * 100, 2)
    return {
        "min": min(tiempos),
        "max": max(tiempos),
        "avg": round(sum(tiempos) / len(tiempos), 2),
        "loss": loss
    }


# ==============================
# ESCANEO DE RED
# ==============================
def scan_network_fast(red):
    nm = nmap.PortScanner()
    print(f"\n🔎 Escaneando red (ping) -> {red}")
    start = time.perf_counter()

    # 1) Ping scan
    try:
        nm.scan(hosts=red, arguments='-sn -n')
    except Exception as e:
        print(f"❌ Error ping-scan {red}: {e}")
        return []

    hosts_activos = nm.all_hosts()
    print(f"➡ Hosts activos: {len(hosts_activos)}")

    if not hosts_activos:
        return []

    # 2) Port scan en lote
    print(f"🔍 Escaneando puertos en {red} ...")

    try:
        nm.scan(hosts=red, ports=PUERTOS_COMUNES, arguments='-T4 -n')
    except Exception as e:
        print(f"❌ Error port-scan {red}: {e}")
        return []

    results = []
    scan_data = nm._scan_result.get("scan", {})

    for host in tqdm(hosts_activos, desc=f"Procesando {red}", unit="host"):
        info = scan_data.get(host, {})
        status = info.get("status", {}).get("state", "")

        if status != "up":
            continue

        # --------------------
        # Puertos abiertos
        # --------------------
        puertos = []
        for proto in ("tcp", "udp"):
            ports = info.get(proto, {})
            for p, pdata in ports.items():
                if pdata.get("state") == "open":
                    puertos.append(str(p))

        # --------------------
        # MAC / Vendor
        # --------------------
        mac = info.get("addresses", {}).get("mac", "")
        vendor = info.get("vendor", {}).get(mac, "") if mac else ""

        # --------------------
        # Hostname
        # --------------------
        hostname = ""
        try:
            hlist = info.get("hostnames", [])
            if hlist and "name" in hlist[0]:
                hostname = hlist[0]["name"]
        except:
            hostname = ""

        if not hostname:
            hostname = safe_hostname(host)

        # --------------------
        # Latencia
        # --------------------
        lat = medir_latencia_win(host, PING_INTENTOS)

        results.append({
            "red": red,
            "ip": host,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "puertos": ", ".join(puertos),
            "lat_min_ms": lat["min"],
            "lat_max_ms": lat["max"],
            "lat_avg_ms": lat["avg"],
            "loss_pct": lat["loss"]
        })

    t = time.perf_counter() - start
    print(f"⏱ Tiempo red {red}: {t:.1f}s")
    return results


# ==============================
# REDES
# ==============================
def cargar_redes(ruta):
    if not os.path.exists(ruta):
        print(f"❌ No existe {ruta}")
        return []

    redes = []
    with open(ruta, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                redes.append(line)

    return redes


# ==============================
# EXPORTAR
# ==============================
def export_results(all_results):
    ensure_dirs()
    ts = now_ts()

    output_cons = os.path.join(EXPORT_FOLDER, f"resultado_scan_consolidado_{ts}.csv")

    # Consolidado
    with open(output_cons, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(all_results)

    # Por red
    by_red = {}
    for row in all_results:
        by_red.setdefault(row["red"], []).append(row)

    for red, rows in by_red.items():
        safe = red.replace("/", "-")
        fname = os.path.join(EXPORT_FOLDER, f"{safe}_{ts}.csv")
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(rows)

    print(f"\n📁 CSV generado: {output_cons}")
    print(f"📁 CSVs por red: {len(by_red)}")


# ==============================
# MAIN
# ==============================
def main():
    ensure_dirs()
    redes = cargar_redes(ARCHIVO_REDES)

    if not redes:
        print("❌ No hay redes para escanear")
        return

    print(f"\n📌 Iniciando auditoría: {len(redes)} redes")
    start_total = time.perf_counter()

    all_results = []

    for red in redes:
        try:
            data = scan_network_fast(red)
            all_results.extend(data)
        except KeyboardInterrupt:
            print("⛔ Interrumpido")
            break

    print(f"\n✅ Auditoría completa - {len(all_results)} hosts detectados")
    export_results(all_results)

    print(f"⏱ Tiempo total: {time.perf_counter() - start_total:.1f}s")


if __name__ == "__main__":
    main()
