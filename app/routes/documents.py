from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.bookmark import Bookmark
from app.schemas.document import DocumentResponse
from app.services.pdf import save_pdf, extract_text
from app.services.dependencies import get_current_user
from app.services.tts import text_to_speech
from fastapi.responses import FileResponse
import uuid
import fitz
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


def ensure_document_file_exists(document: Document):
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=404,
            detail="Fichier PDF introuvable. Veuillez supprimer ce document et le ré-uploader."
        )


@router.post("/upload", response_model=DocumentResponse)
def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    file_bytes = file.file.read()
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = save_pdf(file_bytes, unique_filename)
    text, total_pages = extract_text(file_path)

    document = Document(
        user_id=current_user.id,
        title=file.filename.replace(".pdf", ""),
        filename=unique_filename,
        file_path=file_path,
        total_pages=total_pages
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Document).filter(Document.user_id == current_user.id).all()


@router.get("/{document_id}/file")
def get_pdf_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    ensure_document_file_exists(document)

    return FileResponse(
        document.file_path,
        media_type="application/pdf",
        filename=document.filename
    )


@router.get("/{document_id}/audio")
def get_audio(
    document_id: int,
    lang: str = "fr",
    genre: str = "feminin",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Audio request for document {document_id}")

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    ensure_document_file_exists(document)

    try:
        doc = fitz.open(document.file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
    except Exception as e:
        logger.error(f"PDF read error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lecture PDF: {str(e)}")

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte extractible")

    try:
        audio_path = text_to_speech(full_text, document_id, lang=lang, genre=genre)
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=500, detail="Audio généré introuvable")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=f"document_{document_id}.mp3"
    )


@router.put("/{document_id}/progress")
def update_progress(
    document_id: int,
    page: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    page = max(0, min(page, document.total_pages or page))
    document.last_page = page
    db.commit()

    return {"message": f"Progression sauvegardée à la page {page}"}


@router.get("/{document_id}/progress")
def get_progress(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    return {"document_id": document_id, "last_page": document.last_page}


@router.get("/{document_id}/text")
def get_text(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    ensure_document_file_exists(document)

    try:
        doc = fitz.open(document.file_path)
        pages = []
        for i, page in enumerate(doc):
            pages.append({"page": i + 1, "text": page.get_text()})
        doc.close()
        return {"pages": pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture PDF: {str(e)}")


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    db.query(Bookmark).filter(Bookmark.document_id == document_id).delete(synchronize_session=False)

    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    audio_path = f"audio_outputs/document_{document_id}.mp3"
    if os.path.exists(audio_path):
        os.remove(audio_path)

    db.delete(document)
    db.commit()

    return {"message": "Document supprimé"}