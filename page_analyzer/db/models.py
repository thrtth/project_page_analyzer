from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Urls(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime)


class UrlChecks(Base):
    __tablename__ = 'url_checks'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('urls.id'))
    status_code = Column(Integer)
    h1 = Column(Text)
    title = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime)
    url = relationship("Urls")
