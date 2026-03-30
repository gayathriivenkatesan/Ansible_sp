import re
from netmiko import ConnectHandler
from ansible.errors import AnsibleFilterError

def sp_ssh_connectivity(_value, ec_host: str, ec_username: str, ec_password: str):
    """
    Filter 3: Check SSH connectivity to Silver Peak device.
    Returns True if connection succeeds, otherwise raises error.
    """
    device = {
        "device_type": "silverpeak_vxoa",
        "host": ec_host,
        "username": ec_username,
        "password": ec_password,
        "fast_cli": False,
    }
    try:
        conn = ConnectHandler(**device)
        conn.disconnect()
        return True
    except Exception as e:
        raise AnsibleFilterError(f"SSH connectivity check failed: {e}")


def _ping_and_get_loss(device: dict, ec_command: str) -> float:
    """
    Connects to a device, runs ping, and extracts packet loss percentage as float.
    """
    try:
        conn = ConnectHandler(**device)
        # Using send_command_timing is safer for long-running commands like ping -c 10
        output = conn.send_command_timing(ec_command)
        conn.disconnect()
    except Exception as e:
        raise AnsibleFilterError(f"Failed SSH/connect/send failed: {e}")

    if not output:
        raise AnsibleFilterError("Failed Empty output from device")

    # Try common 'X% packet loss' patterns
    m = re.search(r'([\d.]+)\s*%\s*packet\s+loss', output, re.IGNORECASE) \
        or re.search(r'([\d.]+)\s*%\s*loss', output, re.IGNORECASE)

    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass

    # Fallback: compute from 'X packets transmitted, Y received'
    tx_rx = re.search(
        r'(?P<tx>\d+)\s+packets?\s+transmitted.*?(?P<rx>\d+)\s+packets?\s+received',
        output, re.IGNORECASE | re.DOTALL
    ) or re.search(
        r'(?P<tx>\d+)\s+packets?\s+transmitted.*?(?P<rx>\d+)\s+received',
        output, re.IGNORECASE | re.DOTALL
    )

    if tx_rx:
        tx = int(tx_rx.group('tx'))
        rx = int(tx_rx.group('rx'))
        if tx > 0:
            return round((tx - rx) * 100.0 / tx, 1)

    # If none matched, return the raw output in the error for debugging
    raise AnsibleFilterError(f"Failed Could not parse packet loss from output: {output}")


def sp_ssh_cli(_value,ec_host: str, ec_username: str, ec_password: str, ec_command: str):
    """
    Filter 1: Run a CLI command over SSH and return the raw output (string).
    """
    device = {
        "device_type": "silverpeak_vxoa",
        "host": ec_host,
        "username": ec_username,
        "password": ec_password,
        "fast_cli": False,
    }
    try:
        conn = ConnectHandler(**device)
        out = conn.send_command_timing(ec_command)
        conn.disconnect()
        return (out or "").strip()
    except Exception as e:
        raise AnsibleFilterError(f"SilverPeak SSH connection failed: {e}")


def sp_ping_loss(_value,ec_host: str, ec_username: str, ec_password: str, ec_command: str):
    """
    Filter 2: Run the ping command and return only the loss percentage (float).
    """
    device = {
        "device_type": "silverpeak_vxoa",
        "host": ec_host,
        "username": ec_username,
        "password": ec_password,
        "fast_cli": False,
    }
    return _ping_and_get_loss(device, ec_command)


class FilterModule(object):
    def filters(self):
        # These names are what you will call from Jinja in your playbook
        return {
            "sp_ssh_cli": sp_ssh_cli,
            "sp_ping_loss": sp_ping_loss,
            'sp_ssh_connectivity': sp_ssh_connectivity
        }

#ec_host="172.22.184.19"
#ec_username="admin2"
#ec_password="Admin@123"
#r=sp_ssh_connectivity("dummy", ec_host, ec_username, ec_password)
#print(r)
#ec_command="ping -I wan0 gateway.zscalerthree.net -c 10"
#a1=sp_ping_loss("dummy",ec_host,ec_username,ec_password,ec_command)
#print(a1)
#a2=sp_ssh_cli("dummy",ec_host,ec_username,ec_password,ec_command)
#print(a2)

