## Developer Notes

To you develop & build cibutler you'll need [uv](https://docs.astral.sh/uv/) installed.
uv is a single tool to replace pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, and more.

Mac:

- `brew install uv`

Mac or Linux:

- `curl -LsSf https://astral.sh/uv/install.sh | sh`

Windows:

- `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### Running locally
```
uv run cibutler
```

### Building locally
```
uv build
```

### Install locally built packages via pipx
```
pipx install ./dist/cibutler-0.1.0-py3-none-any.whl --include-deps --pip-args="--extra-index-url=https://community.opengroup.org/api/v4/projects/148/packages/pypi/simple"
```
