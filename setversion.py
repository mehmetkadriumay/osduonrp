#!/usr/bin/env python3
import typer
import time
from datetime import datetime
from typing_extensions import Annotated
import re
from git import Repo


def main(
    path: Annotated[str, typer.Argument(envvar="CI_PROJECT_NAME")],
    branch: Annotated[
        str, typer.Option("--branch", help="Release", envvar="CI_COMMIT_REF_NAME")
    ] = "dev",
    build: Annotated[
        str, typer.Option("--build", help="Build ID", envvar="CI_PIPELINE_IID")
    ] = "0",
    commit_id: Annotated[str, typer.Option(envvar="CI_COMMIT_SHA")] = "",
    commit_message: Annotated[str, typer.Option(envvar="CI_COMMIT_MESSAGE")] = "",
    commit_ref_slug: Annotated[str, typer.Option(envvar="CI_COMMIT_REF_SLUG}")] = "",
    commit_timestamp: Annotated[str, typer.Option(envvar="CI_COMMIT_TIMESTAMP")] = None,
    pyfile: Annotated[
        str, typer.Option("--pyfile", help="python file")
    ] = "_version.py",
    versionfile: Annotated[
        str, typer.Option("--version-file", help="Version file")
    ] = "VERSION",
    repo_path: Annotated[str, typer.Option(help="path to your repo")] = ".",
):
    """
    Simple utility to get pipeline version information and create _version.py
    """

    with open(versionfile, "r") as f:
        (major, minor, patch) = f.read().strip().split(".")

    try:
        repo = Repo(repo_path)
        git_branch = repo.active_branch
        branch = str(git_branch)
    except Exception:
        pass

    if branch == "master" or branch == "main":
        release = f"rc{patch}.dev{build}"
    elif branch.startswith("release"):
        release = f"{patch}"
    elif branch.startswith("trusted"):
        release = f"b{patch}.dev{build}"
    else:
        release = f"a{patch}.dev{build}"

    __version__ = f"{major}.{minor}.{release}"
    print(f"{__version__}")

    if not commit_timestamp:
        today = datetime.now()
        commit_timestamp = today.isoformat()

    regex = re.compile("[^a-zA-Z0-9_]")
    # comment_message = commit_message
    # commit_message = regex.sub("", commit_message[0:128])

    with open(path + "/" + pyfile, "w") as f:
        f.write(f'__version__ = "{__version__}"\n')
        f.write(f'__branch__ = "{branch}"\n')
        f.write(f'__build__ = "{build}"\n')
        f.write(f'__release__ = "{release}"\n')
        f.write(f"__buildtime__ = {time.time()}\n")
        f.write(f'__commitid__ = "{commit_id}"\n')
        f.write(f'__commitmessage__ = """{commit_message.strip()}"""\n')
        f.write(f'__committimestamp__ = "{commit_timestamp}"\n')
        f.write(f'__commitrefslug__ = "{commit_ref_slug}"\n')


if __name__ == "__main__":
    typer.run(main)
