# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Multi-Role Dialogue System (MRC)** - a comprehensive full-stack application for creating configurable, multi-role conversation environments with integrated **RAGFlow Knowledge Base System** and **Document Management** capabilities. The system enables users to orchestrate conversations between multiple virtual roles (teachers, students, experts, officials, etc.) around specific topics using structured dialogue flows with advanced features like loops, conditions, and real-time execution. The knowledge base system provides powerful retrieval-augmented generation capabilities through RAGFlow integration, including document upload, processing, and chunking functionality. The project was migrated from `D:\ProjectPackage\MultiRoleChat\backend` on 2025-12-05.

## Architecture

### Technology Stack
- **Backend**: Flask 2.3.3 with SQLAlchemy, Flask-RESTful, Flask-Migrate
- **Frontend**: React 18.2.0 with TypeScript, Vite, Tailwind CSS
- **Database**: SQLite with migration support
- **LLM Integration**: OpenAI API (configurable for other providers)
- **Knowledge Base**: RAGFlow integration for retrieval-augmented generation
- **Real-time**: WebSocket and Server-Sent Events support

### Project Structure
```
MRC/
├── backend/           # Flask REST API server (port 5010)
│   ├── app/
│   │   ├── api/      # API endpoints (roles, flows, sessions, messages, llm, knowledge_bases)
│   │   ├── models/   # SQLAlchemy models (Role, FlowTemplate, Session, Message, KnowledgeBase)
│   │   ├── services/ # Business logic services (knowledge_base_service.py, ragflow_service.py)
│   │   └── utils/    # Utilities (monitoring, error handling)
│   ├── run.py        # Application entry point with CLI commands
│   ├── add_knowledge_base_tables.py  # Knowledge base database migration
│   └── conversations.db  # SQLite database
├── doc/              # Documentation (ragflow.md - RAGFlow API reference)
└── front/            # React TypeScript frontend (port 3000)
    ├── src/
    │   ├── api/      # API client modules (knowledgeApi.ts)
    │   ├── components/ # React components (KnowledgeBaseManagement.tsx, KnowledgeBaseList.tsx)
    │   ├── hooks/    # Custom React hooks
    │   ├── types/    # TypeScript types (knowledge.ts)
    │   └── utils/    # Frontend utilities
    └── vite.config.ts # Development proxy to backend:5010
```

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Environment validation and quick start (recommended)
python quick_start.py          # Comprehensive environment check + validation

# Install dependencies
pip install -r requirements.txt

# Initialize database
python run.py init-db

# Create built-in roles and flows (中文注释的命令)
python run.py create_builtin-roles
python run.py create-builtin-flows

# Run development server (port 5010)
python run.py

# Database utilities
python check_db.py              # Check database status
python clean_db.py              # Clean database
python clear_templates.py       # Clear flow templates
python reset_templates.py       # Reset to built-in templates
python check_database.py        # Alternative database status check
python init_database.py         # Initialize database with schema
python apply_migration.py       # Apply database migrations
python update_topic_length.py   # Update topic field length migration
python cleanup_llm_records.py   # Clean LLM interaction records

# Knowledge base system setup
python add_knowledge_base_tables.py  # Add knowledge base tables to database
python add_knowledge_base_config_migration.py  # Add knowledge base configuration fields

# Document management system setup (new)
python add_document_management_tables.py  # Add document management tables to database

# Code verification and utilities
python check_syntax.py          # Check Python syntax
python verify_fix.py            # Verify applied fixes
python char_count_monitor.py   # Monitor character usage
```

### Frontend Development
```bash
# Navigate to frontend directory (note: directory name is "front", not "frontend")
cd front

# Install dependencies
npm install

# Run development server (port 3000, proxies /api to backend:5010)
npm run dev

# Build for production (runs TypeScript compiler first, will fail due to syntax errors)
npm run build

# Preview production build
npm run preview

# Lint code (requires ESLint configuration)
npm run lint

# Quick check (lint + build)
npm run check

# Run tests
npm test                                    # Run Jest tests
npm run test:watch                         # Run tests in watch mode
npm run test:coverage                      # Run test coverage
npm run test:knowledge-base                # Run specific knowledge base tests
```

### Quick Development Workflow
```bash
# Terminal 1: Start backend (with environment validation)
cd backend && python quick_start.py
# Or if environment already validated: python run.py

