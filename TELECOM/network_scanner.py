import nmap
import subprocess
import socket
import csv
import os
from datetime import datetime
import re
from multiprocessing import Pool, cpu_count

# Carpeta fija donde se guardarán los CSV
EXPORT_FOLDER = r"C:\Users\kramos\Documents\TPC - TECNICO\ESTACIONES DE TRABAJAO"


# =============================================
# CONFIGURACIÓN
# =============================================

REDES = [
    "10.1.60.0/24",
    "10.1.115.0/24",
    "10.1.230.1/24",
    "10.1.228.1/24",
    "10.1.227.1/24",
    "10.1.226.1/24",
    "10.1.221.1/24",
    "10.1.220.1/24",
    "10.1.215.1/24",
    "10.1.208.1/24",
    "10.1.207.1/24",
    "10.1.206.1/24",
    "10.1.130.1/24",
    "10.1.128.1/24",
    "10.1.127.1/24",
    "10.1.126.1/24",
    "10.1.124.1/24",
    "10.1.121.1/24",
    "10.1.120.1/24",
    "10.1.119.1/24",
    "10.1.118.1/24",
    "10.1.117.1/24",
    "10.1.116.1/24",
    "10.1.115.1/24",
    "10.1.60.1/24"
    # Agrega aquí tus 23 redes
]

PUERTOS_COMUNES = "22,80,443,445,3389,5900,8080,8443"

# =============================================
# OBTENER MAC ADDRESS
# =============================================
def get_mac(ip):
    try:
        arp = subprocess.check_output(f"arp -a {ip}", shell=True).decode()
        mac = re.search(r"([0-9a-f]{2}[:-]){5}[0-9a-f]{2}", arp, re.I)
        return mac.group(0) if mac else ""
    except:
        return ""


# =============================================
# OBTENER HOSTNAME
# =============================================
def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""


# =============================================
# ESCANEO DE HOST INDIVIDUAL
# =============================================
def scan_host(args):
    ip, scanner = args

    try:
        result = scanner.scan(ip, PUERTOS_COMUNES)
        estado = result["scan"][ip]["status"]["state"]
        
        if estado != "up":
            return None

        puertos_abiertos = []
        if "tcp" in result["scan"][ip]:
            for port, data in result["scan"][ip]["tcp"].items():
                if data["state"] == "open":
                    puertos_abiertos.append(str(port))

        hostname = get_hostname(ip)
        mac = get_mac(ip)

        # Vendor del fabricante (si nmap lo detecta)
        vendor = ""
        if "addresses" in result["scan"][ip] and "mac" in result["scan"][ip]["addresses"]:
            vendor = result["scan"][ip]["vendor"].get(result["scan"][ip]["addresses"]["mac"], "")

        return {
            "ip": ip,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "puertos": ",".join(puertos_abiertos)
        }

    except:
        return None


# =============================================
# ESCANEAR RED COMPLETA
# =============================================
def scan_network(red):
    print(f"\n🔎 Escaneando red: {red}")

    scanner = nmap.PortScanner()
    scanner.scan(hosts=red, arguments="-sn")

    hosts_activos = scanner.all_hosts()
    print(f"➡ {len(hosts_activos)} hosts activos detectados")

    pool = Pool(cpu_count())
    resultados = pool.map(scan_host, [(ip, nmap.PortScanner()) for ip in hosts_activos])
    pool.close()
    pool.join()

    return [r for r in resultados if r]


# =============================================
# EXPORTAR A CSV
# =============================================
def export_csv(data):
    keys = ["ip", "hostname", "mac", "vendor", "puertos"]

    # Crear carpeta si no existe
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

    # Crear nombre automático con fecha y hora
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"resultado_scan_{timestamp}.csv"

    # Ruta completa para guardar
    full_path = os.path.join(EXPORT_FOLDER, file_name)

    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        
        # Normalizar puertos en caso de ser lista
        for row in data:
            if isinstance(row.get("puertos"), list):
                row["puertos"] = ", ".join(str(p) for p in row["puertos"])
        writer.writerows(data)

    print(f"\n📁 CSV generado correctamente:")
    print(f"➡ {full_path}")

# =============================================
# MAIN
# =============================================
def main():
    todos = []

    for red in REDES:
        datos_red = scan_network(red)
        todos.extend(datos_red)

    export_csv(todos)


if __name__ == "__main__":
    main()
