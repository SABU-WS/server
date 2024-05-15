#!/bin/bash

# STOP SABU SERVICE
systemctl stop sabu.service >/dev/null

# NFTABLES MAINTENANCE
sh /sabu/server/core/scripts/filtering_maintenance.sh
sleep 3

# UPDATE SOURCES
cd /sabu/server
git stash
git config --global --add safe.directory /sabu/server
git pull

# UPDATE VENV
source /sabu/venv-sabu/bin/activate >/dev/null
pip3 install -r /sabu/server/requirements.txt >/dev/null
flask db upgrade

# UPDATE PERMISSIONS
chmod -R 0750 /sabu/ >/dev/null
chown -R svc-sabu:svc-sabu /sabu/ >/dev/null

# START SABU SERVICE
systemctl start sabu.service >/dev/null

# CHECK SABU SERVICE
COMMAND=$(systemctl status sabu.service)
STATUS=$?

if [ $STATUS -eq 0 ]
then
    echo "SABU: Updated"

else
    echo "ERROR: Start service"
fi

# NFTABLES PROD
sh /sabu/server/core/scripts/filtering_prod.sh
sleep 3