# Terminal 2: Start frontend (auto-reloads)
cd front && npm run quick-start
# Or if environment already validated: npm run dev

# Access application at http://localhost:3000
# API available at http://localhost:3000/api/* (proxied to backend:5010)
# Health check: http://localhost:3000/api/health

# Knowledge Base Setup (one-time)
cd backend && python add_knowledge_base_tables.py
# Configure RAGFlow in .env file (RAGFLOW_API_KEY, RAGFLOW_BASE_URL)
# Access Knowledge Base tab in the UI to sync datasets

# Document Management Setup (one-time, new)
cd backend && python add_document_management_tables.py
# Document management UI will be available in Knowledge Base details page
# Supports drag-and-drop upload, progress tracking, and chunk visualization
```

### Quick Start Scripts (Recommended for First-time Setup)

#### Backend Quick Start
The `backend/quick_start.py` script provides comprehensive environment validation:
- Checks Python version (requires 3.8+)
- Validates all dependencies from requirements.txt
- Verifies database file and schema
- Checks for required .env configuration
- Provides step-by-step guidance for setup issues

#### Frontend Quick Start
The `front/quick-start.js` script provides automated environment validation:
- Checks Node.js version (requires 16+)
- Validates project structure and required files (package.json, vite.config.ts, tsconfig.json, src files)
- Verifies dependencies (auto-installs if missing)
- Validates backend proxy configuration
- Starts development server with comprehensive error handling and colored output

#### Quick Start Commands
```bash
# Backend quick start (environment check + validation + setup guidance)
cd backend && python quick_start.py

