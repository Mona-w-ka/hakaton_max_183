import sqlite3
import json
import os

con = sqlite3.connect("db.sqlite")

con.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER,
        segment TEXT,
        seed INTEGER,
        num_resolved_tasks INTEGER
    )
""")

con.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER,
        segment TEXT
    )
""")

def create_task_table(jsonl_file):
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            segment = obj["segment"]
            con.execute("INSERT INTO tasks (id, segment) VALUES (?, ?)", (i, segment))

create_task_table("tasks.jsonl")

con.commit()
con.close()
