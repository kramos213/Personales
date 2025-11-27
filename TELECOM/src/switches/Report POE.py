import paramiko
import csv
import os
from datetime import datetime

# Ruta para guardar los reportes
output_dir = r"C:/Users/kramos/Desktop/Log de Script/POE"

# Crear la carpeta si no existe
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Obtener la fecha actual en formato 'YYYY-MM-DD'
current_date = datetime.now().strftime("%Y-%m-%d")

# Diccionario de áreas y sus respectivas IPs de switches
switch_ips_by_area = {
    "PSO": ["172.16.0.151", "172.16.0.150", "172.16.0.118", "172.16.0.101", "172.16.0.147", "172.16.0.148", "172.16.0.116"],
    "PPB": ["172.16.0.105", "172.16.0.103", "172.16.0.104", "172.16.0.142", "172.16.0.143", "172.16.0.106", "172.16.0.107"],
    "P06": ["172.16.0.108", "172.16.0.109", "172.16.0.202", "172.16.0.140", "172.16.0.146"],
    "P07": ["172.16.0.110", "172.16.0.111", "172.16.0.112", "172.16.0.141", "172.16.0.115"],
    "P08": ["172.16.0.113", "172.16.0.114"],
    "P09": ["172.16.0.120", "172.16.0.121", "172.16.0.119"],
    "P10": ["172.16.0.123", "172.16.0.124"],
    "P11": ["172.16.0.125", "172.16.0.137", "172.16.0.126", "172.16.0.139"],
    "P14": ["172.16.0.127", "172.16.0.128"],
    "P16": ["172.16.0.129", "172.16.0.130", "172.16.0.138"],
    "P17": ["172.16.0.131", "172.16.0.132", "172.16.0.136"],
    "P18": ["172.16.0.133", "172.16.0.134", "172.16.0.135"],
    "P24": ["172.16.0.200", "172.16.0.145"]
    # Agrega el resto de las áreas y sus IPs según sea necesario
}

# Usuario y contraseña para todos los switches
username = "TPC"
password = "Tpc2020*"

# Función para conectar y ejecutar comandos en el switch
def get_poe_data(ip, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Conexión SSH al switch
        client.connect(ip, username=username, password=password)
        
        # Enviar comandos
        stdin, stdout, stderr = client.exec_command("sh power-inline")
        
        # Leer y procesar la salida
        output = stdout.read().decode().strip()
        
        # Verificar si PoE está deshabilitado o no está en ejecución
        if "Power-inline is disabled" in output or "Power-inline is not running" in output:
            print(f"PoE deshabilitado o no en ejecución en el switch {ip}.")
            return {"IP": ip, "Area": "", "PoE Status": "Disabled/Not Running", "Stack Members": [], "PoE Interfaces": []}
        
        # Procesar los datos si PoE está habilitado
        return parse_poe_output(output)
        
    except Exception as e:
        print(f"Error connecting to switch {ip}: {e}")
        return None
    finally:
        client.close()

# Función para parsear la salida y extraer la información de PoE
def parse_poe_output(output):
    lines = output.splitlines()
    poe_data = {"Stack Members": [], "PoE Interfaces": []}
    section = None

    for line in lines:
        # Detectar secciones
        if "PoE Status:" in line:
            section = "stack"
        elif "PoE Interface:" in line:
            section = "interface"
        elif section == "stack" and "Stack member" in line:
            member_info = {"Stack Member": line.strip()}
            poe_data["Stack Members"].append(member_info)
        elif section == "stack" and line.strip():
            key_value = line.strip().split(":")
            if len(key_value) == 2:
                key, value = key_value
                if poe_data["Stack Members"]:  # Verificar que haya miembros en stack
                    poe_data["Stack Members"][-1][key.strip()] = value.strip()
        elif section == "interface" and line.strip():
            interface_info = line.split()
            if len(interface_info) >= 7:
                interface_data = {
                    "Interface": interface_info[0],
                    "Admin": interface_info[1],
                    "Pri": interface_info[2],
                    "Oper": interface_info[3],
                    "Power (mW)": interface_info[4],
                    "Device": interface_info[5],
                    "Class": interface_info[6],
                    "Max (mW)": interface_info[7] if len(interface_info) > 7 else "n/a"
                }
                poe_data["PoE Interfaces"].append(interface_data)
    
    return poe_data

# Escribir los datos del Stack en un archivo CSV
def write_stack_report(data):
    file_path = os.path.join(output_dir, f"stack_report_{current_date}.csv")
    with open(file_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        
        # Escribir encabezados para los datos de Stack
        writer.writerow(["Área", "Switch IP", "Stack Member", "Nominal Power", "Power Allocated", 
                         "Power Requested", "Actual Power Consumption", "Operational Status",
                         "Power Usage Threshold", "Power Source", "Power Management Mode"])
        
        # Escribir datos de Stack
        for switch in data:
            if switch.get("PoE Status") == "Disabled/Not Running":
                continue
            for member in switch["Stack Members"]:
                writer.writerow([
                    switch["Area"],
                    switch["IP"],
                    member.get("Stack Member", ""),
                    member.get("Nominal Power", ""),
                    member.get("Power Allocated", ""),
                    member.get("Power Requested", ""),
                    member.get("Actual Power Consumption", ""),
                    member.get("Operational Status", ""),
                    member.get("Power Usage Threshold", ""),
                    member.get("Power Source", ""),
                    member.get("Power management mode", "")
                ])

# Escribir los datos de Puertos PoE en un archivo CSV
def write_ports_report(data):
    file_path = os.path.join(output_dir, f"ports_report_{current_date}.csv")
    with open(file_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        
        # Escribir encabezados para los datos de PoE Interfaces
        writer.writerow(["Área", "Switch IP", "Interface", "Admin", "Pri", "Oper", "Power (mW)", "Device", "Class", "Max (mW)"])
        
        # Escribir datos de PoE Interfaces
        for switch in data:
            if switch.get("PoE Status") == "Disabled/Not Running":
                continue
            for interface in switch["PoE Interfaces"]:
                writer.writerow([
                    switch["Area"],
                    switch["IP"],
                    interface.get("Interface", ""),
                    interface.get("Admin", ""),
                    interface.get("Pri", ""),
                    interface.get("Oper", ""),
                    interface.get("Power (mW)", ""),
                    interface.get("Device", ""),
                    interface.get("Class", ""),
                    interface.get("Max (mW)", "")
                ])

# Recopilar datos de todos los switches
all_poe_data = []
for area, ips in switch_ips_by_area.items():
    for ip in ips:
        poe_data = get_poe_data(ip, username, password)
        if poe_data:
            poe_data["IP"] = ip
            poe_data["Area"] = area
            all_poe_data.append(poe_data)

# Generar los archivos CSV de Stack y Puertos
write_stack_report(all_poe_data)
write_ports_report(all_poe_data)
print("Los archivos CSV 'stack_report.csv' y 'ports_report.csv' han sido generados y guardados en la carpeta especificada.")
