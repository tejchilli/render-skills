# Render Blueprints Guide

Complete guide to infrastructure-as-code on Render using Blueprints. Define your entire application stack in a `render.yaml` file and manage it through Git.

## Table of Contents

- [What are Blueprints?](#what-are-blueprints)
- [Blueprint File Structure](#blueprint-file-structure)
- [Service Definitions](#service-definitions)
- [Database Definitions](#database-definitions)
- [Environment Variables](#environment-variables)
- [Preview Environments](#preview-environments)
- [Blueprint Sync](#blueprint-sync)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Migration Guide](#migration-guide)

---

## What are Blueprints?

Blueprints enable infrastructure-as-code for Render. Instead of manually creating services through the dashboard or API, define your entire stack in a `render.yaml` file in your repository.

**Benefits**:
- **Version Control**: Infrastructure lives in Git alongside your code
- **Reproducibility**: Identical environments from same blueprint
- **Preview Environments**: Automatic temporary environments for pull requests
- **Git Sync**: Infrastructure updates via Git push
- **Team Collaboration**: Review infrastructure changes like code
- **Documentation**: Blueprint serves as living documentation

**How it Works**:
1. Create `render.yaml` in your repository root
2. Connect repo to Render
3. Render creates/updates all defined resources
4. Push changes to trigger updates

---

## Blueprint File Structure

A `render.yaml` file contains arrays of resource definitions:

```yaml
services:
  - type: web
    name: api-server
    runtime: node
    plan: starter
    # ... service configuration

  - type: worker
    name: job-processor
    runtime: python
    plan: starter
    # ... service configuration

databases:
  - name: main-db
    plan: standard
    # ... database configuration

  - name: cache
    plan: starter
    # ... Redis configuration
```

**Top-Level Keys**:
- `services`: Array of service definitions (web, worker, cron, static, private)
- `databases`: Array of database definitions (Postgres, Redis)
- `envVarGroups`: Reusable environment variable groups

---

## Service Definitions

### Web Service

```yaml
services:
  - type: web
    name: api-server
    runtime: node
    plan: starter
    region: oregon
    buildCommand: npm install && npm run build
    startCommand: npm start
    healthCheckPath: /health
    envVars:
      - key: NODE_ENV
        value: production
      - key: PORT
        value: 10000
      - key: DATABASE_URL
        fromDatabase:
          name: main-db
          property: connectionString
```

**Type-Specific Fields**:
- `healthCheckPath`: Endpoint for health checks
- `autoDeploy`: `true` to deploy on every push (default: true)
- `branch`: Git branch to track (default: main)

### Background Worker

```yaml
services:
  - type: worker
    name: job-processor
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A tasks worker --loglevel=info
    envVars:
      - key: REDIS_URL
        fromDatabase:
          name: cache
          property: connectionString
```

### Cron Job

```yaml
services:
  - type: cron
    name: daily-backup
    runtime: python
    plan: starter
    schedule: "0 2 * * *"  # 2 AM daily
    buildCommand: pip install -r requirements.txt
    startCommand: python backup.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: main-db
          property: connectionString
```

### Static Site

```yaml
services:
  - type: web
    name: marketing-site
    runtime: static
    buildCommand: npm run build
    staticPublishPath: ./dist
    pullRequestPreviewsEnabled: yes
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=3600
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

**Static Site Fields**:
- `staticPublishPath`: Directory to serve (relative to repo root)
- `headers`: Array of HTTP header rules
- `routes`: Array of redirect/rewrite rules

### Private Service

```yaml
services:
  - type: pserv
    name: internal-api
    runtime: go
    plan: starter
    buildCommand: go build -o app
    startCommand: ./app
    envVars:
      - key: INTERNAL_PORT
        value: 10000
```

Private services have no public endpoint. Access via `{name}.render-internal.com` from other services.

---

## Database Definitions

### Postgres

```yaml
databases:
  - name: production-db
    databaseName: myapp
    user: myapp_user
    plan: standard
    region: oregon
    ipAllowList: []  # Empty = allow all
```

**Postgres Fields**:
- `databaseName`: Initial database name
- `user`: Database username
- `plan`: `free | starter | standard | pro | pro_plus`
- `region`: Same as service regions
- `ipAllowList`: Array of CIDR blocks for external access control
- `highAvailability`: `true` for primary-replica setup (Pro Plus only)

**High Availability Example**:
```yaml
databases:
  - name: ha-db
    plan: pro_plus
    highAvailability: true
```

### Redis

```yaml
databases:
  - name: cache
    plan: starter
    maxmemoryPolicy: allkeys-lru
    region: oregon
```

**Redis Fields**:
- `maxmemoryPolicy`: `noeviction | allkeys-lru | allkeys-lfu | volatile-lru | volatile-ttl`
- `plan`: `free | starter | standard | pro | pro_plus`

---

## Environment Variables

### Direct Values

```yaml
envVars:
  - key: NODE_ENV
    value: production
  - key: API_TIMEOUT
    value: "30000"
```

### From Database Connection

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: production-db
      property: connectionString

  - key: REDIS_HOST
    fromDatabase:
      name: cache
      property: host
```

**Available Properties**:
- Postgres: `connectionString`, `host`, `port`, `user`, `password`, `database`
- Redis: `connectionString`, `host`, `port`, `password`

### From Services

```yaml
envVars:
  - key: API_URL
    fromService:
      name: api-server
      type: web
      property: host
```

**Properties**: `host` (e.g., `myservice.onrender.com`)

### Secrets (Sync from Dashboard)

```yaml
envVars:
  - key: API_SECRET
    sync: false  # Managed in dashboard, not in blueprint
```

Use `sync: false` for sensitive values. Set them manually in the Render dashboard.

### Environment Variable Groups

Reuse common variables across services:

```yaml
envVarGroups:
  - name: common-config
    envVars:
      - key: LOG_LEVEL
        value: info
      - key: TIMEZONE
        value: UTC

services:
  - type: web
    name: api
    envVars:
      - fromGroup: common-config
      - key: SERVICE_NAME
        value: api

  - type: worker
    name: worker
    envVars:
      - fromGroup: common-config
      - key: SERVICE_NAME
        value: worker
```

---

## Preview Environments

Preview environments are temporary, isolated copies of your app created for pull requests.

**Enable in Blueprint**:
```yaml
services:
  - type: web
    name: api
    pullRequestPreviewsEnabled: yes
```

**How it Works**:
1. Open pull request on tracked branch
2. Render creates temporary environment
3. Unique URL provided (e.g., `api-pr-123.onrender.com`)
4. Close/merge PR → environment deleted after 48 hours

**Preview Environment Features**:
- Separate database instances (free tier)
- Isolated from production
- Same configuration as production
- Automatic comments on PR with preview URLs

**Customizing Preview Environments**:
```yaml
services:
  - type: web
    name: api
    pullRequestPreviewsEnabled: yes
    previewsExpireAfterDays: 3  # Delete after 3 days of inactivity
```

---

## Blueprint Sync

### Initial Setup

**Via API**:
```bash
curl -X POST https://api.render.com/v1/blueprints/sync \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "https://github.com/username/repo",
    "branch": "main",
    "autoDeploy": "yes"
  }'
```

**Via Dashboard**:
1. Go to "Blueprints" section
2. Click "New Blueprint Instance"
3. Connect repository
4. Select branch
5. Review and create

### Updating Infrastructure

1. Modify `render.yaml` in your repository
2. Commit and push changes
3. Render automatically syncs blueprint

**What Syncs**:
- New services/databases are created
- Existing resources are updated
- Environment variables are updated
- Build/start commands are updated

**What Doesn't Sync**:
- Deleted services (must be deleted manually)
- Database downgrades (must be done manually)
- Environment variables with `sync: false`

### Manual Sync Trigger

```bash
curl -X POST https://api.render.com/v1/blueprints/{blueprintId}/sync \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

---

## Examples

### Simple Web App

```yaml
services:
  - type: web
    name: my-app
    runtime: node
    plan: starter
    buildCommand: npm install
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
```

### Full-Stack Application

```yaml
databases:
  - name: postgres-db
    databaseName: myapp
    user: myapp
    plan: starter

  - name: redis-cache
    plan: starter
    maxmemoryPolicy: allkeys-lru

services:
  - type: web
    name: api
    runtime: node
    plan: standard
    buildCommand: npm install && npm run build
    startCommand: npm start
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: postgres-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: redis-cache
          property: connectionString
      - key: NODE_ENV
        value: production

  - type: worker
    name: job-queue
    runtime: node
    plan: starter
    buildCommand: npm install
    startCommand: npm run worker
    envVars:
      - key: REDIS_URL
        fromDatabase:
          name: redis-cache
          property: connectionString

  - type: cron
    name: cleanup-job
    runtime: node
    plan: starter
    schedule: "0 3 * * *"
    buildCommand: npm install
    startCommand: npm run cleanup
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: postgres-db
          property: connectionString
```

### Microservices Architecture

```yaml
databases:
  - name: users-db
    databaseName: users
    plan: starter

  - name: orders-db
    databaseName: orders
    plan: starter

  - name: shared-cache
    plan: starter

services:
  - type: web
    name: users-service
    runtime: python
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: users-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: shared-cache
          property: connectionString

  - type: web
    name: orders-service
    runtime: python
    plan: standard
    buildCommand: pip install -r services/orders/requirements.txt
    rootDirectory: ./services/orders
    startCommand: gunicorn app:app
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: orders-db
          property: connectionString
      - key: USERS_SERVICE_URL
        fromService:
          name: users-service
          type: web
          property: host

  - type: pserv
    name: internal-notifications
    runtime: node
    plan: starter
    buildCommand: npm install
    startCommand: npm start
```

---

## Best Practices

### 1. Use Environment Variable Groups

Define common configuration once:
```yaml
envVarGroups:
  - name: shared-config
    envVars:
      - key: LOG_LEVEL
        value: info
      - key: TZ
        value: America/Los_Angeles
```

### 2. Separate Secrets from Blueprint

Never commit secrets to `render.yaml`. Use `sync: false`:
```yaml
envVars:
  - key: API_SECRET
    sync: false  # Set in dashboard
```

### 3. Use Appropriate Service Types

- Public-facing APIs → Web Service
- Queue processors → Worker
- Scheduled tasks → Cron Job
- Internal APIs → Private Service

### 4. Enable Preview Environments for Development

```yaml
pullRequestPreviewsEnabled: yes
```

### 5. Use Same Region for All Resources

Minimize latency by keeping services and databases in same region:
```yaml
services:
  - region: oregon

databases:
  - region: oregon
```

### 6. Document with Comments

```yaml
services:
  - type: web
    name: api
    # Main API server serving REST endpoints
    # Connects to Postgres and Redis
    runtime: node
```

### 7. Version Your Blueprint

Tag blueprint changes in Git:
```bash
git tag -a v1.0.0 -m "Initial production blueprint"
git push origin v1.0.0
```

---

## Migration Guide

### From Manual Setup to Blueprint

**Step 1: Document Current Infrastructure**

List all existing services and databases:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services

curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres
```

**Step 2: Create render.yaml**

Convert each service to blueprint format. For a web service:
```yaml
services:
  - type: web
    name: existing-service-name  # Use exact name
    runtime: node
    plan: starter
    buildCommand: "npm install"
    startCommand: "npm start"
```

**Step 3: Handle Environment Variables**

For each service, copy env vars to blueprint:
```bash
# Get existing env vars
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/env-vars
```

Add to blueprint:
```yaml
envVars:
  - key: VAR_NAME
    value: value  # Non-secret values
  - key: SECRET_VAR
    sync: false  # Secrets stay in dashboard
```

**Step 4: Test with New Blueprint Instance**

Create a new blueprint instance to test:
```bash
curl -X POST https://api.render.com/v1/blueprints/sync \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -d '{"repo": "...", "branch": "test-blueprint"}'
```

**Step 5: Adopt Existing Services**

Once tested, connect blueprint to existing services by using exact names. Render will adopt them instead of creating duplicates.

**Step 6: Clean Up**

Remove any test instances and old configurations.

---

## Troubleshooting

### Blueprint Fails to Sync

**Check YAML Syntax**:
```bash
# Validate YAML locally
python3 -c "import yaml; yaml.safe_load(open('render.yaml'))"
```

**Common Issues**:
- Invalid indentation
- Missing required fields (`name`, `type`, `runtime`)
- Invalid enum values (`plan`, `region`, `maxmemoryPolicy`)

### Service Not Updating

- Ensure service name matches exactly
- Check if field is syncable (some fields like `plan` require manual approval)
- Verify `autoDeploy` is enabled

### Environment Variables Not Syncing

- Check if variable has `sync: false`
- Verify database/service names in `fromDatabase`/`fromService`
- Ensure secrets are set in dashboard, not blueprint

---

For complete examples, see `assets/templates/blueprint-example.yaml`.
For operational guidance, see `OPERATIONS-GUIDE.md`.
