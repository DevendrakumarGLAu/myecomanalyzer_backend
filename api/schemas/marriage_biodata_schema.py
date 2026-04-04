from pydantic import BaseModel
from typing import Dict, Any

class BiodataSchema(BaseModel):
    user_id: int
    template_id: str
    data: Dict[str, Any]