# Render Workflow Examples

End-to-end examples of common Render workflows. Each example shows complete API calls and expected outcomes.

## Table of Contents

1. [Deploy New Web Service](#1-deploy-new-web-service)
2. [Full-Stack Application Setup](#2-full-stack-application-setup)
3. [Implement CI/CD Pipeline](#3-implement-cicd-pipeline)
4. [Migrate to Blueprint](#4-migrate-to-blueprint)
5. [Database Backup & Restore](#5-database-backup--restore)
6. [Scale Service Dynamically](#6-scale-service-dynamically)
7. [Run Database Migrations](#7-run-database-migrations)

---

## 1. Deploy New Web Service

**Goal**: Deploy a Node.js web service from GitHub repository.

### Step 1: Get Owner ID

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/owners
```

Save the `id` from response: `own_abc123`

### Step 2: Create Web Service

```bash
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web_service",
    "name": "my-api",
    "ownerId": "own_abc123",
    "repo": "https://github.com/username/my-api",
    "autoDeploy": "yes",
    "branch": "main",
    "runtime": "node",
    "plan": "starter",
    "region": "oregon",
    "buildCommand": "npm install && npm run build",
    "startCommand": "npm start",
    "healthCheckPath": "/health",
    "envVars": [
      {"key": "NODE_ENV", "value": "production"},
      {"key": "PORT", "value": "10000"}
    ]
  }'
```

Save service ID from response: `srv_xyz789`

### Step 3: Monitor Deployment

```bash
# Check deploy status
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789

# Watch build logs
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv_xyz789/logs?type=build&tail=100"
```

Wait for `serviceDetails.url` to become available (e.g., `my-api.onrender.com`).

### Step 4: Add Custom Domain

```bash
curl -X POST https://api.render.com/v1/services/srv_xyz789/custom-domains \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api.example.com"
  }'
```

### Step 5: Configure DNS

Add CNAME record:
```
api  CNAME  my-api.onrender.com
```

Wait 1-10 minutes for SSL provisioning.

### Step 6: Verify Service

```bash
curl https://api.example.com/health
```

**Result**: Web service deployed with custom domain and SSL.

---

## 2. Full-Stack Application Setup

**Goal**: Deploy web app, background worker, and Postgres database.

### Step 1: Create Postgres Database

```bash
curl -X POST https://api.render.com/v1/postgres \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-db",
    "ownerId": "own_abc123",
    "plan": "standard",
    "region": "oregon",
    "databaseName": "myapp",
    "databaseUser": "myapp_user"
  }'
```

Save postgres ID: `dpg_123456`

Get connection string:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres/dpg_123456
```

Save `connectionInfo.internalConnectionString`: `postgresql://user:pass@host.render-internal.com/myapp`

### Step 2: Create Redis Instance

```bash
curl -X POST https://api.render.com/v1/redis \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "app-cache",
    "ownerId": "own_abc123",
    "plan": "starter",
    "maxmemoryPolicy": "allkeys-lru",
    "region": "oregon"
  }'
```

Save redis ID: `red_789012`

### Step 3: Create Web Service

```bash
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web_service",
    "name": "web-app",
    "ownerId": "own_abc123",
    "repo": "https://github.com/username/fullstack-app",
    "branch": "main",
    "runtime": "node",
    "plan": "standard",
    "region": "oregon",
    "buildCommand": "npm install && npm run build",
    "startCommand": "npm start",
    "envVars": [
      {"key": "DATABASE_URL", "value": "postgresql://user:pass@host.render-internal.com/myapp"},
      {"key": "REDIS_URL", "value": "redis://..."}
    ]
  }'
```

### Step 4: Create Background Worker

```bash
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "worker",
    "name": "job-worker",
    "ownerId": "own_abc123",
    "repo": "https://github.com/username/fullstack-app",
    "branch": "main",
    "runtime": "node",
    "plan": "starter",
    "region": "oregon",
    "buildCommand": "npm install",
    "startCommand": "npm run worker",
    "envVars": [
      {"key": "DATABASE_URL", "value": "postgresql://user:pass@host.render-internal.com/myapp"},
      {"key": "REDIS_URL", "value": "redis://..."}
    ]
  }'
```

**Result**: Complete stack deployed with web frontend, background processing, and databases.

---

## 3. Implement CI/CD Pipeline

**Goal**: Automatic deployments with notifications on success/failure.

### Step 1: Enable Auto-Deploy

Already enabled when creating service with `"autoDeploy": "yes"`.

To enable on existing service:
```bash
curl -X PATCH https://api.render.com/v1/services/srv_xyz789 \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "autoDeploy": "yes"
  }'
```

### Step 2: Create Webhook for Notifications

```bash
curl -X POST https://api.render.com/v1/webhooks \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook/render",
    "events": ["deploy_started", "deploy_succeeded", "deploy_failed"],
    "serviceId": "srv_xyz789"
  }'
```

### Step 3: Create Webhook Handler

```javascript
// Express.js webhook handler
app.post('/webhook/render', (req, res) => {
  const { event, service, deploy } = req.body;

  if (event === 'deploy_succeeded') {
    // Send Slack notification
    sendSlackMessage(`✅ ${service.name} deployed successfully!`);
  } else if (event === 'deploy_failed') {
    // Send error notification
    sendSlackMessage(`❌ ${service.name} deployment failed!`);
  }

  res.sendStatus(200);
});
```

### Step 4: Test CI/CD

```bash
# Make code change
git commit -m "Test CI/CD"
git push origin main

# Monitor deployment
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789/deploys?limit=1
```

### Step 5: Implement Rollback on Failure

```javascript
app.post('/webhook/render', async (req, res) => {
  const { event, service, deploy } = req.body;

  if (event === 'deploy_failed') {
    // Get previous successful deploy
    const deploys = await getRenderDeploys(service.id);
    const lastSuccessful = deploys.find(d => d.status === 'live' && d.id !== deploy.id);

    if (lastSuccessful) {
      // Trigger rollback
      await triggerDeploy(service.id, lastSuccessful.commitId);
      sendAlert(`Rolled back ${service.name} to ${lastSuccessful.commitId}`);
    }
  }

  res.sendStatus(200);
});
```

**Result**: Fully automated CI/CD with notifications and automatic rollback on failure.

---

## 4. Migrate to Blueprint

**Goal**: Convert existing manually-created services to blueprint.

### Step 1: Document Current Infrastructure

```bash
# List all services
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services > services.json

# List databases
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres > databases.json
```

### Step 2: Get Environment Variables

```bash
# For each service
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789/env-vars > env-vars-srv_xyz789.json
```

### Step 3: Create render.yaml

Convert services to blueprint format:

```yaml
databases:
  - name: production-db  # Use exact name from step 1
    databaseName: myapp
    user: myapp_user
    plan: standard
    region: oregon

services:
  - type: web
    name: web-app  # Use exact name from step 1
    runtime: node
    plan: standard
    region: oregon
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: production-db
          property: connectionString
      - key: API_SECRET
        sync: false  # Keep secret in dashboard
```

### Step 4: Test in Separate Branch

```bash
git checkout -b test-blueprint
# Create render.yaml
git add render.yaml
git commit -m "Add blueprint"
git push origin test-blueprint
```

### Step 5: Create Test Blueprint Instance

```bash
curl -X POST https://api.render.com/v1/blueprints/sync \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "https://github.com/username/repo",
    "branch": "test-blueprint"
  }'
```

This creates NEW instances. Verify they work correctly.

### Step 6: Adopt Existing Services

Once verified, merge blueprint to main:
```bash
git checkout main
git merge test-blueprint
git push origin main
```

Connect blueprint to main branch. Render will adopt existing services if names match exactly.

### Step 7: Clean Up Test Instances

Delete test services created in step 5.

**Result**: Infrastructure now managed as code with version control.

---

## 5. Database Backup & Restore

**Goal**: Create backup and restore Postgres database.

### Step 1: Trigger Manual Backup

```bash
curl -X POST https://api.render.com/v1/postgres/dpg_123456/backups \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

Response contains backup ID: `bkp_abc123`

### Step 2: Monitor Backup Progress

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres/dpg_123456/backups/bkp_abc123
```

Wait for status: `completed`

### Step 3: List All Backups

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres/dpg_123456/backups
```

### Step 4: Restore from Backup

```bash
curl -X POST https://api.render.com/v1/postgres/dpg_123456/restore \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "backupId": "bkp_abc123"
  }'
```

**Warning**: This overwrites current database. Existing connections will be terminated.

### Step 5: Verify Restoration

```bash
# Check database status
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres/dpg_123456
```

**Result**: Database backed up and restored successfully.

---

## 6. Scale Service Dynamically

**Goal**: Configure auto-scaling based on CPU usage.

### Step 1: Check Current Configuration

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789
```

### Step 2: Enable Auto-Scaling

```bash
curl -X PATCH https://api.render.com/v1/services/srv_xyz789 \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "standard",
    "autoscaling": {
      "enabled": true,
      "min": 1,
      "max": 10,
      "targetCPU": 70,
      "targetMemory": 80
    }
  }'
```

**Note**: Auto-scaling requires Standard plan or higher.

### Step 3: Monitor Scaling Events

```bash
# Check current instance count
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789

# View metrics
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv_xyz789/metrics?from=2024-01-01T00:00:00Z&to=2024-01-01T23:59:59Z"
```

### Step 4: Test Scaling

Generate load to trigger scaling:
```bash
# Use load testing tool (e.g., Apache Bench)
ab -n 10000 -c 100 https://your-service.onrender.com/
```

Monitor instance count increase.

**Result**: Service automatically scales based on load.

---

## 7. Run Database Migrations

**Goal**: Run database migration as one-off job.

### Step 1: Create Migration Job

```bash
curl -X POST https://api.render.com/v1/services/srv_xyz789/jobs \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "startCommand": "npm run migrate",
    "planId": "starter"
  }'
```

Save job ID from response: `job_456789`

### Step 2: Monitor Job Execution

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789/jobs/job_456789
```

Check `status` field:
- `pending`: Job queued
- `running`: Job executing
- `succeeded`: Job completed successfully
- `failed`: Job failed

### Step 3: View Job Logs

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_xyz789/jobs/job_456789/logs
```

### Step 4: Verify Migration

Connect to database and verify:
```bash
# Using psql
psql $DATABASE_URL -c "SELECT * FROM schema_migrations;"
```

### Alternative: Pre-Deploy Migration

Instead of one-off job, run migration as pre-build command:

```bash
curl -X PATCH https://api.render.com/v1/services/srv_xyz789 \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "preBuildCommand": "npm run migrate"
  }'
```

Migration runs automatically before each deployment.

**Result**: Database schema updated safely via migration job.

---

## Summary

These examples demonstrate common Render workflows:
1. **Basic Deployment**: Service creation and custom domains
2. **Full-Stack**: Multi-service architecture with databases
3. **CI/CD**: Automated deployments with notifications
4. **Infrastructure-as-Code**: Blueprint migration
5. **Data Management**: Backup and restore procedures
6. **Scaling**: Auto-scaling configuration
7. **Operations**: Database migrations and one-off jobs

For configuration details, see `RESOURCES.md`.
For troubleshooting, see `OPERATIONS-GUIDE.md`.
For blueprints, see `BLUEPRINTS.md`.
