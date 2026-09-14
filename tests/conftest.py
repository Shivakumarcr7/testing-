"""
Test-suite-wide setup.

services/config.py raises RuntimeError at import time if SARVAM_API_KEY
isn't set (by design, for the running app). For tests we don't want to
require a real key -- external Sarvam calls are mocked in the tests that
would otherwise make them -- so provide a harmless placeholder value if
the environment doesn't already have one set.

This must run before any test module imports anything under services/,
which pytest guarantees for a conftest.py at the tests/ root.
"""
import os

os.environ.setdefault("SARVAM_API_KEY", "test-dummy-key-for-unit-tests")
