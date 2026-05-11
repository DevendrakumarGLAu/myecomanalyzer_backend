from typing import Iterable

from fastapi import HTTPException, UploadFile
from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE


def validate_file_extension(
    file: UploadFile,
    allowed_extensions: Iterable[str],
    field_name: str = "file"
):
    filename = file.filename or ""
    normalized_extensions = [ext.lower() for ext in allowed_extensions]

    if not any(filename.lower().endswith(ext) for ext in normalized_extensions):
        raise HTTPException(
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "success": False,
                "message": "Invalid file type",
                "details": {
                    "field": field_name,
                    "filename": filename,
                    "allowed_extensions": normalized_extensions,
                    "received_content_type": file.content_type,
                },
            },
        )
