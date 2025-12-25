import paramiko

class SSHClient:
    def __init__(self, host, user, password, timeout=10):
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout

    def run(self, command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                timeout=self.timeout
            )

            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()

            return output, error

        finally:
            client.close()
