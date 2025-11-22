import platform
import subprocess
import statistics
import time

def medir_qos(host, paquetes=50):
    print("=== Analizador de Calidad de Servicio (QoS) ===\n")
    print(f"Probando calidad de conexión con {host}...\n")

    sistema = platform.system().lower()

    # Configurar comando de ping según el sistema operativo
    if sistema == "windows":
        comando = ["ping", host, "-n", str(paquetes), "-w", "1000"]
    else:
        comando = ["ping", "-c", str(paquetes), "-i", "0.2", host]

    try:
        salida = subprocess.check_output(comando, universal_newlines=True)
    except subprocess.CalledProcessError:
        print("❌ Error al ejecutar ping. El host no responde.")
        return

    # Extraer tiempos de ping
    tiempos = []
    for linea in salida.splitlines():
        if "tiempo" in linea or "time=" in linea:
            partes = linea.replace("=", " ").split()
            for p in partes:
                if p.endswith("ms"):
                    try:
                        tiempo = float(p.replace("ms", "").replace(",", "."))
                        tiempos.append(tiempo)
                    except ValueError:
                        continue

    if not tiempos:
        print("❌ No se pudieron medir los tiempos de respuesta (ICMP bloqueado o error).")
        return

    # Calcular métricas QoS
    enviados = paquetes
    recibidos = len(tiempos)
    perdidos = enviados - recibidos
    perdida_pct = (perdidos / enviados) * 100
    latencia_min = min(tiempos)
    latencia_max = max(tiempos)
    latencia_prom = statistics.mean(tiempos)
    jitter = statistics.pstdev(tiempos)

    # Mostrar resultados
    print("--- Resultados de la prueba ---")
    print(f"Paquetes enviados: {enviados}")
    print(f"Paquetes recibidos: {recibidos}")
    print(f"Pérdida de paquetes: {perdida_pct:.1f}%")
    print(f"Latencia promedio: {latencia_prom:.2f} ms")
    print(f"Latencia mínima: {latencia_min:.2f} ms")
    print(f"Latencia máxima: {latencia_max:.2f} ms")
    print(f"Jitter (variación): {jitter:.2f} ms")

    # Evaluar calidad
    print("\n--- Evaluación de Calidad ---")
    if perdida_pct > 10 or latencia_prom > 300:
        calidad = "❌ Deficiente"
        consejo = "Hay alta latencia o pérdida. Posible congestión o QoS mal configurado."
    elif jitter > 100 or latencia_prom > 150:
        calidad = "⚠️ Regular"
        consejo = "La conexión presenta variaciones notables. Revisa colas o priorización de tráfico."
    else:
        calidad = "✅ Buena"
        consejo = "La conexión es estable, latencia baja y sin pérdida significativa."

    print(f"Calidad general del enlace: {calidad}")
    print(f"Sugerencia: {consejo}\n")

    # Diagnóstico adicional
    print("--- Diagnóstico técnico ---")
    if jitter > 50:
        print("• Alta variación de tiempos (jitter alto): posible congestión o mala configuración QoS.")
    if perdida_pct > 0:
        print("• Pérdida de paquetes detectada: verifica colas o tráfico saturado.")
    if latencia_prom > 150:
        print("• Latencia elevada: puede ser ruta larga o enlace sobrecargado.")
    if perdida_pct == 0 and jitter < 20 and latencia_prom < 100:
        print("• El enlace muestra comportamiento óptimo para voz, video o tráfico sensible.\n")
    print("Fin del análisis.\n")

if __name__ == "__main__":
    host = input("Introduce la IP o nombre del servidor a analizar: ").strip()
    medir_qos(host)
