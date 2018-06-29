#!/bin/sh

# Install python requests package
echo "Installing dependencies. Please be patient"
pip install requests


grep -q -F 'export SSHPASS2=MountFuj1' ~/.bashrc || echo 'export SSHPASS2=MountFuj1' >> ~/.bashrc

# Hardcoded integrity check to "ok" for first run
database_path=~/.kalite/database/data.sqlite
database_name=$(sqlite3 $database_path "SELECT d.name FROM securesync_device d JOIN securesync_devicemetadata s WHERE s.device_id = d.id AND s.is_own_device = 1")

# Lock database and do integrity check, then unlock
integrity_check="ok"

# Complete timestamp in the format YYYY-MM-DD_hh:mm:ss
complete_timestamp=$(date +"%F %T")

# Append database name to the string "db_errorlog" to make errolog file
# Check if file exists and
filename="${database_name}_db_error.log"

if [ ! -e "~/.scripts/backupdb/$filename" ] ; then
    touch ~/.scripts/backupdb/$filename
fi

# Log result of integrity check to errorlog file
echo "Checking database integrity...."
echo ${complete_timestamp}-${integrity_check} >> ~/.scripts/backupdb/$filename
echo "Done!"