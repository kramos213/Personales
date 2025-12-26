#!/bin/bash
set -e

### ===== VARIABLES =====
ZABBIX_SERVER="10.1.1.201"
HOSTNAME_LOCAL=$(hostname)

echo "======================================="
echo " Instalador Universal Zabbix Agent"
echo "======================================="

fail() {
  echo "❌ ERROR: $1"
  exit 1
}

service_start() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable zabbix-agent
    systemctl restart zabbix-agent
  else
    chkconfig zabbix-agent on
    service zabbix-agent restart
  fi
}

open_firewall() {
  if command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port=10050/tcp || true
    firewall-cmd --reload || true
  elif command -v ufw >/dev/null 2>&1; then
    ufw allow 10050/tcp || true
  fi
}

# ===== DETECTAR SO =====
[ -f /etc/os-release ] || fail "No se puede detectar el sistema operativo"
. /etc/os-release

ARCH=$(uname -m)
echo "➡ SO detectado: $NAME $VERSION_ID ($ARCH)"

# ===== RHEL / ORACLE / CENTOS =====
if [[ "$ID" =~ ^(ol|rhel|centos)$ ]]; then
  MAJOR=$(echo "$VERSION_ID" | cut -d'.' -f1)

  if [ "$MAJOR" -ge 8 ]; then
    rpm -Uvh https://repo.zabbix.com/zabbix/7.0/rhel/8/x86_64/zabbix-release-7.0-1.el8.noarch.rpm
    dnf clean all
    dnf install -y zabbix-agent || fail "Fallo instalación"
  elif [ "$MAJOR" == "7" ]; then
    rpm -Uvh https://repo.zabbix.com/zabbix/6.0/rhel/7/x86_64/zabbix-release-6.0-4.el7.noarch.rpm
    yum clean all
    yum install -y zabbix-agent || fail "Fallo instalación"
  fi
fi

# ===== UBUNTU =====
if [ "$ID" == "ubuntu" ]; then
  if [ "$VERSION_ID" == "22.04" ]; then
    wget -q https://repo.zabbix.com/zabbix/7.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_7.0-1+ubuntu22.04_all.deb
    dpkg -i zabbix-release_7.0-1+ubuntu22.04_all.deb
  fi

  apt update
  apt install -y zabbix-agent || fail "Fallo instalación"
fi

# ===== CONFIGURAR =====
CONF="/etc/zabbix/zabbix_agentd.conf"
[ -f "$CONF" ] || fail "No existe zabbix_agentd.conf"

sed -i "s/^Server=.*/Server=${ZABBIX_SERVER}/" $CONF
sed -i "s/^ServerActive=.*/ServerActive=${ZABBIX_SERVER}/" $CONF
sed -i "s/^Hostname=.*/Hostname=${HOSTNAME_LOCAL}/" $CONF

open_firewall
service_start

echo "✅ Zabbix Agent instalado correctamente"
echo "Hostname: $HOSTNAME_LOCAL"
echo "Server:   $ZABBIX_SERVER"
