FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# These directories are mount points for the persistent disk at runtime
RUN mkdir -p data sessions

EXPOSE 8447

CMD ["python", "checkMeIn.py", "container.conf"]