# Frontend quick start (environment check + auto-install deps + start dev server)
cd front && npm run quick-start
# Or use the Node.js script directly
cd front && node quick-start.js
```

## Core System Components

### Backend Models
- **Role** - Defines virtual participants with style, constraints, and focus points (unique names, unified prompt field)
- **FlowTemplate** - Defines conversation structures with steps, conditions, and termination configuration
- **FlowStep** - Individual steps with speaker/target references, task types, and conditional logic
- **Session** - Active conversation instances with status tracking, current step, and flow/role snapshots
- **SessionRole** - Junction table mapping template roles to actual roles in sessions
- **Message** - Individual messages with speaker/target roles, threading support, and round tracking
- **LLMInteraction** - Detailed LLM API logging with token usage, performance metrics, and provider tracking
- **StepExecutionLog** - Step execution tracking with performance metrics, loop iteration, and debugging snapshots

#### Knowledge Base System Models
- **KnowledgeBase** - RAGFlow dataset integration with metadata, document count, and status tracking
- **KnowledgeBaseConversation** - Test conversation history with RAGFlow responses and reference tracking
- **RoleKnowledgeBase** - Junction table linking roles to knowledge bases with priority and retrieval configuration

#### Document Management System Models (New)
- **Document** - Document tracking within knowledge bases with file metadata and processing status
- **DocumentChunk** - Document chunk storage and retrieval with content, metadata, and scoring capabilities
- **ProcessingLog** - Document processing operation tracking with status, error handling, and performance metrics

### Backend Services Architecture
The backend includes a comprehensive services layer (`backend/app/services/`):

#### Core Services
- **FlowEngineService** (`flow_engine_service.py`) - Core conversation execution engine with step-by-step processing (46KB)
- **SessionService** (`session_service.py`) - Session management, state tracking, and lifecycle control
- **MessageService** (`message_service.py`) - Message processing, threading, and conversation history management
- **FlowService** (`flow_service.py`) - Flow template management, validation, and versioning

#### LLM Integration Services
- **LLM Service** (`services/llm/`) - Simplified LLM integration focused on Anthropic Claude with automatic provider detection
- **LLM File Record Service** (`llm_file_record_service.py`) - LLM interaction file recording and management
- **Conversation Manager** (`conversation_manager.py`) - LLM conversation state management and context handling

#### System Services
- **CacheService** (`cache_service.py`) - Performance caching mechanisms for frequently accessed data
- **HealthService** (`health_service.py`) - System health monitoring and status reporting
- **RateLimitService** (`rate_limit_service.py`) - API rate limiting and request throttling
- **SecurityService** (`security_service.py`) - Security utilities and input validation

#### Knowledge Base Services
- **KnowledgeBaseService** (`knowledge_base_service.py`) - Complete knowledge base management with CRUD operations, RAGFlow synchronization, role associations, and statistics
- **RAGFlowService** (`ragflow_service.py`) - RAGFlow API integration with dataset management, chat assistant functionality, connection management, and retry logic

#### Document Management Services (New)
- **DocumentService** (`document_service.py`) - Core document management with CRUD operations, validation, and metadata handling
- **UploadService** (`upload_service.py`) - File upload service with streaming, progress tracking, and multi-format support
- **ChunkService** (`chunk_service.py`) - Document chunking and retrieval service with configurable strategies and metadata

#### Utility Services
- **LLM Logger** (`utils/llm_logger.py`) - Specialized LLM request/response logging with detailed metrics
- **Prompt Optimizer** (`utils/prompt_optimizer.py`) - Prompt optimization and enhancement utilities
- **Token Counter** (`utils/token_counter.py`) - Usage tracking and token limit management
- **Request Tracker** (`utils/request_tracker.py`) - Request monitoring and debugging support

### Database Architecture
- **Session Isolation**: Sessions use snapshots to preserve template versions at creation time
- **JSON Configuration**: Complex configurations stored as JSON (termination, logic, context scopes)
- **Performance Optimization**: Comprehensive indexing for common query patterns
- **Multi-level Tracking**: Support for nested loops, rounds, and step execution sequences
- **Error Handling**: Built-in error tracking and debugging capabilities throughout the schema

### Frontend Components (Actual Implementation)
- **MultiRoleDialogSystem.tsx** - Main application interface with comprehensive role and flow management (78KB)
- **LLMTestPage.tsx** - LLM API testing and validation interface
- **SessionTheater.tsx** - Real-time conversation visualization and monitoring
- **StepProgressDisplay.tsx** - Real-time progress tracking for conversation execution
- **StepVisualization.tsx** - Multi-view flow visualization and debugging

#### Knowledge Base Components
- **KnowledgeBaseManagement.tsx** - Main knowledge base interface with connection status monitoring and view management
- **KnowledgeBaseList.tsx** - Knowledge base listing with search, filtering, and status management
- **KnowledgeBaseDetails.tsx** - Detailed knowledge base view with statistics, role associations, and test conversation interface
- **TestConversation.tsx** - Knowledge base test conversation interface with reference tracking and history

#### Document Management Components (New)
- **DocumentUpload.tsx** - Document upload interface with drag-and-drop, progress tracking, and file validation
- **DocumentList.tsx** - Document listing with search, filtering, pagination, and bulk operations
- **DocumentView.tsx** - Detailed document view with metadata, chunk visualization, and management capabilities
- **DocumentUploadFallback.tsx** - Fallback upload component for browsers with limited file API support

#### Note on Frontend Structure
Some directories mentioned in architectural documentation have limited current implementation:
- **hooks/** directory is mostly empty (custom hooks mentioned in docs are not yet implemented)
- **types/** directory is minimal (only basic role types defined)
- Available components are functional but fewer than initially documented

### API Endpoints Structure
- `/api/roles` - Role management (CRUD operations)
- `/api/flows` - Flow template management with statistics
- `/api/sessions` - Session management and execution control
- `/api/sessions/{id}/messages` - Message management and export
- `/api/llm` - LLM integration and interaction tracking
- `/api/monitoring` - System health and performance metrics
- `/api/health` - Health check endpoint
- `/api/knowledge-bases` - Knowledge base management and RAGFlow integration

#### Health Monitoring Endpoints
- `GET /api/health` - Comprehensive system health check with component status
- `GET /api/monitoring/metrics` - Current performance metrics (CPU, memory, request rates)
- `GET /api/monitoring/history` - Historical performance data (query: `hours=1-168`)
- `GET /api/monitoring/dashboard` - Combined dashboard data with overview and system info
- `GET /api/monitoring/system-info` - Detailed system information (OS, Python version, dependencies)
- `PUT /api/monitoring/alerts` - Update monitoring alert thresholds
- `POST /api/monitoring/control` - Control monitoring service (start/stop/clear)

#### LLM Monitoring Endpoints
- `GET /api/sessions/{id}/llm-statistics` - LLM interaction statistics for a session
- `GET /api/llm-interactions/active` - Currently active LLM interactions
- `GET /api/llm-interactions/errors` - LLM interaction error logs
- `GET /api/llm-interactions/metrics` - LLM-specific system metrics

#### Knowledge Base Endpoints
- `GET /api/knowledge-bases` - List knowledge bases with pagination, search, and filtering
- `POST /api/knowledge-bases` - Execute knowledge base operations (refresh datasets, sync with RAGFlow)
- `GET /api/knowledge-bases/{id}` - Get detailed knowledge base information with statistics and role associations
- `POST /api/knowledge-bases/{id}` - Execute test conversations and retrieve conversation history
- `GET /api/knowledge-bases/statistics` - Get comprehensive knowledge base system statistics
- `GET /api/knowledge-bases/{id}/conversations/{conversation_id}` - Get detailed test conversation information
- `DELETE /api/knowledge-bases/{id}/conversations/{conversation_id}` - Delete test conversation records

#### Document Management Endpoints (New)
- `POST /api/knowledge-bases/{id}/documents` - Upload documents to knowledge base with progress tracking
- `GET /api/knowledge-bases/{id}/documents` - List documents with pagination, search, and filtering
- `GET /api/documents/{document_id}` - Get detailed document information with metadata and processing status
- `PUT /api/documents/{document_id}` - Update document metadata and configuration
- `DELETE /api/documents/{document_id}` - Delete document and associated chunks
- `GET /api/documents/{document_id}/chunks` - Get document chunks with content and metadata
- `POST /api/documents/{document_id}/reprocess` - Reprocess document with updated configuration
- `GET /api/documents/{document_id}/status` - Get real-time processing status and progress

## Key Features

### Role Management
- Built-in roles: Teacher, Student, Expert, Reviewer
- Custom role creation with style guidelines and constraints
- Focus point configuration for targeted responses

### Flow Template System
- Structured conversation flows with steps
- Conditional branching and looping support
- Context scope management (none, last_message, last_round, all)
- Task types: ask_question, answer_question, review_answer, summarize

### Real-time Execution
- Step-by-step conversation execution
- LLM integration with configurable providers
- Performance monitoring and interaction logging
- WebSocket support for real-time updates

### Monitoring and Debugging
- Comprehensive health monitoring
- LLM interaction performance tracking
- Error logging and system metrics
- Debug visualization tools

### Knowledge Base System (RAGFlow Integration)
- **RAGFlow Dataset Management**: Sync and manage external knowledge bases from RAGFlow instances
- **Role-Knowledge Base Associations**: Link knowledge bases to specific roles with priority and retrieval configuration
- **Test Conversations**: Conduct test dialogues with knowledge bases to validate responses and reference quality
- **Real-time Connection Monitoring**: Track RAGFlow service availability and connection status
- **Comprehensive Statistics**: Track document counts, usage patterns, and performance metrics
- **Reference Tracking**: View source document references and confidence scores for knowledge base responses
- **Batch Operations**: Bulk update knowledge base status and synchronize datasets from RAGFlow
- **Caching and Performance**: Optimized data retrieval with intelligent caching mechanisms

### Document Management System (New)
- **Multi-Format Upload Support**: Upload documents in various formats (PDF, DOCX, TXT, MD, etc.)
- **Real-time Processing Status**: Track document processing progress with live status updates
- **Document Chunking**: Automatic document chunking with configurable strategies and metadata
- **Visual Document Management**: Complete UI for viewing, managing, and organizing uploaded documents
- **Search and Filtering**: Advanced document search with filtering by status, type, and content
- **Bulk Operations**: Support for bulk document operations (upload, delete, reprocess)
- **Processing Logs**: Comprehensive logging of document processing operations with error tracking
- **Version Management**: Document version tracking and rollback capabilities

## Development Guidelines

### Backend Development
1. **Database Migrations**: Use Flask-Migrate with Alembic for schema versioning and field updates
2. **API Responses**: Follow consistent JSON format with success/error structure
3. **Error Handling**: Centralized error handlers in `app/__init__.py` with specialized LLM error tracking
4. **LLM Integration**: Use the simplified LLM service layer focused on Anthropic integration with automatic provider detection
5. **Service Architecture**: Follow the service layer pattern for business logic separation
6. **Logging**: Comprehensive file logging with specialized LLM request tracking in `logs/`
7. **Performance Monitoring**: Built-in health monitoring, rate limiting, and performance metrics

### Frontend Development
1. **API Integration**: Use centralized API clients in `src/api/` with proper TypeScript interfaces
2. **Component Architecture**: Follow the existing single-page application pattern with React Router
3. **Styling**: Use Tailwind CSS utility classes with the existing theme system (5 color schemes)
4. **Icons**: Use Lucide React for consistent iconography throughout the application
5. **Build Issues**: TypeScript compilation fails due to syntax errors in `src/components/` (development server works correctly)
6. **State Management**: Currently uses local component state (hooks directory is empty/not implemented)
7. **Development Environment**: Use Vite dev server with API proxy to backend port 5010

### Environment Configuration

#### Backend Configuration (.env file)
```python
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///multi_role_chat.db

