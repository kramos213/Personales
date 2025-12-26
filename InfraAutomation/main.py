from getpass import getpass
from core.inventory import load_inventory
from modules.zabbix.installer import install_zabbix_agent
from core.ssh_client import SSHClient

MODULES = {
    "zabbix": install_zabbix_agent,
}

def run_module(module_name, servers, user, password):
    action = MODULES.get(module_name)
    if not action:
        print(f"Módulo {module_name} no encontrado")
        return

    for host in servers:
        try:
            ssh = SSHClient(host, user, password)
            ssh.connect()
            action(ssh)
            ssh.close()
            print(f"✅ {host} - {module_name} ejecutado correctamente")
        except Exception as e:
            print(f"❌ {host} - Error: {e}")

if __name__ == "__main__":
    inventory = load_inventory("inventory/servers.txt")

    print("Selecciona módulo:")
    for i, m in enumerate(MODULES.keys(), 1):
        print(f"{i}) {m}")

    module_option = int(input("Opción: "))
    module_name = list(MODULES.keys())[module_option - 1]

    print("Selecciona servicio:")
    groups = list(inventory.keys())
    for i, g in enumerate(groups, 1):
        print(f"{i}) {g}")

    service_option = int(input("Opción: "))
    servers = inventory[groups[service_option - 1]]

    user = input("Usuario SSH: ")
    password = getpass("Password SSH: ")

    run_module(module_name, servers, user, password)
