from __future__ import annotations
from datetime import datetime, UTC
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text
from app.database import Base
from pathlib import Path
from sqlalchemy import JSON

# class User(Base):
#     __tablename__ = "users"

#     id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     username:Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
#     email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
#     password_hash:Mapped[str] = mapped_column(String, nullable=False)
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(UTC))


class Document(Base):
    __tablename__ = "documents"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stored_filename: Mapped[str] = mapped_column(String(200),nullable=False)
    original_filename:Mapped[str] = mapped_column(String(200), nullable=False)
    uploaded_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(UTC))
    questions:Mapped[list[Question]] = relationship(back_populates="document", cascade="all, delete-orphan")
    summary: Mapped[Summary] = relationship(back_populates="document", uselist=False, cascade="all, delete-orphan")
    extraction:Mapped[Extraction] = relationship(back_populates="document", uselist=False, cascade="all, delete-orphan")
    analysis: Mapped["DocumentAnalysis"] = relationship(back_populates="document", uselist=False, cascade="all, delete-orphan")

    @property
    def filepath(self) -> str:
        return str(
            Path("uploads")/self.stored_filename
        )
    
    @property
    def file_exists(self) -> bool:
        return Path(self.filepath).exists()


class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"),unique=True, nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(100),nullable=False)
    summary: Mapped[str] = mapped_column(Text)
    extracted_json: Mapped[dict] = mapped_column(JSON)
    faq_json: Mapped[list[dict]] = mapped_column(JSON)
    generated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(UTC))
    document: Mapped["Document"] = relationship(back_populates="analysis")



class Question(Base):
    __tablename__ = "questions"
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id:Mapped[int] = mapped_column(Integer, ForeignKey("documents.id",ondelete="CASCADE"), nullable=False , index=True)
    question: Mapped[str] = mapped_column(Text)
    answer:Mapped[str] = mapped_column(Text)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(UTC))
    document:Mapped[Document] = relationship(back_populates="questions")



class Summary(Base):
    __tablename__ = "summaries"
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id:Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False , index=True)
    summary_text:Mapped[str] = mapped_column(Text)
    generated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(UTC))
    document:Mapped[Document] = relationship(back_populates="summary")


class Extraction(Base):
    __tablename__ = "extractions"
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id:Mapped[int] = mapped_column(Integer, ForeignKey("documents.id",ondelete="CASCADE"),unique=True, nullable=False , index=True)
    extracted_json: Mapped[dict] = mapped_column(JSON)
    generated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(UTC))
    document:Mapped[Document] = relationship(back_populates="extraction")
