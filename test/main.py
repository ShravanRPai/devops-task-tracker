from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_health_check():
	response = client.get("/")
	assert response.status_code == 200
	assert response.json() == {"status": "healthy", "service": "task-weightage-api"}


def test_create_task():
	payload = {
		"id": 1,
		"title": "Setup CI Pipeline",
		"weightage": 50,
		"completed": False
	}
	response = client.post("/tasks/", json=payload)
	assert response.status_code == 200
	assert response.json()["title"] == "Setup CI Pipeline"
