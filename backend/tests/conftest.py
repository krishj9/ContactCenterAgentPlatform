"""Pytest configuration and environment defaults."""

import os

# Set CC_APP_PROFILE="test" before any app module imports or settings initialization
os.environ["CC_APP_PROFILE"] = "test"
