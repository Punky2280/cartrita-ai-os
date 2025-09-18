"""
File Security Utilities for Cartrita AI OS
Provides secure file access with path traversal protection and validation.
"""

import hashlib
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import List, Optional

from fastapi import HTTPException


class SecureFileManager:
    """Secure file manager with path traversal protection."""

    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".log",
        ".yaml",
        ".yml",
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".xml",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
        ".flac",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    }

    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # Maximum filename length
    MAX_FILENAME_LENGTH = 255

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize secure file manager."""
        if base_dir is None:
            # Use secure temporary directory
            base_dir = Path(tempfile.gettempdir()) / "cartrita_secure"

        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.uploads_dir = self.base_dir / "uploads"
        self.temp_dir = self.base_dir / "temp"
        self.logs_dir = self.base_dir / "logs"

        for directory in [self.uploads_dir, self.temp_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and other attacks."""
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Remove path components and keep only the filename
        filename = os.path.basename(filename)

        # Convert to PurePosixPath for cross-platform handling
        pure_path = PurePosixPath(filename)
        sanitized = pure_path.name

        # Remove or replace dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "_")

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # If the filename is now empty (e.g., it was just "."), generate a name.
        if not sanitized:
            sanitized = f"file_{hashlib.sha256(filename.encode()).hexdigest()[:8]}.txt"

        # Ensure filename length is within limits
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            # Preserve extension if possible
            name_part, ext = os.path.splitext(sanitized)
            max_name_len = self.MAX_FILENAME_LENGTH - len(ext)
            sanitized = name_part[:max_name_len] + ext

        # Ensure it's not empty after sanitization
        if not sanitized:
            # Use SHA-256 instead of MD5 for security (non-cryptographic use case)
            sanitized = f"file_{hashlib.sha256(filename.encode()).hexdigest()[:8]}.txt"

        return sanitized

    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension against allowed list."""
        ext = Path(filename).suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS

    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size against maximum allowed size."""
        return 0 < file_size <= self.MAX_FILE_SIZE

    def _validate_subdirectory(self, subdirectory: str):
        """Prevent path traversal in subdirectory name."""
        if ".." in subdirectory or "/" in subdirectory or "\\" in subdirectory:
            raise ValueError(f"Invalid subdirectory name: {subdirectory}")

    def get_secure_path(self, filename: str, subdirectory: str = "uploads") -> Path:
        """Get secure file path within the base directory."""
        # Sanitize filename
        safe_filename = self.sanitize_filename(filename)

        # Choose appropriate subdirectory
        if subdirectory == "uploads":
            target_dir = self.uploads_dir
        elif subdirectory == "temp":
            target_dir = self.temp_dir
        elif subdirectory == "logs":
            target_dir = self.logs_dir
        else:
            self._validate_subdirectory(subdirectory)
            target_dir = self.base_dir / subdirectory
            target_dir.mkdir(parents=True, exist_ok=True)

        # Construct full path
        full_path = target_dir / safe_filename

        # Resolve and verify it's within base directory
        resolved_path = full_path.resolve()

        if not str(resolved_path).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Path traversal attempt detected: {filename}")

        return resolved_path

    def safe_write_file(
        self, filename: str, content: bytes, subdirectory: str = "uploads"
    ) -> Path:
        """Safely write file with security checks."""
        # Validate file size
        if not self.validate_file_size(len(content)):
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE} bytes",
            )

        # Validate file extension
        if not self.validate_file_extension(filename):
            raise HTTPException(
                status_code=415,
                detail=f"File extension not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
            )

        # Get secure path
        file_path = self.get_secure_path(filename, subdirectory)

        # Write file securely
        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with restricted permissions
            with open(file_path, "wb") as f:
                f.write(content)

            # Set restrictive permissions (owner read/write only)
            os.chmod(file_path, 0o600)

            return file_path

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to write file: {str(e)}"
            ) from e

    def safe_read_file(self, filename: str, subdirectory: str = "uploads") -> bytes:
        """Safely read file with security checks."""
        # Get secure path
        file_path = self.get_secure_path(filename, subdirectory)

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")

        # Check if it's actually a file (not directory)
        if not file_path.is_file():
            raise HTTPException(
                status_code=400, detail=f"Path is not a file: {filename}"
            )

        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read file: {str(e)}"
            ) from e

    def safe_delete_file(self, filename: str, subdirectory: str = "uploads") -> bool:
        """Safely delete file with security checks."""
        # Get secure path
        file_path = self.get_secure_path(filename, subdirectory)

        # Check if file exists
        if not file_path.exists():
            return False

        # Only delete files, not directories
        if not file_path.is_file():
            raise HTTPException(
                status_code=400, detail=f"Cannot delete directory: {filename}"
            )

        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete file: {str(e)}"
            ) from e

    def list_files(
        self, subdirectory: str = "uploads", pattern: str = "*"
    ) -> List[str]:
        """List files in subdirectory with pattern matching."""
        if subdirectory == "uploads":
            target_dir = self.uploads_dir
        elif subdirectory == "temp":
            target_dir = self.temp_dir
        elif subdirectory == "logs":
            target_dir = self.logs_dir
        else:
            self._validate_subdirectory(subdirectory)
            target_dir = self.base_dir / subdirectory

        if not target_dir.exists():
            return []

        try:
            # Only return files, not directories
            files = [f.name for f in target_dir.glob(pattern) if f.is_file()]
            return sorted(files)
        except Exception:
            return []

    def get_file_info(self, filename: str, subdirectory: str = "uploads") -> dict:
        """Get secure file information."""
        file_path = self.get_secure_path(filename, subdirectory)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")

        stat = file_path.stat()
        return {
            "filename": filename,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "extension": file_path.suffix.lower(),
            "safe_path": str(file_path),
        }


# Global secure file manager instance
secure_file_manager = SecureFileManager()
