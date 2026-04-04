import base64
from django.core.files.base import ContentFile

def base64_to_file(base64_str, file_name="image"):
    """
    Converts base64 image to Django ContentFile
    """
    if not base64_str:
        return None
    format, imgstr = base64_str.split(';base64,')
    ext = format.split('/')[-1]  # e.g., 'png', 'webp'
    return ContentFile(base64.b64decode(imgstr), name=f"{file_name}.{ext}")