"""
Input Validation and Security Middleware for Cartrita AI OS
Provides comprehensive input validation, sanitization, and security checks
"""

import html
import json
import mimetypes
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from urllib.parse import quote, unquote

import bleach
import magic
import sqlparse
import structlog
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


@dataclass
class ValidationRule:
    """Input validation rule configuration"""

    name: str
    pattern: str
    message: str
    severity: str = "HIGH"
    enabled: bool = True


@dataclass
class SecurityViolation:
    """Security violation detected during validation"""

    rule_name: str
    violation_type: str
    input_field: str
    input_value: str
    severity: str
    message: str
    timestamp: str
    client_ip: str
    user_agent: str


class InputSanitizer:
    """Comprehensive input sanitization"""

    # Dangerous patterns to detect and block
    SECURITY_PATTERNS = {
        "sql_injection": [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|EXECUTE)\b)",
            r"(--|\|\||;|/\*|\*/)",
            r"(\b(OR|AND)\b.*?[=<>].*?(\b(OR|AND)\b|$))",
            r"(\b(admin|root|sys|dbo)\b.*?[='])",
            r"(1=1|0=0|true=true|false=false)",
        ],
        "xss_injection": [
            r"(<script[^>]*>.*?</script>)",
            r"(<iframe[^>]*>.*?</iframe>)",
            r"(<object[^>]*>.*?</object>)",
            r"(<embed[^>]*>)",
            r"(javascript:|vbscript:|onload=|onerror=|onclick=)",
            r"(<img[^>]*src=[^>]*>)",
        ],
        "command_injection": [
            r"(\||&|;|`|\$\(|\${)",
            r"(rm\s+-rf|del\s+/|format\s+c:)",
            r"(cat\s+/etc/passwd|type\s+%WINDIR%)",
            r"(wget|curl).*?(http|https|ftp)://",
            r"(nc\s+|netcat\s+|telnet\s+)",
        ],
        "path_traversal": [
            r"(\.\.\/|\.\.\\)",
            r"(%2e%2e%2f|%2e%2e%5c)",
            r"(\/etc\/passwd|\/etc\/shadow)",
            r"(%252e%252e%252f|%c0%ae%c0%ae%c0%af)",
        ],
        "nosql_injection": [
            r"(\$where|\$ne|\$gt|\$lt|\$regex|\$exists)",
            r"({\s*\$.*?:.*?})",
            r"(Object\s*\.\s*keys|this\s*\.\s*)",
        ],
        "ldap_injection": [
            r"(\*|\|\&|\!|\=|\>|\<|\~)",
            r"(objectClass=|cn=|uid=|ou=)",
        ],
        "template_injection": [
            r"({{.*?}}|\${.*?}|<%.*?%>)",
            r"(__import__|exec|eval|compile)",
            r"(config\.|self\.|request\.)",
        ],
    }

    # Allowed HTML tags and attributes for content sanitization
    ALLOWED_HTML_TAGS = [
        "p",
        "br",
        "strong",
        "em",
        "u",
        "i",
        "b",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "code",
        "pre",
    ]

    ALLOWED_HTML_ATTRIBUTES = {
        "*": ["class", "id"],
        "a": ["href", "title"],
        "img": ["src", "alt", "title", "width", "height"],
    }

    def __init__(self):
        """Initialize the input sanitizer"""
        self.violations: List[SecurityViolation] = []

    def detect_security_violations(
        self,
        input_value: str,
        field_name: str = "unknown",
        client_ip: str = "unknown",
        user_agent: str = "unknown",
    ) -> List[SecurityViolation]:
        """
        Detect security violations in input

        Args:
            input_value: The input to validate
            field_name: Name of the field being validated
            client_ip: Client IP address
            user_agent: Client user agent

        Returns:
            List of security violations found
        """
        violations = []

        for violation_type, patterns in self.SECURITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, input_value, re.IGNORECASE | re.MULTILINE)
                if matches:
                    violation = SecurityViolation(
                        rule_name=f"{violation_type}_detection",
                        violation_type=violation_type,
                        input_field=field_name,
                        input_value=input_value[:100],  # Truncate for logging
                        severity="HIGH",
                        message=f"Detected {violation_type} pattern: {pattern}",
                        timestamp=str(datetime.utcnow().isoformat()),
                        client_ip=client_ip,
                        user_agent=user_agent,
                    )
                    violations.append(violation)

                    logger.warning(
                        "Security violation detected",
                        violation_type=violation_type,
                        field=field_name,
                        client_ip=client_ip,
                        pattern_matched=pattern,
                    )

        return violations

    def sanitize_html_content(self, content: str) -> str:
        """
        Sanitize HTML content to remove dangerous elements

        Args:
            content: HTML content to sanitize

        Returns:
            Sanitized HTML content
        """
        if not content:
            return content

        # Use bleach to sanitize HTML
        sanitized = bleach.clean(
            content,
            tags=self.ALLOWED_HTML_TAGS,
            attributes=self.ALLOWED_HTML_ATTRIBUTES,
            strip=True,
        )

        # Additional escaping for safety
        sanitized = html.escape(sanitized, quote=False)

        return sanitized

    def sanitize_sql_input(self, sql_input: str) -> str:
        """
        Sanitize SQL input to prevent injection

        Args:
            sql_input: SQL input to sanitize

        Returns:
            Sanitized SQL input
        """
        if not sql_input:
            return sql_input

        # Parse and validate SQL
        try:
            parsed = sqlparse.parse(sql_input)
            # Only allow SELECT statements
            for statement in parsed:
                if not statement.get_type() == "SELECT":
                    raise ValueError("Only SELECT statements are allowed")

            # Remove comments and normalize
            sanitized = sqlparse.format(
                sql_input, strip_comments=True, reindent=True, keyword_case="upper"
            )

            return sanitized

        except Exception as e:
            logger.warning("SQL parsing failed", error=str(e), input=sql_input[:50])
            raise ValueError("Invalid SQL input detected")

    def validate_file_upload(
        self, file_path: str, file_content: bytes
    ) -> Dict[str, Any]:
        """
        Validate file uploads for security

        Args:
            file_path: Path/name of the uploaded file
            file_content: File content bytes

        Returns:
            Validation results
        """
        results = {
            "valid": False,
            "mime_type": None,
            "detected_type": None,
            "size": len(file_content),
            "violations": [],
        }

        # Check file size
        max_size = 100 * 1024 * 1024  # 100MB
        if results["size"] > max_size:
            results["violations"].append(
                f"File size {results['size']} exceeds maximum {max_size}"
            )
            return results

        # Get MIME type from extension
        mime_type, _ = mimetypes.guess_type(file_path)
        results["mime_type"] = mime_type

        # Detect actual file type using magic
        try:
            detected_type = magic.from_buffer(file_content, mime=True)
            results["detected_type"] = detected_type

            # Check for MIME type mismatch
            if mime_type and detected_type and mime_type != detected_type:
                results["violations"].append(
                    f"MIME type mismatch: extension suggests {mime_type}, content is {detected_type}"
                )

        except Exception as e:
            logger.warning("File type detection failed", error=str(e))
            results["violations"].append("Could not determine file type")

        # Check allowed file types
        allowed_types = {
            "application/pdf",
            "text/plain",
            "application/json",
            "text/csv",
            "image/png",
            "image/jpeg",
            "image/jpg",
            "application/zip",
        }

        if results["detected_type"] not in allowed_types:
            results["violations"].append(
                f"File type {results['detected_type']} not allowed"
            )

        # Check for executable signatures
        executable_signatures = [
            b"\x4d\x5a",  # Windows PE
            b"\x7f\x45\x4c\x46",  # ELF
            b"\xfe\xed\xfa",  # Mach-O
        ]

        for signature in executable_signatures:
            if file_content.startswith(signature):
                results["violations"].append("Executable file detected")
                break

        results["valid"] = len(results["violations"]) == 0
        return results

    def normalize_input(self, input_value: str) -> str:
        """
        Normalize input to prevent encoding-based attacks

        Args:
            input_value: Input to normalize

        Returns:
            Normalized input
        """
        if not input_value:
            return input_value

        # URL decode multiple times to prevent double encoding attacks
        normalized = input_value
        for _ in range(3):  # Decode up to 3 times
            try:
                decoded = unquote(normalized)
                if decoded == normalized:
                    break  # No more decoding needed
                normalized = decoded
            except Exception:
                break

        # Normalize Unicode
        try:
            normalized = normalized.encode("utf-8").decode("utf-8")
        except UnicodeError:
            logger.warning("Unicode normalization failed for input")

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def sanitize_json_input(self, json_input: Any) -> Any:
        """
        Sanitize JSON input recursively

        Args:
            json_input: JSON input to sanitize

        Returns:
            Sanitized JSON input
        """
        if isinstance(json_input, dict):
            sanitized = {}
            for key, value in json_input.items():
                # Sanitize key
                sanitized_key = self.normalize_input(str(key))
                # Recursively sanitize value
                sanitized_value = self.sanitize_json_input(value)
                sanitized[sanitized_key] = sanitized_value
            return sanitized

        elif isinstance(json_input, list):
            return [self.sanitize_json_input(item) for item in json_input]

        elif isinstance(json_input, str):
            # Sanitize string values
            return self.normalize_input(json_input)

        else:
            # Return other types as-is (int, float, bool, None)
            return json_input


class InputValidationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for input validation and security"""

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):
        """
        Initialize the input validation middleware

        Args:
            app: FastAPI application
            max_request_size: Maximum request size in bytes
        """
        super().__init__(app)
        self.max_request_size = max_request_size
        self.sanitizer = InputSanitizer()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through input validation

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        try:
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_request_size:
                logger.warning(
                    "Request size exceeded",
                    size=content_length,
                    max_size=self.max_request_size,
                    client_ip=client_ip,
                )
                raise HTTPException(status_code=413, detail="Request too large")

            # Check rate limiting (if enabled)
            await self._check_rate_limiting(client_ip)

            # Validate and sanitize request body
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_body(request, client_ip, user_agent)

            # Validate query parameters
            await self._validate_query_params(request, client_ip, user_agent)

            # Validate headers
            await self._validate_headers(request, client_ip, user_agent)

            # Continue to next middleware
            response = await call_next(request)

            # Add security headers to response
            response = self._add_security_headers(response)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Input validation middleware error",
                error=str(e),
                client_ip=client_ip,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error during validation"},
            )

    async def _validate_request_body(
        self, request: Request, client_ip: str, user_agent: str
    ):
        """Validate request body content"""
        try:
            # Read and parse body
            body = await request.body()
            if body:
                # Try to parse as JSON
                try:
                    json_data = json.loads(body)
                    # Validate JSON for security violations
                    violations = self._check_json_for_violations(
                        json_data, client_ip, user_agent
                    )
                    if violations:
                        logger.warning(
                            "Security violations in request body",
                            violations=len(violations),
                            client_ip=client_ip,
                        )
                        raise HTTPException(
                            status_code=400, detail="Invalid input detected"
                        )

                except json.JSONDecodeError:
                    # Not JSON, treat as text
                    text_data = body.decode("utf-8", errors="ignore")
                    violations = self.sanitizer.detect_security_violations(
                        text_data, "request_body", client_ip, user_agent
                    )
                    if violations:
                        raise HTTPException(
                            status_code=400, detail="Invalid input detected"
                        )

        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid character encoding")

    async def _validate_query_params(
        self, request: Request, client_ip: str, user_agent: str
    ):
        """Validate query parameters"""
        for param, value in request.query_params.items():
            violations = self.sanitizer.detect_security_violations(
                value, f"query_param_{param}", client_ip, user_agent
            )
            if violations:
                logger.warning(
                    "Security violation in query parameter",
                    param=param,
                    client_ip=client_ip,
                )
                raise HTTPException(
                    status_code=400, detail=f"Invalid query parameter: {param}"
                )

    async def _validate_headers(
        self, request: Request, client_ip: str, user_agent: str
    ):
        """Validate HTTP headers"""
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "x-originating-ip"]

        for header_name, header_value in request.headers.items():
            # Skip standard headers
            if header_name.lower() in ["authorization", "content-type", "accept"]:
                continue

            # Check for header injection
            if "\n" in header_value or "\r" in header_value:
                logger.warning(
                    "Header injection detected", header=header_name, client_ip=client_ip
                )
                raise HTTPException(status_code=400, detail="Invalid header format")

            # Check suspicious forwarding headers
            if header_name.lower() in suspicious_headers:
                logger.info(
                    "Suspicious forwarding header detected",
                    header=header_name,
                    value=header_value[:50],
                    client_ip=client_ip,
                )

    def _check_json_for_violations(
        self, json_data: Any, client_ip: str, user_agent: str, field_path: str = ""
    ) -> List[SecurityViolation]:
        """Recursively check JSON data for security violations"""
        violations = []

        if isinstance(json_data, dict):
            for key, value in json_data.items():
                current_path = f"{field_path}.{key}" if field_path else key

                # Check key for violations
                key_violations = self.sanitizer.detect_security_violations(
                    str(key), f"json_key_{current_path}", client_ip, user_agent
                )
                violations.extend(key_violations)

                # Recursively check value
                value_violations = self._check_json_for_violations(
                    value, client_ip, user_agent, current_path
                )
                violations.extend(value_violations)

        elif isinstance(json_data, list):
            for i, item in enumerate(json_data):
                current_path = f"{field_path}[{i}]" if field_path else f"[{i}]"
                item_violations = self._check_json_for_violations(
                    item, client_ip, user_agent, current_path
                )
                violations.extend(item_violations)

        elif isinstance(json_data, str):
            # Check string values
            string_violations = self.sanitizer.detect_security_violations(
                json_data, f"json_value_{field_path}", client_ip, user_agent
            )
            violations.extend(string_violations)

        return violations

    async def _check_rate_limiting(self, client_ip: str):
        """Check rate limiting for client IP"""
        # This would integrate with Redis or similar for distributed rate limiting
        # For now, just log the request
        logger.debug("Rate limiting check", client_ip=client_ip)

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


# Export main classes
__all__ = [
    "InputSanitizer",
    "InputValidationMiddleware",
    "ValidationRule",
    "SecurityViolation",
]
