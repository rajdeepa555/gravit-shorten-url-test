"""
Pytest configuration and shared fixtures.
"""
import os
import sys

# Ensure project root is in path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
