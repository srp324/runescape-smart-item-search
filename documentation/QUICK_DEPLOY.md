# Quick Deployment Guide

This is a simplified guide for quickly deploying the application. For detailed deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🐳 Docker Compose (Easiest Method)

### Prerequisites
- Docker and Docker Compose installed
- Git

### Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone <your-repo-url>
   cd runescape-smart-item-search
   ```

2. **Create environment file**:
   ```bash
   # Linux/macOS
   ./deploy.sh
   
   # Windows PowerShell
   .\deploy.ps1
   ```
   
   Or manually create `.env`:
   ```bash
   echo "DB_PASSWORD=your_secure_password_here" > .env
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**:
   ```bash
   docker-compose exec backend python init_database.py
   ```

5. **Verify deployment**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Access database
docker-compose exec db psql -U game_user -d game_items

# Rebuild after code changes
docker-compose up -d --build
```

## ☁️ Cloud Platform Quick Deploy

### Railway (Recommended for beginners)

1. **Connect GitHub**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository

2. **Add PostgreSQL**:
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Railway automatically provides `DATABASE_URL`

3. **Deploy Backend**:
   - Click "+ New" → "GitHub Repo"
   - Select your repo
   - Set root directory to `backend`
   - Railway will auto-detect and deploy

4. **Set Environment Variables**:
   - Go to your service → Variables
   - Add: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
   - `DATABASE_URL` is automatically set

5. **Initialize Database**:
   - Go to your backend service → Deployments
   - Click on the latest deployment → View Logs
   - Run: `railway run python init_database.py`

### Render

1. **Create Account**: [render.com](https://render.com)

2. **Deploy Backend**:
   - New → Web Service
   - Connect GitHub repo
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add PostgreSQL**:
   - New → PostgreSQL
   - Render automatically provides connection string

4. **Set Environment Variables**:
   - In your web service settings
   - Add `DATABASE_URL` (from PostgreSQL service)
   - Add `EMBEDDING_MODEL=all-MiniLM-L6-v2`

5. **Initialize Database**:
   - Use Render Shell or SSH
   - Run: `python init_database.py`

### Vercel (Web Frontend)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   cd web
   vercel
   ```

3. **Set Environment Variable**:
   - In Vercel dashboard → Project Settings → Environment Variables
   - Add: `VITE_API_URL=https://your-backend-url.com`

4. **Redeploy**:
   ```bash
   vercel --prod
   ```

## 🔧 Production Checklist

Before going live:

- [ ] Set strong database password
- [ ] Configure CORS origins (not `*`)
- [ ] Enable HTTPS for API
- [ ] Set production API URL in web app (`VITE_API_URL`)
- [ ] Enable database backups
- [ ] Set up monitoring/alerting
- [ ] Test all endpoints
- [ ] Review security settings

## 🆘 Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is correct
- Check firewall/security group rules
- Ensure database is accessible from deployment environment

### CORS Errors
- Update `CORS_ORIGINS` environment variable
- Include exact protocol (http/https) and domain
- No trailing slashes

### Web App Can't Connect
- Verify API URL in environment variables (`VITE_API_URL`)
- Check CORS configuration in backend
- Ensure backend allows web app origin

For more details, see [DEPLOYMENT.md](DEPLOYMENT.md).

