"""AWS Lambda handler for FastAPI application."""

from mangum import Mangum

from ai_legal_os.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")