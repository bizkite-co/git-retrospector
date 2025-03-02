import unittest


def main():
    """Runs the tests."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="../../tests", top_level_dir=".")
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if result.errors or result.failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
