# Family Photo Hub

A private, family-only AI-powered photo hub that provides intelligent organization, conversational search, and secure multi-device access to your family's photo and video collection.

## 🎯 Project Goal

Build a cost-effective (< $100/year), private photo management system that supports:

- **Multi-device upload** (mobile browser, desktop browser)
- **Cost-efficient storage** (Hot previews + Cool originals)
- **Intelligent organization** (AI tagging, face clustering, timeline grouping)
- **AI conversational search** ("Find last year's Christmas photos", "Show all beach pictures")
- **Family roles & permissions** (admin/member/viewer)
- **Secure access** via JWT + private Blob Storage + SAS tokens
- **Simple, maintainable, scalable codebase** suitable for long-term use

> **Note**: This system is single-tenant, serving only one family.

## ✨ Features

- 📸 **Photo & Video Upload**: Support for JPG, JPEG, PNG, WebP, MP4, MOV
- 🤖 **AI-Powered Organization**: Automatic tagging, face clustering, and timeline grouping
- 🔍 **Conversational Search**: Natural language queries to find your memories
- 👥 **Role-Based Access**: Admin, member, and viewer roles with granular permissions
- 🔒 **Secure Storage**: Private Azure Blob Storage with short-lived SAS tokens
- 💰 **Cost-Optimized**: Tiered storage strategy to minimize costs
- 📱 **Responsive Design**: Works seamlessly on mobile and desktop browsers

## 🏗️ Architecture

### System Components

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │──────│  Backend API │──────│  PostgreSQL │
│  (Next.js)  │      │   (FastAPI)  │      │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            │
                     ┌──────┴──────┐
                     │             │
              ┌──────▼──────┐ ┌───▼────────┐
              │ AI Worker   │ │ Azure Blob │
              │ (Celery/    │ │  Storage   │
              │ APScheduler)│ │            │
              └─────────────┘ └────────────┘
```

### Storage Strategy

- **Original Media** → Azure Blob Cool tier (cost-efficient long-term storage)
- **Preview Images & Low-bitrate Video** → Azure Blob Hot tier (fast access)
- **AI Processing** → Analyzes preview files only (reduces costs)

### Security Flow

1. User logs in → Receives JWT access token
2. Frontend calls API with JWT
3. API validates permissions
4. API generates short-lived SAS token (5-15 min, read-only)
5. Frontend fetches media from Blob using SAS token

### AI Pipeline

1. Upload triggers an AI job
2. Worker processes jobs asynchronously (batches)
3. Database stores embeddings, tags, and clusters
4. Conversational search uses embeddings + metadata

## 🛠️ Technology Stack

### Backend
- **Python** 3.10+
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** 2.x - ORM
- **Alembic** - Database migrations
- **Pydantic** v2 - Data validation
- **Celery** (optional) or **APScheduler** - Task queue
- **httpx** - Async HTTP client
- **OpenAI API** - Vision + Embeddings

### Frontend
- **Next.js** 14+ - React framework
- **React** 18
- **TypeScript** 5.x
- **TailwindCSS** - Styling
- **React Query** (@tanstack/react-query) - Data fetching
- **Axios** - HTTP client

### Infrastructure
- **PostgreSQL** 14+ - Database (Azure Flexible Server or self-hosted)
- **Azure Blob Storage** - Object storage
- **Azure Container Apps** - Deployment platform
- **Azure Container Registry** - Container registry
- **GitHub Actions** - CI/CD

## 📁 Directory Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── media.py
│   │   │       ├── albums.py
│   │   │       ├── search.py
│   │   │       └── ai.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       ├── user.py
│   │   │       ├── media.py
│   │   │       ├── album.py
│   │   │       ├── tag.py
│   │   │       └── face.py
│   │   │   └── migrations/
│   │   ├── services/
│   │   │   ├── media_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── album_service.py
│   │   │   └── search_service.py
│   │   ├── workers/
│   │   │   └── ai_worker.py
│   │   ├── utils/
│   │   │   ├── azure_blob.py
│   │   │   └── image_tools.py
│   │   └── main.py
│   ├── tests/
│   └── pyproject.toml
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── login/
    │   │   ├── upload/
    │   │   ├── albums/
    │   │   ├── media/[id]/
    │   │   └── search/
    │   ├── components/
    │   ├── lib/
    │   └── hooks/
    ├── public/
    └── next.config.js
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm/yarn
- PostgreSQL 14+
- Azure account with Blob Storage configured
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Configure environment variables:**
   Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/family_photo
   JWT_SECRET=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key
   AZURE_BLOB_CONNECTION_STRING=your-azure-connection-string
   AZURE_BLOB_CONTAINER_ORIGINAL=media-original
   AZURE_BLOB_CONTAINER_PREVIEW=media-preview
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Configure environment variables:**
   Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

The frontend will be available at `http://localhost:3000` and the backend API at `http://localhost:8000`.

