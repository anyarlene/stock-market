#!/bin/bash

echo "Checking Python environment..."
if python -c "import sys; assert sys.prefix != sys.base_prefix, 'Not in a virtual environment'"; then
    echo "✓ Virtual environment is active"
else
    echo "✗ Virtual environment is not active"
    exit 1
fi

echo "Checking required packages..."
pip freeze | grep -iE "pandas|yfinance|sqlalchemy|flask|pre-commit"

echo "Checking pre-commit installation..."
if pre-commit --version; then
    echo "✓ pre-commit is installed"
else
    echo "✗ pre-commit is not installed"
    exit 1
fi

echo "Checking directory structure..."
required_dirs=("analytics/database" "analytics/etl" "analytics/models" "analytics/utils" "website" "data" "tests")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir exists"
    else
        echo "✗ $dir is missing"
        exit 1
    fi
done

echo "Checking configuration files..."
required_files=(".env" ".pre-commit-config.yaml" "pyproject.toml" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing"
        exit 1
    fi
done

echo "All checks completed successfully!"