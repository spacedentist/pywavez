#!/bin/bash -e

shopt -s globstar

# Format all Python code
black --line-length 79 *.py pywavez/**/*.py

# Run flake8
flake8 \
    --ignore=E121,E123,E126,E226,E24,E704,W503,W504,E203,E501 \
    *.py pywavez/**/*.py
