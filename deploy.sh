#!/bin/bash

# Quick deployment script for RuneScape Smart Item Search
# This script helps deploy the application using Docker Compose

set -e

echo "🚀 RuneScape Smart Item Search - Deployment Script"
echo "=================================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating one from template..."
    echo "DB_PASSWORD=$(openssl rand -base64 32)" > .env
    echo "EMBEDDING_MODEL=all-MiniLM-L6-v2" >> .env
    echo "✅ Created .env file with random password"
    echo "⚠️  Please review and update .env file with your settings"
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "📦 Building and starting services..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

echo ""
echo "🔧 Initializing database..."
docker-compose exec -T backend python init_database.py || {
    echo "⚠️  Database initialization may have failed. Check logs with: docker-compose logs backend"
}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🔗 Access points:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo "   - View database: docker-compose exec db psql -U game_user -d game_items"
echo ""

