from random import randint
# Properties file for remote support client


# authentication values
username = "techzm"  # this user will need to be setup via
password = "techzm"  # the admin console

develop_mode = False
DEBUG_LEVEL = 1
cert_file = "edulution.crt"
enable_https = False  # ONLY set to True when running against an HTTPS server

# reverse tunnel config
reverse_tunnel_port = randint(10000,99999)
reverse_tunnel_username = "kapsakala"
reverse_tunnel_server = "35.229.55.248"

# default configuration
default_path = '~/.scripts'  # path from original script for image
default_path_to_ka_lite = "~/.kalite/database/data.sqlite"
default_update_api = "/app/update/"
default_backup_path = "~/backups/"
default_connect_status_api = "/app/connectStatus/"

# ka lite query
kalite_query = """
        select d.name,version from securesync_device d
        join securesync_devicemetadata s
        where s.device_id = d.id
        and s.is_own_device = 1 """
