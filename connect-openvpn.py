import os
import subprocess
import netifaces
import configparser
import time
import socket
import logging


config = configparser.ConfigParser()
logger = logging.getLogger()


ping_servers = [
    "1.1.1.1",
    "8.8.8.8",
    "8.8.4.4",
    "208.67.222.222" # OpenDNS
] 


def interface_exists(interface_name):
    logger.info("Checking if interface '{}' exists".format(interface_name))
        

    if interface_name in netifaces.interfaces():
        logger.debug("Interface '{}' exists".format(interface_name))
        return True

    logger.debug("Interface {} does not exist".format(interface_name))
    return False


def is_openvpn_running():
    logger.info("Checking if the OpenVPN client is currently running")
    proc = subprocess.Popen(
        ["ps", "-a"], stdout=subprocess.PIPE
    )
    output = str(proc.communicate())
    if "openvpn" in output:
        logger.debug("There was keyword 'openvpn' in processes, so OpenVPN client is running")
        return True
    logger.debug("There was not keyword 'openvpn' in processes, so OpenVPN client is not running")
    return False


def connect_openvpn(certificate="certificate.ovpn"):
    logger.info("Connecting to the OpenVPN server using certificte '{}'".format(certificate))
    # Start OpenVPN client, using the ovpn profile. Send output to null and run in background.
    status = os.system("sudo openvpn --config " + str(certificate) + " > /dev/null &")
    logger.debug("Status of the OpenVPN client execution: {}".format(str(status)))


def kill_openvpn_client():
    logger.info("Killing OpenVPN client")
    status = os.system("sudo pkill -9 openvpn")
    logger.debug("Status of the OpenVPN client kill: {}".format(str(status)))


def ping(address):

    try:
        socket.setdefaulttimeout(int(config['general']['SOCKET_TIMEOUT']))
        socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        ).connect((address, 53))
        return True
    except Exception as e:
        return False


def is_network_up():
    logger.debug("Checking whether the Internet connection is up")
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
    logger.info("Checking if the connection is stable. Calling 'is_network_up()'")

    up_status = is_network_up()

    logger.info("Up_status of the network is '{}'".format(up_status))

    if up_status:
        # If network is up wait for CONNECTION_STABLE_TIME

        logger.info("Network was up, waiting '{}'s".format(
            config["general"]["CONNECTION_STABLE_TIME"]
        ))

        # Do not just wait CONNECTION_STABLE_TIME and check the connection,
        # do the cheking in smaller time interval continuously
        polling_interval = 10

        if config["general"]["CONNECTION_STABLE_TIME"] < 60:
            polling_interval = 5

        for i in range(0, config["general"]["CONNECTION_STABLE_TIME"] / polling_interval):
            if not is_network_up():
                logger.info("In polling for stable connection, connection went down at some point")
                up_status = False
                break
            else:
                time.sleep(polling_interval)
                up_status = True

        if up_status:
            # We have stable connection
            logger.info("Connection was ok whole time, so we have stable connection")
            return True
        else:
            # No stable connection
            logger.info("No stable connection")
            return False
    else:
        # No stable connection
        logger.info("The first time when cheking is network up, it failed")
        return False

def main():
    # Read configurations from config.ini
    try:
        config.read_file(open('config.ini'))

        logging.basicConfig(level=logging.DEBUG)
        logger_h = logging.FileHandler(config['general']['LOG_FILE'])
        logger_h.setFormatter(logging.Formatter('%(name)s - %(funcName)20s() - %(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(logger_h)

    except Exception as e:
        logger.exception("Could not read config.ini file")
        raise

    while True:

        if is_connection_stable():

            logger.info("Stable connection")

            if not is_openvpn_running():
                #  Network is stable and openvpn is not running, we can connect to VPN
                logger.info("OpenVPN not running, connecting!")
                connect_openvpn(config["general"]["CERTIFICATE"])

            # Else the connection is stable and vpn is running, so we do nothing

        else:
            # Unstable connection

            logger.info("Unstable connection")

            if is_openvpn_running():
                # If the VPN is running, we need to kill it
                logger.info("OpenVPN running, killing it")
                kill_openvpn_client()
            
            # If the VPN is not yet running, do nothing
        
        # Wait 5 sec for next check
        time.sleep(5)

if __name__=="__main__":
    main()
    pass