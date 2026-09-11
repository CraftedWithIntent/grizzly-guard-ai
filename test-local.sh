#!/bin/bash
# Local CI pipeline — run before pushing

set -e

if [ ! -d "/tmp/.venv_grizzly" ]; then
    echo "Setting up venv..."
    /opt/homebrew/opt/python@3.14/bin/python3 -m venv /tmp/.venv_grizzly
    . /tmp/.venv_grizzly/bin/activate
    pip install -q -e ".[dev]" 2>&1 | grep -i error || true
fi

. /tmp/.venv_grizzly/bin/activate

echo "=== RUFF LINTING ==="
ruff check src tests && echo "✅ PASS" || exit 1

echo ""
echo "=== PYRIGHT TYPE CHECKING ==="
pyright src && echo "✅ PASS" || exit 1

echo ""
echo "=== PYTEST ==="
pytest tests -q && echo "✅ PASS" || exit 1

echo ""
echo "=== PYTHON BUILD ==="
python -m build >/dev/null && echo "✅ BUILD SUCCESSFUL" || exit 1

echo ""
echo "🎉 ALL CHECKS PASSED - Ready to push"
