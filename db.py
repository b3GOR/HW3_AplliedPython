from datetime import  datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, create_engine, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from config import DB_URL




engine = create_engine(url=DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели базы данных
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    links = relationship("LinkDB", back_populates="user")

class LinkDB(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("UserDB", back_populates="links")
    stats = relationship("LinkStatsDB", back_populates="link", uselist=False, cascade="all, delete-orphan")

class LinkStatsDB(Base):
    __tablename__ = "links_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    short_link = Column(String, ForeignKey("links.short_code"), unique=True)
    access_count = Column(Integer, default=0)
    last_access = Column(DateTime, nullable=True)
    
    link = relationship("LinkDB", back_populates="stats")

Base.metadata.create_all(bind=engine)