from core.ssh_client import SSHClient

def execute(host, user, password):
    """
    Ejecuta el script de actualización del sistema en el host remoto.
    Igual lógica que en zabbix installer.
    """
    ssh = SSHClient(host, user, password)
    ssh.connect()

    remote_script_path = "/tmp/update_system.sh"
    ssh.upload("modules/patching/update_system.sh", remote_script_path)
    ssh.run(f"chmod +x {remote_script_path}")

    output = ssh.run(remote_script_path, sudo=True)

    ssh.close()
    return output
