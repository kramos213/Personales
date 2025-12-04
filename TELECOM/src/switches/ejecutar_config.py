import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from netmiko import ConnectHandler

# ======================
# CARGAR .ENV
# ======================
load_dotenv()
USER = os.getenv("SW_USER")
PASSWORD = os.getenv("SW_PASSWORD")
SNMP_COMM = os.getenv("SNMP_COMMUNITY")
SNMP_CONTACT = os.getenv("SNMP_CONTACT")

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
        return f.read()


def preparar_comandos(ip, plantilla):
    c = plantilla.replace("{{IP}}", ip)
    c = c.replace("{{SNMP}}", SNMP_COMM)
    c = c.replace("{{CONTACTO}}", SNMP_CONTACT)
    return c.splitlines()


def ejecutar_en_switch(ip, comandos):
    print(f"🔌 Conectando a {ip}...")

    device = {
        "device_type": "allied_telesis_awplus",   # Para Allied Telesis
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

        print(f"✅ Configuración aplicada en {ip}")
        return f"[OK] {ip}\n{salida}\n"

    except Exception as e:
        print(f"❌ Error en {ip}: {e}")
        return f"[ERROR] {ip} - {e}\n"


# ======================
# PROGRAMA PRINCIPAL
# ======================
areas = cargar_areas("../config/areas.txt")
plantilla = cargar_comandos("../config/comandos.txt")

# LOG
with open("../outputs/log_config.txt", "w") as log:

    for area, ips in areas.items():
        print(f"\n===== Área {area} =====")

        # Ejecutar en paralelo (hasta 10 switches simultáneos)
        with ThreadPoolExecutor(max_workers=10) as executor:

            tareas = {
                executor.submit(
                    ejecutar_en_switch,
                    ip,
                    preparar_comandos(ip, plantilla)
                ): ip for ip in ips
            }

            for tarea in tareas:
                resultado = tarea.result()
                log.write(resultado)
