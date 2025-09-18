"""
Enhanced filesystem tools for LangChain agents with secure file operations.
Provides secure file system operations with path traversal protection.
"""

from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict

import structlog

# Import secure file manager
from cartrita.orchestrator.utils.secure_file import secure_file_manager

logger = structlog.get_logger(__name__)


class SecureFileSystemTool:
    """Enhanced filesystem tool with secure operations."""

    def __init__(self):
        """Initialize filesystem tool with secure manager."""
        self.temp_dir = Path(gettempdir())
        logger.info("SecureFileSystemTool initialized", temp_dir=str(self.temp_dir))

    def read_file(self, file_path: str, subdirectory: str = "temp") -> str:
        """Securely read a file."""
        try:
            # Extract filename from path
            filename = Path(file_path).name

            # Use secure file manager for reading
            content = secure_file_manager.safe_read_file(filename, subdirectory)

            if isinstance(content, bytes):
                # Decode bytes to string
                content = content.decode("utf-8")

            logger.info(
                "File read successfully",
                filename=filename,
                subdirectory=subdirectory,
                size=len(content),
            )
            return content

        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            logger.error("File read failed", file_path=file_path, error=str(e))
            return f"Error: {error_msg}"

    def write_file(
        self, file_path: str, content: str, subdirectory: str = "temp"
    ) -> str:
        """Securely write content to a file."""
        try:
            # Convert content to bytes if it's a string
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            else:
                content_bytes = content

            # Extract filename from path
            filename = Path(file_path).name

            # Use secure file manager for writing
            actual_path = secure_file_manager.safe_write_file(
                filename=filename, content=content_bytes, subdirectory=subdirectory
            )

            logger.info(
                "File written successfully",
                requested_path=file_path,
                actual_path=str(actual_path),
                size=len(content_bytes),
            )

            return f"File written successfully to: {actual_path}"

        except Exception as e:
            error_msg = f"Failed to write file: {str(e)}"
            logger.error("File write failed", file_path=file_path, error=str(e))
            return f"Error: {error_msg}"

    def list_files(self, subdirectory: str = "temp") -> str:
        """Securely list files in a directory."""
        try:
            # Get secure directory path using dummy filename approach
            temp_filename = "dummy.txt"
            dir_path = secure_file_manager.get_secure_path(
                temp_filename, subdirectory
            ).parent

            if not dir_path.exists():
                return f"Directory does not exist: {subdirectory}"

            if not dir_path.is_dir():
                return f"Path is not a directory: {subdirectory}"

            # List files with basic information
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    try:
                        file_info = {
                            "name": item.name,
                            "size": item.stat().st_size,
                            "modified": item.stat().st_mtime,
                        }
                        files.append(file_info)
                    except Exception as stat_error:
                        logger.warning(
                            "Failed to get file stats",
                            file=str(item),
                            error=str(stat_error),
                        )
                        files.append(
                            {
                                "name": item.name,
                                "size": "unknown",
                                "modified": "unknown",
                            }
                        )

            logger.info(
                "Directory listed successfully",
                subdirectory=subdirectory,
                file_count=len(files),
            )

            if not files:
                return f"No files found in directory: {subdirectory}"

            # Format file listing
            file_list = []
            for file_info in files:
                file_list.append(f"- {file_info['name']} ({file_info['size']} bytes)")

            return f"Files in {subdirectory}:\n" + "\n".join(file_list)

        except Exception as e:
            error_msg = f"Failed to list directory: {str(e)}"
            logger.error(
                "Directory listing failed", subdirectory=subdirectory, error=str(e)
            )
            return f"Error: {error_msg}"

    def delete_file(self, file_path: str) -> str:
        """Securely delete a file."""
        try:
            # Extract filename and determine full path
            filename = Path(file_path).name

            # Try to find file in allowed directories
            for subdir in ["temp", "uploads", "logs"]:
                try:
                    # Try to delete using secure file manager
                    if secure_file_manager.safe_delete_file(filename, subdir):
                        logger.info(
                            "File deleted successfully",
                            requested_path=file_path,
                            filename=filename,
                            subdirectory=subdir,
                        )
                        return f"File deleted successfully: {filename}"

                except Exception as delete_error:
                    logger.debug(
                        "File not found in directory",
                        subdirectory=subdir,
                        filename=filename,
                        error=str(delete_error),
                    )
                    continue

            # File not found in any allowed directory
            return f"File not found or access denied: {filename}"

        except Exception as e:
            error_msg = f"Failed to delete file: {str(e)}"
            logger.error("File deletion failed", file_path=file_path, error=str(e))
            return f"Error: {error_msg}"

    def get_file_info(self, file_path: str) -> str:
        """Get secure information about a file."""
        try:
            filename = Path(file_path).name

            # Try to find file in allowed directories
            for subdir in ["temp", "uploads", "logs"]:
                try:
                    full_path = secure_file_manager.get_secure_path(filename, subdir)

                    if full_path.exists() and full_path.is_file():
                        stat_info = full_path.stat()

                        file_info = {
                            "name": full_path.name,
                            "size": stat_info.st_size,
                            "modified": stat_info.st_mtime,
                            "subdirectory": subdir,
                            "extension": full_path.suffix,
                            "absolute_path": str(full_path),
                        }

                        logger.info(
                            "File info retrieved",
                            filename=filename,
                            subdirectory=subdir,
                        )

                        return (
                            f"File: {file_info['name']}\n"
                            f"Size: {file_info['size']} bytes\n"
                            f"Directory: {file_info['subdirectory']}\n"
                            f"Extension: {file_info['extension']}\n"
                            f"Modified: {file_info['modified']}"
                        )

                except Exception:
                    continue

            return f"File not found or access denied: {filename}"

        except Exception as e:
            error_msg = f"Failed to get file info: {str(e)}"
            logger.error("File info failed", file_path=file_path, error=str(e))
            return f"Error: {error_msg}"


# Create global instance for use by agents
secure_filesystem_tool = SecureFileSystemTool()


def get_secure_filesystem_tools() -> Dict[str, Any]:
    """Get dictionary of secure filesystem tools for LangChain agents."""
    return {
        "read_file": secure_filesystem_tool.read_file,
        "write_file": secure_filesystem_tool.write_file,
        "list_files": secure_filesystem_tool.list_files,
        "delete_file": secure_filesystem_tool.delete_file,
        "get_file_info": secure_filesystem_tool.get_file_info,
    }
