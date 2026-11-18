#!/usr/bin/env python3
"""Allow running as python -m constitution_linter."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
