def install_zabbix_agent(ssh):
    remote_path = "/tmp/install_agent.sh"
    ssh.upload("modules/zabbix/install_agent.sh", remote_path)
    ssh.run(f"chmod +x {remote_path}")
    
    output, error = ssh.run(remote_path, sudo=True)
    print(f"Salida de instalación en {ssh.host}:\n{output}")
    if error:
        print(f"Error durante instalación en {ssh.host}:\n{error}")
