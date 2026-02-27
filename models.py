from sqlalchemy import Column, Integer, String, JSON, ForeignKey, create_engine, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    openrouter_key = Column(String, nullable=True)
    # New fields for enhancements
    theme = Column(String, default="dark")  # dark, light, cyberpunk, minimal
    profile_image = Column(String, nullable=True)  # Profile image URL
    portfolios = relationship("Portfolio", back_populates="owner")
    analytics = relationship("Analytics", back_populates="user", uselist=False)
    contacts = relationship("ContactSubmission", back_populates="user")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(JSON)  # Stores the generated portfolio JSON
    # New: Project links stored as JSON: {"github": "...", "demo": "..."}
    project_links = Column(JSON, nullable=True)
    owner = relationship("User", back_populates="portfolios")

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_visits = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    chat_interactions = Column(Integer, default=0)
    last_visit = Column(DateTime, nullable=True)
    visitor_ips = Column(JSON, default=list)  # Store unique IPs
    user = relationship("User", back_populates="analytics")

class ContactSubmission(Base):
    __tablename__ = "contact_submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    visitor_name = Column(String)
    visitor_email = Column(String)
    message = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="contacts")

engine = create_engine("sqlite:///./platform.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

