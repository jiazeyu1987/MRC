# Knowledge Base Document Management API Documentation

## Overview

The Knowledge Base Document Management API provides comprehensive endpoints for uploading, managing, and processing documents within knowledge bases. This API integrates with RAGFlow for document processing, chunking, and retrieval-augmented generation.

**Base URL**: `http://localhost:5010/api`
**Version**: 1.0.0
**Content-Type**: `application/json` (except for file uploads)

## Authentication

All API requests require proper authentication. Include your API key in the request headers:

```http
Authorization: Bearer YOUR_API_KEY
```

## Common Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "error_code": null
}
```

### Error Response Format

```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

## Document Management Endpoints

### Upload Document

Upload a document to a knowledge base for processing.

**Endpoint**: `POST /api/knowledge-bases/{knowledge_base_id}/documents/upload`
**Content-Type**: `multipart/form-data`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The document file to upload |
| `upload_id` | String | Optional | Unique upload identifier for progress tracking |

#### File Upload Constraints

- **Maximum file size**: 50MB (configurable)
- **Supported formats**: PDF, DOC, DOCX, TXT, MD, HTML, RTF, JPG, PNG, GIF, BMP, SVG, ZIP, RAR, 7Z, TAR, GZ, MP4, AVI, MOV, WMV, FLV, WEBM, XML, JSON
- **Security scanning**: Automatic virus and content scanning

#### Request Example

```bash
curl -X POST \
  http://localhost:5010/api/knowledge-bases/kb-123/documents/upload \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'file=@document.pdf'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "document_id": "doc-abc123",
    "upload_id": "upload-def456",
    "document": {
      "id": "doc-abc123",
      "knowledge_base_id": "kb-123",
      "filename": "document_20240108_123456.pdf",
      "original_filename": "document.pdf",
      "file_size": 2048576,
      "file_type": "pdf",
      "mime_type": "application/pdf",
      "upload_status": "uploading",
      "processing_status": "pending",
      "chunk_count": 0,
      "created_at": "2024-01-08T12:34:56Z",
      "updated_at": "2024-01-08T12:34:56Z"
    }
  },
  "message": "Document upload initiated successfully"
}
```

### Get Documents

Retrieve a list of documents from a knowledge base with optional filtering and pagination.

**Endpoint**: `GET /api/knowledge-bases/{knowledge_base_id}/documents`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | Integer | No | 1 | Page number for pagination |
| `limit` | Integer | No | 20 | Number of documents per page (max: 100) |
| `search` | String | No | | Search term for document names |
| `status` | String | No | | Filter by status (`uploading`, `pending`, `processing`, `completed`, `failed`) |
| `file_type` | String | No | | Filter by file type (`pdf`, `doc`, `txt`, etc.) |
| `sort_by` | String | No | created_at | Sort field (`filename`, `created_at`, `file_size`, `status`) |
| `sort_order` | String | No | desc | Sort order (`asc`, `desc`) |

#### Request Example

```bash
curl -X GET \
  "http://localhost:5010/api/knowledge-bases/kb-123/documents?page=1&limit=20&search=report&status=completed"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "doc-abc123",
        "knowledge_base_id": "kb-123",
        "filename": "annual_report_2024.pdf",
        "original_filename": "Annual Report 2024.pdf",
        "file_size": 3072000,
        "file_type": "pdf",
        "mime_type": "application/pdf",
        "upload_status": "completed",
        "processing_status": "completed",
        "chunk_count": 25,
        "created_at": "2024-01-08T12:34:56Z",
        "updated_at": "2024-01-08T12:45:23Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "has_more": false
    }
  },
  "message": "Documents retrieved successfully"
}
```

### Get Document Details

Retrieve detailed information about a specific document.

**Endpoint**: `GET /api/knowledge-bases/{knowledge_base_id}/documents/{document_id}`

#### Request Example

