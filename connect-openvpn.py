import os
import subprocess
import netifaces
import configparser


config = configparser.ConfigParser()
config.read_file(open('config.ini'))


ping_servers = [
    "elisa.fi",
    "telia.fi",
    "google.com",
    "apple.com"
]


def interface_exists(interface_name):
    if (interface_name in netifaces.interfaces()):
        return True
    return False


def is_openvpn_running():
    proc = subprocess.Popen(
        ["ps", "-a"], stdout=subprocess.PIPE
    )
    output = str(proc.communicate())
    if "openvpn" in output:
        return True
    return False


def connect_openvpn(certificate):
    if (not certificate):
        certificate = "certificate.ovpn"
    # Start OpenVPN client, using the ovpn profile. Send output to null and run in background.
    os.system("sudo openvpn --config " + str(certificate) + " > /dev/null &")


def kill_openvpn_client():
    os.system("sudo pkill -9 openvpn")


def ping(address):
    proc = subprocess.Popen(
        ["ping", "-c", "1", "-w", "3", str(address)], stdout=subprocess.PIPE
    )
    output = str(proc.communicate())
    if (
        "1 packets transmitted" in output and
        "1 received" in output
    ):
        return True
    return False

def is_network_up():
    # If the fist server says that the connection is up, we can assume that 
    # it is really up. 
    for i, server in enumerate(ping_servers):
        network_up = ping(server)
        if not network_up:
            if i == len(ping_servers) - 1:
                # Last server that we are checking against
                return False
            else:
                continue
                
        else:
            return True


'''

Check if the network is up. 

If the network connection is up wait CONNECTION_STABLE_TIME.
If it still up, we can assume that it is stable connection. 

Then OpenVPN client can connect to OpenVPN server using *.ovpn profile.

In case network goes down (we cannot get reply for the ping from servers)
interface might be dropped (down) and then back up, kill the client and
start it again.

'''
