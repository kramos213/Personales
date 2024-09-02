import paramiko
import datetime
import os
import time
import concurrent.futures
import csv
from loguru import logger

# Diccionario con IPs organizadas por piso o área
switch_ips_by_area = {
    "P06-IT": ["172.16.0.201", "172.16.0.224"]
    # Agrega más áreas según sea necesario
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

def validate_vlan_id(vlan_id):
    return vlan_id.isdigit() and 1 <= int(vlan_id) <= 4095

def manage_switch(switch_ip, area, action, **kwargs):
    #results = []
    try:
        # Crear una instancia SSHClient
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conectarse al switch
        ssh.connect(switch_ip, username=kwargs['ssh_username'], password=kwargs['ssh_password'])
        
        # Crear una instancia de transporte para el canal
        shell = ssh.invoke_shell()
        time.sleep(2)  # Esperar para que la conexión se estabilice
        
        if action == 'create_vlan':
            vlan_id = kwargs['vlan_id']
            vlan_name = kwargs['vlan_name']
            if not validate_vlan_id(vlan_id):
                logger.error(f"ID de VLAN '{vlan_id}' no válido en {switch_ip} ({area}).")
                results.append((switch_ip, area, action, f"ID de VLAN '{vlan_id}' no válido"))
                return
            execute_command(shell, 'enable', delay=2)
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, 'vlan database', delay=2)
            execute_command(shell, f'vlan {vlan_id} name {vlan_name}', delay=2)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"VLAN '{vlan_name}' (ID: {vlan_id}) creada en {switch_ip} ({area}).")
            results.append((switch_ip, area, action, f"VLAN '{vlan_name}' (ID: {vlan_id}) creada"))

        elif action == 'rename_port':
            port = kwargs['port']
            new_name = kwargs['new_name']
            execute_command(shell, 'enable', delay=2)
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'interface {port}', delay=2)
            execute_command(shell, f'description {new_name}', delay=2)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Puerto '{port}' renombrado a '{new_name}' en {switch_ip} ({area}).")
            results.append((switch_ip, area, action, f"Puerto '{port}' renombrado a '{new_name}'"))

        elif action == 'toggle_port':
            port = kwargs['port']
            state = kwargs['state']  # 'shutdown' or 'no shutdown'
            execute_command(shell, 'enable', delay=2)
            execute_command(shell, 'conf t', delay=2)
            execute_command(shell, f'interface {port}', delay=2)
            execute_command(shell, state, delay=2)
            execute_command(shell, 'end', delay=2)
            execute_command(shell, 'write memory', delay=5)
            logger.info(f"Puerto '{port}' en {switch_ip} ({area}) ha sido {'apagado' if state == 'shutdown' else 'encendido'}.")
            results.append((switch_ip, area, action, f"Puerto '{port}' {'apagado' if state == 'shutdown' else 'encendido'}"))

        elif action == 'find_mac':
            mac_address = kwargs['mac_address']
            output = execute_command(shell, 'enable', delay=2)
            output += execute_command(shell, f'sh mac add | inc {mac_address}', delay=5)
            logger.info(f"Resultado de la búsqueda de MAC '{mac_address}' en {switch_ip} ({area}):\n{output}")
            results.append((switch_ip, area, action, f"Resultado de búsqueda de MAC: {output}"))

        elif action == 'config_port':
            port_conf = kwargs['port_conf']
            output = execute_command(shell, 'enable', delay=2)
            output += execute_command(shell, f'sh run int {port_conf}', delay=5)
            logger.info(f"Resultado de la configuración del '{port_conf}' en {switch_ip} ({area}):\n{output}")
            results.append((switch_ip, area, action, f"Resultado de configuración: {output}"))

        ssh.close()
    except paramiko.AuthenticationException:
        logger.error(f"Error de autenticación al conectar con {switch_ip} ({area}). Verifica las credenciales.")
        results.append((switch_ip, area, action, "Error de autenticación"))
    except Exception as e:
        logger.error(f"Ocurrió un error al realizar la acción '{action}' en {switch_ip} ({area}): {e}")
        results.append((switch_ip, area, action, f"Error: {e}"))
    finally:
        return results

if __name__ == "__main__":
    actions = {
        1: 'create_vlan',
        2: 'rename_port',
        3: 'toggle_port',
        4: 'find_mac',
        5: 'remove',
        6: 'modify',
        7: 'create',
        8: 'config_port',
        9: 'exit'
    }
    
    action_descriptions = {
        1: "Crear VLAN",
        2: "Renombrar Puerto",
        3: "Encender/Apagar Puerto",
        4: "Buscar Dirección MAC",
        5: "Eliminar Usuario",
        6: "Modificar Usuario",
        7: "Crear Usuario",
        8: "Configuración de Puerto",
        9: "Salir"
    }

    while True:
        print("\nSeleccione una acción:")
        for num, description in action_descriptions.items():
            print(f"{num}. {description}")
        
        try:
            action_index = int(input("\nIngrese el número de la acción deseada: ").strip())
            if action_index not in actions:
                raise ValueError("Número de acción no válido.")

            action = actions[action_index]
            
            if action == 'exit':
                print("Saliendo del programa.")
                break

            ssh_username = 'TPC'
            ssh_password = 'Tpc2020*'
            kwargs = {'ssh_username': ssh_username, 'ssh_password': ssh_password}

            if action == 'create_vlan':
                kwargs['vlan_id'] = input("Ingrese el ID de la VLAN: ")
                kwargs['vlan_name'] = input("Ingrese el nombre de la VLAN: ")

            elif action == 'rename_port':
                kwargs['port'] = input("Ingrese el puerto a renombrar (e.g., port1.0.x): ")
                kwargs['new_name'] = input("Ingrese el nuevo nombre del puerto: ")

            elif action == 'toggle_port':
                kwargs['port'] = input("Ingrese el puerto a apagar/encender (e.g., port1.0.x): ")
                state = input("¿Desea apagar o encender el puerto? (apagar/encender): ").strip().lower()
                kwargs['state'] = 'shutdown' if state == 'apagar' else 'no shutdown'

            elif action == 'find_mac':
                kwargs['mac_address'] = input("Ingrese la dirección MAC a buscar: ")
            
            elif action == 'config_port':
                kwargs['port_conf'] = input("Ingrese el puerto a buscar la configuración: ")

            elif action in ['remove', 'modify', 'create']:
                kwargs['username'] = input("Ingrese el nombre del usuario: ")

            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_ip = {
                    executor.submit(manage_switch, switch_ip, area, action, **kwargs): (switch_ip, area)
                    for area, ips in switch_ips_by_area.items()
                    for switch_ip in ips
                }
                for future in concurrent.futures.as_completed(future_to_ip):
                    switch_ip, area = future_to_ip[future]
                    try:
                        result = future.result()
                        results.extend(result)
                    except Exception as exc:
                        logger.error(f"{switch_ip} ({area}) generó una excepción: {exc}")

        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Se produjo un error: {e}")
