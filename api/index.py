"""
Vercel Serverless Function entry point for Ocean Freight Rate & Shipment Tracker.
Exposes the FastAPI ASGI app.
"""

import sys
import os

# Add root directory to python path for module imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the FastAPI application instance
from app import app
