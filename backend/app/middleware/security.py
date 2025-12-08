"""
Security Middleware for Document Management System

This module implements security middleware including rate limiting,
CSRF protection, security headers, and input validation.

Author: Knowledge Base Document Management System
Version: 1.0.0
"""

import os
import hashlib
import time
import re
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Callable

from flask import request, g, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import jwt
from werkzeug.utils import secure_filename

# Security headers configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
}

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

# Rate limiting storage
try:
    rate_limiter_storage = redis.from_url(
        os.environ.get('REDIS_URL', 'redis://localhost:6379'),
        decode_responses=True
    )
    rate_limiter_available = True
except (redis.ConnectionError, ImportError):
    rate_limiter_storage = None
    rate_limiter_available = False

# Initialize rate limiter
if rate_limiter_available:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=os.environ.get('REDIS_URL', 'redis://localhost:6379')
    )
else:
    limiter = None


class SecurityHeaders:
    """Security headers middleware."""

    @staticmethod
    def add_headers(response):
        """Add security headers to response."""
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        response.headers['Content-Security-Policy'] = CSP_POLICY
        return response


class InputValidator:
    """Input validation utilities."""

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'<?php',
        r'<%',
        r'<%',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'shell_exec\s*\(',
        r'passthru\s*\(',
        r'base64_decode',
        r'unserialize\s*\(',
        r'file_get_contents\s*\(',
        r'fopen\s*\(',
        r'file_put_contents\s*\(',
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(\\;))(\s)*(union|select|insert|update|delete|drop|create|alter|exec|execute)",
        r"(\*\|)|(\|)",
        r"(--|#)",
        r"/\*.*\*/",
    ]

    @classmethod
    def validate_string(cls, input_string: str, max_length: int = 1000) -> bool:
        """Validate string input for dangerous patterns."""
        if not isinstance(input_string, str):
            return False

        if len(input_string) > max_length:
            return False

        # Check for dangerous patterns (case insensitive)
        input_lower = input_string.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE | re.DOTALL):
                return False

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                return False

        return True

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        if not filename:
            return "unnamed_file"

        # Use Werkzeug's secure_filename
        safe_name = secure_filename(filename)

        # Additional sanitization
        safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')

        # Ensure filename is not empty
        if not safe_name or safe_name.startswith('.'):
            safe_name = f"file_{safe_name or 'unnamed'}"

        return safe_name[:255]  # Limit length

    @classmethod
    def validate_file_content(cls, content: bytes) -> bool:
        """Validate file content for malicious patterns."""
        if not content:
            return True

        # Convert to string for pattern matching
        try:
            content_str = content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            # Binary file, check specific binary signatures
            return cls._validate_binary_content(content)

        content_lower = content_str.lower()

        # Check for dangerous patterns in first 10KB
        content_sample = content_lower[:10240]
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, content_sample, re.IGNORECASE | re.DOTALL):
                return False

        return True

    @staticmethod
    def _validate_binary_content(content: bytes) -> bool:
        """Validate binary file content."""
        # Check file signatures
        dangerous_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'PK\x03\x04',  # ZIP archive (could contain executables)
        ]

        for signature in dangerous_signatures:
            if content.startswith(signature):
                return False

        return True


class CSRFProtection:
    """CSRF protection middleware."""

    @staticmethod
    def generate_token() -> str:
        """Generate CSRF token."""
        return hashlib.sha256(
            f"{os.urandom(32)}{time.time()}".encode()
        ).hexdigest()

    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate CSRF token."""
        if not token:
            return False

        # Store tokens in Redis with expiration
        if rate_limiter_storage:
            stored = rate_limiter_storage.get(f"csrf:{token}")
            return bool(stored)

        return True

    @staticmethod
    def store_token(token: str, expiration: int = 3600):
        """Store CSRF token in Redis."""
        if rate_limiter_storage:
            rate_limiter_storage.setex(f"csrf:{token}", expiration, "1")


class RateLimitProtection:
    """Rate limiting protection."""

    @staticmethod
    def get_client_ip() -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_ips = [
            request.headers.get('X-Forwarded-For'),
            request.headers.get('X-Real-IP'),
            request.remote_addr
        ]

        for ip in forwarded_ips:
            if ip:
                # Get first IP in comma-separated list
                ip = ip.split(',')[0].strip()
                if ip and ip != 'unknown':
                    return ip

        return 'unknown'

    @staticmethod
    def check_rate_limit(key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded."""
        if not rate_limiter_storage:
            return True  # Allow if Redis not available

        client_key = f"rate_limit:{key}"
        current_count = rate_limiter_storage.get(client_key)

        if current_count is None:
            # First request in window
            rate_limiter_storage.setex(client_key, window, 1)
            return True
        else:
            current_count = int(current_count)
            if current_count >= limit:
                return False
            else:
                rate_limiter_storage.incr(client_key)
                return True


