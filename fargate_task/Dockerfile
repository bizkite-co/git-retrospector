# Base Stage: Install OS packages and uv
FROM python:3.11-slim as base

WORKDIR /app

# Install git and curl, then uv, then cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*

# Add uv to PATH - Corrected path
ENV PATH="/root/.local/bin:${PATH}"

# Application Stage: Install dependencies and copy application code
FROM base as application

WORKDIR /app

# Copy requirements and install Python dependencies using uv
COPY requirements.txt .
RUN uv pip install --no-cache --system -r requirements.txt

# Copy the application script
COPY process_single_commit_task.py .

# Define the command to run the application
CMD ["python", "process_single_commit_task.py"]
