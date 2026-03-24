import psutil
import json

def get_cpu_temp():
    """Return CPU temperature in degrees Celsius."""
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read().strip()) / 1000


def get_cpu_load():
    """Return CPU load as a percentage over a 0.5s sample window."""
    return psutil.cpu_percent(interval=0.5)


def get_wifi_strength():
    """
    Return Wi-Fi signal strength as a tuple of (dBm, percentage, quality label).
    Reads directly from the kernel wireless info file instead of parsing iwconfig.
    dBm range: -100 (weakest) to -50 (strongest).
    Percentage mapping: -100 dBm = 0%, -50 dBm = 100%.
    """
    with open("/proc/net/wireless") as f:
        lines = f.readlines()

    # Lines 0 and 1 are headers, line 2 is the first wireless interface
    if len(lines) < 3:
        return None  # no wireless interface found

    dbm = int(float(lines[2].split()[3].rstrip(".")))
    percent = f"{max(0, min(100, 2 * (dbm + 100)))}%"

    if dbm >= -50:   quality = "Excellent"
    elif dbm >= -60: quality = "Good"
    elif dbm >= -70: quality = "Fair"
    elif dbm >= -80: quality = "Weak"
    else:            quality = "Very Poor"

    return dbm, percent, quality

def return_sys_health():
    return json.dumps({
        "cpu_temp": get_cpu_temp(),
        "cpu_load": get_cpu_load(),
        "wifi_strength": get_wifi_strength()
    })

if __name__ == "__main__":
    print(return_sys_health())
