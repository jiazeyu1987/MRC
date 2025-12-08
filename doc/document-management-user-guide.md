# Knowledge Base Document Management User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Document Upload](#document-upload)
4. [Document Management](#document-management)
5. [Document Search and Retrieval](#document-search-and-retrieval)
6. [Test Conversations](#test-conversations)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

## Introduction

The Knowledge Base Document Management system allows you to upload, organize, and manage documents within your knowledge bases. This system integrates with RAGFlow to provide intelligent document processing, chunking, and retrieval-augmented generation capabilities.

### Key Features
- **Multi-format Support**: Upload PDFs, Word documents, text files, images, and more
- **Real-time Processing**: Track upload and processing progress in real-time
- **Intelligent Search**: Search within document content and retrieve relevant chunks
- **Document Organization**: Organize, filter, and manage your documents efficiently
- **Test Conversations**: Test your knowledge base with targeted document searches

### Supported File Types
- **Documents**: PDF, DOC, DOCX, TXT, MD, HTML, RTF
- **Images**: JPG, JPEG, PNG, GIF, BMP, SVG
- **Archives**: ZIP, RAR, 7Z, TAR, GZ
- **Videos**: MP4, AVI, MOV, WMV, FLV, WEBM
- **Data**: XML, JSON

## Getting Started

### Prerequisites
- Active RAGFlow instance with proper API configuration
- Sufficient storage space for document uploads
- Appropriate permissions for the knowledge base

### Accessing Document Management

1. **Navigate to Knowledge Base Management**
   - Go to the Knowledge Base tab in your MRC dashboard
   - Select the knowledge base you want to manage documents for

2. **Document Management Section**
   - The Document Management section appears above the Test Conversation area
   - You'll see options to upload documents or view existing document lists

## Document Upload

### Upload Methods

#### Method 1: Drag and Drop (Recommended)
1. Click the **"上传文档"** button or navigate to the upload interface
2. Drag files directly from your computer into the drop zone
3. Release the files to start uploading

#### Method 2: File Selection
1. Click anywhere in the drop zone area
2. Select files from your computer's file browser
3. Click "Open" to start uploading

### Upload Limits and Requirements
- **Maximum file size**: 50MB per file
- **Maximum concurrent uploads**: 10 files
- **Security scanning**: All files are scanned for security threats
- **File validation**: Only supported file types are accepted

### Upload Process

1. **File Validation** (Instant)
   - File type checking
   - Size validation
   - Security scan initiation

2. **Upload Progress** (Real-time)
   - Progress bar shows upload percentage
   - Upload speed and time remaining
   - Can pause/resume or cancel uploads

3. **RAGFlow Processing** (Background)
   - Document parsing and analysis
   - Content extraction and chunking
   - Index creation for search

4. **Completion**
   - Processing complete notification
   - Document available in list and search

### Managing Upload Queue

**View Active Uploads**
- Each upload shows:
  - File name and size
  - Current progress (0-100%)
  - Status (uploading, processing, completed, error)
  - Action buttons (pause, cancel, retry)

**Upload Actions**
- **Pause**: Temporarily stop an upload (can be resumed)
- **Cancel**: Stop and remove an upload
- **Retry**: Restart a failed upload
- **Remove**: Clear completed or failed uploads from the queue

## Document Management

### Document List View

**Access Document List**
1. From Document Management section, click **"文档列表"**
2. View all documents in your knowledge base

**List Features**
- **Search**: Search by document filename
- **Filters**: Filter by status, file type, processing state
- **Sorting**: Sort by name, date, size, or status
- **View Modes**: Toggle between list and grid views
- **Pagination**: Navigate through large document sets

### Document Information

Each document card displays:
- **Filename**: Original file name
- **File Size**: Human-readable size format (KB, MB, GB)
- **Status**: Current processing status with color indicator
- **File Type**: File type icon and label
- **Upload Date**: When the document was uploaded
- **Chunk Count**: Number of searchable chunks created

### Document Status Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| 🟢 已完成 | Green | Document fully processed and searchable |
| 🔵 处理中 | Blue | Currently being processed in RAGFlow |
| 🟡 等待处理 | Yellow | Uploaded, waiting for processing |
| 🔴 上传中 | Red | File is currently uploading |
| ❌ 失败 | Red | Error during upload or processing |

### Document Actions

**View Document Details**
- Click the eye icon 👁️ to view document details
- See metadata, processing logs, and chunks

**Delete Document**
- Click the trash icon 🗑️ to delete a document
- Confirm deletion in the dialog
- Document and all chunks are permanently removed

### Batch Operations

**Select Multiple Documents**
- Use checkboxes to select multiple documents
- Select all checkbox in the header for bulk selection

**Batch Actions**
- **Delete**: Remove selected documents in bulk
- Clear selection when done

## Document Search and Retrieval

### Search Within Knowledge Base

**Global Document Search**
1. Go to Document List view
2. Use the search bar at the top
3. Enter search terms to find documents by name
4. Results update in real-time

**Advanced Search Options**
- Filter by file type (PDF, DOC, TXT, etc.)
- Filter by processing status
- Sort results by relevance, date, or size

### Chunk Content Search

**Access Document View**
1. Click on a document to open detailed view
2. Switch to "文档块" tab
3. Use the search bar to search within document content

**Search Features**
- **Real-time Results**: Search results appear as you type
- **Chunk Highlighting**: Relevant chunks are highlighted
- **Context Display**: See surrounding content for each match
- **Chunk Expansion**: Click to view full chunk content
- **Relevance Scoring**: Results ranked by relevance to search query

### Search Results

**Chunk Information**
- **Chunk Index**: Position in document
- **Content Preview**: First part of chunk content
- **Word/Character Count**: Size of the chunk
- **Creation Time**: When chunk was created
- **Actions**: Copy content, view full text

**Result Actions**
- **Copy**: Copy chunk content to clipboard
- **Expand**: View full chunk content
- **View Metadata**: See processing information

## Test Conversations

### Document-Aware Conversations

**Start a Test Conversation**
1. From Knowledge Base Details, go to Test Conversation section
2. Click the **"选择文档"** button to select specific documents
3. Search and select documents you want to reference
4. Ask questions about the selected documents

**Document Selection Features**
- **Search Documents**: Find documents by name
- **Multi-Selection**: Select multiple documents for focused responses
- **Selection Counter**: See how many documents are selected
- **Clear Selection**: Remove all selected documents

### Enhanced Conversation Features

**Document Context**
- Selected documents are mentioned in conversation context
- Responses prioritize information from selected documents
- More focused and relevant answers

**Reference Tracking**
- See which documents were used in responses
- View specific chunks that informed the answer
- Confidence scores for each reference

### Conversation History

**View Past Conversations**
- Access conversation history from the knowledge base
- See questions, answers, and used documents
- Export conversation data for analysis

## Advanced Features

### Document Analytics

**View Document Statistics**
1. Go to Document List view
2. Check the statistics panel at the bottom
3. See:
   - Total documents count
   - Total storage used
   - Processing status breakdown
   - File type distribution

### Processing Logs

**Access Processing Information**
1. Open Document View for any document
2. Go to "基本信息" tab
3. Review:
   - Upload and processing timestamps
   - Processing status and duration
   - Error messages (if any)
   - RAGFlow metadata

### File Format Conversion

**Automatic Processing**
- Documents are automatically processed by RAGFlow
- Content extraction and text recognition
- Image OCR for scanned documents
- Format normalization for consistent processing

### Integration Features

**RAGFlow Synchronization**
- Documents synced with RAGFlow datasets
- Real-time status updates from RAGFlow
- Automatic retry on processing failures

**API Access**
- RESTful API for programmatic document management
- WebSocket support for real-time progress tracking
- Webhook support for processing completion events

## Troubleshooting

### Common Issues

#### Upload Failures

**Problem**: File upload fails immediately
**Solutions**:
- Check file size (must be under 50MB)
- Verify file type is supported
- Ensure you have proper permissions
- Check internet connection stability

**Problem**: Upload gets stuck during processing
**Solutions**:
- Processing time depends on file size and complexity
- Large PDFs may take several minutes
- Check RAGFlow service status
- Retry after waiting a few minutes

#### Search Issues

**Problem**: Search returns no results
**Solutions**:
- Ensure documents are fully processed (status: 已完成)
- Check spelling of search terms
- Try different keywords from the document
- Verify document content was properly extracted

**Problem**: Search results are not relevant
**Solutions**:
- Use more specific search terms
- Try different word variations
- Check if document content was properly OCR'd
- Consider re-uploading problematic documents

#### Processing Errors

**Problem**: Document shows failed status
**Solutions**:
- Check error message in document details
- Try re-uploading the file
- Ensure file is not password protected
- Verify file is not corrupted

### Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "File size exceeds limit" | File > 50MB | Compress file or split into smaller parts |
| "Unsupported file type" | Invalid file extension | Convert to supported format |
| "Security scan failed" | Suspicious content | Check file for viruses/malware |
| "RAGFlow processing failed" | RAGFlow error | Check RAGFlow service status |
| "Storage quota exceeded" | Storage limit reached | Delete unused documents |

### Performance Optimization

**Improve Upload Speed**
- Use a stable internet connection
- Upload files during off-peak hours
- Compress large files before upload
- Close other bandwidth-intensive applications

**Optimize Search Performance**
- Use specific search terms
- Limit search results when possible
- Clear browser cache regularly
- Use filters to narrow search scope

## Best Practices

### File Management

**Before Upload**
- Organize files with clear naming conventions
- Remove sensitive information from documents
- Compress large files when possible
- Verify file integrity before upload

**During Upload**
- Upload related documents together
- Monitor progress for large files
- Keep uploads organized by project or topic
- Use descriptive filenames for easy searching

**After Upload**
- Verify documents processed successfully
- Test search functionality with uploaded content
- Organize documents using consistent naming
- Regular cleanup of unused or outdated documents

### Search Optimization

**Effective Search Terms**
- Use specific keywords from the document
- Include technical terms and proper nouns
- Try variations of search terms
- Use quotes for exact phrases

**Search Strategies**
- Start broad, then narrow down
- Use filters to reduce result scope
- Check document context for related terms
- Review chunk content for detailed information

### System Maintenance

**Regular Tasks**
- Monitor storage usage and quotas
- Review processing logs for errors
- Update document metadata when needed
- Backup important conversations and data

**Performance Monitoring**
- Track upload and processing times
- Monitor search result quality
- Check system resource usage
- Review error rates and patterns

## FAQ

### General Questions

**Q: What happens to my documents after upload?**
A: Documents are processed by RAGFlow, which extracts text content, creates searchable chunks, and indexes them for retrieval. The original files are stored securely and can be deleted if needed.

**Q: Can I edit documents after upload?**
A: Documents cannot be directly edited after upload. To modify content, delete the original document and upload the updated version.

**Q: How long does document processing take?**
A: Processing time varies by file size and complexity:
- Small text files: 1-2 minutes
- Medium PDFs (10-50 pages): 5-10 minutes
- Large PDFs (50+ pages): 10-30 minutes

**Q: Is my data secure?**
A: Yes, all documents are encrypted during transmission and storage. RAGFlow processing follows security best practices, and you can delete documents at any time.

### Technical Questions

**Q: What file formats are best for search accuracy?**
A: Text-based formats (TXT, MD, DOCX) provide the best search accuracy. PDFs work well if they contain text content, while images may require OCR processing.

**Q: Can I upload password-protected documents?**
A: No, password-protected files cannot be processed. Remove password protection before uploading.

**Q: How many documents can I upload?**
A: There's no hard limit on document count, but storage quotas may apply. Monitor your storage usage in the statistics panel.

**Q: What happens if RAGFlow is down?**
A: Documents will be uploaded but won't be processed until RAGFlow is available. Processing will resume automatically when the service is restored.

### Troubleshooting Questions

**Q: Why is my document stuck in "processing" status?**
A: This usually indicates RAGFlow is processing the document. Large files or complex formats take longer. Wait and check again later.

**Q: Search results are not finding content I know exists. What should I do?**
A: First, ensure the document shows "已完成" status. If it does, try different keywords or check if the content was properly extracted during processing.

**Q: My upload failed with a "security scan" error. What does this mean?**
A: The file contains potentially malicious content. Scan your local file for viruses and ensure it's safe before attempting to upload again.

**Q: Can I upload the same file multiple times?**
A: Yes, but it's not recommended as it creates duplicate entries. If you need to update a document, delete the old one first.

### Integration Questions

**Q: Can I access documents via API?**
A: Yes, comprehensive REST APIs are available for document management, search, and progress tracking. See the API documentation for details.

**Q: How do I get real-time upload progress?**
A: Use the WebSocket endpoint for real-time progress updates, or periodically poll the progress endpoint.

**Q: Can I integrate with external document management systems?**
A: Yes, the API supports integration with external systems. Webhooks are available for processing completion events.

For additional support:
- **Email**: support@yourcompany.com
- **Documentation**: https://docs.yourcompany.com
- **Community Forum**: https://community.yourcompany.com