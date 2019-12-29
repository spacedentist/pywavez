#!/bin/bash -e

shopt -s globstar

# Format all Python code
black --line-length 79 *.py pywavez/**/*.py

# Run flake8
flake8 *.py pywavez/**/*.py
