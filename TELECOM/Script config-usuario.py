import paramiko
import datetime
import os
import time
import concurrent.futures
from loguru import logger

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area = {
    "P06-IT": ["172.16.0.201", "172.16.0.224"],
    # Agrega más pisos o áreas según sea necesario
}

# Carpeta para guardar los logs
log_folder = "C:/Users/kramos/Desktop/Scritp de Respaldos/Log config"
os.makedirs(log_folder, exist_ok=True)

# Configuración de loguru
log_filename = os.path.join(log_folder, f"log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log")
logger.add(log_filename, format="{time} {level} {message}", level="INFO")

def execute_command(shell, command, delay=2):
    shell.send(f'{command}\n')
    time.sleep(delay)
    output = shell.recv(65535).decode()
    return output

def extract_usernames(output):
    usernames = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == 'username':
            usernames.append(parts[1])
    return usernames

def analyze_logs(output, keywords):
    log_entries = []
    for line in output.splitlines():
        if any(keyword in line for keyword in keywords):
            log_entries.append(line)
    return log_entries

def fetch_and_analyze_logs(switch_ip, area, ssh_username, ssh_password, keywords):
    try:
        # Crear una instancia SSHClient
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Conectarse al switch
        ssh.connect(switch_ip, username=ssh_username, password=ssh_password)

        # Crear una instancia de transporte para el canal
        shell = ssh.invoke_shell()
        time.sleep(2)  # Esperar para que la conexión se estabilice

        # Ejecutar el comando para obtener los logs
        output_logs = execute_command(shell, 'enable', delay=2)#terminal length 0
        output_logs = execute_command(shell, 'terminal length 0', delay=2)
        output_logs = execute_command(shell, 'show log', delay=5)
        log_entries = analyze_logs(output_logs, keywords)

        ssh.close()

    except paramiko.AuthenticationException:
        logger.error(f"Error de autenticación al conectar con {switch_ip} ({area}). Verifica las credenciales.")
    except Exception as e:
        logger.error(f"Ocurrió un error al obtener y analizar los logs en {switch_ip} ({area}): {e}")

def manage_user(switch_ip, area, action, username, new_password=None, ssh_username=None, ssh_password=None):
    try:
        # Crear una instancia SSHClient
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conectarse al switch
        ssh.connect(switch_ip, username=ssh_username, password=ssh_password)
        
        # Crear una instancia de transporte para el canal
        shell = ssh.invoke_shell()
        time.sleep(2)  # Esperar para que la conexión se estabilice

        if action in ['modify', 'remove']:
            # Obtener lista de usuarios
            execute_command(shell, 'enable', delay=2)
            output_show = execute_command(shell, 'show running-config | include username', delay=5)
            usernames = extract_usernames(output_show)

            if username not in usernames:
                logger.info(f"Usuario '{username}' no encontrado en {switch_ip} ({area}).")
                ssh.close()
                return

        if action == 'remove':
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'no username {username}', delay=5)
            execute_command(shell, f'no ssh server allow-users {username}', delay=5)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Usuario '{username}' eliminado en {switch_ip} ({area}).")

        elif action == 'modify':
            new_user = input(f"Ingrese el nuevo nombre de usuario para modificar en {switch_ip} ({area}): ")
            new_password = input(f"Ingrese la nueva contraseña para '{new_user}': ")
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'username {new_user} privilege 15 password {new_password}', delay=5)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Usuario '{username}' modificado a '{new_user}' en {switch_ip} ({area}).")

        elif action == 'create':
            if new_password is None:
                new_password = input(f"Ingrese la contraseña para '{username}': ")
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'username {username} password {new_password}', delay=5)
            execute_command(shell, f'ssh server allow-users {username}', delay=5)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Usuario '{username}' creado en {switch_ip} ({area}).")

        ssh.close()

    except paramiko.AuthenticationException:
        logger.error(f"Error de autenticación al conectar con {switch_ip} ({area}). Verifica las credenciales.")
    except Exception as e:
        logger.error(f"Ocurrió un error al {action} el usuario '{username}' en {switch_ip} ({area}): {e}")

if __name__ == "__main__":
    while True:
        action = input("\n¿Qué acción desea realizar? (remove/modify/create/fetch_logs/exit): ").strip().lower()

        if action == 'exit':
            print("Saliendo del programa.")
            break

        if action not in ['remove', 'modify', 'create', 'fetch_logs']:
            print("Acción no válida. Por favor, elija 'remove', 'modify', 'create', 'fetch_logs' o 'exit'.")
            continue
        
        else:
            if action == 'modify':
                username = input("Ingrese el nombre de usuario a modificar: ")
                new_password = input(f"Ingrese la nueva contraseña para '{username}': ")
            elif action in ['remove', 'create']:
                username = input("Ingrese el nombre de usuario a eliminar o crear: ")
                if action == 'create':
                    new_password = input(f"Ingrese la contraseña para '{username}': ")
                else:
                    new_password = None

            # Credenciales de SSH
            ssh_username = 'XXX'
            ssh_password = 'XXXX*'

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(manage_user, ip, area, action, username, new_password, ssh_username, ssh_password)
                    for area, ips in switch_ips_by_area.items()
                    for ip in ips
                ]
                concurrent.futures.wait(futures)
        
        # Preguntar si desea realizar otra acción
        again = input("¿Desea realizar otra acción? (si/no): ").strip().lower()
        if again != 'si':
            print("Saliendo del programa.")
            break