```bash
curl -X GET \
  http://localhost:5010/api/knowledge-bases/kb-123/documents/doc-abc123
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "doc-abc123",
    "knowledge_base_id": "kb-123",
    "ragflow_document_id": "ragflow-doc-789",
    "filename": "annual_report_2024.pdf",
    "original_filename": "Annual Report 2024.pdf",
    "file_size": 3072000,
    "file_type": "pdf",
    "mime_type": "application/pdf",
    "upload_status": "completed",
    "processing_status": "completed",
    "chunk_count": 25,
    "error_message": null,
    "ragflow_metadata": {
      "processing_time": 45.2,
      "language": "en",
      "extracted_entities": 15
    },
    "created_at": "2024-01-08T12:34:56Z",
    "updated_at": "2024-01-08T12:45:23Z",
    "uploaded_at": "2024-01-08T12:35:12Z",
    "processed_at": "2024-01-08T12:45:23Z"
  },
  "message": "Document details retrieved successfully"
}
```

### Delete Document

Delete a document from the knowledge base.

**Endpoint**: `DELETE /api/knowledge-bases/{knowledge_base_id}/documents/{document_id}`

#### Request Example

```bash
curl -X DELETE \
  http://localhost:5010/api/knowledge-bases/kb-123/documents/doc-abc123
```

#### Response Example

```json
{
  "success": true,
  "data": null,
  "message": "Document deleted successfully"
}
```

### Get Document Chunks

Retrieve chunks belonging to a specific document.

