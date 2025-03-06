import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


def set_output(*, name: str, value: str) -> None:
    """
    Set an output for a GitHub Actions job.

    See the GitHub Actions documentation for [defining output for jobs] and
    changes to [deprecate the set-output command].

    [defining output for jobs]: https://docs.github.com/en/actions/using-jobs/defining-outputs-for-jobs
    [deprecate the set-output command]: https://github.blog/changelog/2022-10-11-github-actions-deprecating-save-state-and-set-output-commands/
    """

    if github_output := os.getenv("GITHUB_OUTPUT"):
        with Path(github_output).open("a") as out:
            print(f"{name}={value}", file=out, flush=True)


@contextmanager
def log_group(group: str) -> Iterator[None]:
    """
    Create an expandable log group in GitHub Actions job logs.

    Only prints log group markers when running in GitHub Actions CI. See the GitHub
    Actions documentation for [grouping log lines].

    Args:
        group (str): The name of the log group.

    [grouping log lines]: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#grouping-log-lines
    """
    if os.getenv("CI") != "true" or os.getenv("GITHUB_ACTIONS") != "true":
        # Do nothing if not running in GitHub Actions
        yield
        return

    # intentionally use print instead of logger to ensure the group is created.
    # These tokens are specially recognized by GitHub Actions to create log
    # groups.
    print(f"::group::{group}", flush=True)
    try:
        yield
    finally:
        print("::endgroup::", flush=True)


def emit_metadata() -> None:
    if os.getenv("CI") != "true" or os.getenv("GITHUB_ACTIONS") != "true":
        return
    with log_group("Workflow metadata"):
        if repository := os.getenv("GITHUB_REPOSITORY"):
            logger.info("GitHub Repository: %s", repository)
        if actor := os.getenv("GITHUB_ACTOR"):
            logger.info("GitHub Actor: %s", actor)
        if workflow := os.getenv("GITHUB_WORKFLOW"):
            logger.info("GitHub Workflow: %s", workflow)
        if job := os.getenv("GITHUB_JOB"):
            logger.info("GitHub Job: %s", job)
        if run_id := os.getenv("GITHUB_RUN_ID"):
            logger.info("GitHub Run ID: %s", run_id)
        if ref := os.getenv("GITHUB_REF"):
            logger.info("GitHub Ref: %s", ref)
        if ref_name := os.getenv("GITHUB_REF_NAME"):
            logger.info("GitHub Ref Name: %s", ref_name)
        if sha := os.getenv("GITHUB_SHA"):
            logger.info("GitHub SHA: %s", sha)


def runner_tempdir() -> Path | None:
    """
    Get the temporary directory used by the GitHub Actions runner.

    This function retrieves the path to the temporary directory used by the GitHub
    Actions runner during job execution. The directory path is taken from the
    `RUNNER_TEMP` environment variable, which is set by GitHub Actions. This
    directory is used for storing temporary files generated during the job run.

    Returns:
        Optional[Path]: A Path object pointing to the runner's temporary directory if
            the `RUNNER_TEMP` environment variable is set; otherwise, returns None.

    Example:
        >>> temp_dir = runner_tempdir()
        >>> if temp_dir:
        ...     print(f"Temporary directory: {temp_dir}")
    """

    if temp := os.getenv("RUNNER_TEMP"):
        return Path(temp)
    return None
