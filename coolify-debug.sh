#!/bin/bash

# Coolify Debug Script
# Run this in your Coolify server to debug Django deployment

echo "🔍 COOLIFY DJANGO DEBUG INFORMATION"
echo "=================================="

# Check system info
echo "📊 System Information:"
echo "  - OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo "  - Docker version: $(docker --version)"
echo "  - Available memory: $(free -h | grep ^Mem | awk '{print $2}')"
echo "  - Available disk: $(df -h / | tail -1 | awk '{print $4}')"

# Check environment variables
echo ""
echo "🌍 Environment Variables:"
echo "  - DB_HOST: ${DB_HOST:-'NOT SET'}"
echo "  - DB_PORT: ${DB_PORT:-'NOT SET'}"
echo "  - DB_NAME: ${DB_NAME:-'NOT SET'}"
echo "  - DB_USER: ${DB_USER:-'NOT SET'}"
echo "  - SECRET_KEY: ${SECRET_KEY:0:10}... (truncated)"
echo "  - DEBUG: ${DEBUG:-'NOT SET'}"
echo "  - ALLOWED_HOSTS: ${ALLOWED_HOSTS:-'NOT SET'}"

# Test database connection
echo ""
echo "🗄️  Testing Database Connection:"
if command -v nc &> /dev/null; then
    if nc -z $DB_HOST $DB_PORT 2>/dev/null; then
        echo "  ✅ Database connection successful"
    else
        echo "  ❌ Database connection failed"
        echo "     - Host: $DB_HOST"
        echo "     - Port: $DB_PORT"
    fi
else
    echo "  ⚠️  netcat not available, cannot test connection"
fi

# Test DNS resolution
echo ""
echo "🌐 DNS Resolution Test:"
if command -v nslookup &> /dev/null; then
    echo "  - Testing registry-1.docker.io:"
    nslookup registry-1.docker.io 2>&1 | head -5
else
    echo "  ⚠️  nslookup not available"
fi

# Check if Django can start
echo ""
echo "🐍 Django Check:"
if [ -f "manage.py" ]; then
    echo "  - manage.py found"
    python manage.py check --verbosity=0 2>&1 | head -10
else
    echo "  ❌ manage.py not found"
fi

# Container resources
echo ""
echo "📦 Container Resources:"
echo "  - CPU cores: $(nproc)"
echo "  - Container memory limit: $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo 'unlimited')"

echo ""
echo "🔚 Debug information collection complete!"
echo "📋 If you see issues, please check:"
echo "   1. Database connection parameters"
echo "   2. DNS resolution for Docker registry"
echo "   3. Environment variables are set correctly"
echo "   4. Container has enough resources"
