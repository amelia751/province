"""AWS Lambda handler for FastAPI application."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mangum import Mangum
from province.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")