# LLM Provider Configuration
LLM_PROVIDER=openai  # Can be openai, anthropic, or claude_cli

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_TEMPERATURE=0.7

# Claude CLI Configuration
CLAUDE_CLI_COMMAND=claude
CLAUDE_CLI_TIMEOUT=120
CLAUDE_CLI_MAX_RETRIES=3
CLAUDE_CLI_RETRY_DELAY=1

# Default LLM Provider
LLM_DEFAULT_PROVIDER=claude_cli

# RAGFlow Configuration (Knowledge Base System)
RAGFLOW_API_KEY=your-ragflow-api-key
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
RAGFLOW_TIMEOUT=30
RAGFLOW_MAX_RETRIES=3
RAGFLOW_RETRY_DELAY=1.0
RAGFLOW_VERIFY_SSL=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=5010
API_DEBUG=True

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

#### Frontend Environment Variables
```bash
# Optional: Alternative API base URL configuration
VITE_API_BASE_URL_ALT=http://localhost:5010
```

#### Database and Logging
- **Database**: SQLite file located at `backend/multi_role_chat.db` (auto-created on init)
- **Logging**: File logging enabled by default, logs stored in `logs/` directory
- **LLM Logging**: Specialized LLM request logging to `logs/llm_requests.log`

## Known Issues

