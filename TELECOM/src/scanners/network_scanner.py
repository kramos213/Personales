import nmap
import subprocess
import socket
import csv
import os
from datetime import datetime
import re
from multiprocessing import Pool, cpu_count
 
# ============================================
# CONFIG
# ============================================

EXPORT_FOLDER = r"C:\Users\kramos\Documents\TPC - TECNICO\ESTACIONES DE TRABAJAO"
ARCHIVO_REDES = r"C:\Git-Kevin\Personales\TELECOM\config\redes.txt"   # <--- ruta editable

PUERTOS_COMUNES = "22,80,443,445,3389,5900,8080,8443"


# ============================================
# CARGAR REDES DESDE TXT
# ============================================
def cargar_redes(ruta):
    if not os.path.exists(ruta):
        print(f"❌ No se encontró el archivo de redes: {ruta}")
        return []

    redes = []
    with open(ruta, "r") as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                redes.append(linea)
    return redes


# ============================================
# OBTENER MAC
# ============================================
def get_mac(ip):
    try:
        salida = subprocess.check_output(f"arp -a {ip}", shell=True).decode()
        mac = re.search(r"([0-9a-f]{2}[:-]){5}[0-9a-f]{2}", salida, re.I)
        return mac.group(0) if mac else ""
    except:
        return ""


# ============================================
# OBTENER HOSTNAME
# ============================================
def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""


# ============================================
# ESCANEAR UN HOST
# ============================================
def scan_host(ip):
    scanner = nmap.PortScanner()

    try:
        result = scanner.scan(ip, PUERTOS_COMUNES)
        info = result.get("scan", {}).get(ip, {})

        if info.get("status", {}).get("state") != "up":
            return None

        puertos = []
        for port, data in info.get("tcp", {}).items():
            if data["state"] == "open":
                puertos.append(str(port))

        mac = get_mac(ip)
        hostname = get_hostname(ip)

        vendor = ""
        mac_addr = info.get("addresses", {}).get("mac")
        if mac_addr:
            vendor = info.get("vendor", {}).get(mac_addr, "")

        return {
            "ip": ip,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "puertos": ", ".join(puertos)
        }

    except Exception:
        return None


# ============================================
# ESCANEAR RED COMPLETA
# ============================================
def scan_network(red):
    print(f"\n🔎 Escaneando red: {red}")

    scanner = nmap.PortScanner()
    scanner.scan(hosts=red, arguments="-sn")

    hosts_activos = scanner.all_hosts()
    print(f"➡ {len(hosts_activos)} hosts activos detectados")

    with Pool(cpu_count()) as pool:
        resultados = pool.map(scan_host, hosts_activos)

    return [r for r in resultados if r]


# ============================================
# EXPORTAR A CSV
# ============================================
def export_csv(data):
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

    archivo = f"resultado_scan_{datetime.now():%Y-%m-%d_%H-%M-%S}.csv"
    ruta = os.path.join(EXPORT_FOLDER, archivo)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ip", "hostname", "mac", "vendor", "puertos"])
        writer.writeheader()
        writer.writerows(data)

    print(f"\n📁 CSV generado: {ruta}")


# ============================================
# MAIN
# ============================================
def main():
    redes = cargar_redes(ARCHIVO_REDES)

    if not redes:
        print("❌ No hay redes para escanear.")
        return

    resultado_total = []

    for red in redes:
        resultado_total.extend(scan_network(red))

    export_csv(resultado_total)


if __name__ == "__main__":
    main()
