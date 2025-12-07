#!/usr/bin/env python3
# network_audit_full.py
"""
Auditoría completa:
 - Grupos de redes (archivo redes.txt con [GRUPO])
 - Descubrimiento: ping, ARP
 - Escaneo puertos + servicios (-sV opcional)
 - Latencia (ping) robusto en Windows y Linux
 - Intento SNMP con community 'public' (si pysnmp está instalado)
 - Detección de riesgos automáticos
 - Export CSV por red y HTML consolidado
"""

import os
import csv
import re
import subprocess
import socket
import time
import argparse
from datetime import datetime
from tqdm import tqdm

try:
    import nmap  # python-nmap
except Exception:
    nmap = None

# pysnmp es opcional
try:
    from pysnmp.hlapi import *
    PYSNMP_AVAILABLE = True
except Exception:
    PYSNMP_AVAILABLE = False

# ----------------------
# CONFIG
# ----------------------
EXPORT_FOLDER = os.path.expanduser(r"./network_audit_output")
ARCHIVO_REDES = os.path.expanduser(r"./redes.txt")
PUERTOS_COMUNES = "22,80,443,445,3389,5900,8080,8443"
PING_INTENTOS = 3

CSV_FIELDS = [
    "timestamp", "grupo", "red", "ip", "hostname", "mac", "vendor",
    "puertos", "servicios", "lat_min_ms", "lat_max_ms", "lat_avg_ms", "loss_pct",
    "snmp_public", "snmp_sysdescr", "riesgos"
]

# Riesgos por puertos
PUERTOS_RIESGO = {
    "3389": "RDP abierto (riesgo elevado - ransomware)",
    "445": "SMB abierto (riesgo de gusanos y exfiltracion)",
    "23": "Telnet (credenciales en claro)",
    "5900": "VNC",
    "21": "FTP sin seguridad",
    "3306": "MySQL (exposición)"
}

# ----------------------
# UTIL
# ----------------------
def ensure_dirs():
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

def now_ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def safe_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""

def run_cmd(cmd, timeout=6):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, encoding="utf-8", timeout=timeout)
        return out
    except subprocess.CalledProcessError:
        return ""
    except subprocess.TimeoutExpired:
        return ""

# ----------------------
# Latencia (robusta)
# ----------------------
def medir_latencia(ip, intentos=PING_INTENTOS):
    """
    Intenta ping varias veces y extrae tiempos en ms.
    Soporta formatos en español e ingles y 'time<1ms'
    """
    tiempos = []
    hechos = 0
    # Usamos 'ping -c/ -n' según plataforma
    if os.name == "nt":
        cmd_template = f"ping -n 1 -w 1000 {ip}"
    else:
        # -c 1 -W 1 (timeout 1s)
        cmd_template = f"ping -c 1 -W 1 {ip}"

    for _ in range(intentos):
        salida = run_cmd(cmd_template, timeout=2)
        if not salida:
            continue
        hechos += 1
        # regex: captures both 'time=12ms', 'tiempo=12ms', 'time<1ms', 'tiempo<1ms'
        m = re.search(r"(?:time|tiempo)\s*[=<]\s*([0-9]+)", salida, re.IGNORECASE)
        if m:
            try:
                tiempos.append(int(m.group(1)))
            except:
                pass
        else:
            # Buscar pattern like time=12 ms or time = 12 ms
            m2 = re.search(r"(?:time|tiempo)\s*[=<]\s*([0-9]+)\s*ms", salida, re.IGNORECASE)
            if m2:
                try:
                    tiempos.append(int(m2.group(1)))
                except:
                    pass
            else:
                # Special: "time<1ms" we treat as 1
                m3 = re.search(r"(?:time|tiempo)\s*<\s*1", salida, re.IGNORECASE)
                if m3:
                    tiempos.append(1)

    if hechos == 0:
        return {"min": None, "max": None, "avg": None, "loss": 100}

    if not tiempos:
        return {"min": None, "max": None, "avg": None, "loss": round((1 - 0 / hechos) * 100, 2)}

    loss = round((1 - len(tiempos) / hechos) * 100, 2)
    return {"min": min(tiempos), "max": max(tiempos), "avg": round(sum(tiempos) / len(tiempos),2), "loss": loss}

