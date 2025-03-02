
```
retros/
├── <remote_name_1>/       # Directory for a remote repo
│   ├── config.toml        # Configuration file for this remote
│   └── test-output/       # Directory for test output
│       └── <commit_hash>/  # Directory for a specific commit
│           ├── playwright.xml # Playwright JUnit-schema test output
│           ├── vitest.xml # Vitest JUnit-schema test output
│           └── tool-summary/   # Summary of test results
│               ├── playwright.csv   # CSV file with Playwright test results
│               └── vitest.csv      # CSV file with Vitest test results (if applicable)
│           └── playwright.xml # Raw Playwright XML output
│           └── ...            # Other output files (screenshots, videos, traces)
├── <remote_name_2>/       # Another remote repository
│   ├── config.toml
│   └── test-output/
│       └── ...
└── ...
```
