from pydantic import BaseModel
from datetime import datetime

class BookmarkCreate(BaseModel):
    page: int
    note: str = None

class BookmarkResponse(BaseModel):
    id: int
    document_id: int
    page: int
    note: str = None
    created_at: datetime

    class Config:
        from_attributes = True