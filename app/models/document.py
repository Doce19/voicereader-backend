from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    total_pages = Column(Integer, default=0)
    last_page = Column(Integer, default=0)
    last_position = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="documents")