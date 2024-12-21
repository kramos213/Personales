import os
import time
import threading
from ping3 import ping
from flask import Flask, render_template_string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configuración segura (usar variables de entorno en producción)
EMAIL_FROM = os.getenv("SMTP_EMAIL_FROM", "apps@thepanamaclinic.com")
PASSWORD_SMTP = os.getenv("SMTP_PASSWORD", "Informatica2019")
EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "kramos@thepanamaclinic.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# Logging para monitoreo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de switches por segmentos
switch_ips_by_segment = {
    "PSO": ["172.16.0.151", "172.16.0.150", "172.16.0.118", "172.16.0.101", "172.16.0.102", "172.16.0.147", "172.16.0.148", "172.16.0.116"],
    "PPB": ["172.16.0.105", "172.16.0.103", "172.16.0.104", "172.16.0.142", "172.16.0.143", "172.16.0.106", "172.16.0.107"],
    "P06": ["172.16.0.108","172.16.0.109","172.16.0.201","172.16.0.202","172.16.0.140","172.16.0.224","172.16.0.146"],
    "P07": ["172.16.0.110","172.16.0.111","172.16.0.112","172.16.0.141","172.16.0.115","172.16.0.149"],
    "P08": ["172.16.0.113","172.16.0.114"],
    "P09": ["172.16.0.120","172.16.0.121","172.16.0.119"],
    "P10": ["172.16.0.123","172.16.0.124"],
    "P11": ["172.16.0.125","172.16.0.137","172.16.0.126","172.16.0.139"],
    "P14": ["172.16.0.127","172.16.0.128"],
    "P16": ["172.16.0.130","172.16.0.138"],
    "P17": ["172.16.0.131","172.16.0.132","172.16.0.136"],
    "P18": ["172.16.0.133","172.16.0.134","172.16.0.135"],
    "P24": ["172.16.0.200","172.16.0.145"]
    
}

# Información adicional de switches
switch_details = {
    "172.16.0.118": {"PISO": "P-SO", "AREA": "CCTV", "CANTIDAD": 1, "MODELO": "x230-10GP", "SERIAL": "G26ZH402R", "VERSION": "5.5.4-1.5"},
    "172.16.0.151": {"PISO": "P-SO", "AREA": "ALMACEN", "CANTIDAD": 1, "MODELO": "AT-x530L-52GPX", "SERIAL": "A10231G212800126", "VERSION": "5.5.4-0.5"},
}

# Estado global de los switches
switch_status = {ip: "unknown" for segment in switch_ips_by_segment for ip in switch_ips_by_segment[segment]}

# Aplicación Flask
app = Flask(__name__)

