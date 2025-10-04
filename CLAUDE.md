# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Province is an AI-native legal operating system with a Next.js frontend and Python FastAPI backend. The project includes:

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, Clerk authentication, and Supabase integration
- **Backend**: FastAPI with AWS Bedrock agents, DynamoDB, S3, and AWS CDK infrastructure
- **AI Features**: Legal document drafting, template generation, citation validation, deadline management

## Commands

### Frontend (Next.js)
```bash
cd frontend
npm run dev          # Start development server with Turbopack
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend (Python)
```bash
cd backend
make install-dev     # Install development dependencies
make test           # Run pytest with coverage
make lint           # Run flake8, black, and isort
make format         # Format code with black and isort
make type-check     # Run mypy type checking
make run            # Start FastAPI development server (port 8000)
make deploy         # Deploy AWS infrastructure with CDK
make clean          # Clean build artifacts and venv
```

### Testing
```bash
# Backend tests
cd backend
make test                    # All tests with coverage
pytest tests/test_*.py -v    # Specific test patterns
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m aws               # AWS-dependent tests

# Frontend (no specific test setup configured)
cd frontend
# Tests would use standard Next.js/React testing patterns
```

## Architecture

### Frontend Structure
- **`src/app/`**: Next.js App Router with nested layouts
  - **`app/`**: Main application pages (protected routes)
  - **`onboarding/`**: User onboarding flow
  - **`api/`**: API routes for data processing and lead management
- **`src/components/`**: Reusable React components
  - **`ui/`**: shadcn/ui component library
  - **`interface/`**: Main app layout and navigation
  - **`start-screen/`**: Landing/welcome interface
  - **`explorer-panel/`**: File/document explorer
  - **`dashboard/`**: Analytics and stats components
- **Authentication**: Clerk with organization support
- **Database**: Supabase (PostgreSQL) with migrations in `supabase/migrations/`
- **Styling**: Tailwind CSS with custom components

### Backend Structure
- **`src/province/`**: Main Python package
  - **`agents/`**: AWS Bedrock agent integration and AI workflows
    - **`drafting/`**: Document drafting with citation validation
    - **`tools/`**: Bedrock agent tools (deadline management, contract generation)
  - **`api/`**: FastAPI routes organized by feature (v1 API structure)
  - **`models/`**: Pydantic data models for documents, matters, templates
  - **`repositories/`**: Data access layer for DynamoDB operations
  - **`services/`**: Business logic (AI template generation, document processing)
  - **`core/`**: Configuration, logging, exceptions
- **Infrastructure**: AWS CDK stacks in `infrastructure/` directory
- **Database**: DynamoDB with GSI indexes for efficient querying
- **Storage**: S3 buckets for document and template storage

### Key Integrations
- **AWS Bedrock**: Claude models for legal document generation
- **AWS DynamoDB**: NoSQL database for matters, documents, templates
- **AWS S3**: Object storage for files and generated content
- **Clerk**: Authentication and organization management
- **Supabase**: PostgreSQL database for frontend data

## Environment Setup

### Frontend Environment Variables
Create `frontend/.env.local`:
```bash
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_key
CLERK_SECRET_KEY=your_secret
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/app
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/app
NEXT_PUBLIC_CLERK_AFTER_CREATE_ORGANIZATION_URL=/app
NEXT_PUBLIC_CLERK_AFTER_LEAVE_ORGANIZATION_URL=/app

# Database
DATABASE_URL=your_supabase_url
```

### Backend AWS Configuration
Requires AWS credentials with permissions for:
- DynamoDB (tables: `province-templates`, `province-matters`, `province-documents`)
- S3 (buckets for documents and templates)
- Bedrock (Claude models)
- CloudFormation/CDK (for infrastructure deployment)

Refer to `AWS_SETUP_GUIDE.md` for detailed IAM permission setup.

## Development Workflow

1. **Frontend Development**: Use `npm run dev` in frontend directory
2. **Backend Development**: Use `make run` in backend directory  
3. **Testing**: Run `make test` for backend, ensure 80% coverage requirement
4. **Code Quality**: Use `make lint` and `make format` before commits
5. **Infrastructure**: Deploy with `make deploy` after AWS setup
6. **Type Checking**: Run `make type-check` for Python type validation

## Important Notes

- Frontend uses TypeScript with strict mode enabled
- Backend requires Python 3.11+ with type hints
- AWS resources are region-specific (us-east-2)
- Clerk organization features require specific redirect URL configuration
- DynamoDB tables use composite keys and GSI for efficient querying
- All legal AI features require proper AWS Bedrock access