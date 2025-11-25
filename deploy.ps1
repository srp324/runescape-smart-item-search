# Quick deployment script for RuneScape Smart Item Search (Windows PowerShell)
# This script helps deploy the application using Docker Compose

Write-Host "🚀 RuneScape Smart Item Search - Deployment Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  No .env file found. Creating one from template..." -ForegroundColor Yellow
    $randomPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    @"
DB_PASSWORD=$randomPassword
EMBEDDING_MODEL=all-MiniLM-L6-v2
"@ | Out-File -FilePath .env -Encoding utf8
    Write-Host "✅ Created .env file with random password" -ForegroundColor Green
    Write-Host "⚠️  Please review and update .env file with your settings" -ForegroundColor Yellow
    Write-Host ""
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose is not installed. Please install it and try again." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Building and starting services..." -ForegroundColor Cyan
docker-compose up -d --build

Write-Host ""
Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "🔧 Initializing database..." -ForegroundColor Cyan
docker-compose exec -T backend python init_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Database initialization may have failed. Check logs with: docker-compose logs backend" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🔗 Access points:" -ForegroundColor Cyan
Write-Host "   - API: http://localhost:8000"
Write-Host "   - API Docs: http://localhost:8000/docs"
Write-Host "   - Health Check: http://localhost:8000/health"
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "   - View logs: docker-compose logs -f"
Write-Host "   - Stop services: docker-compose down"
Write-Host "   - Restart services: docker-compose restart"
Write-Host "   - View database: docker-compose exec db psql -U game_user -d game_items"
Write-Host ""