## 🔒 Security

### Authentication
- JWT access tokens (15-30 min expiry)
- Refresh tokens stored in HTTP-only cookies
- Password hashing using Argon2 or bcrypt

### Blob Access
- Containers are always private
- Short-lived SAS tokens (5-15 min validity)
- Read-only permissions for media access

### Input Validation
- All API requests validated with Pydantic v2 schemas
- Upload size limits enforced server-side
- Allowed MIME types: `jpg/jpeg/png/webp/mp4/mov`

### Secrets Management
- Secrets stored in Azure Key Vault or GitHub Secrets
- Never commit `.env` files
- CORS whitelist for explicit frontend URLs only

## 📝 API Error Handling

All API errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-friendly error message",
    "details": { /* optional additional details */ }
  }
}
```

### Error Categories
- `AUTH_ERROR` - Authentication/authorization failures
- `VALIDATION_ERROR` - Input validation errors
- `NOT_FOUND` - Resource not found
- `PERMISSION_DENIED` - Insufficient permissions
- `BLOB_ERROR` - Azure Blob Storage errors
- `AI_ERROR` - AI service errors
- `INTERNAL_SERVER_ERROR` - Unexpected server errors

## 🧪 Testing

### Test Types
- **Unit tests** - Services and utilities
- **Integration tests** - API endpoints using TestClient
- **AI pipeline tests** - Mocked external API calls
- **Frontend component tests** - Optional
- **End-to-end tests** - Playwright (optional in v2)

### Requirements
- Coverage target: 60% minimum
- All tests run in CI (GitHub Actions)
- No real OpenAI calls in CI → must be mocked
- No real Blob uploads in CI → use local Azurite or mock layer

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

## 🚢 Deployment

### Deployment Target: Azure Container Apps

### Process

1. **Build Docker images** for backend + frontend
2. **Push to Azure Container Registry**
3. **Deploy backend** → expose API with Ingress
4. **Deploy frontend**
5. **Configure environment variables**
6. **Assign custom domain** (optional)
7. **Set minReplicas = 0** (cost control)

### Required Environment Variables

- `DATABASE_URL`
- `JWT_SECRET`
- `OPENAI_API_KEY`
- `AZURE_BLOB_CONNECTION_STRING`
- `AZURE_BLOB_CONTAINER_ORIGINAL`
- `AZURE_BLOB_CONTAINER_PREVIEW`

### Zero-Downtime Deployment

- Use ACA revisions
- Gradual traffic rollout
- Auto-rollback if health check fails

## 📋 Code Style

### Backend (Python)
- Follow PEP8
- Use **Black** for formatting
- Use **isort** for imports
- Max line length: 100
- Type hints mandatory in all functions
- Prefer dependency injection via `fastapi.Depends`

### Frontend (TypeScript/JavaScript)
- **Prettier** + **ESLint** (Next.js default recommended)
- Strong typing mandatory
- No `any` except when explicitly justified
- No inline business logic inside components

## 📚 Naming Conventions

### Python / Backend
- Files: `snake_case.py`
- Variables: `snake_case`
- Classes: `PascalCase`
- Functions: `snake_case`
- API route prefixes: `/api/v1/...`
- DB tables: singular (`media`, `user`, `album`)
- Foreign key names: `xxx_id`

### TypeScript / Frontend
- Components: `PascalCase.tsx`
- Hooks: `useSomething.ts`
- Utility files: `camelCase.ts`
- API clients: `clientName.ts`

## 📦 Dependencies

### Backend (pyproject.toml)
```
fastapi == 0.115.*
uvicorn == 0.32.*
sqlalchemy == 2.0.*
alembic == 1.14.*
pydantic == 2.8.*
httpx == 0.27.*
azure-storage-blob == 12.23.*
pillow == 10.*
opencv-python == 4.10.*
openai == latest stable
```

### Frontend (package.json)
```
next: 14.x
react: 18.x
typescript: 5.x
tailwindcss: 3.x
@tanstack/react-query: 5.x
axios: 1.x
```

## 🤝 Contributing

This is a private family project. If you're contributing:

1. Follow the code style guidelines
2. Write tests for new features
3. Ensure all tests pass
4. Update documentation as needed

## 📄 License

Private project - All rights reserved

## 🆘 Support

For issues or questions, please refer to the project documentation or contact the project maintainer.

---

**Built with ❤️ for family memories**

