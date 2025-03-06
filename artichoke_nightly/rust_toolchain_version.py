#!/usr/bin/env python3

import argparse
import logging
import sys
import tomllib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import assert_never

from ._utils.github_actions import emit_metadata, log_group, set_output
from ._utils.logger import setup_logger

logger = logging.getLogger(__name__)


class OutputFormat(StrEnum):
    """Enum for output format options."""

    PLAIN = "plain"
    GITHUB = "github"


@dataclass(frozen=True, kw_only=True)
class Args:
    """Dataclass to store command line arguments."""

    file: Path = field(metadata={"help": "Path to the rust-toolchain.toml file."})
    format: OutputFormat = field(
        metadata={"help": "Output format: either 'plain' or 'github'."}
    )


def parse_args() -> Args:
    """Parse command line arguments into an Args dataclass."""
    parser = argparse.ArgumentParser(description="Set Rust toolchain version.")
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        required=True,
        help="Path to the rust-toolchain.toml file.",
    )
    parser.add_argument(
        "--format",
        type=OutputFormat,
        choices=list(OutputFormat),
        default=OutputFormat.PLAIN,
        help="Output format: either 'plain' or 'github'.",
    )
    args = parser.parse_args()
    return Args(file=args.file, format=args.format)


def read_toolchain_version(file_path: Path) -> str:
    """
    Read the Rust toolchain version from the rust-toolchain.toml file.

    Args:
        file_path (Path): Path to the rust-toolchain.toml file.

    Returns:
        str: The Rust toolchain version specified in the TOML file.

    Raises:
        FileNotFoundError: If the file does not exist or cannot be accessed.
        ValueError: If the TOML file is malformed.
        TypeError: If the TOML file does not contain the expected structure.
    """
    try:
        with file_path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Failed to parse rust-toolchain.toml file: {e}") from e

    # Validate the structure and type of the expected keys
    toolchain = data.get("toolchain")
    if toolchain is None:
        raise TypeError("Malformed rust-toolchain.toml: 'toolchain' stanza is missing.")
    if not isinstance(toolchain, dict):
        raise TypeError(
            "Malformed rust-toolchain.toml: 'toolchain' should be a dictionary."
        )

    channel = toolchain.get("channel")
    if channel is None:
        raise TypeError("Malformed rust-toolchain.toml: 'channel' field is missing.")
    if not isinstance(channel, str):
        raise TypeError("Malformed rust-toolchain.toml: 'channel' should be a string.")
    if not channel:
        raise ValueError("Malformed rust-toolchain.toml: 'channel' is empty.")

    return channel


def format_output(toolchain_version: str, output_format: OutputFormat) -> None:
    """
    Format the output based on the selected format.

    Args:
        toolchain_version (str): The Rust toolchain version.
        output_format (OutputFormat): The desired output format, either 'plain' or
            'github'.
    """
    match output_format:
        case OutputFormat.PLAIN:
            logger.info("Rust toolchain version: %s", toolchain_version)
        case OutputFormat.GITHUB:
            set_output(name="version", value=toolchain_version)
        case _:
            assert_never(output_format)


def main() -> int:
    """Main function to set Rust toolchain version."""
    setup_logger()
    emit_metadata()
    args = parse_args()

    with log_group("Setting Rust toolchain version"):
        try:
            toolchain_version = read_toolchain_version(args.file)
            format_output(toolchain_version, args.format)
        except (FileNotFoundError, OSError, ValueError, TypeError) as e:
            print(e, file=sys.stderr, flush=True)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
