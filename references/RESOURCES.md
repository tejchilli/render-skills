# Render Resources Guide

Complete reference for Render services and datastores, including configuration options, runtime environments, and connection patterns.

## Table of Contents

- [Services](#services)
  - [Web Services](#web-services)
  - [Background Workers](#background-workers)
  - [Cron Jobs](#cron-jobs)
  - [Static Sites](#static-sites)
  - [Private Services](#private-services)
- [Datastores](#datastores)
  - [Postgres](#postgres)
  - [Redis](#redis)
  - [Key-Value Stores](#key-value-stores)
- [Persistent Disks](#persistent-disks)

---

## Services

All Render services share common configuration options, then add type-specific features.

### Common Service Configuration

```json
{
  "type": "web_service | worker | cron_job | static_site | private_service",
  "name": "my-service",
  "ownerId": "owner-id",
  "repo": "https://github.com/username/repo",
  "autoDeploy": "yes | no",
  "branch": "main",
  "rootDir": "./",
  "runtime": "node | python | go | rust | ruby | elixir | docker | image",
  "buildCommand": "npm install",
  "startCommand": "npm start",
  "envVars": [
    {"key": "ENV_VAR", "value": "value"}
  ],
  "plan": "free | starter | standard | pro | pro_plus",
  "region": "oregon | frankfurt | ohio | singapore"
}
```

### Runtime Environments

**Node.js**
```json
{
  "runtime": "node",
  "buildCommand": "npm install",
  "startCommand": "npm start"
}
```
Auto-detects Node version from `.nvmrc` or `package.json` engines field.

**Python**
```json
{
  "runtime": "python",
  "buildCommand": "pip install -r requirements.txt",
  "startCommand": "gunicorn app:app"
}
```
Auto-detects Python version from `runtime.txt` or uses latest 3.x.

**Go**
```json
{
  "runtime": "go",
  "buildCommand": "go build -o app",
  "startCommand": "./app"
}
```

**Rust**
```json
{
  "runtime": "rust",
  "buildCommand": "cargo build --release",
  "startCommand": "./target/release/app"
}
```

**Ruby**
```json
{
  "runtime": "ruby",
  "buildCommand": "bundle install",
  "startCommand": "bundle exec rails server"
}
```

**Docker**
```json
{
  "runtime": "docker",
  "dockerfilePath": "./Dockerfile",
  "dockerContext": "./"
}
```
No build command needed - uses Dockerfile.

**Pre-built Image**
```json
{
  "runtime": "image",
  "imagePath": "docker.io/username/image:tag"
}
```
Deploys from Docker registry (Docker Hub, GitHub Container Registry, etc.).

---

### Web Services

HTTP services with automatic HTTPS, custom domains, and auto-scaling.

**Key Features**:
- Public HTTPS endpoint (*.onrender.com)
- Custom domain support with automatic SSL
- Auto-scaling based on traffic
- Health checks
- Zero-downtime deployments

**Configuration Example**:
```json
{
  "type": "web_service",
  "name": "api-server",
  "runtime": "node",
  "buildCommand": "npm install && npm run build",
  "startCommand": "npm start",
  "healthCheckPath": "/health",
  "plan": "starter",
  "envVars": [
    {"key": "PORT", "value": "10000"}
  ]
}
```

**Health Checks**:
```json
{
  "healthCheckPath": "/health",
  "healthCheckInterval": 30,
  "healthCheckTimeout": 5
}
```
Render calls `healthCheckPath` every `healthCheckInterval` seconds. If it returns 200 OK within `healthCheckTimeout` seconds, the service is healthy.

**Port Binding**:
Web services MUST bind to the port specified in the `PORT` environment variable (default: 10000).

```javascript
// Node.js example
const port = process.env.PORT || 10000;
app.listen(port, '0.0.0.0');
```

**Auto-Scaling**:
Available on Standard plans and higher. Configure in service settings:
```json
{
  "numInstances": 2,
  "autoscaling": {
    "enabled": true,
    "min": 1,
    "max": 10,
    "targetCPU": 70,
    "targetMemory": 80
  }
}
```

---

### Background Workers

Long-running processes for background tasks, queues, and event processing.

**Key Features**:
- No public endpoint
- Continuous execution
- Ideal for queues (Sidekiq, Celery, Bull)
- Can connect to databases in the same account

**Configuration Example**:
```json
{
  "type": "worker",
  "name": "job-processor",
  "runtime": "python",
  "buildCommand": "pip install -r requirements.txt",
  "startCommand": "celery -A tasks worker",
  "plan": "starter"
}
```

**Common Use Cases**:
- Queue workers (Redis-backed job queues)
- Event stream processors
- Scheduled data syncing
- Email/notification sending
- Image/video processing

---

### Cron Jobs

Scheduled tasks that run on a defined schedule.

**Key Features**:
- Cron schedule syntax
- Manual trigger support
- Runs in isolated container
- Automatic retries on failure

**Configuration Example**:
```json
{
  "type": "cron_job",
  "name": "daily-report",
  "runtime": "python",
  "buildCommand": "pip install -r requirements.txt",
  "startCommand": "python generate_report.py",
  "schedule": "0 9 * * *"
}
```

**Schedule Syntax** (standard cron):
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Examples**:
- `0 9 * * *` - Daily at 9:00 AM
- `*/15 * * * *` - Every 15 minutes
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 */6 * * *` - Every 6 hours

**Manual Trigger**:
```bash
curl -X POST https://api.render.com/v1/services/{cronJobId}/jobs \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

---

### Static Sites

Static content hosting with global CDN.

**Key Features**:
- Automatic CDN distribution
- Custom domains with SSL
- Build from static site generators (Next.js, Gatsby, Hugo, etc.)
- Headers and redirect configuration

**Configuration Example**:
```json
{
  "type": "static_site",
  "name": "marketing-site",
  "buildCommand": "npm run build",
  "publishPath": "./dist",
  "headers": [
    {
      "path": "/*",
      "name": "X-Frame-Options",
      "value": "DENY"
    }
  ],
  "routes": [
    {
      "type": "rewrite",
      "source": "/*",
      "destination": "/index.html"
    }
  ]
}
```

**Headers**: Set custom HTTP headers (security, caching, CORS)
**Routes**: Configure redirects and rewrites for SPA routing

---

### Private Services

Internal services accessible only within your Render account.

**Key Features**:
- No public internet access
- Internal DNS (servicename.render-internal.com)
- Lower latency for internal communication
- Reduced attack surface

**Configuration Example**:
```json
{
  "type": "private_service",
  "name": "internal-api",
  "runtime": "go",
  "buildCommand": "go build -o app",
  "startCommand": "./app"
}
```

**Access from other services**:
```bash
# Automatic internal hostname
http://internal-api.render-internal.com:10000
```

Environment variable automatically available: `INTERNAL_API_URL`

---

## Datastores

### Postgres

Fully managed PostgreSQL databases with automated backups and high availability.

**Plans**:
- **Free**: 90 days, 256 MB RAM, 1 GB storage, expires after 90 days of inactivity
- **Starter**: 1 GB RAM, 10 GB storage, daily backups
- **Standard**: 4 GB RAM, 50 GB storage, daily backups
- **Pro**: 8 GB RAM, 100 GB storage, point-in-time recovery
- **Pro Plus**: 16 GB RAM, 200 GB storage, high availability

**Creating via API**:
```bash
curl -X POST https://api.render.com/v1/postgres \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-db",
    "ownerId": "owner-id",
    "plan": "standard",
    "region": "oregon",
    "databaseName": "myapp",
    "databaseUser": "myapp_user",
    "enableHighAvailability": false
  }'
```

**Connection Strings**:
Render provides two connection strings:

1. **Internal** (for services in same account):
   ```
   postgresql://user:pass@hostname.render-internal.com/database
   ```
   - Lower latency
   - No egress charges
   - Automatic injection into services

2. **External** (for external access):
   ```
   postgresql://user:pass@hostname.render.com/database
   ```
   - Public internet access
   - Use for local development or external tools

**Environment Variable Injection**:
When you link a Postgres database to a service, Render automatically injects:
- `DATABASE_URL`: Full connection string
- `POSTGRES_HOST`: Hostname
- `POSTGRES_PORT`: Port (usually 5432)
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Username
- `POSTGRES_PASSWORD`: Password

**Backups**:
- **Starter and above**: Daily automated backups
- **Pro and above**: Point-in-time recovery (PITR) to any second in last 7 days
- Manual backups via API:
```bash
curl -X POST https://api.render.com/v1/postgres/{postgresId}/backups \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

**Restore from Backup**:
```bash
curl -X POST https://api.render.com/v1/postgres/{postgresId}/restore \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "backupId": "backup-id"
  }'
```

**High Availability**:
Pro Plus plans can enable HA:
```json
{
  "enableHighAvailability": true
}
```
- Primary-replica configuration
- Automatic failover
- Read replicas for scaling

---

### Redis

In-memory data store for caching, sessions, and real-time features.

**Plans**:
- **Free**: 25 MB, expires after 90 days
- **Starter**: 256 MB
- **Standard**: 1 GB
- **Pro**: 5 GB
- **Pro Plus**: 10 GB

**Creating via API**:
```bash
curl -X POST https://api.render.com/v1/redis \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "session-cache",
    "ownerId": "owner-id",
    "plan": "starter",
    "maxmemoryPolicy": "allkeys-lru",
    "region": "oregon"
  }'
```

**Maxmemory Policies**:
- `noeviction`: Return errors when memory limit reached
- `allkeys-lru`: Evict least recently used keys
- `allkeys-lfu`: Evict least frequently used keys
- `volatile-lru`: Evict LRU keys with expiration set
- `volatile-ttl`: Evict keys with shortest TTL

**Connection**:
```bash
# Internal connection string
redis://default:password@hostname.render-internal.com:6379
```

**Environment Variables** (auto-injected):
- `REDIS_URL`: Full connection string
- `REDIS_HOST`: Hostname
- `REDIS_PORT`: Port (6379)
- `REDIS_PASSWORD`: Password

**Persistence**:
Redis on Render persists data with RDB + AOF:
- RDB snapshots every 5 minutes
- AOF for write-ahead logging
- Data survives restarts

---

### Key-Value Stores

Simple persistent key-value storage for configuration and small data.

**Features**:
- RESTful HTTP API
- Key-based access
- JSON value storage
- No connection string needed

**Creating via API**:
```bash
curl -X POST https://api.render.com/v1/kv-stores \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "app-config",
    "ownerId": "owner-id"
  }'
```

**Usage**:
```bash
# Set a value
curl -X PUT https://api.render.com/v1/kv-stores/{storeId}/keys/my-key \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"value": {"config": "data"}}'

# Get a value
curl https://api.render.com/v1/kv-stores/{storeId}/keys/my-key \
  -H "Authorization: Bearer $RENDER_API_KEY"

# Delete a value
curl -X DELETE https://api.render.com/v1/kv-stores/{storeId}/keys/my-key \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

**Limitations**:
- Max key size: 256 bytes
- Max value size: 1 MB
- Best for configuration, not high-throughput workloads

---

## Persistent Disks

Attach persistent storage volumes to services for files that survive deployments.

**Use Cases**:
- User uploads
- SQLite databases
- Generated files
- Application state

**Creating and Attaching**:
```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/disks \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "uploads",
    "mountPath": "/app/uploads",
    "sizeGB": 10
  }'
```

**Mount Path**: Absolute path where disk is mounted (e.g., `/app/uploads`)
**Size**: 1 GB to 1000 GB

**Important Notes**:
- Disks are specific to one service
- Data persists across deployments
- Not shared between service instances (use S3 for multi-instance storage)
- Backup by creating snapshots via API

**Backup Disk**:
```bash
curl -X POST https://api.render.com/v1/disks/{diskId}/snapshots \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

---

## Connection Patterns

### Connecting Services to Databases

**Automatic (Recommended)**:
Link database to service in Render dashboard or via blueprint. Connection string automatically injected as environment variable.

**Manual**:
Copy connection string from database details and add as environment variable to service.

### Connection Pooling

For web services with multiple instances, use connection pooling to manage database connections efficiently:

**Node.js (with pg)**:
```javascript
const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

**Python (with psycopg2)**:
```python
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=os.environ['DATABASE_URL']
)
```

### Security Best Practices

1. **Use Internal Connections**: Always use internal connection strings for services in the same account
2. **Limit External Access**: Only allow external connections when necessary
3. **Rotate Credentials**: Periodically rotate database passwords
4. **Use Environment Variables**: Never hardcode credentials
5. **Enable SSL**: Ensure SSL/TLS for external connections

---

## Service Plans and Pricing

**Instance Types**:
- **Free**: 512 MB RAM, 0.1 CPU, sleeps after 15 min inactivity
- **Starter**: 512 MB RAM, 0.5 CPU
- **Standard**: 2 GB RAM, 1 CPU
- **Pro**: 4 GB RAM, 2 CPU
- **Pro Plus**: 8 GB RAM, 4 CPU
- **Custom**: Contact sales for custom configurations

**Regions**:
- Oregon (US West)
- Ohio (US East)
- Frankfurt (Europe)
- Singapore (Asia)

Choose region closest to your users for lowest latency.

---

This guide covers the core resources available on Render. For deployment workflows, monitoring, and operations, see `OPERATIONS-GUIDE.md`.
