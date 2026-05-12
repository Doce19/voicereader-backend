from pydantic import BaseModel
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    total_pages: int
    last_page: int
    created_at: datetime

    class Config:
        from_attributes = True