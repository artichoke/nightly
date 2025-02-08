# tasks.py
from invoke import Collection, Context, task


@task
def lint_python(ctx: Context) -> None:
    """
    Lint Python files with ruff and pyright.
    """
    ctx.run("uv run pyright --warnings .", pty=True)
    ctx.run("uv run ruff check .", pty=True)


@task
def lint_yaml(ctx: Context) -> None:
    """
    Format YAML files with yamllint.
    """
    ctx.run("uv run yamllint .", pty=True)


@task(pre=[lint_python, lint_yaml])
def lint_default(ctx: Context) -> None:
    """
    Lint sources.
    """
    # This task exists solely to provide a common entry point.


lint_ns = Collection("lint")
lint_ns.add_task(lint_python, "python")
lint_ns.add_task(lint_python, "yaml")
lint_ns.add_task(lint_default, "default")


@task
def format_python(ctx: Context) -> None:
    """
    Format Python files with ruff.
    """
    ctx.run("uv run ruff format .", pty=True)
    ctx.run("uv run ruff check --fix .", pty=True)


@task
def format_text(ctx: Context) -> None:
    """
    Format text, YAML, and Markdown sources with prettier.
    """
    ctx.run("npm run fmt", pty=True)


@task(pre=[format_python, format_text])
def format_default(ctx: Context) -> None:
    """
    Format sources using ruff and prettier.
    """
    # This task is a wrapper that calls the two format subtasks.


format_ns = Collection("format")
format_ns.add_task(format_python, "python")
format_ns.add_task(format_text, "text")
format_ns.add_task(format_default, "default")


@task
def fmt_python(ctx: Context) -> None:
    """
    Alias: Format Python files with ruff.
    """
    ctx.run("uv run ruff format .", pty=True)
    ctx.run("uv run ruff check --fix .", pty=True)


@task
def fmt_text(ctx: Context) -> None:
    """
    Alias: Format text, YAML, and Markdown sources with prettier.
    """
    ctx.run("npm run fmt", pty=True)


@task(pre=[fmt_python, fmt_text])
def fmt_default(ctx: Context) -> None:
    """
    Alias: Format sources using ruff and prettier.
    """


fmt_ns = Collection("fmt")
fmt_ns.add_task(fmt_python, "python")
fmt_ns.add_task(fmt_text, "text")
fmt_ns.add_task(fmt_default, "default")


@task(default=True, pre=[format_default, lint_default])
def default(ctx: Context) -> None:
    """
    Default task: Format and lint sources.
    """


ns = Collection()
ns.add_task(default, "default")
ns.add_collection(lint_ns, "lint")
ns.add_collection(format_ns, "format")
ns.add_collection(fmt_ns, "fmt")
