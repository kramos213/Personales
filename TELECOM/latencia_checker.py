import os
import platform
import subprocess
import statistics

def ping_test(host, count=10):
    system = platform.system().lower()
    ping_cmd = ["ping", "-n" if system == "windows" else "-c", str(count), host]

    try:
        output = subprocess.check_output(ping_cmd, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando ping: {e.output}")
        return []

    # Extraer tiempos de respuesta
    latencies = []
    for line in output.split("\n"):
        if "time=" in line.lower():
            parts = line.replace("=", " ").split()
            for p in parts:
                if "ms" in p:
                    try:
                        latencies.append(float(p.replace("ms", "")))
                    except ValueError:
                        pass
    return latencies

def analizar_conexion(latencias):
    enviados = len(latencias)
    recibidos = enviados  # Asumimos todos recibidos si tenemos latencias
    perdida = 0.0  # podrías ajustar si haces un ping más avanzado

    if not latencias:
        print("No se recibieron respuestas del host.")
        return

    lat_min = min(latencias)
    lat_max = max(latencias)
    lat_prom = sum(latencias) / len(latencias)
    jitter = statistics.stdev(latencias) if len(latencias) > 1 else 0.0

    print("\n--- Resultados ---")
    print(f"Paquetes enviados: {enviados}")
    print(f"Paquetes recibidos: {recibidos}")
    print(f"Pérdida de paquetes: {perdida}%")
    print(f"Latencia promedio: {lat_prom:.2f} ms")
    print(f"Latencia mínima: {lat_min:.2f} ms")
    print(f"Latencia máxima: {lat_max:.2f} ms")
    print(f"Jitter: {jitter:.2f} ms")

    # Clasificación de calidad
    if perdida > 5 or lat_prom > 150 or jitter > 50:
        calidad = "Mala"
    elif lat_prom > 80 or jitter > 30:
        calidad = "Regular"
    else:
        calidad = "Buena"

    print(f"Calidad de conexión: {calidad}")

    # Recomendaciones automáticas
    print("\n--- Recomendaciones ---")
    if calidad == "Buena":
        print("✅ La conexión es estable. No se requieren mejoras.")
    else:
        if perdida > 5:
            print("⚠️ Alta pérdida de paquetes. Revisa el cableado, conexión Wi-Fi o congestión en la red.")
        if lat_prom > 150:
            print("📶 Alta latencia. Posible saturación de la red o mala ruta hacia el servidor.")
        if jitter > 50:
            print("📈 Alto jitter. Puede afectar aplicaciones en tiempo real (voz/video).")
        print("🔍 Recomendado: probar con otro cable, otro punto de red o realizar trazado (traceroute) para identificar el salto problemático.")

# --- Programa principal ---
print("=== Analizador de Conexión de Red ===")
nombre = input("Introduce el nombre del servidor o IP: ")
print(f"\nProbando conexión con {nombre}...\n")

latencias = ping_test(nombre)
for i, lat in enumerate(latencias, start=1):
    print(f"Ping {i}: {lat:.2f} ms")

analizar_conexion(latencias)
