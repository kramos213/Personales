import os
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler

# ======================
# CARGAR CREDENCIALES
# ======================
from dotenv import load_dotenv
load_dotenv()
USER = os.getenv("SW_USER")
PASSWORD = os.getenv("SW_PASSWORD")

# ======================
# FUNCIONES
# ======================
def cargar_areas(archivo):
    areas = {}
    area_actual = None

    with open(archivo, "r") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("[") and linea.endswith("]"):
                area_actual = linea[1:-1]
                areas[area_actual] = []
            else:
                areas[area_actual].append(linea)

    return areas


def cargar_comandos(archivo):
    with open(archivo, "r") as f:
        # Solo devuelve las líneas tal cual
        return [linea.strip() for linea in f if linea.strip()]


def ejecutar_en_switch(ip, comandos):
    print(f"🔌 Conectando a {ip}...")

    device = {
        "device_type": "allied_telesis_awplus",
        "host": ip,
        "username": USER,
        "password": PASSWORD,
        "timeout": 15
    }

    try:
        ssh = ConnectHandler(**device)
        ssh.enable()

        salida = ssh.send_config_set(comandos)
        ssh.save_config()
        ssh.disconnect()

        print(f"✅ Comandos ejecutados en {ip}")
        return f"[OK] {ip}\n{salida}\n"

    except Exception as e:
        print(f"❌ Error en {ip}: {e}")
        return f"[ERROR] {ip} - {e}\n"


# ======================
# PROGRAMA PRINCIPAL
# ======================
areas = cargar_areas("C:\\Git-Kevin\\Personales\\TELECOM\\config\\areas.txt")
comandos = cargar_comandos("C:\\Git-Kevin\\Personales\\TELECOM\\config\\comandos.txt")

# LOG
with open("C:\\Git-Kevin\\Personales\\TELECOM\\outputs\\log_config.txt", "w") as log:
    for area, ips in areas.items():
        print(f"\n===== Área {area} =====")

        with ThreadPoolExecutor(max_workers=10) as executor:
            tareas = {
                executor.submit(ejecutar_en_switch, ip, comandos): ip for ip in ips
            }

            for tarea in tareas:
                resultado = tarea.result()
                log.write(resultado)
