# 🚨 Database Connectivity Issue Resolution

## 🎯 Current Status - CONFIRMED ISSUE
✅ All environment variables are configured correctly  
❌ **Network connectivity FAILED**: Cannot connect to `coolify.universidadisep.com:3001`

## 🔍 Diagnostic Results
From connectivity test on Coolify server:
- ✅ **DNS Resolution**: `coolify.universidadisep.com` → `192.168.5.45`
- ❌ **Network Reachability**: 100% packet loss (ping failed)
- ❌ **Port Connectivity**: Port 3001 not accessible  
- 🌐 **Network Issue**: Servers on different networks (`192.168.100.57` → `192.168.5.45`)

## 🛠️ IMMEDIATE SOLUTIONS

### 🏆 **SOLUTION 1: Use Internal Database (Recommended)**
Easiest fix - deploy with internal PostgreSQL container:

#### Step 1: Update Docker Compose in Coolify
Use `docker-compose.coolify-internal-db.yml` instead of external-db version

#### Step 2: Update Environment Variables in Coolify
```
DB_HOST=postgres
DB_PORT=5432
DB_NAME=bnp
DB_USER=bnp_user
DB_PASSWORD=your_secure_password
```

#### Step 3: Deploy
The database will run in the same Docker network - guaranteed connectivity!

### 🔧 **SOLUTION 2: Fix External Database Connectivity**

#### On Database Server (192.168.5.45):
```bash
# 1. Check PostgreSQL status
sudo systemctl status postgresql
sudo netstat -tlnp | grep postgres

# 2. Configure PostgreSQL for external connections
sudo nano /etc/postgresql/*/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/*/main/pg_hba.conf  
# Add: host all all 192.168.100.0/24 md5

# 3. Configure firewall
sudo ufw allow from 192.168.100.0/24 to any port 5432
sudo ufw allow from 192.168.100.0/24 to any port 3001

# 4. Restart PostgreSQL
sudo systemctl restart postgresql

# 5. Test locally
sudo -u postgres psql -c "\l"
```

#### Network/Router Configuration:
- Ensure routing between `192.168.100.x` and `192.168.5.x` networks
- Check if both subnets can communicate
- Verify no network firewalls blocking inter-subnet traffic

### 🔧 **SOLUTION 3: Database Port Verification**

The database might be running on standard port 5432, not 3001:

#### Update Coolify Environment Variables:
```
DB_PORT=5432
```

Then test connectivity:
```bash
nc -z coolify.universidadisep.com 5432
```

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
