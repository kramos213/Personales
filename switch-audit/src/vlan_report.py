#!/usr/bin/env python3
import os
import re
import csv
import time
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

# -----------------------
# Utilidades de archivo
# -----------------------
def load_yaml(path, default=None):
    if not os.path.exists(path):
        return default or {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

# -----------------------
# CLI
# -----------------------
def parse_args():
    p = argparse.ArgumentParser(description="Reporte de VLANs por switch (show vlan brief)")
    p.add_argument("--inventory", required=True, help="Ruta a inventories/*.yml")
    p.add_argument("--env-file", required=True, help="Ruta a creds/.env.* con usuario/clave/etc.")
    p.add_argument("--creds-map", default="creds/credentials.yml", help="Overrides por área/host/vendor")
    p.add_argument("--settings", default="config/settings.yml", help="Ajustes globales")
    p.add_argument("--exclude-defaults", action="store_true",
                   help="Excluye VLAN por defecto (1, 1002-1005)")
    p.add_argument("--max-workers", type=int, help="Override del tamaño de pool")
    p.add_argument("--output-dir", help="Override ruta base de salida")
    # overrides urgentes
    p.add_argument("--username")
    p.add_argument("--password")
    p.add_argument("--enable")
    return p.parse_args()

# -----------------------
# Resolución de credenciales
# -----------------------
def resolve_creds(ip, area, inv_defaults, creds_map):
    base = {
        "username": os.getenv("SSH_USERNAME"),
        "password": os.getenv("SSH_PASSWORD"),
        "enable": os.getenv("ENABLE_SECRET", ""),
        "device_type": None,
        "port": 22
    }
    # defaults de credentials.yml
    if "defaults" in creds_map:
        for k in ("username","password","device_type","port","enable"):
            if k in creds_map["defaults"]:
                base[k] = creds_map["defaults"][k]
    # por área
    if "areas" in creds_map and area in creds_map["areas"]:
        for k,v in creds_map["areas"][area].items():
            if k in base or k == "port":
                base[k] = v
    # por host
    if "hosts" in creds_map and ip in creds_map["hosts"]:
        for k,v in creds_map["hosts"][ip].items():
            if k in base or k == "port":
                base[k] = v

    # device_type por inventory.defaults si sigue vacío
    if not base["device_type"]:
        base["device_type"] = (inv_defaults or {}).get("device_type", "cisco_ios")
    return base

# -----------------------
# Conexión/Comandos
# -----------------------
def netmiko_params(ip, creds, timeouts):
    return {
        "device_type": creds["device_type"],
        "host": ip,
        "username": creds["username"],
        "password": creds["password"],
        "secret": creds.get("enable") or None,
        "port": int(creds.get("port", 22)),
        "fast_cli": True,
        "global_delay_factor": float(timeouts.get("delay_factor", 1.0)),
        "timeout": int(timeouts.get("connect", 20))
    }

def run_commands(ip, params, cmd, read_timeout):
    from netmiko import ConnectHandler
    with ConnectHandler(**params) as conn:
        try:
            if params.get("secret"):
                # algunos equipos no requieren enable
                conn.enable()
        except Exception:
            pass
        conn.send_command_timing("terminal length 0", strip_command=False)
        output = conn.send_command(cmd, expect_string=r"#|\$", read_timeout=int(read_timeout))
        return output

def with_retries(func, retries=1, delay=2, *args, **kwargs):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(delay * (attempt + 1))
    raise last_exc

# -----------------------
# Parser show vlan brief (Cisco-like)
# -----------------------
_vlan_row_re = re.compile(
    r"^\s*(?P<vlan>\d+)\s+(?P<name>\S+)\s+(?P<status>\S+)\s*(?P<ports>.*)$"
)

def parse_show_vlan_brief(output):
    """
    Soporta líneas de continuación de 'Ports' (envueltas a la siguiente línea).
    Devuelve lista de dicts: {"vlan","name","status","ports":[...]}
    """
    lines = output.splitlines()
    results = []
    current = None

    for line in lines:
        if not line.strip():
            continue
        m = _vlan_row_re.match(line)
        if m:
            # Inicia nuevo bloque
            if current:
                results.append(current)
            ports_str = m.group("ports").strip()
            ports = [p.strip() for p in ports_str.split(",") if p.strip()] if ports_str else []
            current = {
                "vlan": m.group("vlan"),
                "name": m.group("name"),
                "status": m.group("status"),
                "ports": ports
            }
        else:
            # Posible línea de continuación (puertos envueltos)
            if current and (line.startswith(" ") or line.startswith("\t")):
                cont = [p.strip() for p in line.strip().split(",") if p.strip()]
                current["ports"].extend(cont)
            # Si no es continuación, la ignoramos (cabeceras/separadores)
    if current:
        results.append(current)
    return results

def count_ports_by_vlan(parsed_rows, exclude_defaults=False):
    """
    Retorna dict { vlan_id: count }.
    exclude_defaults=True excluye VLAN 1 y 1002-1005.
    """
    counts = {}
    for row in parsed_rows:
        vid = int(row["vlan"])
        if exclude_defaults and (vid == 1 or 1002 <= vid <= 1005):
            continue
        port_count = len(row.get("ports", []))
        counts[str(vid)] = counts.get(str(vid), 0) + port_count
    return counts

# -----------------------
# Worker por switch
# -----------------------
def process_switch(ip, area, cmd, timeouts, creds, exclude_defaults):
    params = netmiko_params(ip, creds, timeouts)
    try:
        output = with_retries(
            run_commands,
            retries=1,
            delay=2,
            ip=ip,
            params=params,
            cmd=cmd,
            read_timeout=timeouts.get("command", 25)
        )
        rows = parse_show_vlan_brief(output)
        vlan_counts = count_ports_by_vlan(rows, exclude_defaults=exclude_defaults)
        return {"ip": ip, "area": area, "ok": True, "vlan_counts": vlan_counts, "error": None}
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        return {"ip": ip, "area": area, "ok": False, "vlan_counts": {}, "error": f"{type(e).__name__}: {e}"}
    except Exception as e:
        return {"ip": ip, "area": area, "ok": False, "vlan_counts": {}, "error": f"Unexpected: {e}"}

# -----------------------
# Escritura CSV
# -----------------------
def write_master_csv(path, records):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Área", "IP del Switch", "VLAN ID", "Puertos Configurados", "Estado"])
        for r in records:
            w.writerow(r)

# -----------------------
# Main
# -----------------------
def main():
    args = parse_args()
    load_dotenv(args.env_file)

    inventory = load_yaml(args.inventory, {})
    creds_map = load_yaml(args.creds_map, {})
    settings = load_yaml(args.settings, {})

    timeouts = {
        "connect": settings.get("timeouts", {}).get("connect", 20),
        "command": settings.get("timeouts", {}).get("command", 25),
        "delay_factor": settings.get("global_delay_factor", 1.0),
    }
    max_workers = args.max_workers or int(settings.get("max_workers", 12))

    # Comando por vendor; fall-back a Cisco
    cmds = settings.get("commands", {})
    default_device_type = inventory.get("defaults", {}).get("device_type", "cisco_ios")
    default_cmd = cmds.get(default_device_type, ["terminal length 0", "show vlan brief"])[-1]

    # Directorio de salida
    base_output = args.output_dir or os.getenv("OUTPUT_DIR") or "output"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_output, f"vlan_run_{ts}")
    ensure_dir(run_dir)

    master_records = []
    errors = []

    # Pool
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for area, ips in (inventory.get("areas") or {}).items():
            for ip in ips:
                creds = resolve_creds(ip, area, inventory.get("defaults", {}), creds_map)
                # overrides CLI
                if args.username: creds["username"] = args.username
                if args.password: creds["password"] = args.password
                if args.enable:   creds["enable"]   = args.enable

                device_type = creds.get("device_type") or default_device_type
                cmd = cmds.get(device_type, ["terminal length 0", "show vlan brief"])[-1]

                futures.append(
                    pool.submit(
                        process_switch,
                        ip, area, cmd, timeouts, creds, args.exclude_defaults
                    )
                )

        for fut in as_completed(futures):
            res = fut.result()
            if res["ok"]:
                if res["vlan_counts"]:
                    for vlan_id, count in sorted(res["vlan_counts"].items(), key=lambda x: int(x[0])):
                        master_records.append([res["area"], res["ip"], vlan_id, count, "OK"])
                else:
                    master_records.append([res["area"], res["ip"], "N/A", 0, "SIN_DATOS"])
            else:
                errors.append(res)
                master_records.append([res["area"], res["ip"], "ERROR", "ERROR", res["error"]])

    master_csv = os.path.join(run_dir, "resultados_vlans.csv")
    write_master_csv(master_csv, master_records)

    # Resumen consola
    print(f"\nEjecución terminada. Carpeta: {run_dir}")
    ok_sw = len([r for r in master_records if r[-1] == "OK" or r[-1] == "SIN_DATOS"])
    print(f"Switches procesados: {ok_sw} / {len(futures)}")
    if errors:
        print("Dispositivos con error:")
        for e in errors:
            print(f" - {e['ip']} ({e['area']}): {e['error']}")
    print(f"CSV maestro: {master_csv}")

if __name__ == "__main__":
    main()
