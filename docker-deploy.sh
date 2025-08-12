#!/bin/bash

# BNP Docker Deployment Script

echo "🚀 BNP Docker Deployment Script"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📋 Creating .env from template..."
    cp .env.example .env
    echo "✅ Please update .env file with your actual configuration values"
    echo "🔧 Required variables:"
    echo "   - SECRET_KEY (generate a new one)"
    echo "   - DB_NAME, DB_USER, DB_PASSWORD"
    echo "   - AWS credentials"
    echo "   - ALLOWED_HOSTS"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🔨 Building and starting containers..."

# Build and start services
docker-compose up -d --build

echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Application URL: http://localhost:8000"
    echo "🗄️  Database: PostgreSQL on localhost:5432"
    echo "📱 Admin Panel: http://localhost:8000/admin"
    echo ""
    echo "📋 Default superuser credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo "   (Change these in production!)"
    echo ""
    echo "📝 Useful commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop services: docker-compose down"
    echo "   - Restart: docker-compose restart"
    echo ""
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose logs
fi
