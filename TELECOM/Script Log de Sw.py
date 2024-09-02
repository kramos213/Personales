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

# Archivo único para todos los logs
log_filename = os.path.join(base_log_folder, f"consolidated_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
logger.add(log_filename, format="{time} {level} {message}", level="INFO")

def execute_command(shell, command, delay=2):
    """
    Envía un comando al shell del switch y retorna la salida.
    
    Args:
        shell (paramiko.Channel): El canal SSH del switch.
        command (str): El comando a ejecutar.
        delay (int): Tiempo en segundos para esperar la respuesta.

    Returns:
        str: La salida del comando.
    """
    shell.send(f'{command}\n')
    time.sleep(delay)
    output = shell.recv(65535).decode()
    return output

def analyze_logs(output, keywords):
    """
    Analiza la salida de los logs y filtra las entradas recientes basadas en palabras clave.
    
    Args:
        output (str): La salida del comando 'show log'.
        keywords (list): Lista de palabras clave para filtrar los logs.

    Returns:
        list: Lista de entradas de log relevantes.
    """
    log_entries = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=2)  # Fecha límite para los logs
    
    for line in output.splitlines():
        if any(keyword in line.lower() for keyword in keywords):
            try:
                # Ajusta estos valores según el formato de tus logs
                log_time_str = line[:19]  # Asegúrate de que esto es correcto para tu formato de fecha y hora
                log_time = datetime.datetime.strptime(log_time_str, '%Y %b %d %H:%M:%S')
                
                if log_time >= cutoff_date:
                    log_entries.append(line)
            except ValueError:
                # No se pudo parsear la fecha en el log
                logger.debug(f"No se pudo parsear la fecha en el log: {line}")
                continue

    logger.debug(f"Log entries filtrados: {log_entries}")
    return log_entries

def fetch_and_analyze_logs(switch_ip, area, ssh_username, ssh_password, keywords):
    """
    Conecta al switch, ejecuta comandos y analiza los logs.
    
    Args:
        switch_ip (str): La IP del switch.
        area (str): El área correspondiente al switch.
        ssh_username (str): Nombre de usuario SSH.
        ssh_password (str): Contraseña SSH.
        keywords (list): Lista de palabras clave para filtrar los logs.
    """
    try:
        logger.info(f"Conectando al switch {switch_ip} en el área {area}.")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(switch_ip, username=ssh_username, password=ssh_password)
        shell = ssh.invoke_shell()
        time.sleep(2)

        execute_command(shell, 'enable', delay=2)  # Activar modo privilegiado
        execute_command(shell, 'terminal length 0', delay=2)  # Configurar salida sin paginación
        output_logs = execute_command(shell, 'show log', delay=5)  # Ejecutar el comando para obtener logs
        
        # Agrega este log para verificar el contenido de los logs
        logger.debug(f"Output logs desde {switch_ip} ({area}): {output_logs}")
        
        log_entries = analyze_logs(output_logs, keywords)

        # Escribir encabezado para el área
        logger.info(f"\n\n{'='*50}\nÁrea: {area}\n{'='*50}\n")

        if log_entries:
            for entry in log_entries:
                logger.info(f"Log encontrado en {switch_ip}: {entry}")
        else:
            logger.info(f"No se encontraron entradas de log relevantes en {switch_ip} ({area}).")

        ssh.close()

    except paramiko.AuthenticationException:
        logger.error(f"Error de autenticación al conectar con {switch_ip} ({area}). Verifica las credenciales.")
    except Exception as e:
        logger.error(f"Ocurrió un error al obtener y analizar los logs en {switch_ip} ({area}): {e}")

if __name__ == "__main__":
    keywords = ['error', 'down', 'up', 'warning']  # Palabras clave para filtrar los logs.
    ssh_username = 'TPC'
    ssh_password = 'Tpc2020*'

    # Procesar cada IP de manera secuencial por área
    for area, ips in switch_ips_by_area.items():
        # Agregar encabezado para el área en el archivo de log
        logger.info(f"\n\n{'='*50}\nÁrea: {area}\n{'='*50}\n")
        
        for ip in ips:
            fetch_and_analyze_logs(ip, area, ssh_username, ssh_password, keywords)
