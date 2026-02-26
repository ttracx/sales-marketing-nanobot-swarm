FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

EXPOSE 8200

CMD ["uvicorn", "nanobot.api.gateway:app", "--host", "0.0.0.0", "--port", "8200"]
