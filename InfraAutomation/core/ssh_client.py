import paramiko

class SSHClient:
    def __init__(self, host, user, password, timeout=10):
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(
            hostname=self.host,
            username=self.user,
            password=self.password,
            timeout=self.timeout,
            allow_agent=False,
            look_for_keys=False
        )

    def run(self, command, sudo=False):
        if sudo:
            command = f"sudo -S {command}"

        stdin, stdout, stderr = self.client.exec_command(command)

        if sudo:
            stdin.write(self.password + "\n")
            stdin.flush()

        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")

        exit_status = stdout.channel.recv_exit_status()

        # ✅ SOLO fallar si el exit code es distinto de 0
        if exit_status != 0:
            raise Exception(err if err else out)

        # ✅ devolver TODO (stdout + stderr)
        return out + err

    def close(self):
        if self.client:
            self.client.close()
