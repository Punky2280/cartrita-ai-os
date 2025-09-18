# Files API

> **Source**: https://platform.openai.com/docs/api-reference/files
> **Last Updated**: September 17, 2025

## Overview

Files are used to upload documents that can be used with features like Assistants and Fine-tuning. The Files API allows you to upload, list, retrieve, and delete files.

## File Object

Represents a file that has been uploaded to OpenAI.

### File Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | The file identifier, which can be referenced in the API endpoints. |
| `object` | string | The object type, which is always "file". |
| `bytes` | integer | The size of the file, in bytes. |
| `created_at` | integer | The Unix timestamp (in seconds) for when the file was created. |
| `filename` | string | The name of the file. |
| `purpose` | string | The intended purpose of the file. |

### File Purposes

| Purpose | Description |
|---------|-------------|
| `assistants` | Files used with the Assistants API |
| `fine-tune` | Files used for fine-tuning models |
| `fine-tune-results` | Results from fine-tuning jobs |

## Upload File

Upload a file that can be used across various endpoints.

### HTTP Request
```
POST https://api.openai.com/v1/files
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | The File object (not file name) to be uploaded. |
| `purpose` | string | Yes | The intended purpose of the uploaded file. |

### File Requirements

#### General Requirements
- Maximum file size: 512 MB
- File must be in one of the supported formats

#### Supported Formats by Purpose

**For Assistants (`purpose: "assistants"`):**
- `.c` - C source code
- `.cpp` - C++ source code
- `.csv` - Comma-separated values
- `.docx` - Microsoft Word document
- `.html` - HTML document
- `.java` - Java source code
- `.json` - JSON data
- `.md` - Markdown
- `.pdf` - Portable Document Format
- `.php` - PHP source code
- `.pptx` - Microsoft PowerPoint presentation
- `.py` - Python source code
- `.rb` - Ruby source code
- `.tex` - LaTeX document
- `.txt` - Plain text
- `.css` - Cascading Style Sheets
- `.js` - JavaScript
- `.sh` - Shell script
- `.ts` - TypeScript
- `.xlsx` - Microsoft Excel spreadsheet
- `.xml` - XML document
- `.zip` - ZIP archive

**For Fine-tuning (`purpose: "fine-tune"`):**
- `.jsonl` - JSON Lines format

### Example Requests

#### Upload File for Assistants
```python
from openai import OpenAI

client = OpenAI()

# Upload a PDF document
file = client.files.create(
    file=open("company_policy.pdf", "rb"),
    purpose="assistants"
)

print(f"Uploaded file: {file.id}")
print(f"Filename: {file.filename}")
print(f"Size: {file.bytes} bytes")
```

#### Upload Multiple Files
```python
from openai import OpenAI
import os

client = OpenAI()

def upload_files_from_directory(directory_path, purpose="assistants"):
    """Upload all supported files from a directory"""
    supported_extensions = {
        '.pdf', '.txt', '.md', '.docx', '.csv', '.json',
        '.py', '.js', '.html', '.css', '.xml'
    }

    uploaded_files = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        _, ext = os.path.splitext(filename)

        if os.path.isfile(file_path) and ext.lower() in supported_extensions:
            try:
                print(f"Uploading {filename}...")
                file = client.files.create(
                    file=open(file_path, "rb"),
                    purpose=purpose
                )
                uploaded_files.append({
                    "id": file.id,
                    "filename": file.filename,
                    "size": file.bytes
                })
                print(f"  ✓ Uploaded as {file.id}")

            except Exception as e:
                print(f"  ✗ Error uploading {filename}: {e}")

    return uploaded_files

# Upload all files from a directory
uploaded = upload_files_from_directory("./documents")
print(f"Successfully uploaded {len(uploaded)} files")
```

#### Upload Fine-tuning Data
```python
from openai import OpenAI
import json

client = OpenAI()

# Create fine-tuning dataset
training_data = [
    {"messages": [{"role": "user", "content": "What is 2+2?"}, {"role": "assistant", "content": "4"}]},
    {"messages": [{"role": "user", "content": "What is 3+3?"}, {"role": "assistant", "content": "6"}]},
    {"messages": [{"role": "user", "content": "What is 4+4?"}, {"role": "assistant", "content": "8"}]}
]

# Save as JSONL file
with open("training_data.jsonl", "w") as f:
    for item in training_data:
        f.write(json.dumps(item) + "\n")

# Upload for fine-tuning
file = client.files.create(
    file=open("training_data.jsonl", "rb"),
    purpose="fine-tune"
)

print(f"Training file uploaded: {file.id}")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/files \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F purpose="assistants" \
  -F file="@mydata.pdf"
