# Province Legal OS Backend

This is the Python backend for the AI-native legal OS platform. The backend provides REST APIs and WebSocket support for the Next.js frontend, implementing the core agent runtime, document management, and AWS service integrations.

## Architecture

The backend is built using Python with FastAPI and integrates with various AWS services:

- **Agent Runtime**: Bedrock-powered AI agents for legal workflows
- **Document Service**: S3-based versioned document storage
- **Search Service**: OpenSearch Serverless for hybrid retrieval
- **Matter Management**: DynamoDB for metadata and permissions
- **Real-time Features**: WebSocket support for collaborative editing
- **Security**: Cognito integration, KMS encryption, IAM policies

## Project Structure

```
backend/
├── src/ai_legal_os/           # Main application package
│   ├── api/                   # FastAPI routes and endpoints
│   ├── agents/                # Agent runtime and orchestration
│   ├── core/                  # Configuration and utilities
│   ├── integrations/          # AWS service integrations
│   ├── models/                # Data models and schemas
│   ├── services/              # Business logic services
│   └── main.py                # FastAPI application entry point
├── infrastructure/            # AWS CDK infrastructure code
│   ├── stacks/                # CDK stack definitions
│   ├── app.py                 # CDK application entry point
│   └── cdk.json               # CDK configuration
├── tests/                     # Test suite
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Python project configuration
└── Makefile                  # Development commands
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- AWS CLI configured with appropriate credentials
- Node.js and npm (for AWS CDK)

### Development Setup

1. **Clone the repository and navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   make install-dev
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Copy environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the development server:**
   ```bash
   make run
   ```

   The API will be available at http://localhost:8000

5. **View API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Infrastructure Deployment

1. **Bootstrap CDK (first time only):**
   ```bash
   make bootstrap
   ```

2. **Deploy infrastructure:**
   ```bash
   make deploy
   ```

3. **View synthesized CloudFormation templates:**
   ```bash
   make synth
   ```

### Development Commands

```bash
# Install dependencies
make install          # Production dependencies
make install-dev      # Development dependencies

# Code quality
make lint            # Run linting
make format          # Format code
make type-check      # Run type checking

# Testing
make test            # Run tests with coverage

# Development server
make run             # Start development server

# Infrastructure
make bootstrap       # Bootstrap CDK
make deploy          # Deploy infrastructure
make synth           # Synthesize templates
make destroy         # Destroy infrastructure

# Cleanup
make clean           # Remove build artifacts
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `ENVIRONMENT`: Environment name (development, staging, production)
- `AWS_REGION`: AWS region for services
- `COGNITO_USER_POOL_ID`: Cognito User Pool ID for authentication
- `MATTERS_TABLE_NAME`: DynamoDB table name for matters
- `DOCUMENTS_BUCKET_NAME`: S3 bucket name for documents
- `OPENSEARCH_ENDPOINT`: OpenSearch Serverless endpoint
- `BEDROCK_MODEL_ID`: Default Bedrock model for AI agents

## API Documentation

The API follows RESTful conventions and includes:

- **Authentication**: Cognito-based JWT authentication
- **Authorization**: Role-based access control with tenant isolation
- **Validation**: Pydantic models for request/response validation
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Rate Limiting**: Built-in rate limiting and throttling
- **CORS**: Configurable CORS support for frontend integration

### Key Endpoints

- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed service status
- `POST /api/v1/matters/` - Create new matter
- `GET /api/v1/matters/{matter_id}` - Get matter details
- `POST /api/v1/documents/` - Upload document
- `GET /api/v1/search/` - Search documents
- `POST /api/v1/agents/chat` - Chat with AI agents

## Testing

The test suite includes:

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test AWS service integrations
- **API Tests**: Test FastAPI endpoints and middleware
- **Security Tests**: Test authentication and authorization

Run tests with coverage:
```bash
make test
```

## Security

The backend implements enterprise-grade security:

- **Encryption**: KMS encryption for data at rest
- **Authentication**: Cognito integration with JWT tokens
- **Authorization**: Fine-grained permissions with tenant isolation
- **Network Security**: VPC isolation and security groups
- **Audit Logging**: CloudTrail integration for compliance
- **PII Detection**: Automated scanning with Comprehend and Macie

## Monitoring and Observability

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Metrics**: CloudWatch metrics for performance monitoring
- **Tracing**: X-Ray integration for distributed tracing
- **Health Checks**: Comprehensive health monitoring
- **Cost Tracking**: Token usage and AWS service cost monitoring

## Contributing

1. Follow the existing code style and conventions
2. Add tests for new functionality
3. Update documentation as needed
4. Run linting and type checking before committing
5. Use conventional commit messages

## License

This project is proprietary software. All rights reserved.