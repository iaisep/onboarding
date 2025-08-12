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
  echo "📦 Installing networking tools..."
  apt-get update -qq && apt-get install -y -qq netcat-openbsd iputils-ping dnsutils
fi

# First, test basic network connectivity
echo "🌐 Network diagnostics for $DB_HOST:$DB_PORT"

# Test DNS resolution
echo "  🔍 DNS Resolution:"
if nslookup $DB_HOST > /dev/null 2>&1; then
  echo "    ✅ DNS resolved successfully"
  RESOLVED_IP=$(nslookup $DB_HOST | grep -A1 "Name:" | grep "Address:" | head -1 | awk '{print $2}' || echo "unknown")
  echo "    📍 Resolved to: $RESOLVED_IP"
else
  echo "    ❌ DNS resolution failed"
fi

# Test basic connectivity (ping)
echo "  🏓 Ping test:"
if ping -c 1 -W 3 $DB_HOST > /dev/null 2>&1; then
  echo "    ✅ Host is reachable"
else
  echo "    ❌ Host is not reachable via ping"
fi

# Test port connectivity with detailed feedback
echo "  🔌 Port connectivity test:"
while ! nc -z $DB_HOST $DB_PORT; do
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "    ❌ Database connection timeout after ${TIMEOUT}s"
    echo ""
    echo "🚨 CONNECTION FAILED - Debug Information:"
    echo "  Target: $DB_HOST:$DB_PORT"
    echo "  Timeout: ${TIMEOUT} seconds"
    
    # Additional network debugging
    echo ""
    echo "🔍 Advanced Network Diagnostics:"
    echo "  - Testing connectivity to common ports..."
    
    # Test if host responds to any common ports
    for test_port in 22 80 443 5432 3000; do
      if nc -z -w2 $DB_HOST $test_port 2>/dev/null; then
        echo "    ✅ Port $test_port is open on $DB_HOST"
      fi
    done
    
    # Show routing information
    echo "  - Route to host:"
    ip route get $RESOLVED_IP 2>/dev/null || echo "    ❌ Cannot determine route"
    
    # Check if we're in the right network
    echo "  - Container network info:"
    ip addr show 2>/dev/null | grep "inet " | head -3
    
    echo ""
    echo "💡 Possible Solutions:"
    echo "  1. Verify database host is accessible from this network"
    echo "  2. Check if port $DB_PORT is open on the database server"
    echo "  3. Verify firewall/security group settings"
    echo "  4. Confirm database is running on port $DB_PORT"
    echo "  5. Test connection from Coolify host: nc -z $DB_HOST $DB_PORT"
    
    exit 1
  fi
  
  if [ $((ELAPSED % 10)) -eq 0 ]; then
    echo "    ⏳ Still trying to connect... (${ELAPSED}s/${TIMEOUT}s)"
  fi
  
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done
echo "    ✅ Port $DB_PORT is accessible!"
echo "✅ Database is ready!"

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
