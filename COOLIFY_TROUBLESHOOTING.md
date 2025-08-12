# 🚀 Coolify Deployment Troubleshooting Guide

## ❌ Problem: Container Stuck at "⏳ Waiting for database..."

This indicates that the database connection is failing. Here's how to fix it:

## 🔧 Solution Steps

### 1. 📋 Check Environment Variables in Coolify

Go to your Coolify application → **Environment Variables** and ensure ALL required variables are set:

#### 🗄️ Database Variables (CRITICAL)
```
DB_NAME=your_database_name
DB_USER=your_database_user  
DB_PASSWORD=your_database_password
DB_HOST=your_database_host_ip_or_domain
DB_PORT=5432
```

#### 🔐 Django Variables
```
SECRET_KEY=your-super-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost
```

#### ☁️ AWS Variables
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
AWS_DEFAULT_REGION=us-east-1
```

### 2. 🔍 Verify Database Host Configuration

#### External Database Host Examples:
- **IP Address**: `192.168.1.100`
- **Domain**: `db.example.com`
- **Another Coolify service**: `postgres-service`
- **Cloud provider**: `your-db.amazonaws.com`

⚠️ **Common Mistakes:**
- Using `localhost` or `127.0.0.1` (won't work in containers)
- Wrong port number (PostgreSQL default is `5432`)
- Database not accepting external connections

### 3. 🛠️ Test Database Connection

#### From Coolify Terminal:
```bash
# Test if database host is reachable
ping your_database_host

# Test if database port is open
nc -z your_database_host 5432

# Test DNS resolution
nslookup your_database_host
```

#### Using Docker exec:
```bash
docker exec -it your_container_name bash
nc -z $DB_HOST $DB_PORT
```

### 4. 📊 Check Application Logs

In Coolify logs, look for:
- ✅ `Environment info` section showing all variables
- ❌ `ERROR: Missing required environment variables`
- ❌ `Database connection timeout`

## 🐛 Common Issues & Solutions

### Issue 1: Environment Variables Not Set
**Symptom**: `ERROR: Missing required environment variables`
**Solution**: Add missing variables in Coolify Environment Variables section

### Issue 2: Database Host Unreachable
**Symptom**: `Database connection timeout after 60s`
**Solutions**:
- Verify database host IP/domain
- Check if database accepts external connections
- Verify firewall/security group settings
- Test connectivity from Coolify server

### Issue 3: Wrong Database Port
**Symptom**: Connection timeout or refused
**Solution**: 
- PostgreSQL: port `5432`
- MySQL: port `3306`
- Verify actual port in database configuration

### Issue 4: Database Authentication
**Symptom**: Connection established but authentication fails
**Solutions**:
- Verify DB_USER and DB_PASSWORD are correct
- Check if user has proper permissions
- Verify database exists (DB_NAME)

## 📝 Debug Commands

### Enhanced Logging
The container now includes comprehensive logging. Check these sections:

1. **Environment Check**: All required variables validation
2. **Database Connection**: Network connectivity test  
3. **Django Check**: Application configuration validation
4. **Migrations**: Database schema updates
5. **Static Files**: Asset collection
6. **Superuser**: Admin user creation

### Manual Testing
```bash
# Connect to running container
docker exec -it container_name bash

# Test database manually
python manage.py dbshell

# Check Django configuration
python manage.py check --deploy

# Test migrations
python manage.py showmigrations
```

## ✅ Success Indicators

When working correctly, logs should show:
```
🚀 Starting Django application...
✅ All required environment variables present
✅ Database is ready!
✅ Migrations completed successfully!
🎉 Setup complete! Starting application...
```

## 🆘 Still Not Working?

1. **Copy logs** from Coolify and check for specific error messages
2. **Verify network connectivity** between Coolify and database
3. **Test database connection** from another tool/application
4. **Check database server logs** for connection attempts
5. **Verify Coolify network configuration**

## 📞 Support Information

Include this information when asking for help:
- Database type and version
- Database host type (cloud/self-hosted/Coolify service)
- Coolify version
- Complete error logs
- Network setup (VPC, firewall rules, etc.)
