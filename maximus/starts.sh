#!/bin/sh

uvicorn blacklist_server.black_list:app --port 8000 &
python3 tasks/init_db.py
uvicorn tasks.reg_and_tasks:app --port 8001 &
python3 BOT/main.py &

wait
