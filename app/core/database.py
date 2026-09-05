import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Procura uma variável de ambiente chamada "DATABASE_URL" e, se não encontrar, usa a URL padrão para o banco de dados PostgreSQL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://rideready:rideready@localhost:5432/rideready",
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