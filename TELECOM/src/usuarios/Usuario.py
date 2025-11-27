import paramiko
import datetime
import os
import time
from loguru import logger

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area ={
  #"P-SO": ["172.16.0.118", "172.16.0.151", "172.16.0.148", "172.16.0.150", "172.16.0.102", "172.16.0.116", "172.16.0.101", "172.16.0.147"],
  #"P-PB": ["172.16.0.142", "172.16.0.107", "172.16.0.106", "172.16.0.105", "172.16.0.104", "172.16.0.103", "172.16.0.143"],
  #"P-24": ["172.16.0.145", "172.16.0.200"],
  #"P-18": ["172.16.0.135", "172.16.0.134", "172.16.0.133", "172.16.0.149"],
  #"P-17": ["172.16.0.136", "172.16.0.131", "172.16.0.132"],
  #"P-16": ["172.16.0.138", "172.16.0.130", "172.16.0.129"],
  #"P-14": ["172.16.0.128", "172.16.0.127"],
  #"P-11": ["172.16.0.125", "172.16.0.137", "172.16.0.126", "172.16.0.139"],
  #"P-10": ["172.16.0.124", "172.16.0.123"],
  #"P-09": ["172.16.0.121", "172.16.0.120"],
  #"P-08": ["172.16.0.114", "172.16.0.113"],
  #"P-07": ["172.16.0.141", "172.16.0.115", "172.16.0.112", "172.16.0.110", "172.16.0.111"],
  #"P-06": ["172.16.0.108", "172.16.0.109", "172.16.0.146", "172.16.0.140", "172.16.0.201", "172.16.0.202"]
  
    "P-FLOWIT": ["172.16.0.102","172.16.0.101","172.16.0.151","172.16.0.148","172.16.0.104","172.16.0.142","172.16.0.106","172.16.0.108","172.16.0.146",
                 "172.16.0.111","172.16.0.141","172.16.0.115","172.16.0.113","172.16.0.121","172.16.0.123","172.16.0.137",
                 "172.16.0.127","172.16.0.138","172.16.0.136","172.16.0.135","172.16.0.109"]
    
}


# Carpeta para guardar los logs
log_folder = "C:/Users/kramos/Desktop/TPC2025/Usuario"
os.makedirs(log_folder, exist_ok=True)

# Configuración de loguru
log_filename = os.path.join(log_folder, f"log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log")
logger.add(log_filename, format="{time} {level} {message}", level="INFO")

def execute_command(shell, command, delay=2):
    """Función para ejecutar comandos en la shell y registrar su salida."""
    shell.send(f'{command}\n')
    time.sleep(delay)
    output = shell.recv(65535).decode()
    logger.info(f"Comando ejecutado: {command}")
    #logger.info(f"Salida del comando: {output}")
    return output

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

        # Ejecutar 'enable' para asegurarse de estar en modo privilegiado
        output = execute_command(shell, 'enable', delay=2)
        if 'Password' in output:
            logger.info(f"Se solicitó contraseña para modo privilegiado en {switch_ip} ({area}).")
            execute_command(shell, ssh_password, delay=2)  # Si se requiere la contraseña de habilitación

        if action == 'remove':
            # Eliminar usuario
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'no username {username}', delay=5)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Usuario '{username}' eliminado en {switch_ip} ({area}).")

        elif action == 'create':
            # Crear usuario
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'username {username} privilege 15 password {new_password}', delay=5)
            execute_command(shell, f'ssh server allow-users {username}', delay=5)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Usuario '{username}' creado en {switch_ip} ({area}).")

        elif action == 'modify':
            # Modificar usuario
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'username {username} privilege 15 password {new_password}', delay=5)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Contraseña de usuario '{username}' modificada en {switch_ip} ({area}).")

        ssh.close()

    except paramiko.AuthenticationException:
        logger.error(f"Error de autenticación al conectar con {switch_ip} ({area}). Verifica las credenciales.")
    except Exception as e:
        logger.error(f"Ocurrió un error al {action} el usuario '{username}' en {switch_ip} ({area}): {e}")


if __name__ == "__main__":
    while True:
        action = input("\n¿Qué acción desea realizar? (remove/create/modify/exit): ").strip().lower()

        if action == 'exit':
            print("Saliendo del programa.")
            break

        if action not in ['remove', 'create', 'modify']:
            print("Acción no válida. Por favor, elija 'remove', 'create', 'modify' o 'exit'.")
            continue
        
        username = input("Ingrese el nombre de usuario: ")
        new_password = None

        if action in ['create', 'modify']:
            new_password = input(f"Ingrese la nueva contraseña para '{username}': ")

        # Credenciales de SSH
        ssh_username = 'FLOWIT'
        ssh_password = '8&ci7XPN'

        for area, ips in switch_ips_by_area.items():
            for ip in ips:
                manage_user(ip, area, action, username, new_password, ssh_username, ssh_password)
        
        # Preguntar si desea realizar otra acción
        again = input("¿Desea realizar otra acción? (si/no): ").strip().lower()
        if again != 'si':
            print("Saliendo del programa.")
            break
