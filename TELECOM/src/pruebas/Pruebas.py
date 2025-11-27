import os
import socket
from ping3 import ping
from scapy.all import ARP, Ether, srp
import pandas as pd

# Ruta para guardar el reporte
SAVE_PATH = r"Z:\Monitoreo de red\Prueba"
os.makedirs(SAVE_PATH, exist_ok=True)

def scan_network(ip_range):
    """Escanea todos los dispositivos en un segmento de red usando ARP."""
    print(f"Escaneando la red {ip_range}...")
    arp_request = ARP(pdst=ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp_request
    result = srp(packet, timeout=2, verbose=False)[0]

    devices = []
    for sent, received in result:
        devices.append({'IP': received.psrc, 'MAC': received.hwsrc})
    print(f"Se encontraron {len(devices)} dispositivos.")
    return devices

def test_connectivity(devices):
    """Prueba la conectividad con cada dispositivo."""
    print("\nPruebas de conectividad:")
    for device in devices:
        latency = ping(device['IP'], unit="ms")
        if latency:
            print(f"{device['IP']} ({device['MAC']}) responde en {latency:.2f} ms")
            device['Latency (ms)'] = latency
        else:
            print(f"{device['IP']} ({device['MAC']}) no responde")
            device['Latency (ms)'] = None

def save_results(devices):
    """Guarda los resultados en un archivo CSV."""
    print("\nGuardando resultados...")
    report_path = os.path.join(SAVE_PATH, "network_scan_report.csv")
    df = pd.DataFrame(devices)
    df.to_csv(report_path, index=False)
    print(f"Reporte guardado en: {report_path}")

if __name__ == "__main__":
    # Configura el rango de red
    network_range = "10.1.7.0/24"  # Cambia al rango de tu red

    # Escaneo de red
    devices = scan_network(network_range)

    # Pruebas de conectividad
    test_connectivity(devices)

    # Guardar resultados
    save_results(devices)
