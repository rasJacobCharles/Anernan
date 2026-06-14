"""
Document management and ingestion routes for Anernan.
Provides endpoints for uploading documents, listing pending documents,
approving documents, and rejecting documents.
"""

import os
import uuid
import json
import shutil
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..dependencies import get_current_user, get_current_admin

router = APIRouter(
    tags=["Documents"]
)

# Vault storage path configuration
VAULT_BASE = os.environ.get("VAULT_BASE_DIR", "/vault")

try:
    QUARANTINE_DIR = os.path.join(VAULT_BASE, "quarantine")
    ACTIVE_DIR = os.path.join(VAULT_BASE, "active")
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    os.makedirs(ACTIVE_DIR, exist_ok=True)
except Exception:
    # Fallback to project-relative vault directory on systems with restricted root access (e.g. macOS development)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    VAULT_BASE = os.path.join(BASE_DIR, "vault")
    QUARANTINE_DIR = os.path.join(VAULT_BASE, "quarantine")
    ACTIVE_DIR = os.path.join(VAULT_BASE, "active")
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    os.makedirs(ACTIVE_DIR, exist_ok=True)


@router.post("/api/v1/documents/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    pre_parsed_markdown: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Handle document upload, perform MIME-type validation, store the file in the
    quarantined directory, and save the metadata record in the database as pending approval.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename."
        )

    # Perform MIME-type validation and determine the file type
    ext = os.path.splitext(filename)[1].lower()
    content_type = file.content_type

    if ext == ".pdf" and content_type == "application/pdf":
        file_type = "pdf"
    elif ext in (".md", ".markdown") and content_type in ("text/markdown", "text/plain", "application/octet-stream"):
        file_type = "md"
    elif ext == ".pdf":
        file_type = "pdf"
    elif ext in (".md", ".markdown"):
        file_type = "md"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF and Markdown (.md) files are permitted."
        )

    # Parse JSON-encoded tags if provided
    parsed_tags = None
    if tags:
        try:
            parsed_tags = json.loads(tags)
            if not isinstance(parsed_tags, list):
                raise ValueError("Tags must be a JSON array (list of strings).")
            # Ensure all elements are strings
            if not all(isinstance(t, str) for t in parsed_tags):
                raise ValueError("All tags must be strings.")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for tags."
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )

    # Generate unique ID and target path in quarantine
    doc_id = str(uuid.uuid4())
    # Save the original file with the UUID prefixed to guarantee uniqueness
    saved_filename = f"{doc_id}_{filename}"
    file_path = os.path.join(QUARANTINE_DIR, saved_filename)

    try:
        # Read file content and write it to the quarantine directory
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # If pre-parsed markdown text is provided for a PDF, save it as a companion markdown file
        if file_type == "pdf" and pre_parsed_markdown:
            companion_md_path = os.path.splitext(file_path)[0] + ".md"
            with open(companion_md_path, "w", encoding="utf-8") as f:
                f.write(pre_parsed_markdown)
    except Exception as e:
        # Clean up any partially written files in case of failure
        if os.path.exists(file_path):
            os.remove(file_path)
        companion_md_path = os.path.splitext(file_path)[0] + ".md"
        if os.path.exists(companion_md_path):
            os.remove(companion_md_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # Create the database record
    new_doc = models.Document(
        id=doc_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        status="pending_approval",
        summary=summary,
        tags=parsed_tags,
        uploader_id=current_user.id
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return new_doc


@router.get("/api/v1/admin/pending", response_model=List[schemas.DocumentResponse])
def list_pending_documents(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin)
):
    """
    List all documents currently pending admin review.
    """
    pending_docs = db.query(models.Document).filter(models.Document.status == "pending_approval").all()
    return pending_docs


@router.post("/api/v1/admin/documents/{id}/approve", response_model=schemas.DocumentResponse)
def approve_document(
    id: str,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Approve a pending document, transitioning status to approved,
    moving the physical file(s) to the active directory, and logging approval metadata.
    """
    doc = db.query(models.Document).filter(models.Document.id == id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    if doc.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not pending approval."
        )

    old_file_path = doc.file_path
    new_file_path = os.path.join(ACTIVE_DIR, os.path.basename(old_file_path))

    # Ensure the physical file exists in quarantine
    if not os.path.exists(old_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical document file not found in quarantine."
        )

    try:
        # Move the primary file to the active directory
        shutil.move(old_file_path, new_file_path)

        # Check and move companion markdown file if it exists
        old_companion_md = os.path.splitext(old_file_path)[0] + ".md"
        if os.path.exists(old_companion_md):
            new_companion_md = os.path.splitext(new_file_path)[0] + ".md"
            shutil.move(old_companion_md, new_companion_md)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move document file to active storage: {str(e)}"
        )

    # Update database record status and metadata
    doc.status = "approved"
    doc.file_path = new_file_path
    doc.approved_at = datetime.datetime.utcnow()
    doc.approved_by = current_admin.id

    db.commit()
    db.refresh(doc)

    return doc


@router.post("/api/v1/admin/documents/{id}/reject")
def reject_document(
    id: str,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Reject a pending document, removing the physical file(s) from quarantine
    and deleting the database record.
    """
    doc = db.query(models.Document).filter(models.Document.id == id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    if doc.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending documents can be rejected."
        )

    old_file_path = doc.file_path

    # Try to remove physical files from quarantine
    try:
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        old_companion_md = os.path.splitext(old_file_path)[0] + ".md"
        if os.path.exists(old_companion_md):
            os.remove(old_companion_md)
    except Exception as e:
        # Log error or raise HTTP error, but we want to ensure db cleanup is still possible
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document files from quarantine: {str(e)}"
        )

    # Delete the database record
    db.delete(doc)
    db.commit()

    return {"detail": "Document successfully rejected and deleted."}
