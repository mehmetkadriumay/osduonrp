import subprocess


def docker_info_memtotal():
    """
    Return memory setting/allow to be used by docker
    """
    return int(docker_info(outputformat="{{json .MemTotal}}"))


def docker_info_ncpu():
    """
    Return Number of CPUs setting/allow to be used by docker
    """
    return int(docker_info(outputformat="{{json .NCPU}}"))


def docker_info(outputformat):
    """
    Return docker info
    """
    try:
        output = subprocess.run(
            ["docker", "info", "--format", outputformat], capture_output=True
        )
    except subprocess.CalledProcessError as err:
        return str(err)
    else:
        return output.stdout.decode("ascii").strip()