- **Frontend Build**: TypeScript compilation fails due to syntax errors in `src/components/`
- **ESLint Configuration**: Frontend linting requires proper ESLint config initialization
- **Development Environment**: Despite build issues, development server works correctly

## Testing and Quality Assurance

### Validation Commands
```bash
# Backend testing and validation
cd backend
python check_db.py              # Validate database integrity
python check_syntax.py          # Check Python syntax
python verify_fix.py            # Verify applied fixes
python quick_start.py           # Comprehensive environment validation
python char_count_monitor.py   # Monitor character usage

# Frontend build validation
cd front
npm run check                   # Run lint + build (will fail due to known issues)
npm run build                   # TypeScript compilation only
npm run lint                    # ESLint check (requires config initialization)

# Integration testing (from project root)
python test_role_reference.py   # Test role reference system
python simple_test.py           # Basic integration test

# Knowledge base system testing
cd backend
python -m pytest tests/test_knowledge_base.py                # Knowledge base service tests
python -m pytest tests/test_knowledge_base_integration.py     # Integration tests
python -c "from app.services.knowledge_base_service import get_knowledge_base_service; print('Knowledge base service OK')"  # Quick service test

# Document management system testing (new)
python -m pytest tests/test_document_management_integration.py  # Document management integration tests
python -c "from app.services.document_service import get_document_service; print('Document service OK')"  # Quick document service test

# Custom test runner (comprehensive)
python run_tests.py                             # Run all knowledge base tests with detailed reporting
python run_tests.py --test TestKnowledgeBaseModel  # Run specific test class
python run_tests.py --quick                    # Quick test run (skip integration tests)
python run_tests.py --verbose                  # Verbose output

# Direct unittest execution
python -m unittest tests.test_knowledge_base   # Run specific test file
python -m unittest tests.test_knowledge_base -v  # Run with verbose output
```

