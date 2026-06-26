import os
from app.models.document import Document
from app.models.bookmark import Bookmark
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    ChangePassword,
    ForgotPassword,
    UserUpdate,
)
from app.services.auth import hash_password, verify_password, create_access_token
from app.services.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Aucun compte trouvé avec cet email")

    user.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès"}

@router.post("/change-password")
def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")

    user.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"message": "Mot de passe modifié avec succès"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    email_exists = db.query(User).filter(
        User.email == data.email,
        User.id != current_user.id
    ).first()

    if email_exists:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    username_exists = db.query(User).filter(
        User.username == data.username,
        User.id != current_user.id
    ).first()

    if username_exists:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")

    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.email = data.email
    user.username = data.username

    db.commit()
    db.refresh(user)

    return user

@router.delete("/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    documents = db.query(Document).filter(Document.user_id == user.id).all()

    for document in documents:
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except OSError:
                pass

    db.query(Bookmark).filter(Bookmark.user_id == user.id).delete(synchronize_session=False)

    document_ids = [document.id for document in documents]
    if document_ids:
        db.query(Bookmark).filter(Bookmark.document_id.in_(document_ids)).delete(synchronize_session=False)

    db.query(Document).filter(Document.user_id == user.id).delete(synchronize_session=False)

    db.delete(user)
    db.commit()

    return {"message": "Compte supprimé avec succès"}