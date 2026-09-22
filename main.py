# Doc string
"""
Task Weightage API - Track tasks and calculate dynamic weightage distribution

Supports:
	Task creation
	Weightage calculation
	Health checks
"""


# Imports
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os


# PostgreSQL connection
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-service")
DB_NAME = os.getenv("POSTGRES_DB", "tasktracker")

# Construct the SQLAlchemy URL
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# Create engine object and bind to session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy ORM Model
class TaskDB(Base):
	__tablename__ = "tasks"
	
	id = Column(Integer, primary_key=True, index=True)
	title = Column(String, nullable=False)
	weightage = Column(Float, nullable=False)
	completed = Column(Boolean, default=False)
	category = Column(String, default="General")


# Initialize all tables
Base.metadata.create_all(bind=engine)


# App object
app = FastAPI(
	title="Task Weightage API",
	version="1.0.0",
	description="Backend API for tracking tasks and calculating dynamic weightage distribution",
)


# Pydantic Schemas
class Task(BaseModel):
	id: int
	title: str
	weightage: float = Field(..., gt=0, le=100, description="Task weightage between 0 and 100")
	completed: bool = False
	category: Optional[str] = "General"
	
	class Config:
		from_attributes = True


class WeightageMetrics(BaseModel):
	total_tasks: int
	completed_tasks: int
	total_weightage: float
	completed_weightage: float
	completion_percentage: float


# Database Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


# Endpoints
@app.get("/", tags=["Health"])
def health_check():
	return {"status": "healthy", "message": "Server is up and running."}


@app.get("/tasks/", response_model=List[Task], tags=["Tasks"])
def list_tasks(db: Session = Depends(get_db)):
	return db.query(TaskDB).all()


@app.get("/tasks/{task_id}", response_model=Task | None, tags=["Tasks"])
def get_task(task_id: int, db: Session = Depends(get_db)):
	return db.query(TaskDB).filter(TaskDB.id == task_id).first()


@app.post("/tasks/", response_model=Task, tags=["Tasks"])
def create_task(task: Task, db: Session = Depends(get_db)):
	if db.query(TaskDB).filter(TaskDB.id == task.id).first():
		raise HTTPException(status_code=400, detail=f"Task with id {task.id} already exists")
	
	db_task = TaskDB(**task.model_dump())
	db.add(db_task)
	db.commit()
	db.refresh(db_task)
	return db_task


@app.get("/weightage/", response_model=WeightageMetrics, tags=["Analytics"])
def calculate_weightage(db: Session = Depends(get_db)):
	tasks = db.query(TaskDB).all()
	
	if not tasks:
		return WeightageMetrics(
			total_tasks=0, completed_tasks=0, total_weightage=0.0, completed_weightage=0.0, completion_percentage=0.0
		)
	
	total_tasks = len(tasks)
	completed_tasks = sum(1 for task in tasks if task.completed)
	total_weightage = sum(task.weightage for task in tasks)
	completed_weightage = sum(task.weightage for task in tasks if task.completed)
	
	completion_percentage = (completed_weightage / total_weightage) * 100 if total_weightage > 0 else 0.0
	
	return WeightageMetrics(
		total_tasks=total_tasks,
		completed_tasks=completed_tasks,
		total_weightage=round(total_weightage, 2),
		completed_weightage=round(completed_weightage, 2),
		completion_percentage=round(completion_percentage, 2),
	)
