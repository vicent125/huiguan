# Submission Verification Record

Environment: Python 3.11, Flask test client, temporary writable SQLite database.

Command:

```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

Result: 22 tests passed (OK).

The tests use a temporary database and do not modify the demonstration database included in the submission package.
