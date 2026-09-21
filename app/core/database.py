import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Obtém a URL de conexão com o PostgreSQL a partir das variáveis de ambiente.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "A variável de ambiente DATABASE_URL não está configurada."
    )

# Objeto que gerencia a conexão entre SQLAlchemy e PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Cria uma fábrica de sessões para interagir com o banco de dados
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Define a base class para os modelos do SQLAlchemy
class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()