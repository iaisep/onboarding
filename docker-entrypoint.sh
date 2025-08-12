#!/bin/bash

set -e

echo "🚀 Starting Django application..."
echo "📊 Environment info:"
echo "  - User: $(whoami)"
echo "  - Working directory: $(pwd)"
echo "  - Python version: $(python --version)"

# Check all required environment variables
echo "🔍 Checking required environment variables..."
REQUIRED_VARS=(
  "SECRET_KEY"
  "DB_NAME"
  "DB_USER" 
  "DB_PASSWORD"
  "DB_HOST"
  "DB_PORT"
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "AWS_S3_BUCKET"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    MISSING_VARS+=($var)
    echo "  ❌ $var: NOT SET"
  else
    if [[ "$var" == *"PASSWORD"* ]] || [[ "$var" == *"KEY"* ]]; then
      echo "  ✅ $var: ******* (hidden)"
    else
      echo "  ✅ $var: ${!var}"
    fi
  fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
  echo ""
  echo "❌ ERROR: Missing required environment variables:"
  printf '   - %s\n' "${MISSING_VARS[@]}"
  echo ""
  echo "📋 Please set these variables in Coolify environment configuration:"
  echo "   1. Go to your Coolify application settings"
  echo "   2. Navigate to 'Environment Variables' section"  
  echo "   3. Add the missing variables listed above"
  echo "   4. Refer to .env.coolify.example for guidance"
  echo ""
  exit 1
fi

# Wait for database to be ready
echo "⏳ Waiting for database..."
echo "  - Host: ${DB_HOST:-'NOT SET'}"
echo "  - Port: ${DB_PORT:-'NOT SET'}"
echo "  - Name: ${DB_NAME:-'NOT SET'}"
echo "  - User: ${DB_USER:-'NOT SET'}"

# Check if required variables are set
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  echo "❌ ERROR: DB_HOST and DB_PORT environment variables must be set!"
  echo "Current environment variables:"
  env | grep -E '^(DB_|DATABASE_)' || echo "No DB variables found"
  exit 1
fi

# Test database connection with timeout
echo "🔍 Testing database connection..."
TIMEOUT=60
ELAPSED=0

# Test if netcat is available
if ! command -v nc &> /dev/null; then
  echo "❌ netcat (nc) is not available. Installing..."
  apt-get update && apt-get install -y netcat-openbsd
fi

while ! nc -z $DB_HOST $DB_PORT; do
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "❌ Database connection timeout after ${TIMEOUT}s"
    echo "Debug information:"
    echo "  - Trying to connect to: $DB_HOST:$DB_PORT"
    echo "  - Network test:"
    ping -c 1 $DB_HOST || echo "  - Host unreachable"
    echo "  - DNS resolution:"
    nslookup $DB_HOST || echo "  - DNS resolution failed"
    exit 1
  fi
  echo "⏳ Waiting for database connection... (${ELAPSED}s/${TIMEOUT}s)"
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done
echo "✅ Database is ready!"

# Test Python/Django setup
echo "🧪 Testing Django setup..."
python manage.py check --deploy || {
  echo "⚠️  Django check failed, but continuing..."
}

# Run database migrations with verbose output
echo "🔄 Running database migrations..."
python manage.py makemigrations --verbosity=2 --noinput || {
  echo "❌ makemigrations failed"
  exit 1
}

python manage.py migrate --verbosity=2 --noinput || {
  echo "❌ migrate failed"
  exit 1
}
echo "✅ Migrations completed successfully!"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --verbosity=2 || {
  echo "⚠️  collectstatic failed, but continuing..."
}

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apibase.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created successfully!')
else:
    print(f'Superuser {username} already exists.')
" || {
  echo "⚠️  Superuser creation failed, but continuing..."
}

echo "🎉 Setup complete! Starting application..."
echo "🚀 Executing command: $@"

# Execute the main command
exec "$@"
