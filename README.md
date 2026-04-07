# DocuMate AI – Living Documentation Generator

## Project Structure

```
documate-ai/
├── backend/                 # Python FastAPI backend
│   ├── app/                 # Main application & API routes
│   ├── scanners/            # Repository scanning & file discovery
│   ├── parsers/             # Language-specific code parsers (tree-sitter)
│   ├── generators/          # Documentation generation engine
│   ├── search/              # Vector search & semantic indexing
│   ├── redaction/           # Secret detection & redaction
│   └── models/              # Database models & schemas
├── frontend/                # React + TypeScript UI
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Application pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API client services
│   │   └── styles/          # CSS/styling
│   └── public/              # Static assets
├── shared/                  # Shared types & schemas
│   ├── types/               # TypeScript type definitions
│   └── schemas/             # JSON schemas for validation
└── docs/                    # Project documentation
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (metadata), Weaviate/Pinecone (vector search)
- **Static Analysis**: tree-sitter for AST parsing
- **AI/ML**: 
  - OpenAI/Claude for summarization
  - sentence-transformers for embeddings
  - spaCy for NER-based redaction
- **Task Queue**: Celery + Redis for async scanning
- **Storage**: S3-compatible for generated assets

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand
- **Search**: Algolia InstantSearch or custom vector search UI

### Infrastructure
- **Containerization**: Docker + docker-compose
- **CI/CD**: GitHub Actions
- **Deployment**: Kubernetes-ready, supports self-hosted mode

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & docker-compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Start all services
docker-compose up -d
```

## Core Features (MVP)

1. **Automated Scanning**: Schedule or trigger scans on git push/PR
2. **Multi-Language Support**: Python, JavaScript/TypeScript, Go, Java
3. **Config Parsing**: .env, docker-compose.yml, Kubernetes YAML, Terraform
4. **Example Extraction**: Real usage patterns from codebase
5. **Secret Redaction**: Automatic detection and masking of sensitive data
6. **Semantic Search**: Natural language queries with vector embeddings
7. **Wiki UI**: Clean, searchable documentation interface

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Scanner    │────▶│   Parser    │
│   GitLab    │     │   (Agent)    │     │  (AST/TS)   │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Wiki UI    │◀────│   Search     │◀────│  Generator  │
│  (React)    │     │  (Vector DB) │     │  (Markdown) │
└─────────────┘     └──────────────┘     └─────────────┘
```

## License

MIT License - See LICENSE file for details
