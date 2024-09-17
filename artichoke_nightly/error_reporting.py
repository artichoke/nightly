import subprocess
import textwrap
import traceback
from typing import TextIO


def report_subprocess_error(
    e: subprocess.CalledProcessError, *, output: TextIO
) -> None:
    """
    Prints details of a subprocess error to the specified output stream,
    suitable for use in CLI entry points.

    Args:
        e (subprocess.CalledProcessError): The exception containing details
            about the failed subprocess command, including command, return
            code, stdout, and stderr.
        output (TextIO): The output stream (e.g., file or stderr) where error
            details will be printed.

    Prints the command, return code, stdout, stderr (if available), and the
    traceback to the given output stream, making it ideal for error reporting
    in command-line applications.
    """

    print("Error: failed to invoke command", file=output)
    print(f"    Command: {e.cmd}", file=output)
    print(f"    Return Code: {e.returncode}", file=output)

    if e.stdout and e.stdout.rstrip():
        print("", "Output:", sep="\n", file=output)
        print(textwrap.indent(e.stdout.rstrip(), "    "), file=output)

    if e.stderr and e.stderr.rstrip():
        print("", "Error Output:", sep="\n", file=output)
        print(textwrap.indent(e.stderr.rstrip(), "    "), file=output)

    print("", traceback.format_exc(), sep="\n", file=output)
