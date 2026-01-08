from core.ssh_client import SSHClient

def execute(host, user, password):
    ssh = SSHClient(host, user, password)

    try:
        ssh.connect()

        remote_script_path = "/tmp/install_agent.sh"

        output = ssh.run(
            f"{remote_script_path}",
            sudo=True
        )

        return output

    finally:
        ssh.close()
