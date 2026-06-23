import os
import shutil
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup environment variables for testing
TEMP_VAULT = os.path.abspath("./vault_test_integration")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["VAULT_BASE_DIR"] = TEMP_VAULT

from app.main import app
from app.orm.management.session import Base
from app.orm import get_db, models
from app.authenticate import authentication, authorisation
from app.routers import documents

from sqlalchemy.pool import StaticPool

# Override DB dependency
TestingEngine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TestingEngine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database_and_vault():
    # Override directories in router
    documents.VAULT_BASE = TEMP_VAULT
    documents.QUARANTINE_DIR = os.path.join(TEMP_VAULT, "quarantine")
    documents.ACTIVE_DIR = os.path.join(TEMP_VAULT, "active")
    
    os.makedirs(documents.QUARANTINE_DIR, exist_ok=True)
    os.makedirs(documents.ACTIVE_DIR, exist_ok=True)
    
    Base.metadata.create_all(bind=TestingEngine)
    db = TestingSessionLocal()
    
    # Create standard user
    user = models.User(
        id=str(uuid.uuid4()),
        username="user",
        hashed_password=authentication.get_password_hash("userpass"),
        is_admin=False
    )
    
    # Create admin user
    admin = models.User(
        id=str(uuid.uuid4()),
        username="admin",
        hashed_password=authentication.get_password_hash("adminpass"),
        is_admin=True
    )
    
    db.add(user)
    db.add(admin)
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=TestingEngine)
    if os.path.exists(TEMP_VAULT):
        shutil.rmtree(TEMP_VAULT)

client = TestClient(app)

def get_auth_header(username: str) -> dict:
    token = authorisation.create_access_token(data={"sub": username})
    return {"Authorization": f"Bearer {token}"}