# ----------------------
# Cargar grupos/redes
# ----------------------
def cargar_grupos_y_redes(ruta):
    grupos = {}
    grupo_actual = None
    if not os.path.exists(ruta):
        print(f"❌ No existe {ruta}")
        return grupos
    with open(ruta, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                grupo_actual = line[1:-1].strip()
                grupos[grupo_actual] = []
                continue
            if grupo_actual:
                grupos[grupo_actual].append(line)
    return grupos

# ----------------------
# NMAP WRAPPERS
# ----------------------
def nm_scan_ping(red, use_arp=False):
    """
    Realiza ping scan; si use_arp True usa ARP (-PR)
    Devuelve lista de hosts (IPs) activas y raw scan object (nm)
    """
    if nmap is None:
        # Fallback: usar ping por ip (desglose simple si no hay nmap)
        print("⚠ nmap python module no esta disponible. Instala python-nmap para mejor funcionamiento.")
        # intentar simple: si red es CIDR, generar ips con socket? evitar por simplicidad
        return [], {}
    nm = nmap.PortScanner()
    args = "-sn -n"
    if use_arp:
        args = "-sn -n -PR"
    try:
        nm.scan(hosts=red, arguments=args)
    except Exception as e:
        print(f"❌ Error nmap ping-scan {red}: {e}")
        return [], {}
    hosts = nm.all_hosts()
    return hosts, nm

def nm_scan_ports(red, ports, sV=False):
    if nmap is None:
        return {}
    nm = nmap.PortScanner()
    args = "-T4 -n"
    if sV:
        args += " -sV --version-intensity 0"
    try:
        nm.scan(hosts=red, ports=ports, arguments=args)
    except Exception as e:
        print(f"❌ Error nmap port-scan {red}: {e}")
        return {}
    return nm._scan_result.get("scan", {})

# ----------------------
# SNMP (intento public)
# ----------------------
def snmp_get_sysdescr(ip, community="public", timeout=2):
    if not PYSNMP_AVAILABLE:
        return None
    try:
        iterator = getCmd(SnmpEngine(),
                          CommunityData(community, mpModel=1),  # v2c (mpModel=1)
                          UdpTransportTarget((ip, 161), timeout=timeout, retries=0),
                          ContextData(),
                          ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')))  # sysDescr
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        if errorIndication or errorStatus:
            return None
        for varBind in varBinds:
            return str(varBind[1])
    except Exception:
        return None

# ----------------------
# Detectar riesgos
# ----------------------
def detectar_riesgos(puertos_abiertos, snmp_public=False, servicios=None):
    riesgos = []
    for p in puertos_abiertos:
        if p in PUERTOS_RIESGO:
            riesgos.append(PUERTOS_RIESGO[p])
    if snmp_public:
        riesgos.append("SNMP con community 'public' detectado (revisar acceso)")
    # Servicios con versiones viejas: ejemplo simplificado
    if servicios:
        for svc in servicios:
            # svc ejemplo: "ssh/22 OpenSSH 7.2p2"
            for palabra in ["debian", "ubuntu", "windows xp", "apache 2.2", "php 5.6", "openssl 0.9"]:
                if palabra.lower() in svc.lower():
                    riesgos.append(f"Servicio con versión potencialmente insegura: {svc}")
    return "; ".join(riesgos) if riesgos else ""

# ----------------------
# Procesar un red (pipeline)
# ----------------------
def procesar_red(grupo, red, args):
    # 1) Descubrimiento ping (+ARP opcional)
    use_arp = not args.no_arp
    hosts, nm_ping = nm_scan_ping(red, use_arp=use_arp)
    if not hosts:
        return []

    # 2) Port scan (puertos comunes) y opcional -sV
    sV = not args.no_services
    scan_data = nm_scan_ports(red, PUERTOS_COMUNES, sV=sV)

    results = []
    for host in tqdm(hosts, desc=f"Procesando {red}", unit="host"):
        info = scan_data.get(host, {}) if scan_data else {}
        status = info.get("status", {}).get("state", "")
        # nmap ping-scan puede devolver hosts sin detalles de puertos, igual intentamos
        # Obtener puertos configurados en scan_data (tcp/udp)
        puertos = []
        servicios = []
        for proto in ("tcp", "udp"):
            ports = info.get(proto, {})
            for p, pdata in ports.items():
                if pdata.get("state") == "open":
                    puertos.append(str(p))
                    if sV:
                        # build servicio string
                        svc = pdata.get("name", "")
                        ver = pdata.get("product", "") + " " + pdata.get("version", "")
                        servicios.append(f"{svc}/{p} {ver}".strip())

        mac = info.get("addresses", {}).get("mac", "")
        # vendor detection from nmap vendor map
        vendor = ""
        if mac:
            vendor = info.get("vendor", {}).get(mac, "")

        hostname = ""
        try:
            hlist = info.get("hostnames", [])
            if hlist and "name" in hlist[0]:
                hostname = hlist[0]["name"]
        except:
            hostname = ""
        if not hostname:
            hostname = safe_hostname(host)

        # Latencia robusta
        lat = medir_latencia(host, PING_INTENTOS)

        # SNMP attempt
        snmp_public = False
        snmp_sysdescr = ""
        if not args.no_snmp and PYSNMP_AVAILABLE:
            descr = snmp_get_sysdescr(host, community="public", timeout=2)
            if descr:
                snmp_public = True
                snmp_sysdescr = descr

        # Riesgos
        riesgos = detectar_riesgos(puertos, snmp_public=snmp_public, servicios=servicios)

        results.append({
            "timestamp": now_ts(),
            "grupo": grupo,
            "red": red,
            "ip": host,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "puertos": ", ".join(sorted(puertos)),
            "servicios": "; ".join(servicios),
            "lat_min_ms": lat["min"],
            "lat_max_ms": lat["max"],
            "lat_avg_ms": lat["avg"],
            "loss_pct": lat["loss"],
            "snmp_public": "yes" if snmp_public else "no",
            "snmp_sysdescr": snmp_sysdescr,
            "riesgos": riesgos
        })

    return results

# ----------------------
# Export CSV y HTML
# ----------------------
def export_results(all_results):
    ensure_dirs()
    ts = now_ts()
    csv_all = os.path.join(EXPORT_FOLDER, f"resultado_scan_consolidado_{ts}.csv")
    with open(csv_all, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(all_results)
    # CSV por red
    by_red = {}
    for row in all_results:
        key = f"{row['grupo']}__{row['red']}"
        by_red.setdefault(key, []).append(row)
    for key, rows in by_red.items():
        safe = key.replace("/", "-").replace(" ", "_")
        fname = os.path.join(EXPORT_FOLDER, f"{safe}_{ts}.csv")
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(rows)
    print(f"\n📁 CSV generado: {csv_all}")
    # HTML resumen
    html_file = os.path.join(EXPORT_FOLDER, f"reporte_red_{ts}.html")
    generar_reporte_html(all_results, html_file)
    print(f"📁 Reporte HTML: {html_file}")

def generar_reporte_html(rows, outpath):
    # Generar HTML simple con secciones: resumen, tabla hosts, alertas
    timestamp = now_ts()
    total_hosts = len(rows)
    alerts = [r for r in rows if r.get("riesgos")]
    alerts_html = ""
    for a in alerts:
        alerts_html += f"<tr><td>{a['timestamp']}</td><td>{a['grupo']}</td><td>{a['red']}</td><td>{a['ip']}</td><td>{a['riesgos']}</td></tr>\n"

    # Tabla hosts
    rows_html = ""
    for r in rows:
        rows_html += "<tr>"
        rows_html += f"<td>{r['timestamp']}</td>"
        rows_html += f"<td>{r['grupo']}</td>"
        rows_html += f"<td>{r['red']}</td>"
        rows_html += f"<td>{r['ip']}</td>"
        rows_html += f"<td>{r['hostname']}</td>"
        rows_html += f"<td>{r['mac']}</td>"
        rows_html += f"<td>{r['vendor']}</td>"
        rows_html += f"<td>{r['puertos']}</td>"
        rows_html += f"<td>{r['servicios']}</td>"
        rows_html += f"<td>{r['lat_avg_ms'] or ''}</td>"
        rows_html += f"<td>{r['loss_pct']}</td>"
        rows_html += f"<td>{r['snmp_public']}</td>"
        rows_html += f"<td>{r['riesgos']}</td>"
        rows_html += "</tr>\n"

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reporte Auditoría de Red - {timestamp}</title>
<style>
body{{font-family: Arial, Helvetica, sans-serif; margin:20px}}
h1{{color:#222}}
table{{border-collapse:collapse; width:100%; font-size:12px}}
th,td{{border:1px solid #ddd; padding:6px; text-align:left}}
th{{background:#f4f4f4}}
tr:hover{{background:#fafafa}}
.bad{{color:#a00; font-weight:bold}}
.ok{{color:#080}}
.section{{margin-bottom:24px}}
.small{{font-size:11px; color:#666}}
</style>
</head>
<body>
<h1>Reporte Auditoría de Red</h1>
<div class="section">
<strong>Generado:</strong> {timestamp} <br>
<strong>Total hosts reportados:</strong> {total_hosts} <br>
<strong>Alertas con riesgos:</strong> {len(alerts)}
</div>

<div class="section">
<h2>Alertas / Riesgos detectados</h2>
<table>
<tr><th>Fecha</th><th>Grupo</th><th>Red</th><th>IP</th><th>Riesgos</th></tr>
{alerts_html if alerts_html else '<tr><td colspan="5">Sin alertas detectadas</td></tr>'}
</table>
</div>

<div class="section">
<h2>Hosts detectados</h2>
<table>
<tr>
<th>Fecha</th><th>Grupo</th><th>Red</th><th>IP</th><th>Hostname</th><th>MAC</th><th>Vendor</th><th>Puertos</th><th>Servicios</th><th>Lat avg (ms)</th><th>Loss %</th><th>SNMP public</th><th>Riesgos</th>
</tr>
{rows_html}
</table>
</div>

<div class="small">Generado por script de auditoría. Revisa alertas críticas primero (RDP/SMB/SNMP public).</div>
</body>
</html>
"""
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)

# ----------------------
# MAIN
# ----------------------
def seleccionar_grupo_interactivo(grupos):
    print("\n📌 Grupos disponibles:")
    for i, g in enumerate(grupos.keys(), start=1):
        print(f"{i}. {g}")
    print("0. TODOS LOS GRUPOS")
    op = input("\nSelecciona un grupo (número): ").strip()
    if op == "0":
        return None
    try:
        op = int(op)
        grupo = list(grupos.keys())[op - 1]
        return grupo
    except:
        print("❌ Opción inválida")
        return seleccionar_grupo_interactivo(grupos)

def main():
    parser = argparse.ArgumentParser(description="Auditoría de red completa por grupos")
    parser.add_argument("--grupo", help="Nombre del grupo a escanear (tal como en redes.txt)")
    parser.add_argument("--no-arp", action="store_true", help="Omitir ARP")
    parser.add_argument("--no-snmp", action="store_true", help="Omitir SNMP")
    parser.add_argument("--no-services", action="store_true", help="Omitir escaneo -sV (servicios)")
    parser.add_argument("--arch", help="Archivo de redes (default ./redes.txt)")
    args = parser.parse_args()

    global ARCHIVO_REDES
    if args.arch:
        ARCHIVO_REDES = args.arch

    ensure_dirs()
    grupos = cargar_grupos_y_redes(ARCHIVO_REDES)
    if not grupos:
        print("❌ No hay grupos o redes definidas en", ARCHIVO_REDES)
        return

    # Si el usuario pasó --grupo lo usamos; si no, pregunta interactivo
    grupo_sel = args.grupo if args.grupo else seleccionar_grupo_interactivo(grupos)

    if grupo_sel is None:
        redes = [r for lista in grupos.values() for r in lista]
        print(f"\n▶ Escaneando TODOS los grupos ({len(redes)} redes)")
    else:
        if grupo_sel not in grupos:
            print(f"❌ Grupo {grupo_sel} no existe")
            return
        redes = grupos[grupo_sel]
        print(f"\n▶ Escaneando grupo {grupo_sel} ({len(redes)} redes)")

    all_results = []
    start_total = time.perf_counter()
    for red in redes:
        try:
            grupo = grupo_sel if grupo_sel else "(MULTI)"
            res = procesar_red(grupo, red, args)
            all_results.extend(res)
        except KeyboardInterrupt:
            print("⛔ Interrumpido por usuario")
            break
        except Exception as e:
            print(f"❌ Error procesando {red}: {e}")

    t_total = time.perf_counter() - start_total
    print(f"\n✅ Auditoría completa - hosts detectados: {len(all_results)}")
    print(f"⏱ Tiempo total: {t_total:.1f}s")

    if all_results:
        export_results(all_results)
    else:
        print("⚠ No hay resultados para exportar")

if __name__ == "__main__":
    main()
