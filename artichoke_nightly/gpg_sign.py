#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import traceback
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from .github_actions import emit_metadata, log_group, set_output
from .shell_utils import run_command_with_merged_output

GPG_SIGN_VERSION = "0.3.0"


@dataclass(frozen=True, kw_only=True)
class Args:
    artifact: Path
    release: str


def signing_identity() -> str:
    """
    Signing identity and GPG key fingerprint.
    """

    return "1C4A856ACF86EC1EE841180FAF57A37CAC061452"


def gpg_sign_artifact(*, artifact: Path, release_name: str) -> Path:
    """
    Create a GPG signature for the given artifact.
    """

    stage = Path("dist").joinpath(release_name)
    with log_group(f"Create GPG signature [{artifact.name}]"):
        with suppress(FileNotFoundError):
            shutil.rmtree(stage)
        stage.mkdir(parents=True)

        asc = stage.joinpath(f"{artifact.name}.asc")
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
                str(artifact),
            ]
        )

        return asc


def validate(*, artifact: Path, asc: Path) -> None:
    """
    Verify GPG signature for the given artifact.
    """

    with log_group("Verify GPG signature"):
        run_command_with_merged_output(
            ["gpg", "--batch", "--verify", "-vv", str(asc), str(artifact)]
        )


def parse_args() -> Args:
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

    if not args.artifact:
        raise ValueError("must provide an artifact to compute a signature for")

    artifact, *rest = args.artifact

    if rest:
        raise ValueError("too many artifacts provided")

    if not artifact.is_file():
        raise ValueError(f"artifact file {artifact} does not exist")

    if not args.release:
        raise ValueError("release name must be provided")

    return Args(
        artifact=artifact,
        release=args.release,
    )


def main() -> int:
    try:
        emit_metadata()

        args = parse_args()

        signature = gpg_sign_artifact(artifact=args.artifact, release_name=args.release)
        validate(artifact=args.artifact, asc=signature)

        set_output(name="signature", value=str(signature))
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
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