**Endpoint**: `GET /api/knowledge-bases/{knowledge_base_id}/documents/{document_id}/chunks`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chunk_index_min` | Integer | No | | Minimum chunk index |
| `chunk_index_max` | Integer | No | | Maximum chunk index |
| `sort_by` | String | No | chunk_index | Sort field (`chunk_index`, `word_count`, `created_at`) |
| `sort_order` | String | No | asc | Sort order (`asc`, `desc`) |

#### Request Example

```bash
curl -X GET \
  "http://localhost:5010/api/knowledge-bases/kb-123/documents/doc-abc123/chunks?sort_by=chunk_index&sort_order=asc"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "document_id": "doc-abc123",
    "document_name": "Annual Report 2024.pdf",
    "chunks": [
      {
        "id": "chunk-001",
        "document_id": "doc-abc123",
        "ragflow_chunk_id": "ragflow-chunk-001",
        "chunk_index": 0,
        "content": "Annual Report 2024\n\nThis document provides a comprehensive overview of our company's performance...",
        "content_preview": "Annual Report 2024\n\nThis document provides a comprehensive overview...",
        "word_count": 150,
        "character_count": 850,
        "ragflow_metadata": {
          "position_start": 0,
          "position_end": 1000,
          "keywords": ["annual", "report", "performance", "overview"]
        },
        "embedding_vector_id": "vector-abc123",
        "created_at": "2024-01-08T12:45:23Z",
        "updated_at": "2024-01-08T12:45:23Z"
      }
    ],
    "total_chunks": 25
  },
  "message": "Document chunks retrieved successfully"
}
```

## Search and Retrieval Endpoints

### Search Chunks

Search for document chunks across the knowledge base.

**Endpoint**: `POST /api/knowledge-bases/{knowledge_base_id}/chunks/search`

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | String | Yes | Search query string |
| `document_id` | String | No | Limit search to specific document |
| `min_relevance_score` | Float | No | Minimum relevance score (0.0-1.0) |
| `max_results` | Integer | No | Maximum number of results (default: 10, max: 100) |

#### Request Example

```bash
curl -X POST \
  http://localhost:5010/api/knowledge-bases/kb-123/chunks/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "financial performance metrics",
    "max_results": 20,
    "min_relevance_score": 0.7
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "chunks": [
      {
        "id": "chunk-015",
        "document_id": "doc-abc123",
        "chunk_index": 14,
        "content": "Financial Performance Metrics\n\nRevenue: $125.4M (+18% YoY)\nNet Income: $23.1M (+22% YoY)",
        "content_preview": "Financial Performance Metrics\n\nRevenue: $125.4M...",
        "word_count": 85,
        "character_count": 420,
        "ragflow_metadata": {
          "relevance_score": 0.92,
          "highlighted_terms": ["financial", "performance", "metrics"]
        },
        "created_at": "2024-01-08T12:45:23Z"
      }
    ],
    "total_count": 1,
    "query": "financial performance metrics",
    "search_time": 0.12,
    "filters_applied": {
      "max_results": 20,
      "min_relevance_score": 0.7
    }
  },
  "message": "Chunk search completed successfully"
}
```

## Progress Tracking Endpoints

### Get Upload Progress

Track the progress of a document upload.

**Endpoint**: `GET /api/knowledge-bases/{knowledge_base_id}/documents/upload`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `upload_id` | String | Yes | Upload identifier returned during upload initiation |

#### Request Example

```bash
curl -X GET \
  "http://localhost:5010/api/knowledge-bases/kb-123/documents/upload?upload_id=upload-def456"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "upload_id": "upload-def456",
    "document_id": "doc-abc123",
    "progress": 75,
    "status": "processing",
    "message": "Document uploaded successfully, processing in RAGFlow",
    "start_time": "2024-01-08T12:34:56Z",
    "file_size": 3072000,
    "bytes_uploaded": 3072000,
    "upload_speed": 1048576
  },
  "message": "Upload progress retrieved successfully"
}
```

### Cancel Upload

Cancel an ongoing upload.

**Endpoint**: `DELETE /api/knowledge-bases/{knowledge_base_id}/documents/upload`

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `upload_id` | String | Yes | Upload identifier to cancel |

#### Request Example

```bash
curl -X DELETE \
  http://localhost:5010/api/knowledge-bases/kb-123/documents/upload \
  -H 'Content-Type: application/json' \
  -d '{
    "upload_id": "upload-def456"
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": null,
  "message": "Upload cancelled successfully"
}
```

## Statistics Endpoints

### Get Document Statistics

Get comprehensive statistics about documents in a knowledge base.

**Endpoint**: `GET /api/knowledge-bases/{knowledge_base_id}/documents/statistics`

#### Request Example

```bash
curl -X GET \
  http://localhost:5010/api/knowledge-bases/kb-123/documents/statistics
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "total_documents": 15,
    "total_file_size_bytes": 52428800,
    "total_file_size_mb": 50.0,
    "total_chunks": 342,
    "status_breakdown": {
      "completed": 12,
      "processing": 2,
      "failed": 1
    },
    "file_type_breakdown": {
      "pdf": 8,
      "doc": 3,
      "txt": 2,
      "md": 2
    },
    "updated_at": "2024-01-08T12:50:00Z"
  },
  "message": "Statistics retrieved successfully"
}
```

## Test Conversation Endpoint

### Test Conversation with Documents

Perform a test conversation using the knowledge base documents.

**Endpoint**: `POST /api/knowledge-bases/{knowledge_base_id}`

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | String | Yes | Set to `"test_conversation"` |
| `question` | String | Yes | Question to ask the knowledge base |
| `title` | String | No | Title for the test conversation |

#### Request Example

```bash
curl -X POST \
  http://localhost:5010/api/knowledge-bases/kb-123 \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "test_conversation",
    "question": "What were the main financial highlights in the annual report?",
    "title": "Financial Highlights Test"
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "conv-789",
    "knowledge_base_id": "kb-123",
    "user_question": "What were the main financial highlights in the annual report?",
    "ragflow_response": "Based on the annual report, the main financial highlights include:\n\n1. Revenue of $125.4M, representing an 18% year-over-year increase\n2. Net income of $23.1M, up 22% from the previous year\n3. Customer acquisition growth of 25% compared to last year",
    "confidence_score": 0.92,
    "references": {
      "references": [
        {
          "document_id": "doc-abc123",
          "document_title": "Annual Report 2024.pdf",
          "page_number": 3,
          "snippet": "Revenue: $125.4M (+18% YoY)\nNet Income: $23.1M (+22% YoY)",
          "confidence_score": 0.95
        }
      ]
    },
    "created_at": "2024-01-08T12:55:00Z",
    "updated_at": "2024-01-08T12:55:15Z"
  },
  "message": "Test conversation completed successfully"
}
```

## WebSocket Integration

### Real-time Progress Updates

For real-time progress tracking, connect to the WebSocket endpoint:

**WebSocket URL**: `ws://localhost:5010/ws/document-progress/{knowledge_base_id}`

