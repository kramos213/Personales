import paramiko
import datetime
import os
import time
import re

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area = {
    "area": ["ip del host"],

    # Agrega más pisos o áreas según sea necesario
}


# Credenciales de acceso a los switches
username = 'xx'
password = 'xxxx'

# Especifica la carpeta donde se guardarán los logs
log_folder = "C:/Users/kramos/Desktop/Scritp de Respaldos/Log Sw"

if not os.path.exists(log_folder):
    os.makedirs(log_folder)

log_filename = os.path.join(log_folder, f"log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt")

def log_message(message):
    with open(log_filename, 'a') as log_file:
        log_file.write(message + '\n')

def extract_datetime_from_log(log_entry):
    """
    Extrae la fecha y hora de una entrada de log.
    Ajusta el patrón de acuerdo al formato de tu log.
    """
    pattern = r"(\w+\s+\d+\s+\d+:\d+:\d+)"  # Ejemplo: Aug 31 15:45:30
    match = re.search(pattern, log_entry)
    if match:
        log_time_str = match.group(1)
        log_time = datetime.datetime.strptime(log_time_str, "%b %d %H:%M:%S")
        # Ajustar el año actual
        log_time = log_time.replace(year=datetime.datetime.now().year)
        return log_time
    return None

def analyze_log(output):
    events = []
    now = datetime.datetime.now()
    lines = output.splitlines()

    # Palabras clave para eventos importantes
    important_keywords = ["error", "fail", "critical", "warning", "down", "up", "offline"]

    for line in lines:
        log_time = extract_datetime_from_log(line)
        
        if log_time and (now - log_time).days < 1:
            if any(keyword in line.lower() for keyword in important_keywords):
                events.append(line)
    
    return events

def execute_commands(switch_ip, area, commands):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(switch_ip, username=username, password=password)
        shell = ssh.invoke_shell()
        time.sleep(2)
        
        for command in commands:
            shell.send(f'{command}\n')
            time.sleep(5)
            output = shell.recv(65535).decode()

            events = analyze_log(output)
            if events:
                for event in events:
                    message = f"Evento importante detectado en {switch_ip} ({area}): {event}"
                    print(message)
                    log_message(message)
            else:
                message = f"No se detectaron eventos importantes en {switch_ip} ({area})."
                print(message)
                log_message(message)
        
        ssh.close()
    
    except Exception as e:
        error_message = f"Ocurrió un error con {switch_ip} en {area}: {e}"
        print(error_message)
        log_message(error_message)

def execute_commands_on_all_switches(commands):
    for area, ips in switch_ips_by_area.items():
        start_message = f"Iniciando ejecución de comandos en switches en {area}:"
        print(start_message)
        log_message(start_message)
        
        for ip in ips:
            execute_commands(ip, area, commands)
        
        end_message = f"Ejecución de comandos completada para {area}.\n"
        print(end_message)
        log_message(end_message)

if __name__ == "__main__":
    commands = [
        'en',
        'terminal length 0',
        'sh log'
    ]
    
    execute_commands_on_all_switches(commands)
