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

# Test database connection with Python
echo "🔍 Testing database connection with Python..."
python3 << 'PYTHON_SCRIPT'
import socket
import time
import os
import sys

host = os.environ.get('DB_HOST', '')
port_str = os.environ.get('DB_PORT', '0')

if not host or port_str == '0':
    print("❌ ERROR: DB_HOST and DB_PORT environment variables must be set!")
    sys.exit(1)

port = int(port_str)
timeout = 60
start = time.time()

print(f"🌐 Network diagnostics for {host}:{port}")
print("  🔌 Port connectivity test:")

while time.time() - start < timeout:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"    ✅ Port {port} is accessible!")
            print("✅ Database is ready!")
            sys.exit(0)
        
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0:
            print(f"    ⏳ Still trying to connect... ({elapsed}s/{timeout}s)")
        
        time.sleep(2)
    except Exception as e:
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0:
            print(f"    ⏳ Connection attempt failed: {str(e)[:50]} ({elapsed}s/{timeout}s)")
        time.sleep(2)

# Timeout reached
elapsed = int(time.time() - start)
print(f"    ❌ Database connection timeout after {elapsed}s")
print("")
print("🚨 CONNECTION FAILED - Debug Information:")
print(f"  Target: {host}:{port}")
print(f"  Timeout: {timeout} seconds")
print("")
print("💡 Possible Solutions:")
print("  1. Verify database host is accessible from this network")
print(f"  2. Check if port {port} is open on the database server")
print("  3. Verify firewall/security group settings")
print(f"  4. Confirm database is running on port {port}")
print(f"  5. Test connection: python3 -c 'import socket; socket.create_connection((\"{host}\", {port}), timeout=5)'")
print("")
print("⚠️  Continuing anyway - Django will handle connection errors...")
PYTHON_SCRIPT

echo "✅ Database check complete!"

# Fix log files permissions (running as root)
echo "📝 Setting up log files and permissions..."
mkdir -p /app/logs
touch /app/logs/django.log /app/logs/aws_errors.log
chown -R django:django /app/logs
chmod -R 755 /app/logs
echo "✅ Log files permissions configured!"

# Test Python/Django setup (as django user)
echo "🧪 Testing Django setup..."
runuser -u django --preserve-environment -- python /app/manage.py check --deploy || {
  echo "⚠️  Django check failed, but continuing..."
}

# Run database migrations with verbose output (as django user)
echo "🔄 Running database migrations..."
runuser -u django --preserve-environment -- python /app/manage.py makemigrations --verbosity=2 --noinput || {
  echo "❌ makemigrations failed"
  exit 1
}

runuser -u django --preserve-environment -- python /app/manage.py migrate --verbosity=2 --noinput || {
  echo "❌ migrate failed"
  exit 1
}
echo "✅ Migrations completed successfully!"

# Collect static files (as django user)
echo "📁 Collecting static files..."
runuser -u django --preserve-environment -- python /app/manage.py collectstatic --noinput --verbosity=2 || {
  echo "⚠️  collectstatic failed, but continuing..."
}

# Create superuser if it doesn't exist (as django user)
echo "👤 Creating superuser if needed..."
runuser -u django --preserve-environment -- python /app/manage.py shell -c "
import os
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
echo "🚀 Executing command as django user: $@"

# Execute the main command as django user with proper working directory
cd /app
exec runuser -u django --preserve-environment -- "$@"