#### Message Types

##### Progress Update
```json
{
  "type": "progress_update",
  "data": {
    "upload_id": "upload-def456",
    "document_id": "doc-abc123",
    "progress": 45,
    "status": "uploading",
    "message": "Uploading file...",
    "start_time": "2024-01-08T12:34:56Z"
  }
}
```

##### Status Change
```json
{
  "type": "status_change",
  "data": {
    "document_id": "doc-abc123",
    "old_status": "uploading",
    "new_status": "processing",
    "message": "Document uploaded, starting processing"
  }
}
```

##### Error Event
```json
{
  "type": "error",
  "data": {
    "document_id": "doc-abc123",
    "error": "File size exceeds maximum limit",
    "step": "upload"
  }
}
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_KNOWLEDGE_BASE` | Knowledge base not found or inaccessible |
| `INVALID_DOCUMENT` | Document not found or inaccessible |
| `FILE_TOO_LARGE` | File size exceeds maximum limit |
| `UNSUPPORTED_FILE_TYPE` | File type not supported |
| `UPLOAD_IN_PROGRESS` | Upload already in progress for this file |
| `PROCESSING_ERROR` | Error during document processing |
| `RAGFLOW_ERROR` | Error communicating with RAGFlow service |
| `QUOTA_EXCEEDED` | Storage quota exceeded |
| `SECURITY_SCAN_FAILED` | File failed security scan |
| `VALIDATION_ERROR` | Request validation failed |
| `NETWORK_ERROR` | Network connectivity issue |
| `INTERNAL_ERROR` | Internal server error |

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Upload endpoints**: 10 requests per minute per knowledge base
- **Search endpoints**: 60 requests per minute per knowledge base
- **Other endpoints**: 100 requests per minute per knowledge base

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1641648000
```

## SDK Examples

### Python Example

```python
import requests
import json

class DocumentManagementAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def upload_document(self, kb_id, file_path):
        url = f"{self.base_url}/api/knowledge-bases/{kb_id}/documents/upload"

        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
            response = requests.post(url, headers=headers, files=files)

        return response.json()

    def search_chunks(self, kb_id, query, max_results=10):
        url = f"{self.base_url}/api/knowledge-bases/{kb_id}/chunks/search"
        data = {
            'query': query,
            'max_results': max_results
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

# Usage
api = DocumentManagementAPI('http://localhost:5010', 'your-api-key')
result = api.upload_document('kb-123', '/path/to/document.pdf')
print(result)
```

### JavaScript Example

```javascript
class DocumentManagementAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async uploadDocument(kbId, file) {
        const url = `${this.baseUrl}/api/knowledge-bases/${kbId}/documents/upload`;
        const formData = new FormData();
        formData.append('file', file);

        const headers = { ...this.headers };
        delete headers['Content-Type'];

        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData
        });

        return response.json();
    }

    async searchChunks(kbId, query, maxResults = 10) {
        const url = `${this.baseUrl}/api/knowledge-bases/${kbId}/chunks/search`;
        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                query,
                max_results: maxResults
            })
        });

        return response.json();
    }
}

// Usage
const api = new DocumentManagementAPI('http://localhost:5010', 'your-api-key');
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

api.uploadDocument('kb-123', file).then(result => {
    console.log('Upload result:', result);
});
```

## Best Practices

1. **Progress Tracking**: Use WebSocket connections for real-time upload progress instead of polling
2. **Error Handling**: Always check the `success` field in responses before processing data
3. **File Validation**: Validate files on the client side before upload to reduce unnecessary requests
4. **Batch Operations**: For multiple document operations, use batch endpoints when available
5. **Pagination**: Always use pagination for document lists to improve performance
6. **Caching**: Cache document metadata and chunk data to reduce API calls
7. **Security**: Never expose API keys in client-side code
8. **Rate Limiting**: Implement exponential backoff for rate-limited requests

## Support

For API support and questions:
- Email: support@yourcompany.com
- Documentation: https://docs.yourcompany.com/api
- Status Page: https://status.yourcompany.com