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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# App object
app = FastAPI(
	title="Task Weightage API",
	version="1.0.0",
	description="Backend API for tracking tasks and calculating dynamic weightage distribution",
)


# In-memory data store
tasks_db: List["Task"] = []


# Task object
class Task(BaseModel):
	id: int
	title: str
	weightage: float = Field(..., gt=0, le=100, description="Task weightage between 0 and 100")
	completed: bool = False
	category: Optional[str] = "General"


# Weightage object
class WeightageMetrics(BaseModel):
	total_tasks: int
	completed_tasks: int
	total_weightage: float
	completed_weightage: float
	completion_percentage: float


# Endpoints
@app.get("/", tags=["Health"])
def health_check():
	return {"status": "healthy", "message": "Server is up and running."}


@app.get("/tasks/", response_model=List[Task], tags=["Tasks"])
def list_tasks():
	return tasks_db


@app.get("/tasks/{task_id}", response_model=Task|None, tags=["Tasks"])
def get_task(task_id: int):
	return tasks_db[task_id] if len(tasks_db) > task_id else None


@app.post("/tasks/", response_model=Task, tags=["Tasks"])
def create_task(task: Task):
	if any(t.id == task.id for t in tasks_db):
		raise HTTPException(status_code=400, detail=f"Task with id {task.id} already exists")
	tasks_db.append(task)
	return task


@app.get("/weightage/", response_model=WeightageMetrics, tags=["Analytics"])
def calculate_weightage():
	if not tasks_db:
		return WeightageMetrics(
			total_tasks=0, completed_tasks=0, total_weightage=0.0, completed_weightage=0.0, completion_percentage=0.0
		)
	
	total_tasks = len(tasks_db)
	completed_tasks = sum(1 for task in tasks_db if task.completed)
	total_weightage = sum(task.weightage for task in tasks_db)
	completed_weightage = sum(task.weightage for task in tasks_db if task.completed)
	
	completion_percentage = (completed_weightage / total_weightage) * 100 if total_weightage > 0 else 0.0
	
	return WeightageMetrics(
		total_tasks=total_tasks,
		completed_tasks=completed_tasks,
		total_weightage=round(total_weightage, 2),
		completed_weightage=round(completed_weightage, 2),
		completion_percentage=round(completion_percentage, 2),
	)