class SecurityMiddleware:
    """Main security middleware."""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

        # Configure security settings
        app.config.update({
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=1)
        })

    def before_request(self):
        """Execute before each request."""
        g.security_validated = False

        # Skip security checks for health checks
        if request.endpoint == 'health_check':
            return

        # Validate request size
        if request.content_length:
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)  # 50MB
            if request.content_length > max_size:
                return jsonify({
                    'success': False,
                    'message': 'Request entity too large'
                }), 413

        # Validate JSON input
        if request.is_json and request.get_json():
            if not self._validate_json_input(request.get_json()):
                return jsonify({
                    'success': False,
                    'message': 'Invalid input detected'
                }), 400

        # Rate limiting
        client_ip = RateLimitProtection.get_client_ip()
        endpoint_key = f"{client_ip}:{request.endpoint}"

        # Different rate limits for different endpoints
        if request.endpoint and 'upload' in request.endpoint:
            if not RateLimitProtection.check_rate_limit(endpoint_key, 5, 60):  # 5 uploads per minute
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded for uploads'
                }), 429
        elif request.endpoint and 'search' in request.endpoint:
            if not RateLimitProtection.check_rate_limit(endpoint_key, 60, 60):  # 60 searches per minute
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded for searches'
                }), 429
        else:
            if not RateLimitProtection.check_rate_limit(endpoint_key, 200, 60):  # 200 requests per minute
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded'
                }), 429

        g.security_validated = True

    def after_request(self, response):
        """Execute after each request."""
        # Add security headers
        response = SecurityHeaders.add_headers(response)

        # Remove server information
        response.headers.pop('Server', None)

        return response

    def _validate_json_input(self, data: dict) -> bool:
        """Validate JSON input for dangerous content."""
        if not isinstance(data, dict):
            return False

        for key, value in data.items():
            if isinstance(value, str) and not InputValidator.validate_string(value):
                return False
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and not InputValidator.validate_string(item):
                        return False

        return True


def security_decorator(allowed_methods: List[str] = None):
    """Security decorator for API endpoints."""
    if allowed_methods is None:
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Validate request method
            if request.method not in allowed_methods:
                return jsonify({
                    'success': False,
                    'message': 'Method not allowed'
                }), 405

            # Check if security validation passed
            if not getattr(g, 'security_validated', False):
                return jsonify({
                    'success': False,
                    'message': 'Security validation failed'
                }), 403

            # CSRF protection for state-changing requests
            if request.method in ['POST', 'PUT', 'DELETE']:
                csrf_token = request.headers.get('X-CSRF-Token')
                if not CSRFProtection.validate_token(csrf_token):
                    return jsonify({
                        'success': False,
                        'message': 'Invalid CSRF token'
                    }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def validate_file_upload(f: Callable) -> Callable:
    """Decorator for file upload validation."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400

        file = request.files['file']

        if not file or not file.filename:
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400

        # Validate filename
        safe_filename = InputValidator.sanitize_filename(file.filename)
        if safe_filename != file.filename:
            return jsonify({
                'success': False,
                'message': 'Invalid filename'
            }), 400

        # Validate file size
        max_size = current_app.config.get('MAX_FILE_SIZE', 50 * 1024 * 1024)  # 50MB
        if file.content_length > max_size:
            return jsonify({
                'success': False,
                'message': 'File too large'
            }), 413

        # Validate file content
        file_content = file.read(1024 * 1024)  # Read first 1MB for validation
        file.seek(0)  # Reset file position

        if not InputValidator.validate_file_content(file_content):
            return jsonify({
                'success': False,
                'message': 'File content validation failed'
            }), 400

        return f(*args, **kwargs)

    return decorated_function


class SecurityAuditLogger:
    """Security audit logger."""

    def __init__(self):
        self.log_file = current_app.config.get('SECURITY_LOG_FILE', 'security.log')

    def log_security_event(self, event_type: str, details: dict, severity: str = 'INFO'):
        """Log security-related events."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'ip_address': RateLimitProtection.get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'endpoint': request.endpoint,
            'method': request.method,
            'details': details
        }

        try:
            with open(self.log_file, 'a') as f:
                f.write(f"{event}\n")
        except Exception as e:
            current_app.logger.error(f"Failed to write security log: {e}")

        # Also log to application logger
        if severity == 'HIGH':
            current_app.logger.error(f"Security Event: {event_type} - {details}")
        elif severity == 'MEDIUM':
            current_app.logger.warning(f"Security Event: {event_type} - {details}")
        else:
            current_app.logger.info(f"Security Event: {event_type} - {details}")

    def log_access_denied(self, resource: str, user_id: str = None):
        """Log access denied events."""
        self.log_security_event(
            'ACCESS_DENIED',
            {
                'resource': resource,
                'user_id': user_id,
                'query_params': dict(request.args)
            },
            'MEDIUM'
        )

    def log_input_validation_failed(self, input_type: str, input_value: str):
        """Log input validation failures."""
        self.log_security_event(
            'INPUT_VALIDATION_FAILED',
            {
                'input_type': input_type,
                'input_value_preview': input_value[:100] + '...' if len(input_value) > 100 else input_value
            },
            'HIGH'
        )

    def log_rate_limit_exceeded(self, endpoint: str):
        """Log rate limit exceeded events."""
        self.log_security_event(
            'RATE_LIMIT_EXCEEDED',
            {
                'endpoint': endpoint
            },
            'MEDIUM'
        )


# Global security audit logger
security_audit_logger = SecurityAuditLogger()

# Export main security middleware
__all__ = [
    'SecurityMiddleware',
    'security_decorator',
    'validate_file_upload',
    'InputValidator',
    'CSRFProtection',
    'RateLimitProtection',
    'security_audit_logger'
]