#!/usr/bin/env python
"""
Wrapper manage.py at repository root so running python manage.py
delegates to the inner Django project's manage.py.

This keeps your development workflow simple: you can run the server
from the workspace root instead of changing directories.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INNER_DIR = os.path.join(HERE, 'personalized_medicine_assistant')
INNER = os.path.join(INNER_DIR, 'manage.py')
VENV_PYTHON = os.path.join(INNER_DIR, '.venv', 'Scripts', 'python.exe')

if not os.path.exists(INNER):
    sys.stderr.write(f"Error: expected inner manage.py at '{INNER}'\n")
    sys.exit(1)

# Use virtual environment Python if it exists, otherwise use current Python
python_executable = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

# Change to inner directory so Django can find settings
os.chdir(INNER_DIR)

# Replace the current process with the venv Python running the inner manage.py
os.execv(python_executable, [python_executable, INNER] + sys.argv[1:])
