from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.services.pdf import save_pdf, extract_text
from app.services.dependencies import get_current_user
import uuid
from app.services.tts import text_to_speech
from fastapi.responses import FileResponse
import fitz
from fastapi.responses import FileResponse as FastAPIFileResponse
import os
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
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
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents
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

    return FastAPIFileResponse(
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
    import os
    logger.info(f"Audio request for document {document_id}")

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        logger.error("Document not found in DB")
        raise HTTPException(status_code=404, detail="Document introuvable en BDD")

    logger.info(f"File path: {document.file_path}")
    logger.info(f"File exists: {os.path.exists(document.file_path)}")
    logger.info(f"Current dir: {os.getcwd()}")
    logger.info(f"Uploads dir exists: {os.path.exists('uploads')}")

    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier PDF introuvable: {document.file_path}"
        )

    try:
        doc = fitz.open(document.file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        logger.info(f"Text extracted: {len(full_text)} characters")
    except Exception as e:
        logger.error(f"PDF read error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lecture PDF: {str(e)}")

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte extractible")

    try:
        logger.info(f"Starting TTS with lang={lang} genre={genre}")
        audio_path = text_to_speech(full_text, document_id, lang=lang, genre=genre)
        logger.info(f"Audio generated: {audio_path}")
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")

    return FileResponse(audio_path, media_type="audio/mpeg", filename=f"document_{document_id}.mp3")
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

    document.last_page = page
    db.commit()
    return {"message": f"Progression sauvegardee à la page {page}"}
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

    import fitz
    doc = fitz.open(document.file_path)
    pages = []
    for i, page in enumerate(doc):
        pages.append({"page": i + 1, "text": page.get_text()})
    doc.close()
    return {"pages": pages}
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

    # Supprime d'abord les signets liés
    from app.models.bookmark import Bookmark
    db.query(Bookmark).filter(Bookmark.document_id == document_id).delete()

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    audio_path = f"audio_outputs/document_{document_id}.mp3"
    if os.path.exists(audio_path):
        os.remove(audio_path)

    db.delete(document)
    db.commit()
    return {"message": "Document supprimé"}