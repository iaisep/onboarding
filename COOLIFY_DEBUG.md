# 🐛 Coolify Deployment Debug Guide

## 🎯 Problem: Django App Stops After "Starting Django application..."

### 📊 Symptoms
- Logs show: "🚀 Starting Django application..."
- Logs show: "⏳ Waiting for database..."
- **Process stops here** - no further migration or server startup

### 🔍 Common Causes & Solutions

#### 1. 🗄️ Database Connection Issues

**Check Database Configuration:**
```bash
# In Coolify Environment Variables, verify:
DB_HOST=your-postgres-host.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

**Test Connection Manually:**
```bash
# SSH into your Coolify server and test:
nc -z your-postgres-host.com 5432
# Should return immediately if successful
```

#### 2. 🌐 DNS Resolution Problems

**If you see DNS errors:**
```bash
# Add to Coolify Environment Variables:
EXTRA_HOSTS=registry-1.docker.io:54.230.82.71
```

**Or in docker-compose override:**
```yaml
services:
  app:
    extra_hosts:
      - "registry-1.docker.io:54.230.82.71"
      - "your-postgres-host.com:YOUR_DB_IP"
```

#### 3. 🔐 Permissions & User Issues

The container runs as `django` user. If migrations fail:

```dockerfile
# In Dockerfile, ensure proper permissions:
RUN chown -R django:django /app
USER django
```

#### 4. 🐳 Container Resource Limits

**Check if container has enough resources:**
```bash
# Minimum recommended:
- Memory: 512MB
- CPU: 0.5 cores
```

#### 5. ⏱️ Timeout Issues

**Long migration times might cause timeout:**
```yaml
# In docker-compose, increase timeouts:
services:
  app:
    deploy:
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 5
```

### 🛠️ Debug Steps

#### Step 1: Enable Verbose Logging
Add to Coolify Environment Variables:
```env
PYTHONUNBUFFERED=1
DJANGO_LOG_LEVEL=DEBUG
DEBUG=True  # Only for debugging, set to False in production
```

#### Step 2: Use Debug Entrypoint
The updated `docker-entrypoint.sh` now includes:
- ✅ Connection timeout (60s limit)
- ✅ Verbose migration output
- ✅ Better error handling
- ✅ Environment info logging

#### Step 3: Manual Container Testing
```bash
# Run container manually to test:
docker run -it --env-file coolify-debug.env your-image:latest /bin/bash

# Then manually run commands:
./docker-entrypoint.sh python manage.py runserver 0.0.0.0:8000
```

#### Step 4: Check Coolify Logs
```bash
# In Coolify interface:
1. Go to your application
2. Click "Logs" tab
3. Enable "Stream Logs" 
4. Look for specific error messages after "Starting Django application..."
```

### 🚨 Critical Environment Variables

**Required for Django:**
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,*.coolify.io
DJANGO_SETTINGS_MODULE=apibase.settings
```

**Required for Database:**
```env
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=your-database
DB_USER=your-user
DB_PASSWORD=your-password
```

**Required for AWS (if using S3):**
```env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=your-bucket
AWS_DEFAULT_REGION=us-east-1
```

### 🔧 Quick Fixes

#### Fix 1: Database Connection Timeout
```bash
# Increase timeout in docker-entrypoint.sh:
TIMEOUT=120  # Increase from 60 to 120 seconds
```

#### Fix 2: Migration Lock Issues
```bash
# Clear Django migration locks:
docker exec -it container-name python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("DELETE FROM django_migrations WHERE app = 'your_app' AND name = '0001_initial';")
```

#### Fix 3: Static Files Permission
```bash
# Ensure static directory exists with proper permissions
mkdir -p /app/static
chown django:django /app/static
```

### 📋 Troubleshooting Checklist

- [ ] Database host/port accessible from container
- [ ] All environment variables set correctly
- [ ] DNS resolution working (test with `nslookup registry-1.docker.io`)
- [ ] Container has sufficient memory (>512MB)
- [ ] No firewall blocking database port
- [ ] Database user has proper permissions
- [ ] Secret key is set and valid
- [ ] ALLOWED_HOSTS includes your domain
- [ ] Static files directory has proper permissions

### 🆘 Emergency Recovery

If nothing works, use this minimal entrypoint for debugging:

```bash
#!/bin/bash
echo "🚀 EMERGENCY DEBUG MODE"
echo "Environment: $(env | grep DB_)"
echo "Testing connection: nc -z $DB_HOST $DB_PORT"
nc -z $DB_HOST $DB_PORT && echo "✅ DB OK" || echo "❌ DB FAIL"
echo "Starting shell for manual debugging..."
exec /bin/bash
```

Replace the entrypoint temporarily to get shell access and debug manually.

### 📞 Getting Help

When reporting issues, include:
1. Full Coolify logs from deployment
2. Environment variables (sanitized)
3. Database connection test results
4. Output of `coolify-debug.sh` script
