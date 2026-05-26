from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.bookmark import Bookmark
from app.models.document import Document
from app.schemas.bookmark import BookmarkCreate, BookmarkResponse
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@router.post("/{document_id}", response_model=BookmarkResponse)
def create_bookmark(
    document_id: int,
    bookmark_data: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    bookmark = Bookmark(
        user_id=current_user.id,
        document_id=document_id,
        page=bookmark_data.page,
        note=bookmark_data.note
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark

@router.get("/{document_id}", response_model=list[BookmarkResponse])
def get_bookmarks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmarks = db.query(Bookmark).filter(
        Bookmark.document_id == document_id,
        Bookmark.user_id == current_user.id
    ).all()
    return bookmarks

@router.delete("/{bookmark_id}")
def delete_bookmark(
    bookmark_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Signet introuvable")

    db.delete(bookmark)
    db.commit()
    return {"message": "Signet supprimé"}