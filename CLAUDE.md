- This project is about doing things with the X API. Be careful, do not do something that will post or delete data without my explicit validation.
- When reading docs online, start by checking in an `/llms.txt` entrypoint exists that would make it easier for you to navigate the docs.
- Heavily use the X API documentation at https://docs.x.com/.
- If unsure how to use `requests`, read its documentation at https://docs.python-requests.org/.
- Make the code as simple as possible, only add what I ask for.
- Before finishing any non-trivial changes, run `python validate.py` from the workspace root. It validates all projects in parallel. Fix any errors and re-run until everything passes.
- ALWAYS TYPE CHECK. DO NOT SUPPRESS TYPE CHECKING ERRORS. USE CORRECT FIXES AND GOOD PRACTICES.
- ALWAYS REPORT ERRORS. DO NOT SUPPRESS ERRORS UNLESS ASKED TO DO SO. USE EXCEPTIONS TO REPORT ISSUES.
- Always manage dependencies with `uv`.  Put development, testing, linting dependencies into the `--dev` group. Use `uv run` (`--dev` if needed) to run scripts and tools.
- Use the standard library, then internal code, then existing dependencies, then only add dependencies if needed and reasonable. Do it with `uv add`.
- Use click for CLIs, validate strictly. Make required arguments required, and exclusive arguments exclusive.

## Workspace Structure

The repo is a uv workspace with three top-level directories:

- **`library/`** — the `a_gn_x_api_tests` package, CLI scripts, and tests. Its `pyproject.toml` owns all library dependencies.
- **`terminal_ui/`** — the Textual UI. Its `pyproject.toml` declares `a-gn-x-api-tests` as a workspace dependency and owns all UI-specific dependencies (e.g. `textual`). Never add UI dependencies to `library/`.
- Root `pyproject.toml` — workspace manifest only (`[tool.uv.workspace]`), no library code lives here.

To add a dependency to a project: `cd library` (or `terminal_ui`) then `uv add <pkg>`.

## Terminal UI

- The terminal UI package is `x_api_tui`, living in `terminal_ui/x_api_tui/`.
- The UI must always give the user clear feedback: show progress, confirm destructive actions before executing, display success/failure for every operation. Never silently swallow errors or leave the user wondering what happened.
- Use Textual for the terminal UI. Follow Textual best practices: use `SelectionList` or custom `ListView` for multi-select, use `capture_mouse()` for drag interactions, handle all errors by displaying them in the UI rather than crashing.
