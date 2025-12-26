from core.ssh_client import SSHClient

def install_zabbix(host, user, password):
    ssh = SSHClient(host, user, password)
    ssh.connect()

    ssh.upload(
        "modules/zabbix/install_agent.sh",
        "/tmp/install_zabbix.sh"
    )

    ssh.run("chmod +x /tmp/install_zabbix.sh")
    ssh.run("/tmp/install_zabbix.sh", sudo=True)

    ssh.close()
