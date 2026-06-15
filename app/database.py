from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

# Nettoyage strict et forçage des arguments SSL
if DATABASE_URL:
    # Correction de l'ancien préfixe de Render
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Suppression des paramètres existants s'ils gèrent mal le SSL
    if "?" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.split("?")[0]

# Création de l'engine avec les arguments de connexion natifs de psycopg2
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "sslmode": "require",
        "target_session_attrs": "read-write"
    },
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()