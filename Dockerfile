# Use a lightweight official Python image
FROM python:3.10-slim

# Prevents Python from writing .pyc files and ensures output appears immediately
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Run the startup script
CMD ["sh", "./entrypoint.sh"]