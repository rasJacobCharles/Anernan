"""
Database models definition for Anernan.
Defines tables for users and documents with relationship mappings.
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from .management.session import Base


class User(Base):
    """
    User model representing registered system accounts.
    Supports basic standard users and administrator roles.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    uploaded_documents = relationship(
        "Document",
        back_populates="uploader",
        foreign_keys="Document.uploader_id"
    )
    approved_documents = relationship(
        "Document",
        back_populates="approver",
        foreign_keys="Document.approved_by"
    )


class Document(Base):
    """
    Document model representing files uploaded to the vault.
    Supports a lifecycle status flow: 'pending_approval' -> 'approved' or 'rejected'.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'pdf' or 'md'
    # 'pending_approval' or 'approved'
    status = Column(
        String, default="pending_approval", nullable=False
    )
    summary = Column(String, nullable=True)
    # JSON list of tags (e.g. ["AI", "Research"])
    tags = Column(JSON, nullable=True)
    folder = Column(String, nullable=True)
    uploader_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    uploader = relationship(
        "User",
        back_populates="uploaded_documents",
        foreign_keys=[uploader_id]
    )
    approver = relationship(
        "User",
        back_populates="approved_documents",
        foreign_keys=[approved_by]
    )
