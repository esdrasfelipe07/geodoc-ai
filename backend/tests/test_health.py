def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "online"
    assert "GeoDoc AI" in data["message"]


def test_health_check_endpoint(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "GeoDoc AI"
    assert data["llm_provider"] == "mock"
    assert "indexed_documents_count" in data
