import subprocess
import os
import signal


def start_reverse_tunnel(formatted_host):
    try:		
        subprocess.Popen('sshpass -p $SSHPASS /usr/bin/ssh -N -R ' + formatted_host, shell=True)

    except Exception as e:
        print "Failed to create tunnel: {}".format(e)


def stop_reverse_tunnel(reverse_tunnel_formatted_host):
    print "Stopping reverse tunnel"
    subprocess.call(['pkill', '-f', reverse_tunnel_formatted_host])


def is_tunnel_process_running(reverse_tunnel_formatted_host):
    running = 0
    is_running = subprocess.call(['pgrep', '-f', reverse_tunnel_formatted_host]) == running
    print "Tunnel is running: {}".format(is_running)
    return is_running