```

### Response Object

```json
{
  "id": "file-abc123",
  "object": "file",
  "bytes": 120000,
  "created_at": 1613677385,
  "filename": "mydata.pdf",
  "purpose": "assistants"
}
```

## List Files

Returns a list of files that belong to the user's organization.

### HTTP Request
```
GET https://api.openai.com/v1/files
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `purpose` | string | Only return files with the given purpose. |

### Example Requests

#### List All Files
```python
from openai import OpenAI

client = OpenAI()

files = client.files.list()

print(f"Total files: {len(files.data)}")
for file in files.data:
    print(f"- {file.filename} ({file.id}) - {file.purpose} - {file.bytes} bytes")
```

#### List Files by Purpose
```python
from openai import OpenAI

client = OpenAI()

# List only assistant files
assistant_files = client.files.list(purpose="assistants")

print(f"Assistant files: {len(assistant_files.data)}")
for file in assistant_files.data:
    print(f"- {file.filename}: {file.id}")

# List only fine-tune files
finetune_files = client.files.list(purpose="fine-tune")

print(f"Fine-tune files: {len(finetune_files.data)}")
for file in finetune_files.data:
    print(f"- {file.filename}: {file.id}")
```

#### Organize Files by Purpose
```python
from openai import OpenAI
from collections import defaultdict

client = OpenAI()

def organize_files_by_purpose():
    """Organize all files by their purpose"""
    all_files = client.files.list()
    files_by_purpose = defaultdict(list)

    for file in all_files.data:
        files_by_purpose[file.purpose].append({
            "id": file.id,
            "filename": file.filename,
            "size": file.bytes,
            "created_at": file.created_at
        })

    return dict(files_by_purpose)

organized_files = organize_files_by_purpose()

for purpose, files in organized_files.items():
    print(f"\n{purpose.upper()} files ({len(files)}):")
    for file in files:
        print(f"  - {file['filename']} ({file['id']})")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/files \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Retrieve File

Returns information about a specific file.

### HTTP Request
```
GET https://api.openai.com/v1/files/{file_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | Yes | The ID of the file to use for this request. |

### Example Requests

#### Get File Information
```python
from openai import OpenAI
from datetime import datetime

client = OpenAI()

file = client.files.retrieve("file-abc123")

print(f"File ID: {file.id}")
print(f"Filename: {file.filename}")
print(f"Purpose: {file.purpose}")
print(f"Size: {file.bytes:,} bytes")
print(f"Created: {datetime.fromtimestamp(file.created_at)}")
```

#### Check File Status
```python
from openai import OpenAI

client = OpenAI()

def check_file_status(file_id):
    """Check if a file exists and get its details"""
    try:
        file = client.files.retrieve(file_id)
        return {
            "exists": True,
            "filename": file.filename,
            "purpose": file.purpose,
            "size": file.bytes,
            "created_at": file.created_at
        }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }

# Check multiple files
file_ids = ["file-abc123", "file-def456", "file-xyz789"]

for file_id in file_ids:
    status = check_file_status(file_id)
    if status["exists"]:
        print(f"✓ {file_id}: {status['filename']}")
    else:
        print(f"✗ {file_id}: {status['error']}")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/files/file-abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Delete File

Delete a file.

### HTTP Request
```
DELETE https://api.openai.com/v1/files/{file_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | Yes | The ID of the file to use for this request. |

### Example Requests

#### Delete Single File
```python
from openai import OpenAI

client = OpenAI()

response = client.files.delete("file-abc123")

if response.deleted:
    print(f"File {response.id} deleted successfully")
else:
    print("File deletion failed")
```

#### Bulk Delete Files
```python
from openai import OpenAI

client = OpenAI()

def delete_files_by_purpose(purpose):
    """Delete all files with a specific purpose"""
    files = client.files.list(purpose=purpose)
    deleted_count = 0

    for file in files.data:
        try:
            response = client.files.delete(file.id)
            if response.deleted:
                print(f"✓ Deleted {file.filename} ({file.id})")
                deleted_count += 1
            else:
                print(f"✗ Failed to delete {file.filename} ({file.id})")
        except Exception as e:
            print(f"✗ Error deleting {file.filename}: {e}")

    return deleted_count

# Delete all assistant files (be careful!)
# deleted = delete_files_by_purpose("assistants")
# print(f"Deleted {deleted} assistant files")
```

