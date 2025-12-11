# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Multi-Role Dialogue System (MRC)** - a comprehensive full-stack application for creating configurable, multi-role conversation environments with integrated **RAGFlow Knowledge Base System** and **Document Management** capabilities. The system enables users to orchestrate conversations between multiple virtual roles (teachers, students, experts, officials, etc.) around specific topics using structured dialogue flows with advanced features like loops, conditions, and real-time execution.

## Architecture

### Technology Stack
- **Backend**: Flask 2.3.3 with SQLAlchemy, Flask-RESTful, Flask-Migrate
- **Frontend**: React 18.2.0 with TypeScript, Vite, Tailwind CSS
- **Database**: SQLite with migration support
- **LLM Integration**: OpenAI API (configurable for other providers)
- **Knowledge Base**: RAGFlow integration for retrieval-augmented generation
- **Real-time**: WebSocket and Server-Sent Events support

### High-Level Architecture

The system follows a **service layer pattern** with clear separation of concerns:

#### Backend Service Architecture
```
FlowEngineService (Core Conversation Engine)
├── SessionService (Session Management)
├── SimpleLLMService (LLM Integration with Auto-Detection)
├── KnowledgeBaseService (RAGFlow Integration)
├── MessageService (Message Processing)
├── DocumentService (Document Management)
└── MonitoringService (Performance Tracking)
```

#### Key Architectural Patterns
- **Service Layer Pattern**: Business logic separated into dedicated services
- **Repository Pattern**: Data access through SQLAlchemy models with comprehensive relationships
- **Observer Pattern**: Health monitoring integrated throughout the system
- **Template-Based Flow System**: JSON-based flow templates with versioning
- **Session Isolation**: Sessions use snapshots to preserve template versions

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Database initialization
python run.py init-db                           # Initialize database schema
python run.py create-builtin-roles              # Create system roles
python run.py create-builtin-flows              # Create built-in flow templates

# Start development server (port 5010)
python run.py

# Database utilities
python check_db.py                              # Check database status
python clean_db.py                              # Clean database
python apply_migration.py                       # Apply database migrations

# Knowledge base system setup
python add_knowledge_base_tables.py            # Add knowledge base tables
python add_knowledge_base_config_migration.py  # Add KB configuration fields

# Document management system setup
python add_document_management_tables.py       # Add document management tables

# Code verification
python check_syntax.py                          # Check Python syntax
python verify_fix.py                            # Verify applied fixes
```

### Frontend Development
```bash
# Navigate to frontend directory (note: directory name is "front", not "frontend")
cd front

# Install dependencies
npm install

# Start development server (port 3000, proxies /api to backend:5010)
npm run dev

# Build for production
npm run build                                   # TypeScript compilation + build

# Linting and testing
npm run lint                                    # ESLint
npm run test                                    # Jest tests
npm run test:coverage                          # Test coverage
npm run test:knowledge-base                    # Knowledge base specific tests

# Quick validation
npm run check                                   # Lint + build
```

### Quick Development Workflow
```bash
# Start backend (port 5010)
cd backend && python run.py

# Start frontend (port 3000) - proxies /api to backend:5010
cd front && npm run dev

