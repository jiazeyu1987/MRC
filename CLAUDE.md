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

# Create built-in roles and flows
python run.py create_builtin-roles
python run.py create-builtin-flows

# Run development server (port 5010)
python run.py

# Database utilities
python check_db.py              # Check database status
python clean_db.py              # Clean database
python clear_templates.py       # Clear flow templates
python reset_templates.py       # Reset to built-in templates
```

### Frontend Development
```bash
# Navigate to frontend directory (note: directory name is "front", not "frontend")
cd front

# Install dependencies
npm install

# Run development server (port 3000, proxies /api to backend:5010)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
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

## Core System Components

### Backend Models
- **Role** - Defines virtual participants with style, constraints, and focus points
- **FlowTemplate** - Defines conversation structures with steps and conditions
- **FlowStep** - Individual steps in a conversation flow (speaker, task type, context scope)
- **Session** - Active conversation instances with role assignments
- **Message** - Individual messages with LLM interaction tracking
- **LLMInteraction** - Detailed LLM API call logging and performance metrics

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
- Backend: Copy `.env.example` to `.env` and configure API keys
- Frontend: Uses Vite proxy, no environment variables required
- Database: SQLite file located at `backend/conversations.db`

## Known Issues

- **Frontend Build**: TypeScript compilation fails due to syntax errors in `src/components/`
- **ESLint Configuration**: Frontend linting requires proper ESLint config initialization
- **Development Environment**: Despite build issues, development server works correctly

## Testing and Quality Assurance

- Backend includes health monitoring and performance metrics
- LLM testing interface available in frontend
- Database utilities for maintenance and cleanup
- Comprehensive error handling and logging throughout the system

## Migration Notes

This project was migrated from `D:\ProjectPackage\MultiRoleChat\backend` on 2025-12-05, maintaining complete database structure and functionality while adding enhanced frontend capabilities and monitoring features.