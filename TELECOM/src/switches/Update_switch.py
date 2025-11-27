import paramiko
import time
from datetime import datetime
import os

# Lista de switches con su información
switches = [
    {"piso": "P-PB", "area": "RACK 050", "ip": "172.16.0.107"},
    {"piso": "P-PB", "area": "RACK 050", "ip": "172.16.0.106"},
    {"piso": "P-PB", "area": "RACK PRINCIPAL", "ip": "172.16.0.105"},
    {"piso": "P-PB", "area": "RACK PRINCIPAL", "ip": "172.16.0.104"},
    {"piso": "P-PB", "area": "RACK PRINCIPAL", "ip": "172.16.0.143"},
    {"piso": "P-18", "area": "RACK PRINCIPAL", "ip": "172.16.0.135"},
    {"piso": "P-18", "area": "RACK PRINCIPAL", "ip": "172.16.0.134"},
    {"piso": "P-18", "area": "RACK PRINCIPAL", "ip": "172.16.0.133"},
    {"piso": "P-17", "area": "RACK PRINCIPAL", "ip": "172.16.0.136"},
    {"piso": "P-17", "area": "RACK PRINCIPAL", "ip": "172.16.0.131"},
    {"piso": "P-17", "area": "RACK PRINCIPAL", "ip": "172.16.0.132"},
    {"piso": "P-16", "area": "RACK PRINCIPAL", "ip": "172.16.0.138"},
    {"piso": "P-16", "area": "RACK PRINCIPAL", "ip": "172.16.0.129"},
    {"piso": "P-11", "area": "RACK PRINCIPAL", "ip": "172.16.0.125"},
    {"piso": "P-11", "area": "RACK PRINCIPAL", "ip": "172.16.0.137"},
    {"piso": "P-11", "area": "RACK PRINCIPAL", "ip": "172.16.0.126"},
    {"piso": "P-11", "area": "RACK PRINCIPAL", "ip": "172.16.0.139"},
    {"piso": "P-10", "area": "RACK PRINCIPAL", "ip": "172.16.0.124"},
    {"piso": "P-10", "area": "RACK PRINCIPAL", "ip": "172.16.0.123"},
    {"piso": "P-09", "area": "RACK PRINCIPAL", "ip": "172.16.0.121"},
    {"piso": "P-09", "area": "RACK PRINCIPAL", "ip": "172.16.0.120"}
]

# Credenciales para acceder a los switches
username = "TPC"
password = "Tpc2020*"

# Ruta para guardar el archivo de log y progreso
log_file = "C:/Users/kramos/Desktop/TPC2025/reinicio_switches.log"
progress_file = "C:/Users/kramos/Desktop/TPC2025/progreso_reinicios.txt"

# Función para escribir en el log
def escribir_log(mensaje):
    with open(log_file, "a") as log:
        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {mensaje}\n")

# Leer progreso de reinicios
def cargar_progreso():
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return set(f.read().splitlines())
    return set()

# Guardar progreso de reinicios
def guardar_progreso(ip):
    with open(progress_file, "a") as f:
        f.write(ip + "\n")

# Función para reiniciar un switch
def reiniciar_switch(ip, username, password):
    inicio = datetime.now()
    escribir_log(f"Inicio del reinicio del switch {ip}.")

    try:
        print(f"Conectando a {ip}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)
        shell = ssh.invoke_shell()
        
        time.sleep(1)
        shell.send("enable\n")
        time.sleep(1)
        shell.send("reload\n")
        time.sleep(1)
        shell.send("y\n")  # Confirmar el reinicio
        time.sleep(1)

        ssh.close()
        fin = datetime.now()
        escribir_log(f"Finalizó el reinicio del switch {ip}. Duración: {fin - inicio}.")
        print(f"Reinicio completado para {ip}.")
    except Exception as e:
        escribir_log(f"Error al reiniciar el switch {ip}: {e}")
        print(f"Error al reiniciar el switch {ip}: {e}")

# Bucle para reiniciar todos los switches
progreso = cargar_progreso()

while len(progreso) < len(switches):
    hora_actual = datetime.now().hour
    minuto_actual = datetime.now().minute

    if 2 <= hora_actual < 4 or (hora_actual == 3 and minuto_actual <= 59):
        # Selección del próximo switch no reiniciado
        for switch in switches:
            if switch["ip"] not in progreso:
                escribir_log(f"Seleccionado el switch {switch['ip']} en {switch['piso']} {switch['area']} para reinicio.")
                reiniciar_switch(switch["ip"], username, password)
                guardar_progreso(switch["ip"])
                progreso.add(switch["ip"])
                break
    else:
        escribir_log("Fuera del horario permitido. Esperando...")
        print("Fuera del horario permitido. Esperando...")
        time.sleep(300)

escribir_log("Todos los switches han sido reiniciados.")
print("Todos los switches han sido reiniciados.")
