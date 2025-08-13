#!/bin/bash

# Coolify DNS Fix Script
# This script addresses common DNS resolution issues in Coolify deployments

echo "🔧 Starting Coolify DNS troubleshooting..."

# 1. Check current DNS configuration
echo "📋 Current DNS configuration:"
cat /etc/resolv.conf

echo ""
echo "🧪 Testing DNS resolution:"

# 2. Test basic connectivity
echo "Testing basic connectivity..."
ping -c 2 8.8.8.8 || echo "❌ No internet connectivity"

# 3. Test DNS resolution
echo "Testing DNS resolution..."
nslookup registry-1.docker.io || echo "❌ Cannot resolve Docker registry"
nslookup pypi.org || echo "❌ Cannot resolve PyPI"

# 4. Alternative DNS servers to try
echo ""
echo "🔄 Applying DNS fixes..."

# Backup original resolv.conf
cp /etc/resolv.conf /etc/resolv.conf.backup

# Try Google DNS
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
echo "options timeout:2 attempts:3" >> /etc/resolv.conf

echo "✅ DNS configuration updated"
echo "📋 New DNS configuration:"
cat /etc/resolv.conf

# Test again
echo ""
echo "🧪 Testing with new DNS configuration:"
nslookup registry-1.docker.io && echo "✅ Docker registry resolved" || echo "❌ Still cannot resolve Docker registry"
nslookup pypi.org && echo "✅ PyPI resolved" || echo "❌ Still cannot resolve PyPI"

echo ""
echo "🏁 DNS fix script completed"
echo "💡 If issues persist, check Coolify server's network configuration"
