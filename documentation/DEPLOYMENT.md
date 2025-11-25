# Deployment Guide

This guide covers deployment options for the RuneScape Smart Item Search application.

## Table of Contents

1. [Backend Deployment](#backend-deployment)
2. [Web Frontend Deployment](#web-frontend-deployment)
3. [Database Setup](#database-setup)
4. [Environment Configuration](#environment-configuration)

---

## Backend Deployment

The backend is a FastAPI application that requires PostgreSQL with pgvector extension.

### Option 1: Docker Deployment (Recommended)

#### Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Create docker-compose.yml

Create `docker-compose.yml` in the root directory:

```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: game_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: game_items
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U game_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://game_user:${DB_PASSWORD}@db:5432/game_items
      EMBEDDING_MODEL: all-MiniLM-L6-v2
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Deploy with Docker Compose

```bash
# Create .env file
echo "DB_PASSWORD=your_secure_password_here" > .env

# Start services
docker-compose up -d

# Initialize database
docker-compose exec backend python init_database.py

# View logs
docker-compose logs -f backend
```

### Option 2: Cloud Platform Deployment

#### Railway

1. **Create `railway.json`** in `backend/`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. **Deploy**:
   - Connect your GitHub repo to Railway
   - Add PostgreSQL service (Railway supports pgvector)
   - Set environment variables
   - Deploy

#### Render

1. **Create `render.yaml`** in root:
```yaml
services:
  - type: web
    name: runescape-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: runescape-db
          property: connectionString
      - key: EMBEDDING_MODEL
        value: all-MiniLM-L6-v2

databases:
  - name: runescape-db
    databaseName: game_items
    user: game_user
    plan: starter
```

2. **Deploy**: Push to GitHub and connect to Render

#### AWS (Elastic Beanstalk / ECS)

**Elastic Beanstalk:**
1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init -p python-3.11`
3. Create environment: `eb create`
4. Set environment variables in AWS Console
5. Use AWS RDS PostgreSQL with pgvector

**ECS (Docker):**
1. Build and push Docker image to ECR
2. Create ECS task definition
3. Use AWS RDS for PostgreSQL
4. Deploy to ECS cluster

#### Google Cloud Platform

1. **Cloud Run** (Serverless):
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/runescape-api
gcloud run deploy runescape-api \
  --image gcr.io/PROJECT_ID/runescape-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

2. Use **Cloud SQL** for PostgreSQL (requires manual pgvector installation)

#### Heroku

1. **Create `Procfile`** in `backend/`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. **Deploy**:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:standard-0
heroku config:set EMBEDDING_MODEL=all-MiniLM-L6-v2
git push heroku main
```

**Note**: Heroku PostgreSQL doesn't support pgvector by default. Consider using a custom buildpack or alternative database.

### Option 3: Traditional VPS Deployment

#### Using Nginx + Gunicorn

1. **Install dependencies**:
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib
```

2. **Setup application**:
```bash
cd /opt
git clone your-repo-url runescape-api
cd runescape-api/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

3. **Create systemd service** (`/etc/systemd/system/runescape-api.service`):
```ini
[Unit]
Description=RuneScape API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/runescape-api/backend
Environment="PATH=/opt/runescape-api/backend/venv/bin"
ExecStart=/opt/runescape-api/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

4. **Nginx configuration** (`/etc/nginx/sites-available/runescape-api`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. **Enable and start**:
```bash
sudo systemctl enable runescape-api
sudo systemctl start runescape-api
sudo ln -s /etc/nginx/sites-available/runescape-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

6. **SSL with Let's Encrypt**:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Web Frontend Deployment

The web frontend is a React + Vite application that builds to static files.

### Option 1: Static Hosting (Recommended)

#### Vercel

1. **Install Vercel CLI**:
```bash
npm i -g vercel
```

2. **Deploy**:
```bash
cd web
vercel
```

Or connect GitHub repo to Vercel dashboard.

3. **Environment Variables**:
   - Set `VITE_API_URL` to your backend API URL

#### Netlify

1. **Create `netlify.toml`** in `web/`:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

2. **Deploy**:
   - Connect GitHub repo to Netlify
   - Set build command: `npm run build`
   - Set publish directory: `dist`
   - Set environment variable: `VITE_API_URL`

#### Cloudflare Pages

1. **Deploy via GitHub**:
   - Connect repository
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Set environment variable: `VITE_API_URL`

#### GitHub Pages

1. **Update `vite.config.ts`**:
```typescript
export default defineConfig({
  base: '/your-repo-name/',
  // ... rest of config
})
```

2. **Deploy script** in `package.json`:
```json
{
  "scripts": {
    "deploy": "npm run build && gh-pages -d dist"
  }
}
```

3. **Deploy**:
```bash
npm install -g gh-pages
npm run deploy
```

### Option 2: Traditional Web Server

#### Nginx

1. **Build the application**:
```bash
cd web
npm install
npm run build
```

2. **Nginx configuration**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/runescape-web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

3. **Deploy**:
```bash
sudo cp -r dist/* /var/www/runescape-web/dist/
sudo systemctl reload nginx
```

---

## Database Setup

### Managed PostgreSQL Services

#### AWS RDS
1. Create RDS PostgreSQL instance
2. Install pgvector extension:
```sql
CREATE EXTENSION vector;
```
3. Update `DATABASE_URL` in backend environment

#### Google Cloud SQL
1. Create Cloud SQL PostgreSQL instance
2. Connect and install pgvector (may require custom build)
3. Update connection string

#### Supabase
1. Create Supabase project
2. Enable pgvector extension in SQL editor:
```sql
CREATE EXTENSION vector;
```
3. Use connection string from Supabase dashboard

#### Neon
1. Create Neon project
2. Run in SQL editor:
```sql
CREATE EXTENSION vector;
```
3. Use connection string

### Self-Hosted PostgreSQL

See [SETUP.md](SETUP.md) for detailed instructions on installing PostgreSQL with pgvector.

---

## Environment Configuration

### Backend Environment Variables

Create `.env` file in `backend/`:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/game_items

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Server (for production, use environment variables from platform)
HOST=0.0.0.0
PORT=8000

# CORS Origins (comma-separated)
CORS_ORIGINS=https://your-web-domain.com
```

### Web Frontend Environment Variables

Create `.env.production` in `web/`:

```env
VITE_API_URL=https://your-api-domain.com
```


---

## Production Checklist

### Backend
- [ ] Use production-grade PostgreSQL (managed service recommended)
- [ ] Enable SSL/TLS for database connections
- [ ] Set strong database passwords
- [ ] Configure proper CORS origins (not `*`)
- [ ] Enable HTTPS for API
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Implement rate limiting
- [ ] Add API authentication (JWT tokens)
- [ ] Use environment variables for secrets
- [ ] Set up health check monitoring
- [ ] Configure auto-scaling (if using cloud platform)

### Web Frontend
- [ ] Build optimized production bundle
- [ ] Set correct API URL in environment variables
- [ ] Enable HTTPS
- [ ] Configure CDN for static assets
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Test on all target browsers
- [ ] Optimize images and assets


### Database
- [ ] Enable automated backups
- [ ] Set up replication (if needed)
- [ ] Monitor database performance
- [ ] Optimize vector index parameters
- [ ] Set connection pooling limits
- [ ] Configure database firewall rules

---

## Monitoring & Maintenance

### Recommended Tools

1. **Application Monitoring**: 
   - Sentry (error tracking)
   - Datadog / New Relic (APM)
   - LogRocket (session replay)

2. **Database Monitoring**:
   - pgAdmin
   - Cloud provider monitoring tools
   - Custom health check endpoints

3. **Uptime Monitoring**:
   - UptimeRobot
   - Pingdom
   - StatusCake

### Health Checks

The backend includes a health check endpoint:
```
GET /health
```

Use this for:
- Load balancer health checks
- Monitoring services
- Kubernetes liveness/readiness probes

---

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `DATABASE_URL` is correct
   - Check firewall rules
   - Ensure database is accessible from deployment environment

2. **CORS Errors**
   - Update `CORS_ORIGINS` in backend
   - Verify frontend URL matches allowed origins

3. **pgvector Extension Not Found**
   - Ensure PostgreSQL version supports pgvector
   - Run `CREATE EXTENSION vector;` manually
   - Use managed service with pgvector support

4. **Web App Can't Connect**
   - Verify API URL in environment variables
   - Check CORS configuration
   - Ensure backend allows web app origin

---

## Cost Estimates

### Small Scale (100-1000 users/day)

- **Backend**: $5-20/month (Railway, Render free tier, or small VPS)
- **Database**: $0-15/month (managed PostgreSQL)
- **Web Hosting**: $0/month (Vercel/Netlify free tier)
- **Total**: ~$5-35/month

### Medium Scale (1000-10000 users/day)

- **Backend**: $20-100/month (scaled cloud service)
- **Database**: $15-50/month (managed PostgreSQL)
- **Web Hosting**: $0-20/month
- **CDN**: $0-10/month
- **Total**: ~$35-180/month

### Large Scale (10000+ users/day)

- **Backend**: $100-500+/month (auto-scaling)
- **Database**: $50-200+/month (high-availability)
- **Web Hosting**: $20-100/month
- **CDN**: $10-50/month
- **Monitoring**: $20-100/month
- **Total**: ~$200-950+/month

---

## Support

For deployment issues:
1. Check platform-specific documentation
2. Review error logs
3. Verify environment variables
4. Test database connectivity
5. Check CORS configuration

