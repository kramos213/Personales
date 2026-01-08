#!/bin/bash
set -e

### ======================
### EJECUTAR DESDE /tmp
### ======================
BASE_DIR="/tmp"
cd "$BASE_DIR" || exit 1

### ======================
### VARIABLES
### ======================
ZABBIX_SERVER="10.1.1.201"
HOSTNAME_LOCAL=$(hostname)

echo "======================================="
echo " Reinstalador Universal Zabbix Agent"
echo "======================================="

fail() {
  echo "❌ ERROR: $1"
  exit 1
}

# ======================
# DETECTAR SO
# ======================
[ -f /etc/os-release ] || fail "No se puede detectar el sistema operativo"
. /etc/os-release

ARCH=$(uname -m)
MAJOR=$(echo "$VERSION_ID" | cut -d'.' -f1)

echo "➡ SO detectado: $NAME $VERSION_ID ($ARCH)"

# ======================
# DEFINIR INIT Y SERVICIO
# ======================
if [[ "$ID" =~ ^(ol|rhel|centos)$ ]] && [ "$MAJOR" -le 6 ]; then
  SERVICE="zabbix-agentd"
  INIT="sysv"
else
  SERVICE="zabbix-agent"
  INIT="systemd"
fi

echo "➡ Init: $INIT"
echo "➡ Servicio: $SERVICE"

# ======================
# FUNCIONES
# ======================
stop_service() {
  echo "Deteniendo servicio..."
  if [ "$INIT" == "systemd" ]; then
    systemctl stop "$SERVICE" || true
  else
    service "$SERVICE" stop || true
  fi
}

remove_agent() {
  echo "Eliminando agente previo..."
  case "$ID" in
    ol|rhel|centos|rocky|almalinux)
      if [ "$MAJOR" -ge 8 ]; then
        dnf remove -y zabbix-agent || true
      else
        yum remove -y zabbix-agent || true
      fi
      ;;
    ubuntu|debian)
      apt-get remove -y zabbix-agent || true
      ;;
  esac
}

clean_files() {
  echo "Limpiando archivos residuales..."
  rm -rf /etc/zabbix /var/log/zabbix /var/run/zabbix
}

install_agent() {
  echo "Instalando zabbix-agent..."
  case "$ID" in
    ol|rhel|centos|rocky|almalinux)
      if [ "$MAJOR" -ge 9 ]; then
        rpm -Uvh https://repo.zabbix.com/zabbix/7.0/rhel/9/x86_64/zabbix-release-7.0-1.el9.noarch.rpm
      elif [ "$MAJOR" -ge 8 ]; then
        rpm -Uvh https://repo.zabbix.com/zabbix/7.0/rhel/8/x86_64/zabbix-release-7.0-1.el8.noarch.rpm
      elif [ "$MAJOR" == "7" ]; then
        rpm -Uvh https://repo.zabbix.com/zabbix/6.0/rhel/7/x86_64/zabbix-release-6.0-4.el7.noarch.rpm
      elif [ "$MAJOR" == "6" ]; then
        rpm -Uvh https://repo.zabbix.com/zabbix/5.0/rhel/6/x86_64/zabbix-release-5.0-1.el6.noarch.rpm
      fi

      if [ "$MAJOR" -ge 8 ]; then
        dnf install -y zabbix-agent
      else
        yum install -y zabbix-agent
      fi
      ;;
    ubuntu|debian)
      apt update
      apt install -y zabbix-agent
      ;;
  esac
}

configure_agent() {
  mkdir -p /etc/zabbix /var/log/zabbix /var/run/zabbix

  cat > /etc/zabbix/zabbix_agentd.conf <<EOF
PidFile=/var/run/zabbix/zabbix_agentd.pid
LogFile=/var/log/zabbix/zabbix_agentd.log
Server=${ZABBIX_SERVER}
ServerActive=${ZABBIX_SERVER}
Hostname=${HOSTNAME_LOCAL}
Include=/etc/zabbix/zabbix_agentd.d/*.conf
EOF
}

start_service() {
  if [ "$INIT" == "systemd" ]; then
    systemctl enable "$SERVICE"
    systemctl restart "$SERVICE"
  else
    chkconfig "$SERVICE" on
    service "$SERVICE" restart
  fi
}

# ======================
# EJECUCIÓN
# ======================
stop_service
remove_agent
clean_files
install_agent
configure_agent
start_service

echo "======================================="
echo "✅ Zabbix Agent reinstalado correctamente"
echo "Hostname: $HOSTNAME_LOCAL"
echo "Server:   $ZABBIX_SERVER"
echo "Servicio: $SERVICE"
echo "======================================="
