import time
import threading
from ping3 import ping
from flask import Flask, render_template_string
import smtplib
import logging

# Configuración
USERNAME = "TPC"
PASSWORD = "Tpc2020*"  # Nota: Reemplazar con variables de entorno en producción
EMAIL_FROM = "apps@thepanamaclinic.com"
PASSWORD_SMTP = "Informatica2019"  # Nota: Reemplazar con variables de entorno en producción
EMAIL_TO = "kramos@thepanamaclinic.com"
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

# Logging para monitoreo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de switches por segmentos
switch_ips_by_segment = {
        "PSO": ["172.16.0.151", "172.16.0.150", "172.16.0.118", "172.16.0.101", "172.16.0.147", "172.16.0.148", "172.16.0.116"],
        "PPB": ["172.16.0.105", "172.16.0.103", "172.16.0.104", "172.16.0.142", "172.16.0.143", "172.16.0.106", "172.16.0.107"],
        "P06": ["172.16.0.108", "172.16.0.109", "172.16.0.202", "172.16.0.140", "172.16.0.146"],
        "P07": ["172.16.0.110", "172.16.0.111", "172.16.0.112", "172.16.0.141", "172.16.0.115"],
        "P08": ["172.16.0.113", "172.16.0.114"],
        "P09": ["172.16.0.120", "172.16.0.121", "172.16.0.119"],
        "P10": ["172.16.0.123", "172.16.0.124"],
        "P11": ["172.16.0.125", "172.16.0.137", "172.16.0.126", "172.16.0.139"],
        "P14": ["172.16.0.127", "172.16.0.128"],
        "P16": ["172.16.0.129", "172.16.0.130", "172.16.0.138"],
        "P17": ["172.16.0.131", "172.16.0.132", "172.16.0.136"],
        "P18": ["172.16.0.133", "172.16.0.134", "172.16.0.135"],
        "P24": ["172.16.0.200", "172.16.0.145"]
}

# Estado global de los switches
switch_status = {ip: "unknown" for segment in switch_ips_by_segment for ip in switch_ips_by_segment[segment]}

# Aplicación Flask
app = Flask(__name__)

@app.route("/")
def dashboard():
    """Renderiza el panel de monitoreo."""
    html = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centro de Monitoreo de Switches - 2024</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e2f;
            margin: 0;
            padding: 0;
            color: #fff;
        }
        header {
            background-color: #0a84ff;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 1.8rem;
            font-weight: bold;
        }
        .container {
            max-width: none;
            margin: 50px 20px 20px;
            padding: 20px;
            background: #2b2b3c;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .segment {
            background: #32324e;
            border-radius: 8px;
            padding: 15px;
        }
        .segment h2 {
            background-color: #0a84ff;
            color: white;
            padding: 10px;
            margin: 0 -15px 15px -15px;
            font-size: 1.5rem;
            border-radius: 8px 8px 0 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: center;
            border: 1px solid #3d3d5c;
        }
        th {
            background-color: #3c3c5c;
            font-weight: bold;
            color: #0a84ff;
        }
        .status {
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
        }
        .online {
            background-color: #28a745;
            color: #fff;
        }
        .offline {
            background-color: #dc3545;
            color: #fff;
        }
        .unknown {
            background-color: #6c757d;
            color: #fff;
        }
        footer {
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            font-size: 0.9rem;
            color: #aaa;
        }
    </style>
</head>
<body>
    <header>
        Centro de Monitoreo de Switches - 2024
    </header>
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
                            <tr>
                                <td>{{ ip }}</td>
                                <td><span class="status {{ switch_status[ip] }}">{{ switch_status[ip] }}</span></td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% endfor %}
    </div>
    <footer>
        &copy; 2024 Centro de Monitoreo - Desarrollado para un monitoreo más eficiente
    </footer>
</body>
</html>

    """
    return render_template_string(html, switch_ips_by_segment=switch_ips_by_segment, switch_status=switch_status)

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
    subject = f"Alerta: Switch {ip} está inactivo"
    body = f"El switch con IP {ip} ha pasado a estado inactivo."
    message = f"Subject: {subject}\n\n{body}"
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, PASSWORD_SMTP)
            server.sendmail(EMAIL_FROM, EMAIL_TO, message)
        logging.info(f"Alerta enviada para {ip}")
    except Exception as e:
        logging.error(f"Error al enviar alerta para {ip}: {e}")

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_switches, daemon=True)
    monitor_thread.start()
    app.run(host="0.0.0.0", port=5000)
