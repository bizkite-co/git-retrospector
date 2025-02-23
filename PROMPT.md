You are helping to refactor some Python scripts into a reusable Python module. The goal is to create a module called `git-test-retrospector` that can run tests on a range of Git commits and analyze the results.

The original scripts were located in `/home/mstouffer/repos/handterm-proj/handterm-wiki/scripts/` and have been migrated to `/home/mstouffer/repos/handterm-proj/git-test-retrospector/`.

The module structure has been set up using a `src` layout:

```
git-test-retrospector/
├── pyproject.toml
├── README.md
├── src/
│   └── git_test_retrospector/
│       ├── __init__.py
│       ├── parser.py
│       ├── retrospector.py
│       └── xml_processor.py
└── tests/
    └── test_retrospector.py
```

The `pyproject.toml` file has been configured for `setuptools` with the `src` layout.

The code from the original scripts has been copied to the corresponding module files, and imports have been adjusted.

A basic test file (`tests/test_retrospector.py`) has been created.

The module has been successfully installed in a virtual environment using `uv`.

**Next Steps:**

*   Improve the existing test (currently, it just checks if `get_current_commit_hash` returns a string or None, which isn't very robust).  Consider creating mock git repositories for testing.
*   Add more comprehensive tests for the other functionalities (parsing XML, running tests, etc.).
*   Consider how to best expose the functionality to users (e.g., through a command-line interface, as a library, etc.).
*   Address the error message that occurs during the test, even though the test passes. The error is: "Error getting current commit hash: Command '['git' 'rev-parse' '--short' 'HEAD']' returned non-zero exit status 128." This is happening because the test is being run from a directory that is not a git repository itself (it's inside a git repository).
* Consider adding type hints.