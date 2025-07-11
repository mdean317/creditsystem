```bash
#!/bin/sh

# Wait for PostgreSQL to be ready
while ! nc -z db 5432; do
  sleep 0.1
done

# Run migrations and server
python manage.py migrate
exec "$@"

```bash
chmod +x entrypoint.sh
```