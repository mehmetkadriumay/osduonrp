import subprocess
import math
from dateutil import relativedelta
import string
import secrets
import cpuinfo
import signal
from enum import Enum
import sys
import os
import socket


def getconf_nprocs_online():
    """
    get number of procs online
    """
    try:
        output = subprocess.run(["getconf", "_NPROCESSORS_ONLN"], capture_output=True)
    except subprocess.CalledProcessError as err:
        return str(err)
    except FileNotFoundError:
        print("getconf not installed")
        return None
    else:
        return int(output.stdout.decode("ascii").strip())


def macos_performance_cores():
    cores = 0
    output = subprocess.run(["sysctl", "-a"], capture_output=True)
    for item in output.stdout.decode("ascii").split("\n"):
        if "hw.perflevel0.physicalcpu_max" in item:
            cores = item.split()[1]
    return int(cores)


def cpu_info():
    return cpuinfo.get_cpu_info()["brand_raw"]


def cpu_count():
    return cpuinfo.get_cpu_info()["count"]


def convert_size(size_bytes: int):
    """
    convert size in bytes human readable
    """
    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def convert_time(n):
    """
    Convert relative time to a human readable format
    """
    rd = relativedelta.relativedelta(seconds=int(n))
    return "{}:{:02d}:{:02d}".format(rd.hours, rd.minutes, rd.seconds)


def random_password(length: int = 10):
    letters = string.ascii_letters
    digits = string.digits
    # special_chars = string.punctuation
    # alphabet = letters + digits + special_chars
    alphabet = letters + digits
    pwd = ""
    for _ in range(length):
        pwd += "".join(secrets.choice(alphabet))
    return pwd


class GracefulExiter:
    def __init__(self):
        self.state = False
        signal.signal(signal.SIGINT, self.change_state)

    def change_state(self, signum, frame):
        print("exit flag set to True (repeat to exit now)")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.state = True

    def exit(self):
        return self.state


# setup simple output class
class OutputType(str, Enum):
    human = "human"
    excel = "excel"
    json = "json"
    csv = "csv"
    none = "none"


def open_file(filename):
    try:
        if sys.platform == "win32":
            os.startfile(filename)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filename])
    except FileNotFoundError:
        print(f"Unable to open: {filename}")


def resolvehostname(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


if __name__ == "__main__":
    print(resolvehostname("keycloak.localhost"))
    print(resolvehostname("keycloak.cimpl"))
    print(resolvehostname("foobar.localhost"))
