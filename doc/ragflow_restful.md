# RAGFlow RESTful API Reference

This document provides comprehensive reference information for RAGFlow's HTTP API endpoints, with a focus on file upload and document management operations.

## Table of Contents
- [Authentication](#authentication)
- [File Upload Endpoints](#file-upload-endpoints)
- [Document Management](#document-management)
- [Dataset Operations](#dataset-operations)
- [Error Handling](#error-handling)
- [HTTP Status Codes](#http-status-codes)
- [Configuration](#configuration)

## Authentication

RAGFlow API uses Bearer token authentication. Include your API key in the Authorization header:

```http
Authorization: Bearer YOUR_RAGFLOW_API_KEY
```

### Getting Your API Key
1. Access your RAGFlow admin interface
2. Navigate to Settings/API Keys
3. Generate or copy your API key
4. Include it in all API requests

## File Upload Endpoints

### 1. Upload Single File
**Endpoint:** `POST /api/v1/dataset/upload`

Uploads a single file to a specified dataset for processing and indexing.

**Request Parameters:**
- `dataset_id` (required, string): ID of the target dataset
- `file` (required, file): File to upload (multipart form data)
- `name` (optional, string): Custom name for the uploaded file
- `description` (optional, string): Description of the file content
- `parser_method` (optional, string): Parsing method (`auto`, `ocr`, `structured`)
- `chunk_size` (optional, integer): Chunk size for document processing

**Example Request:**
```bash
curl -X POST \
  http://localhost:9380/api/v1/dataset/upload \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'dataset_id=your_dataset_id' \
  -F 'file=@document.pdf' \
  -F 'name=My Document' \
  -F 'description=Important reference document'
```

**Example cURL Alternative:**
```bash
curl --request POST \
     --url http://localhost:9380/api/v1/dataset/upload \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --form 'dataset_id=your_dataset_id' \
     --form 'file=@./test1.txt'
```

**Response:**
```json
{
  "code": 0,
  "message": "Upload successful",
  "data": {
    "file_id": "file_123456",
    "dataset_id": "dataset_789",
    "filename": "document.pdf",
    "size": 1024000,
    "status": "processing",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Upload Multiple Files
**Endpoint:** `POST /api/v1/dataset/upload_batch`

Upload multiple files to a dataset in a single request.

**Request Parameters:**
- `dataset_id` (required, string): ID of the target dataset
- Multiple `file` fields for batch upload
- Optional metadata for each file

**Example Request:**
```bash
curl -X POST \
  http://localhost:9380/api/v1/dataset/upload_batch \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'dataset_id=your_dataset_id' \
  -F 'file=@document1.pdf' \
  -F 'file=@document2.docx' \
  -F 'file=@document3.txt'
```

### 3. Upload with Advanced Options
**Endpoint:** `POST /api/v1/dataset/upload_with_options`

Upload files with advanced processing options.

**Additional Parameters:**
- `parser_method`: Choose parsing method
  - `auto`: Automatic detection (default)
  - `ocr`: OCR processing for scanned documents
  - `structured`: Process structured documents
  - `manual`: Manual parsing configuration
- `chunk_size`: Set chunk size for document processing (default: 512)
- `chunk_overlap`: Overlap between chunks (default: 50)
- `embedding_model`: Specify embedding model
- `process_options`: JSON object with advanced configuration

### 4. Upload to Dataset by ID
**Endpoint:** `POST /api/v1/datasets/{dataset_id}/documents`

Alternative endpoint for uploading documents to a specific dataset.

**Parameters:**
- `dataset_id` (path parameter): ID of the dataset
- `file` (required): File to upload
- `name` (optional): Document name
- `description` (optional): Document description

**Example Request:**
```bash
curl -X POST \
  http://localhost:9380/api/v1/datasets/dataset_123/documents \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'file=@document.pdf'
```

## Document Management

### 1. List Documents
**Endpoint:** `GET /api/v1/datasets/{dataset_id}/documents`

Retrieves a list of all documents in a dataset.

**Query Parameters:**
- `page` (optional, integer): Page number (default: 1)
- `size` (optional, integer): Page size (default: 20)
- `status` (optional, string): Filter by status (`processing`, `completed`, `failed`)

**Response:**
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "documents": [
      {
        "id": "doc_123",
        "name": "document.pdf",
        "size": 1024000,
        "status": "completed",
        "chunk_count": 45,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 2. Get Document Details
**Endpoint:** `GET /api/v1/documents/{document_id}`

Retrieves detailed information about a specific document.

**Response:**
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "id": "doc_123",
    "name": "document.pdf",
    "size": 1024000,
    "status": "completed",
    "chunk_count": 45,
    "parser_method": "auto",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "metadata": {}
  }
}
```

### 3. Delete Document
**Endpoint:** `DELETE /api/v1/documents/{document_id}`

Deletes a document from the system.

**Response:**
```json
{
  "code": 0,
  "message": "Document deleted successfully"
}
```

### 4. Parse Document
**Endpoint:** `POST /api/v1/documents/{document_id}/parse`

Triggers parsing of an uploaded document.

**Response:**
```json
{
  "code": 0,
  "message": "Parsing started",
  "data": {
    "document_id": "doc_123",
    "status": "parsing"
  }
}
```

## Dataset Operations

### 1. List Datasets
**Endpoint:** `GET /api/v1/datasets`

Retrieves a list of all datasets.

**Response:**
```json
{
  "code": 0,
  "message": "Success",
  "data": [
    {
      "id": "dataset_123",
      "name": "Knowledge Base",
      "description": "Main knowledge base",
      "document_count": 25,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 2. Create Dataset
**Endpoint:** `POST /api/v1/datasets`

Creates a new dataset.

**Request Body:**
```json
{
  "name": "New Dataset",
  "description": "Dataset description"
}
```

### 3. Get Dataset
**Endpoint:** `GET /api/v1/datasets/{dataset_id}`

Retrieves dataset information.

### 4. Update Dataset
**Endpoint:** `PUT /api/v1/datasets/{dataset_id}`

Updates dataset metadata.

### 5. Delete Dataset
**Endpoint:** `DELETE /api/v1/datasets/{dataset_id}`

Deletes a dataset and all its documents.

## Error Handling

RAGFlow API uses standard HTTP status codes and provides detailed error information.

### Error Response Format
```json
{
  "code": 101,
  "message": "No file part!",
  "data": null
}
```

### Common Error Codes
- `101`: No file part - File parameter missing or malformed
- `102`: Invalid dataset ID
- `103`: File too large
- `104`: Unsupported file format
- `105`: Dataset not found
- `106`: Permission denied
- `107`: Processing failed
- `108`: Document not found

## HTTP Status Codes

| Status | Description | Example Response |
|--------|-------------|------------------|
| `200` | Success | `{"code": 0, "message": "Success"}` |
| `201` | Created | `{"code": 0, "message": "Created successfully"}` |
| `400` | Bad Request | `{"code": 101, "message": "No file part!"}` |
| `401` | Unauthorized | `{"code": 102, "message": "Invalid API key"}` |
| `403` | Forbidden | `{"code": 106, "message": "Permission denied"}` |
| `404` | Not Found | `{"code": 105, "message": "Dataset not found"}` |
| `413` | Request Entity Too Large | `{"code": 103, "message": "File too large"}` |
| `500` | Internal Server Error | `{"code": 107, "message": "Processing failed"}` |

## Configuration

### File Size Limits
- Default maximum file size: 50MB
- Can be configured in RAGFlow settings
- Large files may be processed asynchronously

### Supported File Formats
- **Documents**: PDF, DOCX, DOC, TXT, MD, HTML, HTM
- **Spreadsheets**: CSV, XLSX, XLS
- **Presentations**: PPTX, PPT
- **Images**: JPG, JPEG, PNG, GIF, BMP (for OCR processing)
- **Structured Data**: JSON, XML

### Processing Options
- **Automatic Parsing**: Best effort automatic detection
- **OCR Processing**: For scanned documents and images
- **Structured Extraction**: For forms and tables
- **Custom Chunking**: Configurable chunk sizes and overlap

## Best Practices

### File Upload Recommendations
1. **Use the correct parameter name**: Always use `file` as the field name
2. **Include proper MIME types**: Let RAGFlow auto-detect when possible
3. **Handle large files**: Monitor upload status for large documents
4. **Error handling**: Check response codes and messages
5. **Retry logic**: Implement exponential backoff for failed uploads

### Example Python Code
```python
import requests

def upload_to_ragflow(api_key, dataset_id, file_path):
    url = "http://localhost:9380/api/v1/dataset/upload"

    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f)}
        data = {'dataset_id': dataset_id}

        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
```

### Monitoring Upload Progress
```python
def check_upload_status(api_key, dataset_id, upload_id):
    url = f"http://localhost:9380/api/v1/dataset/{dataset_id}/upload/{upload_id}/status"
    headers = {'Authorization': f'Bearer {api_key}'}

    response = requests.get(url, headers=headers)
    return response.json()
```

## API Versioning

- Current API version: `v1`
- Base URL: `http://your-ragflow-instance/api/v1`
- Version is included in the URL path
- Backward compatibility is maintained within major versions

## Rate Limiting

- API requests may be rate-limited
- Check your RAGFlow configuration for specific limits
- Implement appropriate retry logic for rate-limited requests

## Additional Resources

- **Official Documentation**: Check your RAGFlow instance at `/docs`
- **API Explorer**: Available at `/api/docs` in your RAGFlow installation
- **GitHub Repository**: [https://github.com/infiniflow/ragflow](https://github.com/infiniflow/ragflow)
- **Community Support**: Join the RAGFlow community for questions and support

---

*This documentation is based on RAGFlow RESTful API as of 2024-2025. For the most current information, always check your RAGFlow instance's built-in documentation.*