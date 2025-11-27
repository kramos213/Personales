import paramiko
from concurrent.futures import ThreadPoolExecutor
import csv
import os
import re

# Configuración de las credenciales y base de datos
USERNAME = "TPC"
PASSWORD = "Us3r@Tpc2024*"

switch_ips_by_area = {
    "PSO": ["172.16.0.151", "172.16.0.150", "172.16.0.118","172.16.0.102", "172.16.0.101", "172.16.0.147", "172.16.0.148", "172.16.0.116"],
    "PPB": ["172.16.0.105", "172.16.0.103", "172.16.0.104", "172.16.0.142", "172.16.0.143", "172.16.0.106", "172.16.0.107"],
    "P06": ["172.16.0.108", "172.16.0.109", "172.16.0.202", "172.16.0.140", "172.16.0.146", "172.16.0.201", "172.16.0.224" ],
    "P07": ["172.16.0.110", "172.16.0.111", "172.16.0.112", "172.16.0.141", "172.16.0.115"],
    "P08": ["172.16.0.113", "172.16.0.114"],
    "P09": ["172.16.0.120", "172.16.0.121"],
    "P10": ["172.16.0.123", "172.16.0.124"],
    "P11": ["172.16.0.125", "172.16.0.137", "172.16.0.126", "172.16.0.139"],
    "P14": ["172.16.0.127", "172.16.0.128"],
    "P16": ["172.16.0.129", "172.16.0.130", "172.16.0.138"],
    "P17": ["172.16.0.131", "172.16.0.132", "172.16.0.136"],
    "P18": ["172.16.0.133", "172.16.0.134", "172.16.0.135", "172.16.0.149"],
    "P24": ["172.16.0.200", "172.16.0.145"]
}

# Comandos para puertos activos e inactivos
COMMAND_DOWN = "sh int brief | inc dow"     # Puertos inactivos
COMMAND_RUNNING = "sh int brief | inc running"  # Puertos activos

# Patrón para puertos excluidos (X.0.49 y superiores)
#EXCLUDE_PATTERN = re.compile(r"^\d+\.0\.(49|[5-9][0-9]{1,})\s")

def count_ports(ip):
    """Conecta al switch y cuenta los puertos activos e inactivos, excluyendo `lo`, `vlan` y `X.0.49` o superiores."""
    ports_down = 0
    ports_running = 0

    try:
        # Conexión SSH al switch
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=USERNAME, password=PASSWORD)

        # Comando para puertos inactivos
        stdin, stdout, stderr = client.exec_command(COMMAND_DOWN)
        output_down = stdout.read().decode('utf-8')
        for line in output_down.splitlines():
            #print(f"Procesando línea inactiva: {line}")  # Depuración
            if not line.startswith(("lo", "vlan")): #and not EXCLUDE_PATTERN.match(line):
                ports_down += 1

        # Comando para puertos activos
        stdin, stdout, stderr = client.exec_command(COMMAND_RUNNING)
        output_running = stdout.read().decode('utf-8')
        for line in output_running.splitlines():
            #print(f"Procesando línea activa: {line}")  # Depuración
            if not line.startswith(("lo", "vlan")): #and not EXCLUDE_PATTERN.match(line):
                ports_running += 1

        client.close()
        return {"ip": ip, "ports_running": ports_running, "ports_down": ports_down}

    except Exception as e:
        return {"ip": ip, "error": str(e)}

def process_area(area, ips, csv_writer):
    """Procesa todos los switches en un área específica y guarda resultados en CSV."""
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(count_ports, ips))
    
    print(f"\nResultados para el área {area}:")
    for result in results:
        if "error" in result:
            print(f"Switch {result['ip']}: Error - {result['error']}")
            csv_writer.writerow([area, result['ip'], "ERROR", "ERROR", result['error']])
        else:
            print(f"Switch {result['ip']}: Puertos ACTIVOS: {result['ports_running']}, Puertos INACTIVOS: {result['ports_down']}")
            csv_writer.writerow([area, result['ip'], result['ports_running'], result['ports_down'], "OK"])

def main():
    # Directorio para guardar el archivo CSV
    output_dir = r"C:/Users/kramos/Desktop/Log de Script/Reporte Puerto"
    os.makedirs(output_dir, exist_ok=True)
    csv_filename = os.path.join(output_dir, "resultados_switches.csv")

    # Crear y escribir en el archivo CSV
    with open(csv_filename, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Escribir encabezado
        csv_writer.writerow(["Área", "IP del Switch", "Puertos Activos", "Puertos Inactivos", "Estado"])

        for area, ips in switch_ips_by_area.items():
            process_area(area, ips, csv_writer)
    
    print(f"\nResultados guardados en el archivo {csv_filename}")

if __name__ == "__main__":
    main()
