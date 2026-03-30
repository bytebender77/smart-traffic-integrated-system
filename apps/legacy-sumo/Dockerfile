FROM python:3.11-slim

WORKDIR /app

# Install SUMO and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sumo sumo-tools libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV SUMO_HOME=/usr/share/sumo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
