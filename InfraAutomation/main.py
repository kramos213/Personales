from getpass import getpass
from core.ssh_client import SSHClient

USERS_PRIORITY = ["root", "tech", "tpcredis"]

def load_servers():
    with open("inventory/linux_prod.txt") as f:
        return [l.strip() for l in f if l.strip()]

if __name__ == "__main__":
    print("🔐 Credenciales de acceso a servidores Linux")

    passwords = {}

    for user in USERS_PRIORITY:
        pwd = getpass(f"Password para usuario '{user}': ")
        passwords[user] = pwd

    servers = load_servers()

    for host in servers:
        connected = False

        for user in USERS_PRIORITY:
            try:
                ssh = SSHClient(host, user, passwords[user])
                out, err = ssh.run("hostname")

                print(f"✅ {out.strip()} ({user})")
                connected = True
                break

            except Exception:
                continue

        if not connected:
            print("❌ No se pudo conectar a un servidor")
