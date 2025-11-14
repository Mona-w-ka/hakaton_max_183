import json
import math
import sqlite3
import random
from fastapi import FastAPI, HTTPException
from typing import List, Literal
from pydantic import BaseModel, Field
import time

DB_PATH = "db.sqlite"
JSONL_PATH = "tasks.jsonl"

def next_prime(n):
    n = max(n, 2)
    while not is_prime(n):
        n += 1
    return n

def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(math.isqrt(n))
    for i in range(3, r + 1, 2):
        if n % i == 0:
            return False
    return True

class RandomPermutationGenerator:
    def __init__(self, N, seed):
        if N <= 0:
            raise ValueError("N must be positive")
        self.N = N
        self.m = next_prime(N)
        self.a = 1664525
        self.c = 1013904223
        self.state = seed % self.m
        self.seed = seed
        self.generated = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.generated >= self.N:
            self.state = self.seed
        while True:
            self.state = (self.a * self.state + self.c) % self.m
            if self.state < self.N:
                self.generated += 1
                return self.state

class GeneratorsCollection:
    def __init__(self):
        self.collection = {}

    def get_next(self, seed: int, N: int) -> int:
        key = (seed, N)
        if key not in self.collection:
            self.collection[key] = RandomPermutationGenerator(N, seed)
        return next(self.collection[key])

TASKS_DATA: list = []
SEGMENT_TO_TASK_IDS: dict = {}
coll = GeneratorsCollection()
app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,  
        timeout=10.0
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    print("BD")
    return conn

def init_app():
    global TASKS_DATA, SEGMENT_TO_TASK_IDS

    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER,
            segment TEXT,
            seed INTEGER,
            num_resolved_tasks INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER,
            segment TEXT
        )
    """)
    conn.commit()
    conn.close()

    validated_tasks = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                task = PhishingTask.model_validate_json(line)
                validated_tasks.append(task)
            except Exception as e:
                print(f"Validation error on line {line_num}: {e}")
                raise SystemExit("Server is down")

    TASKS_DATA = validated_tasks
    print("Tasks downloaded")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, segment FROM tasks ORDER BY id")
    SEGMENT_TO_TASK_IDS.clear()
    for task_id, segment in cursor:
        if segment not in SEGMENT_TO_TASK_IDS:
            SEGMENT_TO_TASK_IDS[segment] = []
        SEGMENT_TO_TASK_IDS[segment].append(task_id)
    cursor.close()
    conn.close()

class RegisterRequest(BaseModel):
    user_id: int
    segment: Literal["middle_school", "senior_school", "students", "millennials", "retirees"]
    
class DeleteRequest(BaseModel):
    user_id: int

class TaskRequest(BaseModel):
    user_id: int

class PhishingTask(BaseModel):
    situation: str
    question: str
    variants_of_answers: List[str] = Field(..., min_length=4, max_length=4)
    explanation: List[str] = Field(..., min_length=4, max_length=4)
    theme: str
    segment: str
    is_phishing: Literal[0, 1]
    
@app.on_event("startup")
def startup_event():
    import os
    print(os.path.exists("db.sqlite"))
    init_app()

@app.post("/register")
def register_user(data: RegisterRequest):
    conn = get_db_connection()
    print(data.segment)
    try:
        seed = random.randint(1, 2**31 - 1)
        conn.execute(
            "INSERT INTO users (id, segment, seed, num_resolved_tasks) VALUES (?, ?, ?, ?)",
            (data.user_id, data.segment, seed, 0)
        )
        conn.commit()
        return {"status": 1}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: user may exist")
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"DB error: {str(e)}")
    finally:
        conn.close()

@app.post("/delete")
def delete_user(data: DeleteRequest):
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM users WHERE id = ?", (data.user_id,)
            )
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"DB error: {str(e)}")
    finally:
        conn.close()

@app.post("/task")
def assign_next_task(data: TaskRequest):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT segment, seed, num_resolved_tasks FROM users WHERE id = ?",
            (data.user_id,)
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        segment, seed, num_resolved = row
        task_ids = SEGMENT_TO_TASK_IDS.get(segment, [])
        total = len(task_ids)
        print(total)

        perm_index = coll.get_next(seed, total)
        task_id = task_ids[perm_index]
        if task_id >= len(TASKS_DATA) or task_id < 0:
            raise HTTPException(status_code=500, detail="Task ID out of bounds")
        conn.execute(
            "UPDATE users SET num_resolved_tasks = num_resolved_tasks + 1 WHERE id = ?",
            (data.user_id,)
        )
        conn.commit()

        return TASKS_DATA[task_id]

    finally:
        conn.close()
