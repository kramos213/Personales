import paramiko
import csv
import os
import datetime

# Ruta para guardar los reportes
output_dir = r"C:/Users/kramos/Desktop/Log de Script/Reporte Puerto"

# Crear la carpeta si no existe
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Diccionario de switches por área
switches_por_area = {
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
}

# Credenciales del usuario
usuario = "TPC"  # Cambia esto por tu usuario
password = "Tpc2020*"  # Cambia esto por tu contraseña

# Archivo para guardar el reporte
output_file = f'reporte_interfaces_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

# Función para obtener el estado de las interfaces
def obtener_estado_interfaces(ip, username, password):
    try:
        # Conexión SSH al switch
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password)

        # Ejecutar el comando
        stdin, stdout, stderr = client.exec_command('show interface status')
        output = stdout.read().decode()

        # Cerrar conexión
        client.close()

        return output
    except Exception as e:
        print(f'Error al conectar a {ip}: {e}')
        return None

# Crear el archivo CSV y escribir la cabecera
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Área', 'IP', 'Port', 'Name', 'Status', 'Vlan', 'Duplex', 'Speed', 'Type'])

    # Obtener información de cada switch por área
    for area, switches in switches_por_area.items():
        for ip in switches:
            estado = obtener_estado_interfaces(ip, usuario, password)
            if estado:
                # Procesar la salida
                for line in estado.splitlines()[3:]:  # Ignorar las dos primeras líneas
                    if line.strip():  # Ignorar líneas vacías
                        partes = line.split()
                        # Verificar si hay suficiente información
                        if len(partes) >= 8:
                            writer.writerow([area, ip] + partes[:8])  # Escribir datos en el CSV

print(f'Reporte generado: {output_file}')
