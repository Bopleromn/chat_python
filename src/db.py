from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import config


engine = create_engine(config.DB_URL)
SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
