#!/bin/bash

# ==============================================
# Coolify Database Connectivity Test
# ==============================================
# Run this script from your Coolify server to test database connectivity

DB_HOST="${DB_HOST:-coolify.universidadisep.com}"
DB_PORT="${DB_PORT:-3001}"
DB_NAME="${DB_NAME:-bnp}"
DB_USER="${DB_USER:-bnp_user}"

echo "🔍 Testing Database Connectivity from Coolify Server"
echo "=================================================="
echo "Target: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Test 1: DNS Resolution
echo "1. 🌐 DNS Resolution Test:"
if nslookup $DB_HOST; then
    echo "   ✅ DNS resolution successful"
    RESOLVED_IP=$(nslookup $DB_HOST | grep -A1 "Name:" | grep "Address:" | head -1 | awk '{print $2}' 2>/dev/null || echo "unknown")
    echo "   📍 Resolved IP: $RESOLVED_IP"
else
    echo "   ❌ DNS resolution failed"
    echo "   💡 Check if domain exists: $DB_HOST"
fi
echo ""

# Test 2: Network Reachability
echo "2. 🏓 Network Reachability Test:"
if ping -c 3 -W 5 $DB_HOST; then
    echo "   ✅ Host is reachable"
else
    echo "   ❌ Host is not reachable"
    echo "   💡 Check network connectivity and firewall rules"
fi
echo ""

# Test 3: Port Connectivity
echo "3. 🔌 Port Connectivity Test:"
if nc -z -v -w5 $DB_HOST $DB_PORT; then
    echo "   ✅ Port $DB_PORT is open and accessible"
else
    echo "   ❌ Port $DB_PORT is not accessible"
    echo "   💡 Common issues:"
    echo "      - Database not running"
    echo "      - Port closed by firewall"
    echo "      - Database not configured to accept external connections"
fi
echo ""

# Test 4: Check if other common database ports are open
echo "4. 🔍 Database Port Scan:"
echo "   Testing common database ports..."
for port in 5432 3306 1521 1433 3000 3001 3002; do
    if nc -z -w2 $DB_HOST $port 2>/dev/null; then
        if [ "$port" = "$DB_PORT" ]; then
            echo "   ✅ Port $port (target port) - OPEN"
        else
            echo "   ℹ️  Port $port - OPEN (different database?)"
        fi
    fi
done
echo ""

# Test 5: PostgreSQL Connection Test (if psql is available)
echo "5. 🗄️ PostgreSQL Connection Test:"
if command -v psql >/dev/null 2>&1; then
    echo "   Testing PostgreSQL connection..."
    if [ -n "$DB_PASSWORD" ]; then
        export PGPASSWORD="$DB_PASSWORD"
        if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\q" 2>/dev/null; then
            echo "   ✅ PostgreSQL connection successful"
        else
            echo "   ❌ PostgreSQL connection failed"
            echo "   💡 Check credentials and database permissions"
        fi
        unset PGPASSWORD
    else
        echo "   ⏭️ Skipped (DB_PASSWORD not provided)"
    fi
else
    echo "   ⏭️ Skipped (psql not installed)"
    echo "   💡 Install with: apt-get install postgresql-client"
fi
echo ""

# Test 6: Network Information
echo "6. 🌐 Network Information:"
echo "   Local IP addresses:"
ip addr show 2>/dev/null | grep "inet " | sed 's/^/   /'
echo ""
echo "   Routing to database host:"
ip route get $RESOLVED_IP 2>/dev/null | sed 's/^/   /' || echo "   ❌ Cannot determine route"
echo ""

# Test 7: DNS Server Information
echo "7. 🔍 DNS Configuration:"
echo "   DNS servers:"
cat /etc/resolv.conf | grep nameserver | sed 's/^/   /'
echo ""

echo "=================================================="
echo "🎯 Summary and Recommendations:"
echo ""

# Provide specific recommendations based on results
if nc -z -w2 $DB_HOST $DB_PORT 2>/dev/null; then
    echo "✅ CONNECTIVITY: Database is reachable on $DB_HOST:$DB_PORT"
    echo "💡 If Django still can't connect, check:"
    echo "   - Database credentials (DB_USER, DB_PASSWORD)"
    echo "   - Database name (DB_NAME)"
    echo "   - PostgreSQL configuration (pg_hba.conf, postgresql.conf)"
    echo "   - Database user permissions"
else
    echo "❌ CONNECTIVITY: Cannot reach database on $DB_HOST:$DB_PORT"
    echo "💡 Next steps:"
    echo "   1. Verify database server is running"
    echo "   2. Check firewall rules (both host and network)"
    echo "   3. Verify database is configured to accept external connections"
    echo "   4. Test from database server: netstat -tlnp | grep $DB_PORT"
    echo "   5. Check security groups/network ACLs"
fi
echo ""

echo "🛠️ Quick fixes to try:"
echo "   - On database server: systemctl status postgresql"
echo "   - Check PostgreSQL config: sudo nano /etc/postgresql/*/main/postgresql.conf"
echo "   - Verify listen_addresses = '*' or specific IP"
echo "   - Check pg_hba.conf for connection permissions"
echo "   - Restart database: sudo systemctl restart postgresql"
echo ""

echo "📞 Include this output when requesting support!"