#### Safe Delete with Confirmation
```python
from openai import OpenAI

client = OpenAI()

def safe_delete_file(file_id, confirm=False):
    """Safely delete a file with confirmation"""
    try:
        # Get file info first
        file = client.files.retrieve(file_id)

        if not confirm:
            print(f"File to delete:")
            print(f"  ID: {file.id}")
            print(f"  Filename: {file.filename}")
            print(f"  Purpose: {file.purpose}")
            print(f"  Size: {file.bytes} bytes")

            confirmation = input("Are you sure you want to delete this file? (yes/no): ")
            if confirmation.lower() != "yes":
                print("Deletion cancelled")
                return False

        # Delete the file
        response = client.files.delete(file_id)

        if response.deleted:
            print(f"✓ File {file_id} deleted successfully")
            return True
        else:
            print(f"✗ Failed to delete file {file_id}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

# Usage
safe_delete_file("file-abc123")
```

#### cURL Example
```bash
curl -X DELETE https://api.openai.com/v1/files/file-abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Response Object

```json
{
  "id": "file-abc123",
  "object": "file",
  "deleted": true
}
```

## Retrieve File Content

Returns the contents of the specified file.

### HTTP Request
```
GET https://api.openai.com/v1/files/{file_id}/content
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | Yes | The ID of the file whose contents to retrieve. |

### Example Requests

#### Download File Content
```python
from openai import OpenAI

client = OpenAI()

# Get file content
content = client.files.content("file-abc123")

# Save to file
with open("downloaded_file.txt", "wb") as f:
    f.write(content.content)

print("File content downloaded and saved")
```

#### Process File Content
```python
from openai import OpenAI
import json

client = OpenAI()

def download_and_process_file(file_id):
    """Download file content and process based on type"""
    try:
        # Get file info
        file_info = client.files.retrieve(file_id)
        print(f"Processing {file_info.filename}...")

        # Get content
        content = client.files.content(file_id)

        # Process based on file type
        if file_info.filename.endswith('.json'):
            # Parse JSON content
            data = json.loads(content.content.decode('utf-8'))
            print(f"JSON file with {len(data)} items")
            return data

        elif file_info.filename.endswith('.txt'):
            # Process text content
            text = content.content.decode('utf-8')
            lines = text.split('\n')
            print(f"Text file with {len(lines)} lines")
            return text

        elif file_info.filename.endswith('.csv'):
            # Process CSV content
            import csv
            import io

            text = content.content.decode('utf-8')
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            print(f"CSV file with {len(rows)} rows")
            return rows

        else:
            # Save binary content
            filename = f"downloaded_{file_info.filename}"
            with open(filename, "wb") as f:
                f.write(content.content)
            print(f"Binary file saved as {filename}")
            return filename

    except Exception as e:
        print(f"Error processing file: {e}")
        return None

# Usage
result = download_and_process_file("file-abc123")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/files/file-abc123/content \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -o downloaded_file.txt
```

## File Management Utilities