@app.route("/")
def dashboard():
    # Calcula los totales
    total_switches = len(switch_status)
    total_online = sum(1 for status in switch_status.values() if status == "online")
    total_offline = sum(1 for status in switch_status.values() if status == "offline")

    # Renderiza el panel de monitoreo
    html = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard de Monitoreo 2025</title>
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
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
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
            th {
                background-color: var(--table-header-bg);
                color: var(--text-color);
                padding: 10px;
                text-align: center;
            }
            td {
                padding: 10px;
                text-align: center;
                border: 1px solid #444;
            }
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
            footer {
                text-align: center;
                padding: 10px;
                background-color: var(--header-bg);
                color: var(--text-color);
                margin-top: 20px;
            }
            #detailsModal {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: var(--card-bg);
                color: var(--text-color);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.5);
                z-index: 1000;
                width: 400px;
            }
            #detailsModal h3 {
                margin-top: 0;
            }
        </style>
        <script>
            function toggleMode() {
                document.body.classList.toggle('light-mode');
            }
            function showDetails(ip) {
                const details = {{ switch_details | tojson | safe }}[ip];
                if (details) {
                    const modal = document.getElementById('detailsModal');
                    document.getElementById('modalContent').innerHTML = `
                        <h3>Detalles del Switch</h3>
                        <p><strong>IP:</strong> ${ip}</p>
                        <p><strong>Piso:</strong> ${details.PISO}</p>
                        <p><strong>Área:</strong> ${details.AREA}</p>
                        <p><strong>Cantidad:</strong> ${details.CANTIDAD}</p>
                        <p><strong>Modelo:</strong> ${details.MODELO}</p>
                        <p><strong>Serial:</strong> ${details.SERIAL}</p>
                        <p><strong>Versión:</strong> ${details.VERSION}</p>
                    `;
                    modal.style.display = 'block';
                }
            }
            function closeModal() {
                document.getElementById('detailsModal').style.display = 'none';
            }
        </script>
    </head>
    <body>
        <header>
            Dashboard de Monitoreo 2025
            <button id="toggleMode" onclick="toggleMode()">Modo Claro/Oscuro</button>
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
            {% for segment, ips in switch_ips_by_segment.items() %}
            <div class="segment">
                <h2>{{ segment }}</h2>
                <table>
                    <thead>
                        <tr>
                            <th>IP</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for ip in ips %}
                        <tr onclick="showDetails('{{ ip }}')">
                            <td>{{ ip }}</td>
                            <td><span class="status {{ switch_status[ip] }}">{{ switch_status[ip] }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endfor %}
        </div>
        <div id="detailsModal">
            <div id="modalContent"></div>
            <button onclick="closeModal()">Cerrar</button>
        </div>
        <footer>
            &copy; 2025 Dashboard de Monitoreo - Todos los derechos reservados.
        </footer>
    </body>
    </html>"""

    # Asegúrate de que todos los valores de switch_details sean válidos
    cleaned_switch_details = {
        ip: switch_details.get(ip, {
            "PISO": "Desconocido",
            "AREA": "Desconocida",
            "CANTIDAD": 0,
            "MODELO": "N/A",
            "SERIAL": "N/A",
            "VERSION": "N/A"
        })
        for ip in switch_status.keys()
    }

    return render_template_string(
        html,
        switch_ips_by_segment=switch_ips_by_segment,
        switch_status=switch_status,
        total_switches=total_switches,
        total_online=total_online,
        total_offline=total_offline,
        switch_details=cleaned_switch_details  # Pasar datos limpios a la plantilla
    )


def monitor_switches():
    """Monitorea el estado de los switches y actualiza su estado."""
    while True:
        for ip in switch_status.keys():
            try:
                response = ping(ip, timeout=2)
                current_status = "online" if response else "offline"

                if switch_status[ip] != current_status:
                    switch_status[ip] = current_status
                    logging.info(f"Cambio detectado: {ip} -> {current_status}")

                    if current_status == "offline":
                        send_alert(ip)
            except Exception as e:
                logging.error(f"Error al monitorear {ip}: {e}")

        time.sleep(5)  # Intervalo de monitoreo

def send_alert(ip):
    """Envía una alerta por correo cuando un switch cambia a estado inactivo."""
    try:
        subject = f"🚨 Alerta: Switch {ip} inactivo"
        body = f"""
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f9;
                }
                .container {
                    padding: 20px;
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 600px;
                    margin: 60px auto;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                }
                .header {
                    background-color: #dc3545;
                    color: white;
                    padding: 10px;
                    text-align: center;
                    font-size: 1.5rem;
                    font-weight: bold;
                    border-radius: 8px 8px 0 0;
                }
                .body {
                    padding: 20px;
                    text-align: center;
                    color: #333;
                }
                .body p {
                    margin: 0 0 10px;
                    font-size: 1.1rem;
                }
                .footer {
                    text-align: center;
                    padding: 10px;
                    margin-top: 20px;
                    font-size: 0.9rem;
                    color: #aaa;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    🚨 Switch Inactivo: {ip}
                </div>
                <div class="body">
                    <p><strong>Atención:</strong> El switch con dirección IP <strong>{ip}</strong> ha cambiado a estado <strong>inactivo</strong>.</p>
                    <p>Por favor, revise el dispositivo y tome las acciones necesarias.</p>
                </div>
                <div class="footer">
                    &copy; 2024 Centro de Monitoreo de Switches
                </div>
            </div>
        </body>
        </html>"""

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_FROM
        message["To"] = EMAIL_TO

        mime_body = MIMEText(body, "html")
        message.attach(mime_body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, PASSWORD_SMTP)
            server.sendmail(EMAIL_FROM, EMAIL_TO, message.as_string())
        logging.info(f"Alerta enviada para {ip}")
    except smtplib.SMTPException as e:
        logging.error(f"Error SMTP para {ip}: {e}")
    except Exception as e:
        logging.error(f"Error general para {ip}: {e}")

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_switches, daemon=True)
    monitor_thread.start()
    app.run(host="0.0.0.0", port=5000)
