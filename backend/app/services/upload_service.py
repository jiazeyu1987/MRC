"""
Upload Service - Handle file upload operations with validation and progress tracking.

This service provides secure file upload functionality with validation, security scanning,
and real-time progress tracking through WebSocket integration.
"""

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional, BinaryIO
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from app import db
from app.models.document import Document
from app.models.processing_log import ProcessingLog
from app.services.document_service import DocumentService
from app.services.ragflow_service import RAGFlowService
from app.services.security_service import SecurityService
# ProgressService will be created in Task 12
# from app.services.progress_service import ProgressService
import logging

logger = logging.getLogger(__name__)

class UploadService:
    def __init__(self):
        self.document_service = DocumentService()
        self.ragflow_service = RAGFlowService()
        self.security_service = SecurityService()
        # ProgressService will be initialized when available
        self.progress_service = None
        self._init_config()

    def _update_progress(self, upload_id: str, progress: int, message: str = None):
        """Update progress if ProgressService is available."""
        if self.progress_service:
            self.progress_service.update_progress(upload_id, progress, message)
        else:
            logger.debug(f"Progress {progress}%: {message} (upload_id: {upload_id})")

    def _start_upload_tracking(self, upload_id: str, file_info: Any = None):
        """Start upload tracking if ProgressService is available."""
        if self.progress_service:
            self.progress_service.start_upload_tracking(upload_id, file_info)
        else:
            logger.info(f"Started upload tracking for {upload_id} (no progress service)")

    def _set_upload_document_id(self, upload_id: str, document_id: str):
        """Set document ID for upload tracking if ProgressService is available."""
        if self.progress_service:
            if hasattr(self.progress_service, 'active_uploads'):
                if upload_id in self.progress_service.active_uploads:
                    self.progress_service.active_uploads[upload_id]['document_id'] = document_id
        else:
            logger.debug(f"Set document ID {document_id} for upload {upload_id}")

    def _get_upload_status(self, upload_id: str):
        """Get upload status if ProgressService is available."""
        if self.progress_service:
            return self._get_upload_status(upload_id)
        else:
            return {
                'upload_id': upload_id,
                'status': 'unknown',
                'progress': 0,
                'message': 'Progress tracking not available'
            }

    def _cancel_upload(self, upload_id: str):
        """Cancel upload if ProgressService is available."""
        if self.progress_service:
            self._cancel_upload(upload_id)
        else:
            logger.info(f"Cancel upload {upload_id} (no progress service)")

    def _init_config(self):
        """Initialize configuration."""
        # Configuration
        self.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        self.ALLOWED_EXTENSIONS = {
            'pdf', 'doc', 'docx', 'txt', 'md', 'html', 'htm', 'rtf',
            'jpg', 'jpeg', 'png', 'gif', 'bmp'  # Include images
        }
        self.UPLOAD_FOLDER = 'uploads/documents'
        self.SCANNED_FOLDER = 'uploads/scanned'

        # Ensure upload directories exist
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.SCANNED_FOLDER, exist_ok=True)

    def validate_file(self, file: FileStorage) -> Dict[str, Any]:
        """
        Validate uploaded file for type, size, and security.

        Args:
            file: FileStorage object from Flask request

        Returns:
            Dictionary with validation result and details
        """
        validation_result = {
            'valid': False,
            'error': None,
            'file_info': {}
        }

        try:
            if not file or not file.filename:
                validation_result['error'] = "No file selected"
                return validation_result

            # Get file information
            filename = file.filename
            file_size = 0
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Seek back to beginning

            validation_result['file_info'] = {
                'original_filename': filename,
                'file_size': file_size,
                'content_type': file.content_type
            }

            # Check file size
            if file_size > self.MAX_FILE_SIZE:
                validation_result['error'] = f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size (50MB)"
                return validation_result

            if file_size == 0:
                validation_result['error'] = "File is empty"
                return validation_result

            # Check file extension
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_extension not in self.ALLOWED_EXTENSIONS:
                validation_result['error'] = f"File type '.{file_extension}' is not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
                return validation_result

            # Validate MIME type
            detected_mime, _ = mimetypes.guess_type(filename)
            if detected_mime and detected_mime not in self._get_allowed_mime_types():
                validation_result['error'] = f"Detected MIME type '{detected_mime}' is not allowed"
                return validation_result

            # Security scan
            scan_result = self.security_service.scan_file_content(file.read(1024))  # Read first 1KB for scanning
            file.seek(0)  # Reset file pointer

            if not scan_result['safe']:
                validation_result['error'] = f"Security scan failed: {scan_result['reason']}"
                return validation_result

            validation_result['valid'] = True
            return validation_result

        except Exception as e:
            logger.error(f"Error validating file {file.filename if file else 'Unknown'}: {e}")
            validation_result['error'] = f"Validation error: {str(e)}"
            return validation_result

    def process_upload(self, file: FileStorage, knowledge_base_id: str, upload_id: str = None) -> Dict[str, Any]:
        """
        Process file upload with validation, storage, and RAGFlow integration.

        Args:
            file: FileStorage object from Flask request
            knowledge_base_id: ID of the target knowledge base
            upload_id: Optional upload ID for progress tracking

        Returns:
            Dictionary with upload result and document details
        """
        if not upload_id:
            upload_id = str(uuid.uuid4())

        try:
            # Start progress tracking (if available)
            self._start_upload_tracking(upload_id, None)
            self._update_progress(upload_id, 0, "Validating file...")

            # Validate file
            validation_result = self.validate_file(file)
            if not validation_result['valid']:
                self._update_progress(upload_id, 100, f"Upload failed: {validation_result['error']}")
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'upload_id': upload_id
                }

            original_filename = validation_result['file_info']['original_filename']
            file_size = validation_result['file_info']['file_size']

            # Generate secure filename
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            secure_name = secure_filename(original_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{secure_name}" if secure_name else f"{timestamp}_document.{file_extension}"

            self._update_progress(upload_id, 10, "Saving file...")

            # Save file to temporary storage
            file_path = os.path.join(self.UPLOAD_FOLDER, filename)
            file.save(file_path)
            logger.info(f"File saved to: {file_path}")

            self._update_progress(upload_id, 20, "Creating document record...")

            # Create document record
            document = self.document_service.create_document(
                knowledge_base_id=knowledge_base_id,
                filename=filename,
                original_filename=original_filename,
                file_size=file_size,
                file_type=file_extension,
                mime_type=validation_result['file_info']['content_type']
            )

            # Update progress tracking with document ID
            self._set_upload_document_id(upload_id, document.id)
            self._update_progress(upload_id, 30, "Uploading to RAGFlow...")

            # Upload to RAGFlow
            try:
                with open(file_path, 'rb') as f:
                    ragflow_result = self.ragflow_service.upload_document_to_dataset(
                        knowledge_base_id, f, original_filename
                    )

                if ragflow_result.get('success'):
                    document.ragflow_document_id = ragflow_result.get('document_id')
                    document.update_status(upload_status='uploaded')
                    logger.info(f"Document {document.id} uploaded to RAGFlow: {ragflow_result.get('document_id')}")
                else:
                    logger.error(f"RAGFlow upload failed: {ragflow_result.get('error')}")
                    document.update_status(upload_status='failed', error_message=ragflow_result.get('error'))

                self._update_progress(upload_id, 60, "Processing with RAGFlow...")

                # Trigger document parsing
                if document.ragflow_document_id:
                    parse_result = self.ragflow_service.parse_document(document.ragflow_document_id)
                    if parse_result.get('success'):
                        document.update_status(processing_status='processing')
                        ProcessingLog.start_step(document.id, 'parse', 'Document parsing initiated')
                    else:
                        logger.error(f"Document parsing failed: {parse_result.get('error')}")

                self._update_progress(upload_id, 80, "Cleaning up...")

            except Exception as e:
                logger.error(f"RAGFlow integration error: {e}")
                document.update_status(processing_status='failed', error_message=str(e))

            # Clean up temporary file
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {e}")

            self._update_progress(upload_id, 100, "Upload completed")

            result = {
                'success': True,
                'document_id': document.id,
                'upload_id': upload_id,
                'document': document.to_dict()
            }

            logger.info(f"Upload completed successfully for document {document.id}")
            return result

        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            if upload_id:
                self._update_progress(upload_id, 100, f"Upload failed: {str(e)}")

            return {
                'success': False,
                'error': str(e),
                'upload_id': upload_id
            }

    def get_upload_status(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """
        Get upload progress and status.

        Args:
            upload_id: Upload session ID

        Returns:
            Upload status dictionary or None if not found
        """
        return self._get_upload_status(upload_id)

    def cancel_upload(self, upload_id: str) -> bool:
        """
        Cancel an ongoing upload.

        Args:
            upload_id: Upload session ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get upload info before cancelling
            upload_info = self._get_upload_status(upload_id)
            if not upload_info:
                return False

            # Cancel any processing logs
            document_id = upload_info.get('document_id')
            if document_id:
                current_log = ProcessingLog.get_current_step(document_id)
                if current_log:
                    current_log.cancel()

            # Cancel progress tracking
            self._cancel_upload(upload_id)

            logger.info(f"Upload {upload_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Error cancelling upload {upload_id}: {e}")
            return False

    def get_supported_file_types(self) -> Dict[str, Any]:
        """
        Get information about supported file types and limits.

        Returns:
            Dictionary with file type information
        """
        return {
            'allowed_extensions': sorted(self.ALLOWED_EXTENSIONS),
            'max_file_size_bytes': self.MAX_FILE_SIZE,
            'max_file_size_mb': self.MAX_FILE_SIZE / (1024 * 1024),
            'allowed_mime_types': sorted(self._get_allowed_mime_types())
        }

    def _get_allowed_mime_types(self) -> set:
        """Get set of allowed MIME types."""
        return {
            # Documents
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/markdown',
            'text/html',
            'text/htm',
            'application/rtf',
            # Images
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/webp'
        }

    def cleanup_temporary_files(self, hours_old: int = 24) -> int:
        """
        Clean up temporary files older than specified hours.

        Args:
            hours_old: Age in hours for file deletion

        Returns:
            Number of files cleaned up
        """
        try:
            import time
            cutoff_time = time.time() - (hours_old * 3600)
            cleaned_count = 0

            for folder in [self.UPLOAD_FOLDER, self.SCANNED_FOLDER]:
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove temporary file {file_path}: {e}")

            logger.info(f"Cleaned up {cleaned_count} temporary files older than {hours_old} hours")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
            return 0