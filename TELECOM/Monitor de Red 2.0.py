import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from ping3 import ping
from flask import Flask, render_template_string
import paramiko
import logging
import re
from itertools import groupby

# Configuración segura
EMAIL_FROM = os.getenv("SMTP_EMAIL_FROM")
PASSWORD_SMTP = os.getenv("SMTP_PASSWORD")
EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
ssh_credentials = {
    "username": os.getenv("SSH_USERNAME","TPC"),
    "password": os.getenv("SSH_PASSWORD","Us3r@Tpc2024*"),
    "port": int(os.getenv("SSH_PORT", 22))
}

# Configuración de switches con dispositivos esperados
switch_ips_by_segment = {
    "PSO": [
        {"ip": "172.16.0.118", "name": "CCTV", "expected_devices": 1},
        {"ip": "172.16.0.151", "name": "ALMACEN", "expected_devices": 1},
        {"ip": "172.16.0.148", "name": "DATA CENTER", "expected_devices": 1},
        {"ip": "172.16.0.150", "name": "ALMACEN", "expected_devices": 1},
        {"ip": "172.16.0.102", "name": "DATA CENTER", "expected_devices": 2},
        {"ip": "172.16.0.116", "name": "DATA CENTER", "expected_devices": 1},
        {"ip": "172.16.0.101", "name": "DATA CENTER", "expected_devices": 1},
        {"ip": "172.16.0.147", "name": "DATA CENTER", "expected_devices": 1},
    ],
    "PPB": [
        {"ip": "172.16.0.142", "name": "FARMACIA DE CALLE", "expected_devices": 1},
        {"ip": "172.16.0.107", "name": "RACK 050", "expected_devices": 1},
        {"ip": "172.16.0.106", "name": "RACK 050", "expected_devices": 1},
        {"ip": "172.16.0.105", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.104", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.103", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.143", "name": "RACK PRINCIPAL", "expected_devices": 2}
    ],
    "P06": [
        {"ip": "172.16.0.108", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.109", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.146", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.140", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.201", "name": "RACK IT", "expected_devices": 1},
        {"ip": "172.16.0.202", "name": "RACK CTC", "expected_devices": 1},
        {"ip": "172.16.0.224", "name": "RACK IT", "expected_devices": 1}
    ],
    "P07": [
        {"ip": "172.16.0.141", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.115", "name": "RACK UROLOGIA", "expected_devices": 1},
        {"ip": "172.16.0.112", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.149", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.110", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.111", "name": "RACK RRHH", "expected_devices": 1}
    ],
    "P08": [
        {"ip": "172.16.0.114", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.113", "name": "RACK PRINCIPAL", "expected_devices": 3}
    ],
    "P09": [
        {"ip": "172.16.0.119", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.122", "name": "RACK PRINCIPAL", "expected_devices": 0},
        {"ip": "172.16.0.121", "name": "RACK PRINCIPAL", "expected_devices": 3},
        {"ip": "172.16.0.120", "name": "RACK PRINCIPAL", "expected_devices": 1}
    ],
    "P10": [
        {"ip": "172.16.0.124", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.123", "name": "RACK PRINCIPAL", "expected_devices": 4}
    ],
    "P11": [
        {"ip": "172.16.0.125", "name": "RACK PRINCIPAL", "expected_devices": 3},
        {"ip": "172.16.0.137", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.126", "name": "RACK PRINCIPAL", "expected_devices": 3},
        {"ip": "172.16.0.139", "name": "RACK PRINCIPAL", "expected_devices": 2}
    ],
    "P14": [
        {"ip": "172.16.0.128", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.127", "name": "RACK PRINCIPAL", "expected_devices": 4}
    ],
    "P16": [
        {"ip": "172.16.0.138", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.130", "name": "RACK PRINCIPAL", "expected_devices": 3},
        {"ip": "172.16.0.129", "name": "RACK PRINCIPAL", "expected_devices": 3}
    ],
    "P17": [
        {"ip": "172.16.0.136", "name": "RACK PRINCIPAL", "expected_devices": 2},
        {"ip": "172.16.0.131", "name": "RACK PRINCIPAL", "expected_devices": 4},
        {"ip": "172.16.0.132", "name": "RACK PRINCIPAL", "expected_devices": 3}
    ],
    "P18": [
        {"ip": "172.16.0.135", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.149", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.134", "name": "RACK PRINCIPAL", "expected_devices": 3},
        {"ip": "172.16.0.133", "name": "RACK PRINCIPAL", "expected_devices": 4}
    ],
    
    "P24": [
        {"ip": "172.16.0.145", "name": "RACK PRINCIPAL", "expected_devices": 1},
        {"ip": "172.16.0.200", "name": "RACK PRINCIPAL", "expected_devices": 1}
    ],
    # Agrega más segmentos y switches aquí...
}

# Inicialización del estado de switches
switch_status = {
    device["ip"]: {
        "state": "unknown",
        "stack": [],
        "current_devices": 0,
        "expected_devices": device["expected_devices"],
        "name": device["name"]
    }
    for segment in switch_ips_by_segment.values()
    for device in segment
}

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inicialización de la aplicación Flask
app = Flask(__name__)

def execute_ssh_command(ip, command):
    """Ejecuta un comando SSH y devuelve la salida."""
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port=ssh_credentials["port"], username=ssh_credentials["username"],
                        password=ssh_credentials["password"], timeout=5)
            _, stdout, _ = ssh.exec_command(command)
            return stdout.read().decode()
    except Exception as e:
        logging.error(f"Error al conectar con {ip}: {e}")
        return None

def parse_stack_output(output):
    """Parses the `show stack` command output."""
    stack_info = []
    for line in output.splitlines():
        match = re.match(r"^\d+\s+-\s+([\da-fA-F.]+)\s+\d+\s+Ready\s+(Active Master|Backup Member)", line)
        if match:
            mac, role = match.groups()
            stack_info.append({"MAC": mac, "Role": role})
    return stack_info

def monitor_device(ip):
    """Monitorea un dispositivo individual."""
    try:
        response = ping(ip, timeout=2)
        state = "online" if response else "offline"

        if switch_status[ip]["state"] != state:
            switch_status[ip]["state"] = state

        if state == "online":
            output = execute_ssh_command(ip, "show stack")
            if output:
                stack = parse_stack_output(output)
                current_devices = len(stack)

                switch_status[ip]["stack"] = stack
                switch_status[ip]["current_devices"] = current_devices

                # Verifica si faltan dispositivos
                if current_devices < switch_status[ip]["expected_devices"]:
                    switch_status[ip]["state"] = "amber"
                    logging.warning(
                        f"Switch {ip}: Faltan dispositivos. Esperados: {switch_status[ip]['expected_devices']}, actuales: {current_devices}"
                    )
                else:
                    switch_status[ip]["state"] = "online"
    except Exception as e:
        logging.error(f"Error monitoreando {ip}: {e}")

def monitor_switches():
    """Monitorea switches y verifica cantidad de dispositivos físicos de manera simultánea."""
    while True:
        with ThreadPoolExecutor(max_workers=10) as executor:
            for segment, devices in switch_ips_by_segment.items():
                for device in devices:
                    executor.submit(monitor_device, device["ip"])
        time.sleep(10)  # Intervalo ajustado para reducir la carga

@app.route("/")
def dashboard():
    """Renderiza el dashboard."""
    total_switches = len(switch_status)
    total_online = sum(1 for s in switch_status.values() if s["state"] == "online")
    total_offline = total_switches - total_online

    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta http-equiv="refresh" content="5">
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard de Monitoreo</title>
            <style>
           body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background-color: var(--bg-color);
                color: var(--text-color);
                transition: background-color 0.3s, color 0.3s;
            }
            :root {
                --bg-color: #2c2f33;
                --text-color: #ffffff;
                --header-bg: #23272a;
                --card-bg: #373c43;
                --table-header-bg: #475161;
                --online-color: #43a047;
                --offline-color: #e53935;
                --unknown-color: #fb8c00;
                --total-color: #2196f3;
                --stack-role-color: #FFD700;
                --amber-color: #FFA500;
                
            }
            .light-mode {
                --bg-color: #f7f9fc;
                --text-color: #2c2f33;
                --header-bg: #e3e6eb;
                --card-bg: #ffffff;
                --table-header-bg: #f0f1f5;
                --online-color: #43a047;
                --offline-color: #e53935;
                --unknown-color: #fb8c00;
                --total-color: #1976d2;
            }
            header {
                background-color: var(--header-bg);
                padding: 20px;
                text-align: center;
                color: var(--text-color);
                font-size: 2rem;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            }
            #toggleMode {
                position: absolute;
                top: 15px;
                right: 15px;
                background-color: var(--table-header-bg);
                color: var(--text-color);
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            }
            .stats {
                display: flex;
                justify-content: space-around;
                margin: 20px;
                gap: 20px;
            }
            .card {
                background-color: var(--card-bg);
                color: var(--text-color);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                flex: 1;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            }
            .card h3 {
                font-size: 1.5rem;
                margin: 0 0 10px;
            }
            .card p {
                font-size: 2.5rem;
                font-weight: bold;
                margin: 0;
                color: var(--total-color);
            }
            .card.online p {
                color: white;
            }
            .card.offline p {
                color: white;
            }
            
            .container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(650px, 1fr));
                gap: 20px;
                padding: 20px;
            }
            .segment {
                background-color: var(--card-bg);
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            }
            .segment h2 {
                background-color: var(--table-header-bg);
                color: var(--text-color);
                padding: 10px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 15px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            
            th, td {
                padding: 10px;
                text-align: center;
                border: 1px solid #444;
                font-size: 0.9rem;
            }

            th {
                background-color: var(--table-header-bg);
                color: var(--text-color);
                text-transform: uppercase;
            }

            td:first-child {
                text-align: left;
            }

            tr:hover {
                background-color: var(--hover-color);
            }

            /* Status Colors */
            .status {
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                text-transform: uppercase;
                color: #fff;
            }

            .online {
                background-color: var(--online-color);
            }

            .offline {
                background-color: var(--offline-color);
            }

            .unknown {
                background-color: var(--unknown-color);
            }

            .amber {
                background-color: var(--amber-color);
                color: #000;
            }

            /* Stack Info */
            .stack-info {
                text-align: left;
                font-size: 0.9rem;
                line-height: 1.4;
                text-align: justify;
            }

            .stack-role {
                font-weight: bold;
                color: var(--stack-role-color);
            }

            /* Responsiveness */
            @media (max-width: 768px) {
                header {
                    text-align: center;
                    padding: 10px 0;
                    font-size: 1.6rem;
                    margin-bottom: 10px;
                }
                
                #toggleMode  {
                    font-size: 0.9rem;
                    margin-top: 10px;
                }
                
                .stats {
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 10px;
                }
                
                .card {
                    width: 100%;
                    max-width: 280px;
                    margin: 5px auto;
                    text-align: center;
                }

                .container {
                    grid-template-columns: 1fr; /* Ajusta el layout a una sola columna */
                    gap: 15px;
                    padding: 10px;
                }

                .segment {
                    padding: 15px; /* Reduce el padding para mejor ajuste */
                    box-shadow: none; /* Opcional: elimina sombras para un diseño más limpio */
                }

                .segment h2 {
                    font-size: 1rem; /* Ajusta el tamaño de los encabezados */
                    padding: 10px;
                    margin-bottom: 10px;
                }

                table {
                    font-size: 0.8rem; /* Reduce el tamaño del texto en la tabla */
                    overflow-x: auto; /* Habilita scroll horizontal si el contenido es demasiado ancho */
                    display: block; /* Permite que la tabla se adapte al ancho del contenedor */
                }

                th, td {
                    padding: 8px 10px; /* Ajusta el padding para ahorrar espacio */
                    font-size: 0.85rem; /* Disminuye el tamaño de texto */
                    white-space: nowrap; /* Evita que el texto se desborde */
                }

                th {
                    text-align: center; /* Centra el texto de los encabezados */
                }

                td {
                    text-align: left; /* Alinea las celdas a la izquierda */
                }

                .status-online, .status-offline {
                    padding: 4px 8px; /* Reduce el padding de los indicadores de estado */
                    font-size: 0.8rem;
                }           
            }

        </style>
        </head>
        <body>
            <header>
                The Panama Clinic - Dashboard de Monitoreo
            </header>
            <div class="stats">
                <div class="card">
                    <h3>Total Switches</h3>
                    <p>{{ total_switches }}</p>
                </div>
                <div class="card online">
                    <h3>Online</h3>
                    <p>{{ total_online }}</p>
                </div>
                <div class="card offline">
                    <h3>Offline</h3>
                    <p>{{ total_offline }}</p>
                </div>
            </div>
            <div class="container">
                {% for segment, devices in switch_ips_by_segment.items() %}
                <div class="segment">
                    <h2>{{ segment }}</h2>
                    {% for subsegment_name, subsegment_devices in devices|groupby('name') %}
                    <h3>{{ subsegment_name }}</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>IP</th>
                                <th>Estado</th>
                                <th>Dispositivos Físicos</th>
                                <th>Stack</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for device in subsegment_devices %}
                            <tr>
                                <td>{{ device.ip }}</td>
                                <td><span class="status {{ switch_status[device.ip].state }}">{{ switch_status[device.ip].state }}</span></td>
                                <td>
                                    {{ switch_status[device.ip].current_devices }} / {{ switch_status[device.ip].expected_devices }}
                                </td>
                                <td>
                                    {% if switch_status[device.ip].stack %}
                                        {% for stack in switch_status[device.ip].stack %}
                                        <div>
                                            <span>{{ stack.MAC }}</span> - 
                                            <span class="stack-role">{{ stack.Role }}</span>
                                        </div>
                                        {% endfor %}
                                    {% else %}
                                    N/A
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
        </body>
        </html>
        """,
        total_switches=total_switches,
        total_online=total_online,
        total_offline=total_offline,
        switch_ips_by_segment=switch_ips_by_segment,
        switch_status=switch_status
    )

if __name__ == "__main__":
    threading.Thread(target=monitor_switches, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
