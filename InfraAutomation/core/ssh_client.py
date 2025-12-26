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
            timeout=self.timeout
        )

    def run(self, command, sudo=False):
        if not self.client:
            raise Exception("SSH no conectado")

        if sudo:
            # Enviamos la contraseña para sudo con -S
            command = f"echo {self.password} | sudo -S {command}"

        stdin, stdout, stderr = self.client.exec_command(command)

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        return output, error

    def upload(self, local_path, remote_path):
        if not self.client:
            raise Exception("SSH no conectado")

        sftp = self.client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
