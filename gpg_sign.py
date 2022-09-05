#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path

GPG_SIGN_VERSION = "0.1.0"


def run_command_with_merged_output(command):
    """
    Run the given command as a subprocess and merge its stdout and stderr
    streams.

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
            print(line)


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


def signing_identity():
    """
    Signing identity and GPG key fingerprint.
    """

    return "1C4A856ACF86EC1EE841180FAF57A37CAC061452"


def gpg_sign_artifact(*, artifact_path, release_name):
    """
    Create a GPG signature for the given artifact.
    """

    stage = Path("dist").joinpath(release_name)
    with log_group(f"Create GPG signature [{artifact_path.name}]"):
        try:
            shutil.rmtree(stage)
        except FileNotFoundError:
            pass
        os.makedirs(stage, exist_ok=True)

        asc = stage.joinpath(f"{artifact_path.name}.asc")
        run_command_with_merged_output(
            [
                "gpg",
                "--batch",
                "--yes",
                "--detach-sign",
                "-vv",
                "--armor",
                "--local-user",
                signing_identity(),
                "--output",
                str(asc),
                str(artifact_path),
            ]
        )

        return asc


def validate(*, artifact_name, asc):
    """
    Verify GPG signature for the given artifact.
    """

    with log_group("Verify GPG signature"):
        run_command_with_merged_output(
            ["gpg", "--batch", "--verify", "-vv", str(asc), str(artifact_name)]
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compute a GPG signature for an artifact"
    )
    parser.add_argument(
        "-a",
        "--artifact",
        action="append",
        required=True,
        type=Path,
        help="path to artifact to sign",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {GPG_SIGN_VERSION}",
    )
    parser.add_argument("release", help="release name")
    args = parser.parse_args()

    if len(args.artifact) > 1:
        print(
            (
                "Error: Too many artifacts provided. "
                "GPG signing script can only sign one artifact at a time."
            ),
            file=sys.stderr,
        )
        return 1

    artifact = args.artifact[0]
    if not artifact.is_file():
        print(f"Error: artifact file {artifact} does not exist", file=sys.stderr)
        return 1

    try:
        emit_metadata()

        signature = gpg_sign_artifact(artifact_path=artifact, release_name=args.release)
        validate(artifact_name=artifact, asc=signature)

        set_output(name="signature", value=signature)

        return 0
    except subprocess.CalledProcessError as e:
        print("Error: failed to invoke command", file=sys.stderr)
        print(f"    Command: {e.cmd}", file=sys.stderr)
        print(f"    Return Code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print()
            print("Output:", file=sys.stderr)
            for line in e.stdout.splitlines():
                print(f"    {line}", file=sys.stderr)
        if e.stderr:
            print()
            print("Error Output:", file=sys.stderr)
            for line in e.stderr.splitlines():
                print(f"    {line}", file=sys.stderr)
        print()
        print(traceback.format_exc(), file=sys.stderr)
        return e.returncode
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
