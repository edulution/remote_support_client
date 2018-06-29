import requests
import sqlite3
from os.path import expanduser
import subprocess
from datetime import datetime
import httplib
import os
import sys
import cookielib
import urllib, urllib2, httplib, ssl
from utils.authenticationTools import *
from utils.reverseTunnelingTools import *
from utils.client_properties import *

usage = """client.py <HOST URL> <GIT REPO WITH SCRIPTS>"""


scripts_path = ""
django_app_url = ""

# read path from args if provided
if len(sys.argv) == 2:
    django_app_url = sys.argv[1]
    scripts_path = default_path
elif len(sys.argv) == 3:
    django_app_url = sys.argv[1]
    scripts_path = sys.argv[2]
else:
    print "Error - Missing/Too many arguments"
    print usage
    sys.exit(1)


if not develop_mode:

    # check if path exists
    if not os.path.isdir(scripts_path):
        print "Error - Path {} does not exist or is not a directory (i.e. is a file)".format(scripts_path)
        print "Please check and retry with a valid file directory"
        print usage
        sys.exit(1)

    # get top 3 lines of git log to get id and date of most recent commit
    latest_update_in_millis = ""
    try:
        latest_update = subprocess.check_output("cd " + scripts_path + ";git log --date=raw -1 | grep Date:", shell=True)
        latest_update_in_millis = latest_update[8:-7]
    except Exception as e:
        print 'Error - Failed to read Git log - Is path a Git Repository?'
        print e

    # get device name and version from kalite database
    device = ""
    version = ""
    try:
        # connect to kalite database file
        ka_database = expanduser(default_path_to_ka_lite)
        db = sqlite3.connect(ka_database)
        c = db.cursor()
        results = c.execute(kalite_query)
        for row in results:
            device = row[0]
            version = row[1]
    except Exception as e:
        print "Failed to read device name/kalite version"
        print e

    # Get database size in readable format
    database_size = ""
    try:
        database_size = subprocess.check_output("du " + default_path_to_ka_lite + " -s | head -n 1 | awk '{print $1;}'",
                                                shell=True).strip()
    except Exception as e:
        print "Failed to read database size"
        print e

    number_backups = 0
    oldest_backup = "none"
    most_recent_backup = "none"

    # check if backups directory exists,
    if not os.path.isdir(expanduser(default_backup_path)):
        print 'Backups directory {}, not found - setting backup related ' \
              'fields to "none"'.format(default_backup_path)

    else:
        # #Get number of backups in backups folder
        number_backups = subprocess.check_output(
            "find " + default_backup_path + " -mindepth 1 -type f -name '*.sqlite' -printf x | wc -c", shell=True)

        # #Get oldest backup in backups folder
        oldest_backup = subprocess.check_output(
            "basename $(find " + default_backup_path + " -name '*.sqlite' -type f -print0 | xargs -0 ls | head -n 1)| cut -d. -f1",
            shell=True)

        # #Get most recent backup in backups folder
        most_recent_backup = subprocess.check_output(
            "basename $(find " + default_backup_path + " -name '*.sqlite' -type f -print0 | xargs -0 ls | tail -n 1)| cut -d. -f1",
            shell=True)

    last_check = ""
    integrity_result = ""
    try:
        error_log_output = subprocess.check_output(
            "cd " + scripts_path + ";./read_db_errorlog.sh", shell=True)
        output_lines = error_log_output.split('\n')
        output_lines.pop()
        last_check, integrity_result = [':'.join(x[1:]).strip() for x in [y.split(':') for y in output_lines]]
    except Exception as e:
        print "Failed to read last check and/or integrity"
        print e

    distro_version = ""
    try:
        lsb_release_output = subprocess.check_output(
            "cat /etc/lsb-release", shell=True)

        lsb_release_lines = lsb_release_output.split('\n')
        distro_version = lsb_release_lines[1].split('=')[1]
    except Exception as e:
        print "Failed to read distro version"
        print e

else:
    oldest_backup = "none"
    most_recent_backup = "none"
    device = 'TEST_DEVICE8'
    version = 'TEST_VERSION'
    latest_update_in_millis = '100'
    database_size = '100'
    number_backups = 5
    oldest_backup = 'TEST_BACKUP'
    most_recent_backup = str(datetime.today().date())
    last_check = "none"
    integrity_result = "ok"
    distro_version = '16.04'


# call to CONNECT API to check if reverse tunnel is needed
reverse_tunnel_requested = False
reverse_tunnel_ready = False
try:
    url = django_app_url + default_connect_status_api
    data = {'device': device}

    connect_response = requests.get(url, params=data)
    print connect_response

    connect_response_json = connect_response.json()
    print connect_response_json

    reverse_tunnel_requested = connect_response_json['status']
    print "Reverse tunnel status response: {}".format(reverse_tunnel_requested)

    reverse_tunnel_formatted_host = "{}:localhost:22 {}@{}".format(
        reverse_tunnel_port,
        reverse_tunnel_username,
        reverse_tunnel_server
    )
    # if reverse tunnel requested - true
    if reverse_tunnel_requested:
        print "Tunnel requested"
        if not is_tunnel_process_running(reverse_tunnel_formatted_host):
            start_reverse_tunnel(reverse_tunnel_formatted_host)

    # else reverse tunnel requested - false
    else:
        if is_tunnel_process_running(reverse_tunnel_formatted_host):
            stop_reverse_tunnel(reverse_tunnel_formatted_host)

    # check if reverse tunnel is running
    reverse_tunnel_ready = is_tunnel_process_running(reverse_tunnel_formatted_host)

except Exception as e:
    print 'Error - Failed to retrieve connection status'
    print "Unexpected error:", sys.exc_info()[0]
    print e

# Send data
try:
    url = django_app_url + default_update_api
    sendDataService = SendDataService(username,password)

    data = {'device': device,
            'version': version,
            'latest_update_in_milis': latest_update_in_millis,
            'database_size': database_size,
            'number_of_backups': number_backups,
            'oldest_backup': oldest_backup,
            'most_recent_backup': most_recent_backup,
            'last_integrity_check': last_check,
            'integrity_result': integrity_result,
            'distro_version': distro_version,
            "reverse_tunnel_ready": reverse_tunnel_ready,
            "reverse_tunnel_port": reverse_tunnel_port
            }

    response = sendDataService.send_data(url, data)

    print 'Url call: ' + url
    if response:
        print 'Success'
    else:
        print 'Error - Failed to send information to server'
        print 'Server responded with {}'.format(r)
except Exception as e:
    print e
    print 'Error - Failed to send information to server'
    print e.message


# Print device name, version, and most recent commit to screen
print 'Device:', device
print 'Version:', version
print 'Latest Update:', latest_update_in_millis
print 'Database Size:', database_size
print 'Number of Backups:', number_backups
print 'Oldest Backup:', oldest_backup
print 'Most recent Backup:', most_recent_backup
print 'Integrity Check Result:', integrity_result
print 'Last Integrity Check:', last_check
print 'Distro Version:', distro_version
print 'Reverse Tunnel Port:', reverse_tunnel_port
print 'Reverse Tunnel Ready:', reverse_tunnel_ready
