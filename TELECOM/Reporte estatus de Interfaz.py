import paramiko
import os
import csv
import getpass
import time

# Diccionario de switches organizados por área
switch_ips_by_area = {
    "PSO": ["172.16.0.151", "172.16.0.150", "172.16.0.118", "172.16.0.101", "172.16.0.147", "172.16.0.148", "172.16.0.116"],
    "PPB": ["172.16.0.105", "172.16.0.103", "172.16.0.104", "172.16.0.142", "172.16.0.143", "172.16.0.106", "172.16.0.107"],
    "P06": ["172.16.0.108", "172.16.0.109", "172.16.0.202", "172.16.0.140", "172.16.0.146"],
    "P07": ["172.16.0.110", "172.16.0.111", "172.16.0.112", "172.16.0.141", "172.16.0.115"],
    "P08": ["172.16.0.113", "172.16.0.114"],
    "P09": ["172.16.0.120", "172.16.0.121"],
    "P10": ["172.16.0.123", "172.16.0.124"],
    "P11": ["172.16.0.125", "172.16.0.137", "172.16.0.126", "172.16.0.139"],
    "P14": ["172.16.0.127", "172.16.0.128"],
    "P16": ["172.16.0.129", "172.16.0.130", "172.16.0.138"],
    "P17": ["172.16.0.131", "172.16.0.132", "172.16.0.136"],
    "P18": ["172.16.0.133", "172.16.0.134", "172.16.0.135"],
    "P24": ["172.16.0.200", "172.16.0.145"]
}

def execute_commands_on_switch(host, username, password, commands):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password)
        print(f"Conectado al switch {host}")

        remote_conn = ssh.invoke_shell()
        output = ""

        for command in commands:
            remote_conn.send(command + "\n")
            time.sleep(2)  # Esperar a que el comando se ejecute
            while not remote_conn.recv_ready():
                time.sleep(1)  # Asegurarse de que la salida esté lista
            output += remote_conn.recv(65535).decode("utf-8")

        ssh.close()
        return output
    except Exception as e:
        print(f"Error al conectarse al switch {host}: {e}")
        return None

def filter_interface_status(output):
    # Divide la salida en líneas
    lines = output.splitlines()
    filtered_lines = []
    header_found = False

    for line in lines:
        # Busca la cabecera y líneas con datos válidos
        if "Port       Name" in line:
            header_found = True
            filtered_lines.append(line)
        elif header_found:
            if line.strip():  # Ignorar líneas vacías
                filtered_lines.append(line)

    # Retornar solo las líneas de interés
    return filtered_lines

def save_filtered_output_to_csv(filtered_lines, csv_filepath, area, ip):
    if filtered_lines:
        print(f"Guardando CSV en {csv_filepath}")
        with open(csv_filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',')  # Usamos coma como delimitador
            # Escribimos la cabecera con las columnas de área y IP
            writer.writerow(["Área", "IP", "Port", "Name", "Status", "Vlan", "Duplex", "Speed", "Type"])
            for line in filtered_lines:
                # Añadir el área y IP a cada línea filtrada antes de escribirla
                columns = line.split()
                writer.writerow([area, ip] + columns)
    else:
        print(f"Sin datos para guardar en {csv_filepath}")

def main():
    ssh_username = input("Ingrese el nombre de usuario SSH: ")
    ssh_password = getpass.getpass("Ingrese la contraseña SSH: ")

    output_dir = r"C:/Users/kramos/Desktop/Log de Script/Reporte Puerto"
    os.makedirs(output_dir, exist_ok=True)

    commands = ["en", "terminal length 0", "sh int status"]

    for area, ips in switch_ips_by_area.items():
        area_dir = os.path.join(output_dir, area)
        os.makedirs(area_dir, exist_ok=True)

        for ip in ips:
            print(f"Procesando switch: {ip} en el área: {area}")
            output = execute_commands_on_switch(ip, ssh_username, ssh_password, commands)
            if output:
                filtered_lines = filter_interface_status(output)
                if filtered_lines:
                    csv_filename = f"{ip.replace('.', '_')}_interfaces_filtered.csv"
                    csv_filepath = os.path.join(area_dir, csv_filename)
                    save_filtered_output_to_csv(filtered_lines, csv_filepath, area, ip)
                else:
                    print(f"Salida vacía después del filtrado para el switch {ip}")
            else:
                print(f"No se pudo obtener salida para el switch {ip}")

if __name__ == "__main__":
    main()
