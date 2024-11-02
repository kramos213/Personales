import csv
import paramiko
import datetime
import os
import time
from loguru import logger

# Diccionario con IPs organizadas por piso o área
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
}

# Carpeta base para guardar el log
base_log_folder = "C:/Users/kramos/Desktop/Log de Script/Log Sw"
os.makedirs(base_log_folder, exist_ok=True)

# Archivo único para todos los logs y el reporte CSV
log_filename = os.path.join(base_log_folder, f"consolidated_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
csv_filename = os.path.join(base_log_folder, f"report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
logger.add(log_filename, format="{time} {level} {message}", level="INFO")

# Función para guardar en CSV
def save_to_csv(data):
    headers = ['Fecha', 'IP del Switch', 'Área', 'Evento', 'Puerto', 'Detalles']
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for row in data:
            writer.writerow(row)

def execute_command(shell, command, delay=2):
    """Función para enviar comandos al shell SSH y esperar la respuesta."""
    shell.send(command + '\n')
    time.sleep(delay)
    output = shell.recv(65535).decode('utf-8')
    return output

def parse_event(line, switch_ip, area):
    """
    Parsear el evento del log para identificar el tipo de evento, puerto y otros detalles.
    """
    event = ""
    port = ""
    details = line

    if "Disabled learning on" in line:
        event = "Aprendizaje deshabilitado"
        port = line.split("port")[1].split()[0]
    elif "Re-enabled learning on" in line:
        event = "Aprendizaje re-habilitado"
        port = line.split("port")[1].split()[0]
    elif "Port down notification" in line:
        event = "Notificación de puerto apagado"
        port = line.split("port")[1].strip()

    return event, port, details

def analyze_logs(output, keywords, switch_ip, area):
    """
    Analiza la salida de los logs, filtra eventos recientes y retorna datos para el reporte.
    """
    log_entries = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=1)  # Fecha límite para los logs

    for line in output.splitlines():
        if any(keyword in line.lower() for keyword in keywords):
            try:
                log_time_str = line[:19]  # Fecha y hora
                log_time = datetime.datetime.strptime(log_time_str, '%Y %b %d %H:%M:%S')
                if log_time >= cutoff_date:
                    event, port, details = parse_event(line, switch_ip, area)
                    if event:
                        log_entries.append([log_time_str, switch_ip, area, event, port, details])
            except ValueError:
                logger.debug(f"No se pudo parsear la fecha en el log: {line}")
                continue

    logger.debug(f"Log entries filtrados para CSV: {log_entries}")
    return log_entries

def fetch_and_analyze_logs(switch_ip, area, ssh_username, ssh_password, keywords):
    """
    Conecta al switch, ejecuta comandos y analiza los logs.
    """
    try:
        logger.info(f"Conectando al switch {switch_ip} en el área {area}.")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(switch_ip, username=ssh_username, password=ssh_password)
        shell = ssh.invoke_shell()
        time.sleep(2)

        execute_command(shell, 'enable', delay=2)
        execute_command(shell, 'terminal length 0', delay=2)
        output_logs = execute_command(shell, 'show log', delay=5)
        
        log_entries = analyze_logs(output_logs, keywords, switch_ip, area)
        ssh.close()
        return log_entries

    except paramiko.AuthenticationException:
        logger.error(f"Error de autenticación al conectar con {switch_ip} ({area}). Verifica las credenciales.")
        return []
    except Exception as e:
        logger.error(f"Ocurrió un error al obtener y analizar los logs en {switch_ip} ({area}): {e}")
        return []

if __name__ == "__main__":
    keywords = ['error', 'down', 'up', 'warning']
    ssh_username = 'TPC'
    ssh_password = 'Tpc2020*'
    report_data = []

    for area, ips in switch_ips_by_area.items():
        for ip in ips:
            entries = fetch_and_analyze_logs(ip, area, ssh_username, ssh_password, keywords)
            report_data.extend(entries)

    # Guardar el reporte en un archivo CSV
    save_to_csv(report_data)
    logger.info(f"Reporte CSV generado en {csv_filename}")
