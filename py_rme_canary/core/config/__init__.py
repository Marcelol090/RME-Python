"""Configuration and project wrapper helpers.

This package provides:
- A JSON project wrapper around `.otbm` files (explicit validation).
- A configuration manager that resolves which definitions files to load.

The goal is to prevent accidental corruption by opening/saving a map using the
wrong engine/definitions.
"""
