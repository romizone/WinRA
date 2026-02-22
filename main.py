#!/usr/bin/env python3
"""WinRA - Archive Manager for macOS. Extract, compress, and convert ZIP/RAR files."""

import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(__file__))

from app.gui import WinRAApp


def main():
    app = WinRAApp()
    app.mainloop()


if __name__ == "__main__":
    main()