### Quality Assurance Features
- Backend includes comprehensive health monitoring and performance metrics
- LLM testing interface available in frontend (`LLMTestPage.tsx`)
- Database utilities for maintenance, cleanup, and migration with Flask-Migrate support
- Comprehensive error handling and logging throughout the system with specialized LLM tracking
- Real-time debugging capabilities with session visualization and step progress monitoring
- Performance monitoring with rate limiting, caching, and system health tracking
- Environment validation scripts for both backend and frontend quick setup

## Advanced Architecture Patterns

### Backend Service Architecture
- **Service Layer Pattern**: Business logic separated into dedicated services with clear responsibilities
- **Repository Pattern**: Data access through SQLAlchemy models with comprehensive relationships
- **Factory Pattern**: Flask application factory for environment-specific configurations
- **Middleware Pattern**: CORS, logging, monitoring, and rate limiting middleware
- **Observer Pattern**: Health monitoring and performance tracking throughout the system

### LLM Integration Architecture
- **Service Abstraction**: Simplified LLM service with automatic provider detection (primarily Anthropic-focused)
- **Request Tracking**: Comprehensive logging and performance monitoring for all LLM interactions
- **Configuration Management**: Environment-based LLM provider selection with fallback support
- **Error Handling**: Graceful fallback mechanisms and detailed error reporting with retry logic

### Frontend Component Architecture
- **Composition Pattern**: Complex components built from smaller, reusable parts
- **Proxy Pattern**: Vite proxy for API requests during development
- **Theme Pattern**: Centralized theme system with 5 color schemes (blue, purple, emerald, rose, amber)
- **Single-Page Application**: React Router-based navigation with state management

## Knowledge Base System Setup and Configuration

### RAGFlow Prerequisites

Before using the knowledge base system, you need:

1. **RAGFlow Instance**: A running RAGFlow server (self-hosted or cloud)
2. **API Access**: RAGFlow API key with appropriate permissions
3. **Network Connectivity**: The MRC server must be able to reach your RAGFlow instance

### Database Setup

The knowledge base system requires additional database tables:

```bash
# Navigate to backend directory
cd backend

# Add knowledge base tables to existing database
python add_knowledge_base_tables.py

# Apply configuration field migrations (if needed)
python add_knowledge_base_config_migration.py

# Verify database integrity
python check_db.py
```

### RAGFlow Configuration

