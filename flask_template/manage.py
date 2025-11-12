#!/usr/bin/env python
"""
Wrapper manage.py at repository root so running `python .\manage.py ...`
delegates to the inner Django project's manage.py.

This keeps your development workflow simple: you can run the server
from the workspace root instead of changing directories.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INNER = os.path.join(HERE, 'personalized_medicine_assistant', 'manage.py')


if not os.path.exists(INNER):
    sys.stderr.write(f"Error: expected inner manage.py at '{INNER}'\n")
    sys.exit(1)

# Replace the current process with a new Python process that runs the inner manage.py
import shlex
os.execv(sys.executable, [sys.executable, INNER] + sys.argv[1:])
