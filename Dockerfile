# Load Python image
FROM python:3.10-slim

# standard practice - help with output and making docker image more efficient
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Set up entrypoint script
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
