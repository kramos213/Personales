import paramiko
import time
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración de los switches por área
switch_ips_by_area = {
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

# Usuario y contraseña para todos los switches
username = "TPC"
password = "Tpc2020*"

# Configuración de carpeta para guardar logs
log_folder = "/Users/kevinramos/Desktop/Log de Monitoreo de Red"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Configuración de correo electrónico
sender_email = "apps@thepanamaclinic.com"
sender_password = "Informatica2019"
receiver_email = "kramos@thepanamaclinic.com"
smtp_server = "smtp.office365.com"
smtp_port = 587

# Fecha de hoy para filtrar
today_date = datetime.datetime.now().strftime("%Y-%m-%d")

# Función para enviar correo electrónico con alerta
def send_email_alert(ip, logs):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"🚨 Alerta Crítica: Problema en Switch {ip}"

    # Mensaje en HTML
    body = f"""
    <html>
        <body>
            <h2 style="color: red;">🚨 Alerta de Switch</h2>
            <p><strong>IP del Switch:</strong> {ip}</p>
            <p><strong>Fecha de Detección:</strong> {timestamp}</p>
            <p><strong>Mensajes Críticos:</strong></p>
            <div style="border: 1px solid #e0e0e0; padding: 10px; font-family: monospace; background-color: #f8f8f8;">
                <pre>{logs}</pre>
            </div>
        </body>
    </html>
    """

    # Configuración del mensaje de correo
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        # Enviar el correo electrónico
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Correo de alerta enviado.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# Función para enviar correo de confirmación
def send_confirmation_email():
    subject = "✅ Monitoreo Completo: Todo está correcto"
    body = "<html><body><h2>✅ Monitoreo Completo</h2><p>La revisión de los switches se ha completado sin problemas críticos.</p></body></html>"
    
    # Configuración del mensaje de correo
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        # Enviar el correo electrónico
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Correo de confirmación enviado.")
    except Exception as e:
        print(f"Error al enviar el correo de confirmación: {e}")

# Palabras clave específicas para filtrar mensajes críticos
keywords = [
    "disabled learning on",
    "re-enabled learning on",
    "port down notification received",
    "port up notification received",
    "ERROR",
    "HSL: ERROR"
]

# Función de monitoreo para cada switch
def monitor_switch(ip):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_folder, f"log_{ip}_{date_str}.txt")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        # Ingresar al modo enable y ejecutar el comando para obtener los logs
        ssh.exec_command("enable")
        #ssh.exec_command("terminal length 0")
        stdin, stdout, stderr = ssh.exec_command("show log tail 50")
        logs = stdout.read().decode()
        ssh.close()

        # Filtrar los mensajes críticos del día actual que contengan alguna de las palabras clave
        critical_logs = []
        for line in logs.splitlines():
            # Verifica si la línea contiene alguna de las frases clave exactas
            if any(keyword in line.lower() for keyword in keywords):
                critical_logs.append(line)

        # Enviar alerta si hay mensajes críticos del día actual
        if critical_logs:
            critical_log_text = "\n".join(critical_logs)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a") as file:
                file.write(f"\n[{timestamp}] Problema detectado en el switch {ip}:\n{critical_log_text}\n")
            print(f"Alerta: Problema detectado en {ip}.")
            send_email_alert(ip, critical_log_text)
        else:
            # Registrar que no se encontraron problemas
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a") as file:
                file.write(f"\n[{timestamp}] Sin problemas detectados en el switch {ip}.\n")
            print(f"Revisión completada en {ip}, sin problemas detectados.")

    except Exception as e:
        error_message = f"Error al conectar con {ip}: {str(e)}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as file:
            file.write(f"\n[{timestamp}] {error_message}\n")
        
        # Mensaje de error específico para enviar por correo
        connection_error_message = f"Se produjo un error durante el intento de conexión a {ip}. Motivo: {str(e)}"
        print(connection_error_message)
        with open(log_file, "a") as file:
            file.write(f"\n[{timestamp}] {connection_error_message}\n")
        
        # Enviar correo de alerta por error de conexión
        send_email_alert(ip, connection_error_message)

# Función principal para monitorear todos los switches
def main():
    while True:
        for area, ips in switch_ips_by_area.items():
            print(f"Revisando switches en el área: {area}")
            for ip in ips:
                monitor_switch(ip)
        # Enviar correo de confirmación después de la revisión
        send_confirmation_email()
        # Espera de 10 minutos antes de la próxima revisión
        time.sleep(600)

if __name__ == "__main__":
    main()
