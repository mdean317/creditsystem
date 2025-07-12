# load Python image
FROM python:3.10-slim

# standard practice - help with output and making docker image more efficient
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory inside the container
WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy the rest of the code
COPY . .

# copy entrypoint explicitly, give it the needed permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
