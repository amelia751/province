# Province - AI-Powered Tax Filing Assistant

**Province** is an intelligent tax filing system that uses AWS Bedrock, Claude 3.5 Sonnet, and advanced document processing to automate tax return preparation through conversational AI.

## 🎯 Features

- **Conversational Tax Filing**: Chat with an AI agent to complete your tax return
- **Intelligent Document Processing**: Automatic extraction from W-2, 1099, and other tax documents using AWS Bedrock Data Automation
- **Real-time Form Filling**: Watch your Form 1040 fill out automatically as you provide information
- **Smart Field Mapping**: AI-powered mapping between semantic field names and PDF form fields
- **Version History**: Track every change to your tax forms with automatic versioning
- **PII-Safe Storage**: All user data stored using secure Clerk user IDs
- **Live Updates**: Forms auto-refresh as the agent fills them out

## 📁 Project Structure

```
province/
├── backend/          # FastAPI backend with Bedrock integration
├── frontend/         # Next.js 15 frontend with Clerk authentication
├── tax-rules/        # Tax calculation rules engine
└── TEST_SCRIPT.md    # Comprehensive testing guide
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (for backend and tax-rules)
- **Node.js 18+** (for frontend)
- **AWS Account** with:
  - Bedrock access (Claude 3.5 Sonnet model)
  - Bedrock Data Automation project
  - S3 buckets for documents and templates
  - DynamoDB tables for tax data
- **Clerk Account** (for authentication)
- **Supabase Account** (optional, for additional storage)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your credentials:
# - AWS credentials (IAM user with Bedrock access)
# - Bedrock model ID and region
# - S3 bucket names
# - DynamoDB table names
# - Bedrock Data Automation ARNs

# Run the server
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uvicorn province.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your credentials:
# - Clerk publishable key and secret
# - Supabase URL and key
# - Backend API URL (default: http://localhost:8000)

# Run the development server
npm run dev
```

### 3. Tax Rules Setup (Optional)

```bash
cd tax-rules

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your Gemini API key

# The tax rules engine is automatically used by the backend
```

## 🔧 Configuration

### AWS Services Setup

#### 1. Bedrock Configuration

- Enable Bedrock in `us-east-1` region
- Request access to Claude 3.5 Sonnet model
- Note your model ID: `us.anthropic.claude-3-5-sonnet-20240620-v1:0`

#### 2. Bedrock Data Automation

- Create a Data Automation project in AWS Console
- Note the project ARN and profile ARN
- Configure output bucket for processed documents

#### 3. S3 Buckets

Create two S3 buckets:
- **Documents Bucket**: `province-documents-<account-id>-us-east-1`
- **Templates Bucket**: `province-templates-<account-id>-us-east-1`

Upload Form 1040 template to: `s3://province-templates-<account-id>-us-east-1/tax_forms/2024/f1040.pdf`

#### 4. DynamoDB Tables

Create tables with the following names (all in `us-east-1`):
- `province-tax-engagements` - Stores tax filing sessions
- `province-tax-documents` - Document metadata
- `province-form-mappings` - PDF field mappings
- `province-document-versions` - Version history
- Additional tables as needed (see `.env.example`)

#### 5. IAM Permissions

Your IAM user needs:
- Bedrock full access
- S3 read/write access to your buckets
- DynamoDB read/write access to your tables
- Bedrock Data Automation invoke permissions

### Clerk Configuration

1. Create a Clerk application at [clerk.com](https://clerk.com)
2. Get your publishable key and secret key
3. Configure redirect URLs to point to your frontend
4. Enable organizations if needed

### LiveKit Configuration (Optional)

For real-time voice features:
1. Create a LiveKit cloud account
2. Get your LiveKit URL, API key, and secret
3. Add to both backend and frontend `.env.local`

## 📚 API Documentation

Once the backend is running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/

### Key Endpoints

- `POST /api/v1/tax-service/start` - Start a new tax conversation
- `POST /api/v1/tax-service/continue` - Continue conversation
- `GET /api/v1/forms/1040/{engagement_id}/versions` - Get form versions
- `GET /api/v1/forms/{form_type}/template` - Get blank form template
- `DELETE /api/v1/forms/delete-all-filled` - Reset forms for testing

## 🧪 Testing

See [TEST_SCRIPT.md](./TEST_SCRIPT.md) for comprehensive testing instructions.

**Quick Test:**
1. Start backend on port 8000
2. Start frontend on port 3000
3. Upload a W-2 document
4. Follow the agent's conversational prompts
5. Watch Form 1040 fill out automatically

## 📦 Deployment

### Backend Deployment (AWS Lambda)

```bash
cd backend

# Build deployment package
pip install -t package -r requirements.txt
cd package
zip -r ../deployment-package.zip .
cd ..
zip deployment-package.zip -r src/

# Upload to Lambda (or use AWS CDK/SAM)
```

### Frontend Deployment (Vercel)

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
```

## 🔒 Security

- All user data is stored using Clerk user IDs (not names)
- AWS credentials should never be committed to git
- Use IAM roles with least privilege
- All API calls are authenticated via Clerk
- S3 buckets use pre-signed URLs with 1-hour expiration

## 🐛 Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'province'`
**Fix**: `export PYTHONPATH=$PYTHONPATH:$(pwd)/src`

**Issue**: `AccessDeniedException` from Bedrock
**Fix**: Check IAM permissions and Bedrock model access

**Issue**: W-2 processing fails
**Fix**: Verify Bedrock Data Automation role has S3 permissions

### Frontend Issues

**Issue**: Forms not loading
**Fix**: Check Debug Info tab for USER_ID and ENGAGEMENT_ID

**Issue**: PDF viewer shows 404
**Fix**: Verify backend URL in `.env.local` and check CORS settings

**Issue**: Auto-refresh not working
**Fix**: Check browser console for errors, verify WebSocket connection

## 📖 Architecture

### Backend Stack
- **Framework**: FastAPI + Uvicorn
- **AI**: AWS Bedrock (Claude 3.5 Sonnet)
- **Document Processing**: Bedrock Data Automation
- **PDF Manipulation**: PyMuPDF (fitz)
- **Storage**: S3 + DynamoDB
- **Agent Framework**: Custom conversational agent with tools

### Frontend Stack
- **Framework**: Next.js 15 (App Router)
- **Authentication**: Clerk
- **UI**: Tailwind CSS + shadcn/ui
- **PDF Viewing**: PDF.js
- **State**: React hooks + context
- **Real-time**: Polling (5-second intervals)

### Tax Rules Engine
- **Framework**: Python
- **AI**: Google Gemini (for rule interpretation)
- **Rules**: IRS Publication 17, Form 1040 instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly using `TEST_SCRIPT.md`
5. Submit a pull request

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- AWS Bedrock team for Claude 3.5 Sonnet
- Clerk for authentication
- shadcn for UI components
- IRS for tax form specifications

## 📧 Support

For issues, questions, or feature requests, please create an issue in the GitHub repository.

---

**Built with ❤️ for the AWS Hackathon**

