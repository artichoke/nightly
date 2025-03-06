import subprocess

import stamina


@stamina.retry(on=subprocess.CalledProcessError, attempts=3)
def run_command_with_merged_output(command: list[str]) -> None:
    """
    Run the given command as a subprocess and merge its stdout and stderr
    streams. This function will retry the given command on any error, up to 3
    times.

    This is useful for funnelling all output of a command into a GitHub Actions
    log group.

    This command uses `check=True` when delegating to `subprocess`.
    """

    proc = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in proc.stdout.splitlines():
        if line:
            print(line, flush=True)