# Access application at http://localhost:3000
# API available at http://localhost:3000/api/*
# Health check: http://localhost:3000/api/health
```

## Core System Components

### Conversation Flow Engine

**FlowEngineService** is the central execution engine (46KB) that orchestrates multi-role conversations:

1. **Session Creation**: Flow template + role mappings → Session with JSON snapshots
2. **Step Execution**: execute_next_step() → Context Building → LLM Call
3. **Context Construction**: Dynamic context assembly (none, last_message, last_round, all)
4. **Response Processing**: LLM response parsing → Message creation → State updates

**Key Features:**
- Configurable termination conditions (max steps, max rounds, custom logic)
- Nested loops and conditional branching
- Real-time progress tracking with Server-Sent Events
- Comprehensive execution logging and debugging

### LLM Integration Architecture

The system uses a **simplified LLM service** with automatic provider detection:

```python
# Provider Priority:
# 1. Anthropic Claude (if API key available)
# 2. OpenAI (if API key available)
# 3. Claude CLI (if command available)
```

**Key Components:**
- **SimpleLLMService**: Primary interface with auto-detection (`backend/app/services/simple_llm.py`)
- **LLMFileRecordService**: Comprehensive interaction logging
- **ConversationManager**: Context state management
- **LLMLogger**: Specialized request/response logging

**Service Features:**
- Auto-detection of available LLM providers
- Streaming response support for long conversations
- Comprehensive error handling and fallback mechanisms
- Request tracking and performance monitoring
- Support for both simple prompts and complex conversation flows

### Knowledge Base System (RAGFlow Integration)

**RAGFlow Integration Architecture:**
```
KnowledgeBaseService (MRC)
├── RAGFlowService (API Layer)
├── Dataset Sync (Bidirectional)
├── Chat Assistant (Q&A)
└── Connection Management (Health + Retry)
```

**Key Features:**
- Dataset synchronization with RAGFlow instances
- Role-knowledge base associations with priority
- Test conversation validation with reference tracking
- Real-time connection monitoring and statistics

### Document Management System

**Document Lifecycle Services:**
- **DocumentService**: CRUD operations, metadata handling
- **UploadService**: Streaming uploads with progress tracking
- **ChunkService**: Configurable document chunking strategies

**Features:**
- Multi-format upload support (PDF, DOCX, TXT, MD)
- Real-time processing status tracking
- Document chunk visualization and management
- Comprehensive processing logs

## Database Architecture

### Core Models and Relationships
```
FlowTemplate (1:N) → FlowStep (1:N) → Session (1:N) → Message
Session (1:N) → SessionRole (N:1) → Role
Session (1:N) → KnowledgeBase (via RoleKnowledgeBase)
KnowledgeBase (1:N) → Document (1:N) → DocumentChunk
```

### Key Design Decisions
- **Session Isolation**: JSON snapshots preserve template versions at creation time
- **Role Mapping**: Flexible role assignment with mapped/unmapped modes
- **JSON Configuration**: Complex configurations stored as JSON (termination, logic, contexts)
- **Performance Optimization**: Comprehensive indexing for common query patterns

## Frontend Component Architecture

### Main Components
- **MultiRoleDialogSystem.tsx**: Main application interface with role/flow management
- **SessionTheater.tsx**: Real-time conversation visualization and monitoring
- **KnowledgeBaseManagement.tsx**: Knowledge base interface with connection monitoring
- **DocumentUpload/DocumentList/DocumentView**: Complete document management UI
- **StepProgressDisplay.tsx**: Real-time execution progress tracking

### State Management
- **Local Component State**: React hooks for local state management
- **Context Pattern**: LLM Debug Context for real-time debugging
- **Theme System**: Centralized theme configuration (5 color schemes)
- **API Integration**: Centralized API clients with TypeScript interfaces

### Development Environment
- **Vite Dev Server**: Hot reload with API proxy to backend:5010
- **TypeScript**: Strict mode with comprehensive type checking
- **Tailwind CSS**: Utility-first styling with theme system
- **Lucide React**: Consistent iconography

## API Endpoints Structure

### Core Endpoints
- `/api/roles` - Role management (CRUD)
- `/api/flows` - Flow template management with statistics
- `/api/sessions` - Session management and execution control
- `/api/sessions/{id}/messages` - Message management and export
- `/api/health` - Comprehensive health check
- `/api/monitoring/*` - System health and performance metrics

### Knowledge Base Endpoints
- `/api/knowledge-bases` - Knowledge base management and RAGFlow integration
- `/api/knowledge-bases/{id}/documents` - Document management operations
- `/api/documents/{document_id}/chunks` - Document chunk operations

### LLM Monitoring Endpoints
- `/api/sessions/{id}/llm-statistics` - LLM interaction statistics
- `/api/llm-interactions/active` - Currently active LLM interactions
- `/api/llm-interactions/errors` - LLM error logs

## Environment Configuration

### Backend Configuration (.env)
```python
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///conversations.db

# LLM Provider Configuration
LLM_PROVIDER=openai  # openai, anthropic, or claude_cli
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# RAGFlow Configuration (Knowledge Base)
RAGFLOW_API_KEY=your-ragflow-api-key
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
RAGFLOW_TIMEOUT=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=5010
```

### Frontend Environment
- **Vite Proxy**: Automatically proxies `/api` to `http://127.0.0.1:5010`
- **TypeScript**: Strict mode enabled
- **Build**: Production builds to `dist/` directory

## Testing and Quality Assurance

### Frontend Testing
```bash
npm test                                       # Jest tests with React Testing Library
npm run test:watch                            # Jest tests in watch mode
npm run test:coverage                         # Coverage reports
npm run test:knowledge-base                   # Knowledge base specific tests
```

### Validation Commands
```bash
# Backend validation
cd backend
python check_db.py                            # Database integrity
python verify_fix.py                          # Verify applied fixes
python check_syntax.py                        # Check Python syntax

# Frontend validation
cd front
npm run check                                 # Lint + build validation
```

## Development Guidelines

### Backend Development
1. **Service Layer Pattern**: Keep business logic in dedicated services
2. **Database Migrations**: Use Flask-Migrate for schema changes
3. **API Responses**: Consistent JSON format with success/error structure
4. **Error Handling**: Centralized error handlers with comprehensive logging
5. **LLM Integration**: Use SimpleLLMService for all LLM interactions
6. **File Organization**: Services in `backend/app/services/`, models in `backend/app/models/`
7. **Configuration**: Environment-based config with `.env` file support

### Frontend Development
1. **Component Architecture**: Follow composition pattern with reusable parts
2. **TypeScript**: Maintain strict type safety with proper interfaces
3. **API Integration**: Use centralized API clients in `src/api/`
4. **Styling**: Use Tailwind CSS utilities with the theme system
5. **State Management**: Use React hooks for local state, context for global state
6. **File Organization**: Components in `src/components/`, API clients in `src/api/`
7. **Development Server**: Vite dev server with hot reload and API proxy

### Database Development
1. **Migration First**: Always create migrations before model changes
2. **Relationships**: Define comprehensive relationships with proper indexing
3. **JSON Fields**: Use JSON fields for complex configurations
4. **Snapshots**: Use snapshots for version preservation (sessions, flows)

## Known Issues and Limitations

- **Frontend Build**: TypeScript compilation may fail due to syntax errors in some components
- **Development Environment**: Issues don't affect the Vite dev server functionality
- **ESLint Configuration**: Frontend linting requires proper ESLint setup
- **LLM Provider Configuration**: Requires proper API key configuration for each provider
- **Database Path**: SQLite database file location may need adjustment for different environments
- **RAGFlow Integration**: Requires external RAGFlow instance configuration for knowledge base features

## Monitoring and Debugging

### Built-in Monitoring
- **Health Monitoring**: Comprehensive system health checks
- **Performance Metrics**: CPU, memory, request rates, LLM performance
- **LLM Interaction Tracking**: Detailed logging with token usage and timing
- **Knowledge Base Statistics**: Usage patterns and sync status

### Debugging Tools
- **LLM Debug Panel**: Real-time LLM request/response monitoring
- **Session Theater**: Visual conversation execution debugging
- **Step Progress Display**: Real-time execution progress tracking
- **Comprehensive Logging**: File-based logging with structured formats

### Performance Optimization
- **Caching Service**: Intelligent caching for frequently accessed data
- **Rate Limiting**: API rate limiting and request throttling
- **Database Optimization**: Comprehensive indexing and query optimization
- **Connection Pooling**: Efficient database connection management

This architecture provides a solid foundation for a scalable, maintainable multi-role dialogue system with advanced features like knowledge base integration, real-time execution, and comprehensive monitoring capabilities.