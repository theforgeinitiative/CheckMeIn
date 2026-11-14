# Pinned to 3.10: several pins in requirements.txt have no wheels for newer Pythons.
FROM python:3.10-slim

# Timestamps are stored as naive local time, so the container must run in the
# building's timezone or new visits won't line up with existing data.
ENV PYTHONUNBUFFERED=1 \
    TZ=America/New_York \
    DATA_DIR=/data

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# DATA_DIR is a mounted volume, so the sessions directory has to be created at
# start rather than build time.
CMD ["sh", "-c", "mkdir -p \"$DATA_DIR/sessions\" && exec python checkMeIn.py container.conf"]
