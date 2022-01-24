import os
import subprocess
import netifaces
import configparser
import time


config = configparser.ConfigParser()

ping_servers = [
    "elisa.fi",
    "telia.fi",
    "google.com",
    "apple.com"
]


def interface_exists(interface_name):
    if interface_name in netifaces.interfaces():
        return True
    else:
        return False


def is_openvpn_running():
    proc = subprocess.Popen(
        ["ps", "-a"], stdout=subprocess.PIPE
    )
    output = str(proc.communicate())
    if "openvpn" in output:
        return True
    else:
        return False


def connect_openvpn(certificate="certificate.ovpn"):
    # Start OpenVPN client, using the ovpn profile. Send output to null and run in background.
    os.system("sudo openvpn --config " + str(certificate) + " > /dev/null &")


def kill_openvpn_client():
    os.system("sudo pkill -9 openvpn")


def ping(address):
    proc = subprocess.Popen(
        ["ping", "-c", "1", "-W", "1", str(address)], stdout=subprocess.PIPE
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

def is_connection_stable():
    """Function for checking if the connection is stable
    """
    # Check if the network is up. 
    up_status = is_network_up()

    if up_status:
        # If network is up wait for CONNECTION_STABLE_TIME
        time.sleep(config["general"]["CONNECTION_STABLE_TIME"])

        # Check if network is up again
        up_status = is_network_up()

        if up_status:
            # We have stable connection
            return True
        else:
            # No stable connection
            return False
    else:
        # No stable connection
        return False

def main():
    # Read configurations from config.ini
    try:
        config.read_file(open('config.ini'))
    except Exception as e:
        print("Could not read config.ini file")
        raise

    while True:

        if is_connection_stable():

            if not is_openvpn_running():
                #  Network is stable and openvpn is not running, we can connect to VPN
                connect_openvpn(config["general"]["CERTIFICATE"])

            # Else the connection is stable and vpn is running, so we do nothing

        else:
            # Unstable connection

            if is_openvpn_running():
                # If the VPN is running, we need to kill it
                kill_openvpn_client()
            
            # If the VPN is not yet running, do nothing
        
        # Wait 5 sec for next check
        time.sleep(5)

if __name__=="__main__":
    main()
