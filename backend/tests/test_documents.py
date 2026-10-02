import io
import pytest


def create_minimal_pdf_bytes() -> bytes:
    # A tiny valid PDF binary structure for testing
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000053 00000 n \n"
        b"0000000102 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n180\n%%EOF"
    )
    return pdf_content


def test_list_documents_initially_empty(client):
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert isinstance(data["documents"], list)


def test_upload_invalid_extension(client):
    file_content = b"This is a text file, not a pdf."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("relatorio.txt", file_content, "text/plain")}
    )
    assert response.status_code == 400
    assert "apenas documentos pdf" in response.json()["detail"].lower()


def test_upload_valid_pdf_and_lifecycle(client):
    pdf_bytes = create_minimal_pdf_bytes()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("relatorio_geofisica_bacia_santos.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 201
    upload_data = response.json()
    assert "document" in upload_data
    doc = upload_data["document"]
    doc_id = doc["doc_id"]
    assert doc["filename"] == "relatorio_geofisica_bacia_santos.pdf"
    assert doc["total_pages"] >= 1

    # Verify document in listing
    list_resp = client.get("/api/v1/documents/")
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    assert any(d["doc_id"] == doc_id for d in docs)

    # Verify content endpoint for inline viewing
    content_resp = client.get(f"/api/v1/documents/{doc_id}/content")
    assert content_resp.status_code == 200
    assert "application/pdf" in content_resp.headers.get("content-type", "")
    assert "inline" in content_resp.headers.get("content-disposition", "")
    assert len(content_resp.content) > 0

    # Delete document
    del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["doc_id"] == doc_id

    # Verify not found after delete
    del_again = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_again.status_code == 404

    # Verify content also 404 after delete
    content_404 = client.get(f"/api/v1/documents/{doc_id}/content")
    assert content_404.status_code == 404
