# Connect OpenVPN

Automatic reconnecting for OpenVPN client

## Purpose

The Connect OpenVPN is a script that automatically reconnects your OpenVPN client to the server. The script monitors the network, and if the network connection drops due to issues such as a power outage, the script will automatically shut down the old VPN client and automatically reconnect when the network is stable again. 

## Usage

Configure your settings in config.ini and then launch your script with Python:

```jsx
python connect-openvpn.py
```