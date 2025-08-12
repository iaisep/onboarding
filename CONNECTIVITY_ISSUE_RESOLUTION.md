# 🚨 Database Connectivity Issue Resolution

## 🎯 Current Status
✅ All environment variables are configured correctly
❌ Network connectivity issue: Cannot connect to `coolify.universidadisep.com:3001`

## 🔍 Problem Analysis
The container can start and has all required environment variables, but cannot establish a TCP connection to the database server. This indicates a **network/firewall issue**.

## 🛠️ Immediate Solutions to Try

### 1. 🧪 Test from Coolify Server
Run this command on your Coolify server:
```bash
# Test basic connectivity
nc -z coolify.universidadisep.com 3001

# If nc not installed
telnet coolify.universidadisep.com 3001

# Or use our comprehensive test script
curl -O https://raw.githubusercontent.com/iaisep/onboarding/main/coolify-connectivity-test.sh
chmod +x coolify-connectivity-test.sh
./coolify-connectivity-test.sh
```

### 2. 🗄️ Database Server Configuration
Check if PostgreSQL is configured to accept external connections:

```bash
# On database server, check if PostgreSQL is listening
sudo netstat -tlnp | grep :3001
# or
sudo netstat -tlnp | grep :5432

# Check PostgreSQL configuration
sudo nano /etc/postgresql/*/main/postgresql.conf
# Look for: listen_addresses = '*'  # or specific IP

# Check connection permissions
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Should include: host all all 0.0.0.0/0 md5

# Restart PostgreSQL after changes
sudo systemctl restart postgresql
```

### 3. 🔥 Firewall Configuration
Ensure port 3001 (or 5432) is open:

```bash
# Ubuntu/Debian firewall
sudo ufw allow 3001
sudo ufw status

# CentOS/RHEL firewall  
sudo firewall-cmd --permanent --add-port=3001/tcp
sudo firewall-cmd --reload

# Check if port is open
sudo ss -tlnp | grep :3001
```

### 4. 🌐 Network/Cloud Configuration
If using cloud providers:
- **AWS**: Check Security Groups allow inbound on port 3001
- **DigitalOcean**: Check Firewall rules
- **Hetzner**: Check Cloud Firewall settings
- **Custom Server**: Check network ACLs and router configuration

## 🔧 Quick Fixes

### Option A: Use Standard PostgreSQL Port
If your PostgreSQL is actually running on port 5432, update Coolify environment:
```
DB_PORT=5432
```

### Option B: Internal Database Service
If your database is another Coolify service, use the internal service name:
```
DB_HOST=postgres-service-name
DB_PORT=5432
```

### Option C: Localhost Database
If database is on the same server as Coolify:
```
DB_HOST=host.docker.internal
DB_PORT=5432
```

## 🧪 Testing Steps

1. **From Coolify server**, test connectivity:
   ```bash
   ping coolify.universidadisep.com
   nc -z coolify.universidadisep.com 3001
   ```

2. **From database server**, verify PostgreSQL:
   ```bash
   sudo -u postgres psql -c "\l"
   sudo netstat -tlnp | grep postgres
   ```

3. **Test credentials** (from any machine with PostgreSQL client):
   ```bash
   PGPASSWORD='your_password' psql -h coolify.universidadisep.com -p 3001 -U bnp_user -d bnp
   ```

## 📋 Information Needed

To help resolve this issue, please provide:

1. **Database server type**: 
   - [ ] Same server as Coolify
   - [ ] Separate server
   - [ ] Cloud managed database
   - [ ] Another Coolify service

2. **Network setup**:
   - Are both services on the same network?
   - Any firewalls between them?
   - Using custom ports?

3. **Database configuration**:
   ```bash
   # Run on database server
   sudo netstat -tlnp | grep postgres
   sudo systemctl status postgresql
   ```

4. **Connectivity test results**:
   ```bash
   # Run from Coolify server
   nc -z coolify.universidadisep.com 3001
   ```

## 🎯 Most Likely Solutions

Based on the error pattern, the issue is probably:
1. **PostgreSQL not configured for external connections** (80% likely)
2. **Firewall blocking port 3001** (15% likely)  
3. **Wrong port number** (5% likely)

Try the PostgreSQL configuration fix first! 🚀
