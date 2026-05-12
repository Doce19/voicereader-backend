from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth import decode_access_token

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token invalide")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Token expiré ou invalide")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    return user