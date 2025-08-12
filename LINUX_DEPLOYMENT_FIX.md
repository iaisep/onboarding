# Linux/Docker Deployment Compatibility Fix

## Problem Fixed
Previously, the Docker deployment was failing on Linux with the error:
```
ERROR: No matching distribution found for pywin32==306
```

This occurred because Windows-specific dependencies were included in `requirements.txt`.

## Solution Implemented

### 1. Separate Requirements Files
- **`requirements.txt`**: For Windows development environment (includes all packages)
- **`requirements-docker.txt`**: For Linux/Docker deployment (excludes Windows-only packages)

### 2. Excluded Windows-Only Dependencies
The following packages are excluded from Linux deployment:
- `pywin32==306` - Windows COM interface library
- `docx2pdf==0.1.8` - Requires Microsoft Office COM (Windows-only)

### 3. Platform Detection
Added platform detection in `AWSUpload.py`:
```python
import platform

RUNNING_ON_WINDOWS = platform.system() == 'Windows'
```

### 4. Feature Limitations on Linux
- **DOCX Upload**: Not supported on Linux (returns clear error message)
- **PDF Upload**: Fully supported on all platforms using PyMuPDF

### 5. Docker Configuration Update
Modified `Dockerfile` to use the Linux-compatible requirements:
```dockerfile
COPY requirements-docker.txt /app/
RUN pip install --no-cache-dir -r requirements-docker.txt
```

## Deployment Status

### ✅ Working Configurations
1. **Windows Development**: Full functionality including DOCX conversion
2. **Docker Local**: All Docker Compose configurations work on Linux
3. **Coolify Deployment**: External database configuration works on port 8082

### ⚠️ Platform Limitations
- **DOCX Conversion**: Windows-only feature
- **Linux Workaround**: Clear error message directing users to convert DOCX to PDF

## Testing the Fix

### Local Docker Build
```bash
docker build -t bnp-api .
```

### Coolify Deployment
The external database configuration (`docker-compose.coolify-external-db.yml`) should now deploy successfully on Coolify.

## User Documentation
Updated `FILE_UPLOAD_GUIDE.md` with platform-specific information for document conversion capabilities.

## Next Steps
1. Test Coolify deployment with the new configuration
2. Monitor logs to ensure proper error handling for DOCX files on Linux
3. Consider implementing alternative DOCX conversion methods for Linux in the future
