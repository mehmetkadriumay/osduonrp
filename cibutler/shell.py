import shlex
import logging
import subprocess
from rich.console import Console

console = Console()
error_console = Console(stderr=True, style="bold red")


def run_shell_command(command_line):
    command_line_args = shlex.split(command_line)

    logging.info('Subprocess: "' + command_line + '"')
    logging.info(command_line_args)

    try:
        subprocess.call(
            command_line_args,
            # stdout=subprocess.DEVNULL,  # Suppress standard output
            # stderr=subprocess.STDOUT,    # Redirect standard error to standard output
            # shell=False,                 # Use shell=False for security reasons
        )
    except (OSError, subprocess.CalledProcessError) as exception:
        logging.info("Exception occurred: " + str(exception))
        logging.info("Subprocess failed")
        return False
    else:
        # no exception was raised
        logging.info("Subprocess finished")

    return True


if __name__ == "__main__":
    retval = run_shell_command("/bin/echo Hello World")
    if retval:
        logging.info("Command executed successfully")
    else:
        logging.error("Command execution failed")
