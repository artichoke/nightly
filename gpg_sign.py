#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path


def set_output(*, name, value):
    """
    Set an output for a GitHub Actions job.

    https://docs.github.com/en/actions/using-jobs/defining-outputs-for-jobs
    """

    print(f"::set-output name={name}::{value}")


@contextmanager
def log_group(group):
    """
    Create an expandable log group in GitHub Actions job logs.

    https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#grouping-log-lines
    """

    print(f"::group::{group}")
    try:
        yield
    finally:
        print("::endgroup::")


def emit_metadata():
    if os.getenv("CI") != "true":
        return
    with log_group("Workflow metadata"):
        if repository := os.getenv("GITHUB_REPOSITORY"):
            print(f"GitHub Repository: {repository}")
        if actor := os.getenv("GITHUB_ACTOR"):
            print(f"GitHub Actor: {actor}")
        if workflow := os.getenv("GITHUB_WORKFLOW"):
            print(f"GitHub Workflow: {workflow}")
        if job := os.getenv("GITHUB_JOB"):
            print(f"GitHub Job: {job}")
        if run_id := os.getenv("GITHUB_RUN_ID"):
            print(f"GitHub Run ID: {run_id}")
        if ref := os.getenv("GITHUB_REF"):
            print(f"GitHub Ref: {ref}")
        if ref_name := os.getenv("GITHUB_REF_NAME"):
            print(f"GitHub Ref Name: {ref_name}")
        if sha := os.getenv("GITHUB_SHA"):
            print(f"GitHub SHA: {sha}")


def codesigning_identity():
    """
    Codesigning identity and GPG key fingerprint.
    """

    return "1C4A856ACF86EC1EE841180FAF57A37CAC061452"


def gpg_sign_binary(*, binary_path, release_name):
    """
    Create a GPG signature for the given binary.
    """

    stage = Path("dist").joinpath(release_name)
    with log_group(f"Create GPG signature [{binary_path.name}]"):
        try:
            shutil.rmtree(stage)
        except FileNotFoundError:
            pass
        os.makedirs(stage, exist_ok=True)

        asc = stage.joinpath(f"{binary_path.name}.asc")
        subprocess.run(
            [
                "gpg",
                "--batch",
                "--yes",
                "--detach-sign",
                "-vv",
                "--armor",
                "--local-user",
                codesigning_identity(),
                "--output",
                str(asc),
                str(binary_path),
            ],
            check=True,
        )
        return asc


def validate(*, binary_name, asc):
    """
    Verify GPG signature for the given binary.
    """

    with log_group("Verify GPG signature"):
        subprocess.run(
            [
                "gpg",
                "--batch",
                "--verify",
                "-vv",
                str(asc),
                str(binary_name),
            ],
            check=True,
        )


def main(args):
    if not args:
        print("Error: pass name of release as first argument", file=sys.stderr)
        return 1

    release_name, *args = args
    binaries = []
    append_next = None
    for arg in args:
        if append_next is None:
            if arg == "--binary":
                append_next = binaries
                continue
            print(f"Unexpected argument: {arg}", file=sys.stderr)
            return 1
        append_next.append(Path(arg))
        append_next = None

    if append_next is not None:
        if append_next is binaries:
            print("Error: unterminated --binary flag", file=sys.stderr)
        return 1

    if not binaries:
        print("Error: no binaries passed to be codesigned", file=sys.stderr)
        return 1

    for binary in binaries:
        if not binary.is_file():
            print("Error: {binary} does not exist", file=sys.stderr)
            return 1

    if len(binaries) > 1:
        print(
            "Error: Too many --binary arguments. GPG codesigning script can only sign one binary at a time.",
            file=sys.stderr,
        )
        return 1

    binary = binaries[0]

    try:
        emit_metadata()

        signature = gpg_sign_binary(binary_path=binary, release_name=release_name)
        validate(binary_name=binary, asc=signature)

        set_output(name="signature", value=signature)

        return 0
    except subprocess.CalledProcessError as e:
        print(
            f"""Error: failed to invoke command.
            \tCommand: {e.cmd}
            \tReturn Code: {e.returncode}""",
            file=sys.stderr,
        )
        return e.returncode
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(args))
