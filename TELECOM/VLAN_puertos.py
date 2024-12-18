import paramiko
from concurrent.futures import ThreadPoolExecutor
import csv
import os
import re

# Configuración de las credenciales y base de datos
USERNAME = "TPC"
PASSWORD = "Tpc2020*"

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
    "P18": ["172.16.0.133", "172.16.0.134", "172.16.0.135"],
    "P24": ["172.16.0.200", "172.16.0.145"]
}


# Comando para obtener el estado de las VLANs
COMMAND_VLAN = "sh vlan brief"

def count_vlans(ip):
    """Conecta al switch y cuenta cuántos puertos están configurados para cada VLAN, excluyendo la VLAN 1 y líneas con '======'."""
    vlan_counts = {}

    try:
        # Conexión SSH al switch
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=USERNAME, password=PASSWORD)

        # Comando para obtener el estado de las VLANs
        stdin, stdout, stderr = client.exec_command(COMMAND_VLAN)
        output_vlan = stdout.read().decode('utf-8')

        # Procesar las líneas de la salida
        for line in output_vlan.splitlines():
            # Excluir la VLAN 1 (default) y líneas con '======'
            if "1       default" in line or "=======" in line:
                continue

            # Buscar el número de VLAN y los puertos asociados
            parts = line.split()
            if len(parts) > 4:
                vlan_id = parts[0]
                vlan_ports = parts[4:]

                # Contar puertos
                vlan_ports_count = sum(1 for port in vlan_ports if port.startswith("port"))

                if vlan_id not in vlan_counts:
                    vlan_counts[vlan_id] = 0
                vlan_counts[vlan_id] += vlan_ports_count

        client.close()
        return {"ip": ip, "vlan_counts": vlan_counts}

    except Exception as e:
        return {"ip": ip, "error": str(e)}

def process_area(area, ips, csv_writer):
    """Procesa todos los switches en un área específica y guarda los resultados en un archivo CSV."""
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(count_vlans, ips))
    
    print(f"\nResultados para el área {area}:")
    for result in results:
        if "error" in result:
            print(f"Switch {result['ip']}: Error - {result['error']}")
            csv_writer.writerow([area, result['ip'], "ERROR", "ERROR", result['error']])
        else:
            for vlan_id, port_count in result["vlan_counts"].items():
                print(f"Switch {result['ip']}: VLAN {vlan_id} tiene {port_count} puertos configurados.")
                csv_writer.writerow([area, result['ip'], vlan_id, port_count, "OK"])

def main():
    # Directorio para guardar el archivo CSV
    output_dir = r"C:/Users/kramos/Desktop/TPC2025"
    os.makedirs(output_dir, exist_ok=True)
    csv_filename = os.path.join(output_dir, "resultados_vlans.csv")

    # Crear y escribir en el archivo CSV
    with open(csv_filename, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Escribir encabezado
        csv_writer.writerow(["Área", "IP del Switch", "VLAN ID", "Puertos Configurados", "Estado"])

        for area, ips in switch_ips_by_area.items():
            process_area(area, ips, csv_writer)
    
    print(f"\nResultados guardados en el archivo {csv_filename}")

if __name__ == "__main__":
    main()
