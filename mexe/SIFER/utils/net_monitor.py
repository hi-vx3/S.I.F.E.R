import subprocess
def get_ssid():
    try:
        result = subprocess.check_output("netsh wlan show interfaces", shell=True).decode()
        for line in result.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
        return "غير معروف"
    except:
        return "غير معروف"