def test_document_lifecycle_integration():
    user_headers = get_auth_header("user")
    admin_headers = get_auth_header("admin")
    
    # 1. Upload a document as user
    file_content = b"Integration test PDF content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {
        "pre_parsed_markdown": "Companion Markdown Text",
        "summary": "Sample summary",
        "tags": '["test", "integration"]'
    }
    
    response = client.post("/api/v1/documents/upload", files=files, data=data, headers=user_headers)
    assert response.status_code == 201
    doc_res = response.json()
    doc_id = doc_res["id"]
    assert doc_res["filename"] == "test.pdf"
    assert doc_res["status"] == "pending_approval"
    assert doc_res["tags"] == ["test", "integration"]
    
    # Verify files saved in quarantine
    quarantine_file = os.path.join(documents.QUARANTINE_DIR, f"{doc_id}_test.pdf")
    companion_file = os.path.join(documents.QUARANTINE_DIR, f"{doc_id}_test.md")
    assert os.path.exists(quarantine_file)
    assert os.path.exists(companion_file)
    
    # 2. Standard user tries to list pending documents (Should fail - 403)
    response = client.get("/api/v1/pending", headers=user_headers)
    assert response.status_code == 403
    
    # 3. Admin lists pending documents (Should succeed - 200)
    response = client.get("/api/v1/pending", headers=admin_headers)
    assert response.status_code == 200
    pending_list = response.json()
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == doc_id
    
    # 4. Standard user tries to approve (Should fail - 403)
    response = client.post(f"/api/v1/pending/{doc_id}", headers=user_headers)
    assert response.status_code == 403
    
    # 5. Admin approves document (Should succeed - 200)
    response = client.post(f"/api/v1/pending/{doc_id}", headers=admin_headers)
    assert response.status_code == 200
    approved_res = response.json()
    assert approved_res["status"] == "approved"
    assert approved_res["approved_by"] is not None
    
    # Verify files moved to active
    active_file = os.path.join(documents.ACTIVE_DIR, f"{doc_id}_test.pdf")
    active_companion = os.path.join(documents.ACTIVE_DIR, f"{doc_id}_test.md")
    assert not os.path.exists(quarantine_file)
    assert not os.path.exists(companion_file)
    assert os.path.exists(active_file)
    assert os.path.exists(active_companion)
    
    # Upload another file to reject
    files = {"file": ("reject.pdf", b"Reject content", "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files, data=data, headers=user_headers)
    reject_doc_id = response.json()["id"]
    
    reject_quarantine_file = os.path.join(documents.QUARANTINE_DIR, f"{reject_doc_id}_reject.pdf")
    reject_companion_file = os.path.join(documents.QUARANTINE_DIR, f"{reject_doc_id}_reject.md")
    assert os.path.exists(reject_quarantine_file)
    assert os.path.exists(reject_companion_file)
    
    # 6. Standard user tries to reject (Should fail - 403)
    response = client.delete(f"/api/v1/pending/{reject_doc_id}", headers=user_headers)
    assert response.status_code == 403
    
    # 7. Admin rejects document (Should succeed - 200)
    response = client.delete(f"/api/v1/pending/{reject_doc_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "Document successfully rejected and deleted."
    
    # Verify files are deleted from quarantine
    assert not os.path.exists(reject_quarantine_file)
    assert not os.path.exists(reject_companion_file)


def test_document_subfolder_lifecycle_integration():
    user_headers = get_auth_header("user")
    admin_headers = get_auth_header("admin")
    
    # Upload PDF with folder path Work/Research/DeepMind
    file_content = b"Subfolder PDF content"
    files = {"file": ("subfolder_test.pdf", file_content, "application/pdf")}
    data = {
        "pre_parsed_markdown": "Subfolder companion text",
        "summary": "Subfolder test summary",
        "tags": '["subfolder"]',
        "folder": "Work/Research/DeepMind"
    }
    
    response = client.post("/api/v1/documents/upload", files=files, data=data, headers=user_headers)
    assert response.status_code == 201
    doc_res = response.json()
    doc_id = doc_res["id"]
    assert doc_res["folder"] == "Work/Research/DeepMind"
    
    # Approve
    response = client.post(f"/api/v1/pending/{doc_id}", headers=admin_headers)
    assert response.status_code == 200
    
    # Verify file moved to target subfolder structure inside active directory
    target_dir = os.path.join(documents.ACTIVE_DIR, "Work", "Research", "DeepMind")
    active_pdf = os.path.join(target_dir, f"{doc_id}_subfolder_test.pdf")
    active_md = os.path.join(target_dir, f"{doc_id}_subfolder_test.md")
    
    assert os.path.exists(active_pdf)
    assert os.path.exists(active_md)
    with open(active_pdf, "rb") as f:
        assert f.read() == file_content


def test_search_and_retrieval_endpoints():
    user_headers = get_auth_header("user")
    admin_headers = get_auth_header("admin")

    # 1. Upload Doc 1 (approved md)
    doc1_content = b"# Design Study\nA study of interface aesthetics."
    files = {"file": ("design.md", doc1_content, "text/markdown")}
    data = {
        "summary": "A design study about aesthetic interfaces.",
        "tags": '["UI", "Aesthetics"]',
        "folder": "Work/Design"
    }
    res1 = client.post("/api/v1/documents/upload", files=files, data=data, headers=user_headers)
    assert res1.status_code == 201
    doc1_id = res1.json()["id"]

    # Approve Doc 1
    client.post(f"/api/v1/pending/{doc1_id}", headers=admin_headers)

    # 2. Upload Doc 2 (approved pdf with companion markdown)
    pdf_content = b"PDF data"
    files = {"file": ("paper.pdf", pdf_content, "application/pdf")}
    data = {
        "pre_parsed_markdown": "This is the AI paper content in markdown.",
        "summary": "Machine learning paper.",
        "tags": '["AI", "DeepMind"]',
        "folder": "Work/Research"
    }
    res2 = client.post("/api/v1/documents/upload", files=files, data=data, headers=user_headers)
    assert res2.status_code == 201
    doc2_id = res2.json()["id"]

    # Approve Doc 2
    client.post(f"/api/v1/pending/{doc2_id}", headers=admin_headers)

    # 3. Upload Doc 3 (pending md, will not be approved)
    doc3_content = b"# Pasta Recipe\nHow to make pasta."
    files = {"file": ("pasta.md", doc3_content, "text/markdown")}
    data = {
        "summary": "Delicious dinner recipe.",
        "tags": '["Cooking"]',
        "folder": "Personal/Recipes"
    }
    res3 = client.post("/api/v1/documents/upload", files=files, data=data, headers=user_headers)
    assert res3.status_code == 201
    doc3_id = res3.json()["id"]

    # 4. Try querying search endpoint without token (should fail with 401)
    response = client.get("/api/v1/search")
    assert response.status_code == 401

    # 5. Search with q
    # Search for "aesthetic"
    response = client.get("/api/v1/search", params={"q": "aesthetic"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == doc1_id

    # Search for "Cooking" (should be empty as Doc 3 is pending)
    response = client.get("/api/v1/search", params={"q": "Cooking"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0

    # 6. Search with tag
    # Search tag "UI"
    response = client.get("/api/v1/search", params={"tag": "UI"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == doc1_id

    # Search tag "AI"
    response = client.get("/api/v1/search", params={"tag": "AI"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == doc2_id

    # Search tag "Cooking" (should be empty)
    response = client.get("/api/v1/search", params={"tag": "Cooking"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0

    # 7. Search with folder
    # Filter folder "Work/Design"
    response = client.get("/api/v1/search", params={"folder": "Work/Design"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == doc1_id

    # Filter folder "Work" (should match both Doc 1 and Doc 2 via subfolder matching)
    response = client.get("/api/v1/search", params={"folder": "Work"}, headers=user_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    ids = {r["id"] for r in results}
    assert ids == {doc1_id, doc2_id}

    # Filter folder "Personal" (should be empty because Doc 3 is pending)
    response = client.get("/api/v1/search", params={"folder": "Personal"}, headers=user_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

    # 8. Retrieve document content
    # Retrieve Doc 1 (approved markdown)
    response = client.get(f"/api/v1/documents/{doc1_id}", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc1_id
    assert data["content"] == "# Design Study\nA study of interface aesthetics."

    # Retrieve Doc 2 (approved PDF with companion markdown)
    response = client.get(f"/api/v1/documents/{doc2_id}", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc2_id
    assert data["content"] == "This is the AI paper content in markdown."

    # Retrieve Doc 3 (pending, should return 403 Forbidden)
    response = client.get(f"/api/v1/documents/{doc3_id}", headers=user_headers)
    assert response.status_code == 403

    # Retrieve non-existent document
    response = client.get("/api/v1/documents/non-existent-id", headers=user_headers)
    assert response.status_code == 404

