# Castle Blueprint: The Personal TheGuru
# Based on AssemblyAIv2

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy the entire codebase
COPY . .

# Environment Defaults (To be overridden per Castle)
ENV STUDENT_ID="Master_Blueprint"
ENV HUB_API_KEY=""
ENV DEBUG="true"

# The Castle boots as a FastAPI server for the Hub to talk to
EXPOSE 8080

CMD ["python3", "castle_server.py"]
