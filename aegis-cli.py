#!/usr/bin/env python3
"""
Aegis CLI Entry Point

Run with: python aegis-cli.py [command]
Or make executable: chmod +x aegis-cli.py && ./aegis-cli.py [command]
"""

import sys
import os

# Add aegis to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aegis.cli.cli import main

if __name__ == '__main__':
    main()
