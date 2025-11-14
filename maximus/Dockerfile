
FROM python:3.11-slim

WORKDIR /app

RUN apt update -y
RUN apt install sqlite3 libsqlite3-dev -y

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/starts.sh
CMD ["/app/starts.sh"]