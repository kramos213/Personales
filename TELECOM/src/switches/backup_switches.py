import paramiko
import datetime
import time
import os

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area = {
    #"PSO": ["172.16.0.151","172.16.0.150","172.16.0.118","172.16.0.101","172.16.0.147","172.16.0.148","172.16.0.116"],
    #"PPB": ["172.16.0.105","172.16.0.103","172.16.0.104","172.16.0.142","172.16.0.143","172.16.0.106""172.16.0.107"],
    #"P06": ["172.16.0.108","172.16.0.109","172.16.0.201","172.16.0.202","172.16.0.140","172.16.0.224","172.16.0.146"],
    #"P07": ["172.16.0.110","172.16.0.111","172.16.0.112","172.16.0.141","172.16.0.115"],#,"172.16.0.149"],
    #"P08": ["172.16.0.113","172.16.0.114"],
    #"P09": ["172.16.0.120","172.16.0.121","172.16.0.119"],
    #"P10": ["172.16.0.123","172.16.0.124"],
    #"P11": ["172.16.0.125","172.16.0.137","172.16.0.126","172.16.0.139"],
    #"P14": ["172.16.0.127","172.16.0.128"],
    "P16": ["172.16.0.130","172.16.0.138"],
    "P17": ["172.16.0.131","172.16.0.132","172.16.0.136"],
    "P18": ["172.16.0.133","172.16.0.134","172.16.0.135"],
    "P24": ["172.16.0.200","172.16.0.145"]
    # Agrega más pisos o áreas según sea necesario
}

# Credenciales y configuración del servidor TFTP
username = 'TPC'
password = 'Tpc2020*'
tftp_server = '172.16.0.254'

# Especifica la carpeta donde se guardarán los logs
log_folder = "C:/Users/kramos/Desktop/Scritp de Respaldos/Log respaldos"  # Cambia esta ruta por la ruta de tu carpeta de logs

# Asegúrate de que la carpeta exista; si no, créala
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Nombre del archivo de log basado en la fecha y hora actual
log_filename = os.path.join(log_folder, f"backup_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt")

# Función para registrar mensajes en el archivo de log
def log_message(message):
    with open(log_filename, 'a') as log_file:
        log_file.write(message + '\n')

def backup_switch(switch_ip, area):
    # Generar un nombre de archivo único para cada switch
    backup_filename = f"{area}-{switch_ip}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.cfg"
    
    # Comandos interactivos para respaldo
    commands = [
        'en',
        'copy flash tftp',
        'default.cfg',
        tftp_server,
        backup_filename
    ]

    try:
        # Crear una instancia SSHClient
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conectarse al switch
        ssh.connect(switch_ip, username=username, password=password)
        
        # Crear una sesión interactiva
        shell = ssh.invoke_shell()
        shell.settimeout(60)
        
        # Esperar a que el shell esté listo
        time.sleep(2)
        
        # Ejecutar comandos uno por uno
        for command in commands:
            shell.send(command + '\n')
            time.sleep(4)
        
        # Leer la salida para confirmar éxito o fallo
        output = ''
        while True:
            if shell.recv_ready():
                output += shell.recv(4096).decode()
                if 'Successful' in output or 'Failed' in output:
                    break
            time.sleep(2)
        
        # Mensaje de éxito o fallo
        if 'Successful' in output:
            message = f"Respaldo realizado con exito para {switch_ip} en {area}. Archivo guardado como {backup_filename} en el servidor TFTP {tftp_server}"
        else:
            message = f"El respaldo para {switch_ip} en {area} no fue exitoso."
        
        # Imprimir y guardar en el log
        print(message)
        log_message(message)
        
        # Cerrar la conexión
        ssh.close()
    
    except Exception as e:
        error_message = f"Ocurrió un error con {switch_ip} en {area}: {e}"
        print(error_message)
        log_message(error_message)

def backup_switches_by_area():
    for area, ips in switch_ips_by_area.items():
        start_message = f"Iniciando respaldo para switches en {area}:"
        print(start_message)
        log_message(start_message)
        
        for ip in ips:
            backup_switch(ip, area)
        
        end_message = f"Respaldo completado para {area}.\n"
        print(end_message)
        log_message(end_message)

if __name__ == "__main__":
    backup_switches_by_area()
