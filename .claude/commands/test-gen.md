Generate a pytest test file for the module at `$ARGUMENTS`.

Follow these steps:
1. Read the source file at `$ARGUMENTS`
2. Analyze all public functions and classes
3. Generate pytest tests covering:
   - Normal operation with typical inputs
   - Edge cases (empty inputs, None values, boundary conditions)
   - Error cases where the function should raise exceptions
4. Write the test file next to the source:
   - If source is `src/auth.py`, write to `tests/test_auth.py`
   - If source is `utils.py`, write to `test_utils.py`
   - Create the target directory if it does not exist
5. Run `pytest <test_file> -v --tb=short` to verify the tests pass
6. Report the results: how many tests passed, failed, or errored

Use descriptive test names like `test_authenticate_returns_true_for_valid_key`.
Do NOT use mocks unless the function has external dependencies.
Import the module under test using its actual import path.