1. **Set up RAGFlow**: Install and configure your RAGFlow instance following the official documentation
2. **Create Datasets**: Upload and process your documents in RAGFlow to create knowledge bases
3. **Get API Credentials**: Obtain your RAGFlow API key from the RAGFlow admin interface
4. **Configure Environment**: Update your `.env` file with RAGFlow connection details

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# RAGFlow Configuration (Required for Knowledge Base System)
RAGFLOW_API_KEY=your-actual-ragflow-api-key
RAGFLOW_BASE_URL=https://your-ragflow-instance.com  # Without trailing slash
RAGFLOW_TIMEOUT=30                                    # Request timeout in seconds
RAGFLOW_MAX_RETRIES=3                                # Number of retry attempts
RAGFLOW_RETRY_DELAY=1.0                              # Delay between retries (seconds)
RAGFLOW_VERIFY_SSL=true                              # SSL verification for HTTPS
```

### Initial Knowledge Base Setup

1. **Start the Backend Server**:
   ```bash
   cd backend && python run.py
   ```

2. **Access Knowledge Base Interface**:
   - Open http://localhost:3000 in your browser
   - Navigate to the "Knowledge Base" tab
   - The system will automatically check RAGFlow connectivity

3. **Sync Datasets from RAGFlow**:
   - Click "Refresh All" to sync datasets from your RAGFlow instance
   - Or use the API directly: `POST /api/knowledge-bases` with `{"action": "refresh_all"}`

4. **Test Knowledge Base Functionality**:
   - Select a knowledge base from the list
   - Use the "Test Conversation" feature to validate responses
   - Check the conversation history and reference tracking

### Troubleshooting Guide

#### Common Issues and Solutions

**RAGFlow Connection Errors**
```
Error: RAGFlow API调用失败: Connection timeout
```
- **Solution**: Check `RAGFLOW_BASE_URL` and network connectivity
- **Verify**: RAGFlow instance is running and accessible from the MRC server
- **Test**: `curl -H "Authorization: Bearer YOUR_API_KEY" YOUR_RAGFLOW_URL/api/datasets`

**Invalid API Key**
```
Error: RAGFlow API调用失败: 401 Unauthorized
```
- **Solution**: Verify `RAGFLOW_API_KEY` is correct and has proper permissions
- **Check**: API key in RAGFlow admin interface
- **Regenerate**: Create a new API key if needed

**Dataset Sync Issues**
```
Error: 数据集同步失败: RAGFlow服务不可用
```
- **Solution**: Check RAGFlow service status and permissions
- **Verify**: API key has dataset read permissions
- **Manual Check**: Access RAGFlow web interface to confirm datasets exist

**Test Conversation Failures**
```
Error: 测试对话执行失败: 500 Internal Server Error
```
- **Solution**: Check dataset status in RAGFlow (must be fully processed)
- **Verify**: Documents are parsed and chunks are generated
- **Check**: Dataset is active and chat functionality is enabled

**Performance Issues**
- **Large Datasets**: Consider using retrieval configuration to limit results
- **Timeouts**: Increase `RAGFLOW_TIMEOUT` for complex queries
- **Caching**: Enable knowledge base caching in the service configuration

#### Debug Mode for RAGFlow

Enable detailed logging for troubleshooting:

```python
# In backend/app/services/ragflow_service.py
import logging
logging.getLogger('ragflow_service').setLevel(logging.DEBUG)
```

Or add to your `.env`:
```bash
LOG_LEVEL=DEBUG
```

#### Testing RAGFlow Integration Manually

```bash
# Test basic connectivity
curl -H "Authorization: Bearer YOUR_API_KEY" \
     YOUR_RAGFLOW_URL/api/datasets

# Test chat functionality
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"dataset_id": "your_dataset_id", "question": "test query"}' \
     YOUR_RAGFLOW_URL/api/chat
```

### Best Practices

1. **API Security**: Store RAGFlow API keys securely and rotate regularly
2. **Dataset Management**: Keep RAGFlow datasets organized and well-documented
3. **Performance**: Monitor response times and optimize dataset configurations
4. **Testing**: Regularly test knowledge base responses for accuracy and relevance
5. **Monitoring**: Use the built-in statistics tracking to monitor usage patterns

### API Reference Documentation

For complete RAGFlow API documentation, refer to:
- **Backend Reference**: `doc/ragflow.md` - Comprehensive RAGFlow Python API guide
- **RAGFlow Official Docs**: https://ragflow.io/docs/api-reference
- **RAGFlow GitHub**: https://github.com/infiniflow/ragflow

## Migration Notes

This project was migrated from `D:\ProjectPackage\MultiRoleChat\backend` on 2025-12-05, maintaining complete database structure and functionality while adding enhanced frontend capabilities, comprehensive monitoring features, a robust services architecture, the integrated RAGFlow knowledge base system, and a complete document management system with upload, processing, and chunking capabilities.

## Document Management Implementation

The document management system is structured with comprehensive task breakdown in `tasks.md`, featuring 40+ atomic tasks for complete implementation. The system includes:

- **Backend Models**: Document, DocumentChunk, ProcessingLog with full SQLAlchemy integration
- **Services Layer**: DocumentService, UploadService, ChunkService with RAGFlow integration
- **API Endpoints**: Complete REST API for document operations with progress tracking
- **Frontend Components**: React components for upload, listing, viewing, and management
- **Testing Framework**: Comprehensive unit and integration tests

The implementation follows existing MRC patterns and integrates seamlessly with the current knowledge base system, enabling users to upload documents directly to knowledge bases, track processing status, and manage document chunks through an intuitive interface.