from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, Base, get_db


# In-memory SQLite DB for isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
	SQLALCHEMY_DATABASE_URL,
	connect_args={"check_same_thread": False},
	poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
	try:
		db = TestingSessionLocal()
		yield db
	finally:
		db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check():
	response = client.get("/")
	assert response.status_code == 200
	assert response.json() == {"status": "healthy", "message": "Server is up and running."}


def test_create_task():
	payload = {
		"id": 1,
		"title": "Setup CI Pipeline",
		"weightage": 50,
		"completed": False,
		"category": "General"
	}
	response = client.post("/tasks/", json=payload)
	assert response.status_code == 200
	assert response.json()["title"] == "Setup CI Pipeline"


def test_weightage_metrics():
	# Add a completed task to test calculation logic
	payload = {
		"id": 2,
		"title": "Write DB Tests",
		"weightage": 25,
		"completed": True,
		"category": "General"
	}
	client.post("/tasks/", json=payload)
	
	response = client.get("/weightage/")
	assert response.status_code == 200
	data = response.json()
	
	assert data["total_tasks"] == 2
	assert data["completed_tasks"] == 1
	assert data["total_weightage"] == 75.0
	assert data["completed_weightage"] == 25.0
	assert data["completion_percentage"] == round((25.0 / 75.0) * 100, 2)
