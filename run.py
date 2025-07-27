#!/usr/bin/env python3
"""
EBANX PTP Tester – Run Entrypoint
================================
A thin wrapper that simply imports the existing Qt GUI implementation
from `qt_gui` and executes its `main()` function. This allows the
application to be started with a shorter and clearer command:

    python3 run.py

Keeping the full implementation in `qt_gui.py` avoids code duplication
and ensures backwards compatibility (other modules may still
`import qt_gui`).
"""

from qt_gui import main

if __name__ == "__main__":
    main() 