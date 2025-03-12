This issue is to add unit tests to `tests/test_parser.py` to cover the XML parsing and CSV generation logic in `src/git_retrospector/parser.py`. The following test cases should be included:

1.  **Test with Valid Playwright XML:**
    *   Create a temporary directory structure mimicking the output of a test run, including a `playwright.xml` file with valid JUnit XML content.
    *   Call `process_retro` on a `Retro` object configured to use this temporary directory.
    *   Assert that a `playwright.csv` file is created in the correct location (within the `tool-summary` subdirectory of the commit directory).
    *   Assert that the `playwright.csv` file contains the expected headers and data, based on the content of the `playwright.xml` file.

2.  **Test with Valid Vitest XML:**
    *   Similar to the Playwright test, create a `vitest.xml` file with valid JUnit XML content.
    *   Call `process_retro`.
    *   Assert that a `vitest.csv` file is created with the expected headers and data.

3.  **Test with Missing XML Files:**
    *   Create a temporary directory structure *without* the `playwright.xml` and `vitest.xml` files.
    *   Call `process_retro`.
    *   Assert that no CSV files are created (and that no errors are raised).

4.  **Test with Invalid XML:**
    *   Create a `playwright.xml` file with *invalid* XML content (e.g., mismatched tags).
    *   Call `process_retro`.
    *   Assert that no CSV file is created (and that no errors are raised, beyond the existing logging of a `ParseError`).
