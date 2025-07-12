```bash
#!/bin/sh

# Wait for PostgreSQL to be ready
while ! nc -z db 5432; do
  sleep 0.1
done

# Run migrations and server
python manage.py migrate


# Check if database is empty
echo "Checking if database needs to be seeded..."
DATA_COUNT=$(python manage.py shell -c "from credits.models import Practice; print(Practice.objects.count())")

if [ "$DATA_COUNT" -eq "0" ]; then
  echo "Database is empty. Loading backup data..."
  python manage.py loaddata fixtures/backup.json
else
  echo "Database already has data. Skipping load."
fi

exec "$@"