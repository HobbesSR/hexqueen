#!/usr/bin/env python
"""
Simple script to run the HexQueen application.
This script adds the project root to the Python path,
allowing imports to work correctly.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main function
from src.main import main

if __name__ == "__main__":
    main()