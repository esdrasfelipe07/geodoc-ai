def test_chat_validation_short_question(client):
    response = client.post("/api/v1/chat/", json={"question": "a"})
    assert response.status_code == 422  # Pydantic validation error


def test_chat_successful_response(client):
    payload = {
        "question": "Qual a profundidade do horizonte refletor e a velocidade sísmica?",
        "top_k": 3
    }
    response = client.post("/api/v1/chat/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert data["provider"] == "mock"


def test_chat_stream_endpoint(client):
    payload = {
        "question": "Descreva as características estratigráficas do reservatório.",
        "top_k": 2
    }
    response = client.post("/api/v1/chat/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Inspect stream content
    body = response.text
    assert "event: sources" in body
    assert "event: delta" in body
    assert "event: done" in body
