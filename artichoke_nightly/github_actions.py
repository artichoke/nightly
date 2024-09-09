import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


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
            print(f"{name}={value}", file=out)


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

    print(f"::group::{group}")
    try:
        yield
    finally:
        print("::endgroup::")


def emit_metadata() -> None:
    if os.getenv("CI") != "true" or os.getenv("GITHUB_ACTIONS") != "true":
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