### File Manager Class
```python
from openai import OpenAI
import os
import json
from datetime import datetime
from pathlib import Path

class FileManager:
    def __init__(self):
        self.client = OpenAI()

    def upload_directory(self, directory_path, purpose="assistants",
                        file_extensions=None):
        """Upload all files from a directory"""
        if file_extensions is None:
            file_extensions = {
                '.txt', '.md', '.pdf', '.docx', '.csv',
                '.json', '.py', '.js', '.html', '.css'
            }

        directory = Path(directory_path)
        uploaded_files = []

        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    file = self.client.files.create(
                        file=open(file_path, "rb"),
                        purpose=purpose
                    )
                    uploaded_files.append({
                        "local_path": str(file_path),
                        "file_id": file.id,
                        "filename": file.filename,
                        "size": file.bytes
                    })
                    print(f"✓ Uploaded {file_path.name} -> {file.id}")

                except Exception as e:
                    print(f"✗ Failed to upload {file_path.name}: {e}")

        return uploaded_files

    def download_all_files(self, output_dir="downloads"):
        """Download all accessible files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        files = self.client.files.list()
        downloaded = []

        for file in files.data:
            try:
                content = self.client.files.content(file.id)

                # Save file
                file_path = output_path / file.filename
                with open(file_path, "wb") as f:
                    f.write(content.content)

                downloaded.append({
                    "file_id": file.id,
                    "filename": file.filename,
                    "local_path": str(file_path)
                })
                print(f"✓ Downloaded {file.filename}")

            except Exception as e:
                print(f"✗ Failed to download {file.filename}: {e}")

        return downloaded

    def cleanup_old_files(self, days_old=30, purpose=None, dry_run=True):
        """Delete files older than specified days"""
        from time import time

        cutoff_time = time() - (days_old * 24 * 60 * 60)
        files_query = {"purpose": purpose} if purpose else {}
        files = self.client.files.list(**files_query)

        old_files = [
            f for f in files.data
            if f.created_at < cutoff_time
        ]

        if dry_run:
            print(f"Found {len(old_files)} files older than {days_old} days:")
            for file in old_files:
                age_days = (time() - file.created_at) / (24 * 60 * 60)
                print(f"  - {file.filename} ({file.id}) - {age_days:.1f} days old")
            print("Set dry_run=False to actually delete these files")
            return old_files

        deleted_count = 0
        for file in old_files:
            try:
                response = self.client.files.delete(file.id)
                if response.deleted:
                    deleted_count += 1
                    print(f"✓ Deleted {file.filename}")

            except Exception as e:
                print(f"✗ Failed to delete {file.filename}: {e}")

        print(f"Deleted {deleted_count} old files")
        return deleted_count

    def get_usage_summary(self):
        """Get a summary of file usage"""
        files = self.client.files.list()

        summary = {
            "total_files": len(files.data),
            "total_size_bytes": sum(f.bytes for f in files.data),
            "by_purpose": {},
            "by_extension": {}
        }

        for file in files.data:
            # By purpose
            purpose = file.purpose
            if purpose not in summary["by_purpose"]:
                summary["by_purpose"][purpose] = {"count": 0, "size": 0}
            summary["by_purpose"][purpose]["count"] += 1
            summary["by_purpose"][purpose]["size"] += file.bytes

            # By extension
            ext = Path(file.filename).suffix.lower() or "no_extension"
            if ext not in summary["by_extension"]:
                summary["by_extension"][ext] = {"count": 0, "size": 0}
            summary["by_extension"][ext]["count"] += 1
            summary["by_extension"][ext]["size"] += file.bytes

        return summary

# Example usage
manager = FileManager()

# Upload files from directory
uploaded = manager.upload_directory("./documents", purpose="assistants")
print(f"Uploaded {len(uploaded)} files")

# Get usage summary
summary = manager.get_usage_summary()
print(f"Total files: {summary['total_files']}")
print(f"Total size: {summary['total_size_bytes']:,} bytes")

# Cleanup old files (dry run first)
old_files = manager.cleanup_old_files(days_old=30, dry_run=True)
```

## Error Handling

### Common Errors and Solutions

```python
from openai import OpenAI
import openai

client = OpenAI()

def safe_file_upload(file_path, purpose):
    """Upload file with comprehensive error handling"""
    try:
        file = client.files.create(
            file=open(file_path, "rb"),
            purpose=purpose
        )
        return {"success": True, "file_id": file.id, "filename": file.filename}

    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {file_path}"}

    except openai.BadRequestError as e:
        error_msg = str(e).lower()
        if "file size" in error_msg:
            return {"success": False, "error": "File too large (max 512MB)"}
        elif "file type" in error_msg or "format" in error_msg:
            return {"success": False, "error": "Unsupported file format"}
        else:
            return {"success": False, "error": f"Bad request: {e}"}

    except openai.RateLimitError:
        return {"success": False, "error": "Rate limit exceeded"}

    except openai.AuthenticationError:
        return {"success": False, "error": "Invalid API key"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

def safe_file_delete(file_id):
    """Delete file with error handling"""
    try:
        response = client.files.delete(file_id)
        return {"success": response.deleted, "file_id": file_id}

    except openai.NotFoundError:
        return {"success": False, "error": f"File not found: {file_id}"}

    except Exception as e:
        return {"success": False, "error": f"Error deleting file: {e}"}

# Usage examples
upload_result = safe_file_upload("document.pdf", "assistants")
if upload_result["success"]:
    print(f"Uploaded: {upload_result['filename']} ({upload_result['file_id']})")
else:
    print(f"Upload failed: {upload_result['error']}")

delete_result = safe_file_delete("file-abc123")
if delete_result["success"]:
    print(f"Deleted file: {delete_result['file_id']}")
else:
    print(f"Delete failed: {delete_result['error']}")
```

## Best Practices

### File Organization
- Use descriptive filenames
- Organize files by purpose and project
- Keep track of file IDs in your application
- Regularly clean up unused files

### Performance Optimization
- Upload files in appropriate formats
- Compress large files when possible
- Use batch operations for multiple files
- Implement retry logic for uploads

### Security and Compliance
- Validate file contents before upload
- Don't upload sensitive personal data
- Implement access controls for file operations
- Monitor file usage and costs

### Cost Management
- Monitor file storage usage
- Delete unused files regularly
- Use appropriate file sizes
- Consider file retention policies

---

*This documentation covers the complete Files API for uploading, managing, and retrieving files used with OpenAI services. Use these APIs to build file-powered applications with Assistants and Fine-tuning.*
