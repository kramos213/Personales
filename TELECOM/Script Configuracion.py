import paramiko
import datetime
import os
import time

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area = {
     "PSO": ["ip del host"],
    # Agrega más pisos o áreas según sea necesario
}

# Credenciales de acceso a los switches
username = 'xxx'
password = 'xxx'

# Especifica la carpeta donde se guardarán los logs
log_folder = "C:/Users/kramos/Desktop/Scritp de Respaldos/Log config"  # Cambia esta ruta por la ruta de tu carpeta de logs

# Asegúrate de que la carpeta exista; si no, créala
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Nombre del archivo de log basado en la fecha y hora actual
log_filename = os.path.join(log_folder, f"log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt")

# Función para registrar mensajes en el archivo de log
def log_message(message):
    with open(log_filename, 'a') as log_file:
        log_file.write(message + '\n')

def execute_commands(switch_ip, area, commands):
    try:
        # Crear una instancia SSHClient
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conectarse al switch
        ssh.connect(switch_ip, username=username, password=password)
        
        # Crear una instancia de transporte para el canal
        shell = ssh.invoke_shell()
        time.sleep(2)  # Esperar para que la conexión se estabilice
        
        # Ejecutar los comandos
        for command in commands:
            shell.send(f'{command}\n')
            time.sleep(2)  # Ajustar el tiempo según sea necesario
            output = shell.recv(65535).decode()

            # Mensaje de éxito o fallo
            if output:
                message = f"Comando '{command}' ejecutado con éxito en {switch_ip} ({area}):\n{output}"
            else:
                message = f"Error al ejecutar comando '{command}' en {switch_ip} ({area})."
            
            # Imprimir y guardar en el log
            print(message)
            log_message(message)
        
        # Cerrar la conexión
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
    # Definir los comandos a ejecutar
    commands = [
        'en',
        'wr'  # Agregar el comando 'wr' al final para guardar los cambios
    ]
    
    # Ejecutar los comandos en todos los switches
    execute_commands_on_all_switches(commands)
