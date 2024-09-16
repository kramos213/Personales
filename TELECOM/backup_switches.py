import paramiko
import datetime
import time
import os

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area = {
    "PXX": ["IP","IP"]
    # Agrega más pisos o áreas según sea necesario
}

#

# Credenciales y configuración del servidor TFTP
username = 'XXX'
password = 'XXXXX'
tftp_server = 'IP'

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
            time.sleep(2)
        
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
