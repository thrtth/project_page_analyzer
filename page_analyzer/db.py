import os
from contextlib import contextmanager

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

"""
 Без этой конструкции не проходят тесты на платформе Hexlet.
 Hexlet project check падает с ошибкой:
 sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres
 """
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = (DATABASE_URL
                    .replace("postgres://", "postgresql+psycopg2://"))

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


@contextmanager
def db_session():
    session = Session()
    try:
        yield session
        session.commit()
    except exc.SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()
