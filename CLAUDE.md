# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Multi-Role Dialogue System (MRC)** - a comprehensive full-stack application for creating configurable, multi-role conversation environments. The system enables users to orchestrate conversations between multiple virtual roles (teachers, students, experts, officials, etc.) around specific topics using structured dialogue flows with advanced features like loops, conditions, and real-time execution.

## Architecture

### Technology Stack
- **Backend**: Flask 2.3.3 with SQLAlchemy, Flask-RESTful, Flask-Migrate
- **Frontend**: React 18.2.0 with TypeScript, Vite, Tailwind CSS
- **Database**: SQLite with migration support
- **LLM Integration**: OpenAI API (configurable for other providers)
- **Real-time**: WebSocket and Server-Sent Events support

### Project Structure
```
MRC/
├── backend/           # Flask REST API server (port 5010)
│   ├── app/
│   │   ├── api/      # API endpoints (roles, flows, sessions, messages, llm)
│   │   ├── models/   # SQLAlchemy models (Role, FlowTemplate, Session, Message)
│   │   └── utils/    # Utilities (monitoring, error handling)
│   ├── run.py        # Application entry point with CLI commands
│   └── conversations.db  # SQLite database
└── front/            # React TypeScript frontend (port 3000)
    ├── src/
    │   ├── api/      # API client modules
    │   ├── components/ # React components (some have build issues)
    │   ├── hooks/    # Custom React hooks
    │   └── utils/    # Frontend utilities
    └── vite.config.ts # Development proxy to backend:5010
```

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

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
```

### Quick Development Workflow
```bash
# Terminal 1: Start backend
cd backend && python run.py

# Terminal 2: Start frontend (auto-reloads)
cd front && npm run dev

# Access application at http://localhost:3000
# API available at http://localhost:3000/api/* (proxied to backend:5010)
# Health check: http://localhost:3000/api/health
```

### Frontend Quick Start Script
The `front/quick-start.js` script provides automated environment validation:
- Checks Node.js version (requires 16+)
- Validates project structure and required files
- Verifies dependencies (auto-installs if missing)
- Validates backend proxy configuration
- Starts development server with comprehensive error handling

### Quick Start Scripts
```bash
# Frontend quick start (environment check + auto-install deps + start dev server)
cd front && npm run quick-start

# Alternative: Use the Node.js script directly
cd front && node quick-start.js

# Backend quick start (if available)
cd backend && python quick_start.py
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

### Database Architecture
- **Session Isolation**: Sessions use snapshots to preserve template versions at creation time
- **JSON Configuration**: Complex configurations stored as JSON (termination, logic, context scopes)
- **Performance Optimization**: Comprehensive indexing for common query patterns
- **Multi-level Tracking**: Support for nested loops, rounds, and step execution sequences
- **Error Handling**: Built-in error tracking and debugging capabilities throughout the schema

### Frontend Components
- **MultiRoleDialogSystem.tsx** - Main application interface (63KB)
- **LLMTestPage.tsx** - LLM API testing and validation
- **SessionTheater.tsx** - Real-time conversation visualization
- **DebugPanel.tsx** - Comprehensive debugging and monitoring
- **StepVisualization.tsx** - Multi-view flow visualization

### API Endpoints Structure
- `/api/roles` - Role management (CRUD operations)
- `/api/flows` - Flow template management with statistics
- `/api/sessions` - Session management and execution control
- `/api/sessions/{id}/messages` - Message management and export
- `/api/llm` - LLM integration and interaction tracking
- `/api/monitoring` - System health and performance metrics
- `/api/health` - Health check endpoint

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

## Development Guidelines

### Backend Development
1. **Database Migrations**: Use Flask-Migrate for schema changes
2. **API Responses**: Follow consistent JSON format with success/error structure
3. **Error Handling**: Centralized error handlers in `app/__init__.py`
4. **LLM Integration**: Use the LLM abstraction layer for provider flexibility
5. **Logging**: File logging configured in `logs/` directory

### Frontend Development
1. **API Integration**: Use centralized API clients in `src/api/`
2. **State Management**: Custom hooks in `src/hooks/` for complex state
3. **Styling**: Use Tailwind CSS with existing theme system
4. **Icons**: Use Lucide React for consistency
5. **Build Issues**: Components in `src/components/` currently have TypeScript errors

### Environment Configuration
- **Backend**: Copy `.env.example` to `.env` and configure API keys (OpenAI API key required for LLM functionality)
- **Frontend**: Uses Vite proxy, no environment variables required for development
  - Optional: `VITE_API_BASE_URL_ALT` for alternative API base URL configuration
- **Database**: SQLite file located at `backend/conversations.db` (auto-created on init)
- **Logging**: File logging enabled by default, logs stored in `logs/` directory

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
python simple_syntax_test.py    # Basic syntax validation
python verify_fix.py            # Verify applied fixes

# Frontend build validation
cd front
npm run check                   # Run lint + build (will fail due to known issues)
npm run build                   # TypeScript compilation only
npm run lint                    # ESLint check (requires config initialization)

# Integration testing
python test_role_reference.py   # Test role reference system
python test_multi_topics.py     # Test multi-topic functionality
python simple_test.py           # Basic integration test
```

### Quality Assurance Features
- Backend includes comprehensive health monitoring and performance metrics
- LLM testing interface available in frontend (`LLMTestPage.tsx`)
- Database utilities for maintenance, cleanup, and migration
- Comprehensive error handling and logging throughout the system
- Real-time debugging capabilities with `DebugPanel.tsx` and monitoring components
- WebSocket support for real-time conversation updates

## Migration Notes

This project was migrated from `D:\ProjectPackage\MultiRoleChat\backend` on 2025-12-05, maintaining complete database structure and functionality while adding enhanced frontend capabilities and monitoring features.