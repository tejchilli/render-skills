# Render Operations & Troubleshooting Guide

Complete guide for deploying, monitoring, and troubleshooting applications on Render. Includes deployment workflows, logging, monitoring, webhooks, and comprehensive error resolution.

## Table of Contents

### Operations
- [Deployments](#deployments)
- [Logs & Monitoring](#logs--monitoring)
- [Custom Domains](#custom-domains)
- [Environment Management](#environment-management)
- [One-Off Jobs](#one-off-jobs)
- [Webhooks & Notifications](#webhooks--notifications)
- [Audit Logs](#audit-logs)
- [API Basics](#api-basics)

### Troubleshooting
- [Authentication Errors](#authentication-errors)
- [Rate Limiting](#rate-limiting)
- [Resource Errors](#resource-errors)
- [Service Issues](#service-issues)
- [Database Connection Issues](#database-connection-issues)
- [Blueprint Issues](#blueprint-issues)
- [Performance Issues](#performance-issues)
- [Debugging Strategies](#debugging-strategies)

---

## Operations

### Deployments

#### Manual Deployment

Trigger a deployment manually:
```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clearCache": "clear"
  }'
```

**Clear Cache Options**:
- `"clear"`: Clear entire build cache (useful when dependencies change)
- `"do_not_clear"`: Keep existing cache (faster builds)

#### Auto-Deploy

Enable automatic deployments on every Git push:
```bash
curl -X PATCH https://api.render.com/v1/services/{serviceId} \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "autoDeploy": "yes"
  }'
```

**Auto-Deploy Configuration**:
- `"yes"`: Deploy on every push to tracked branch
- `"no"`: Manual deployments only

#### Deploy Hooks

Run scripts before or after deployment:

**Pre-Deploy Hook** (runs before build):
Set in service configuration as `preBuildCommand`:
```json
{
  "preBuildCommand": "./scripts/pre-build.sh"
}
```

**Build Command** (runs during build):
```json
{
  "buildCommand": "npm install && npm run build"
}
```

**Start Command** (runs to start service):
```json
{
  "startCommand": "npm start"
}
```

#### Checking Deploy Status

Get deployment details:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/deploys/{deployId}
```

**Deploy States**:
- `created`: Deploy initiated
- `build_in_progress`: Building application
- `update_in_progress`: Deploying new version
- `live`: Deployment successful, live
- `deactivated`: Deployment was superseded
- `build_failed`: Build failed
- `update_failed`: Deployment failed
- `canceled`: Manually canceled

List recent deployments:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/deploys?limit=10"
```

#### Rollback

To rollback, redeploy a previous commit:
```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clearCache": "do_not_clear",
    "commitId": "previous-commit-sha"
  }'
```

#### Deploy Notifications

Configure webhooks to receive deployment notifications (see [Webhooks](#webhooks--notifications)).

---

### Logs & Monitoring

#### Retrieving Logs

Get recent logs:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?tail=100"
```

**Query Parameters**:
- `tail`: Number of recent lines (default: 100, max: 10000)
- `type`: Filter by log type (`build | deploy | runtime`)
- `startTime`: ISO 8601 timestamp (e.g., `2024-01-01T00:00:00Z`)
- `endTime`: ISO 8601 timestamp

**Log Types**:
- `build`: Build process output
- `deploy`: Deployment process logs
- `runtime`: Application logs (stdout/stderr)

#### Filtering Logs

Filter by type:
```bash
# Build logs only
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?type=build&tail=500"

# Runtime logs from specific time
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?type=runtime&startTime=2024-01-01T00:00:00Z"
```

#### Log Best Practices

**Structured Logging**:
```javascript
// JSON logs for easy parsing
console.log(JSON.stringify({
  level: 'info',
  message: 'User logged in',
  userId: user.id,
  timestamp: new Date().toISOString()
}));
```

**Log Levels**:
Use consistent log levels (DEBUG, INFO, WARN, ERROR) for filtering.

**Avoid Sensitive Data**:
Never log passwords, API keys, or personal information.

#### Metrics

Get service metrics:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/metrics?from=2024-01-01T00:00:00Z&to=2024-01-02T00:00:00Z"
```

**Available Metrics**:
- CPU usage (percentage)
- Memory usage (MB)
- Request count
- Response time (ms)
- Error rate

#### Disk Usage

For services with persistent disks:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/disks/{diskId}
```

Response includes current disk usage and available space.

---

### Custom Domains

#### Adding a Custom Domain

```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/custom-domains \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example.com"
  }'
```

#### DNS Configuration

After adding domain, configure DNS:

**For root domain (example.com)**:
Add ALIAS/ANAME/CNAME record:
```
example.com  ALIAS  your-service.onrender.com
```

**For subdomain (www.example.com)**:
Add CNAME record:
```
www  CNAME  your-service.onrender.com
```

**Render Hostname**:
Find your Render hostname:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}
```
Look for `serviceDetails.url` in response.

#### SSL/TLS Certificates

Render automatically provisions Let's Encrypt certificates for custom domains:
- Free, automatic SSL/TLS
- Auto-renewal before expiry
- Supports wildcard certificates for `*.example.com`

Certificate provisioning takes 1-10 minutes after DNS configuration.

#### Verifying Domain

Check domain status:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/custom-domains/{domainId}
```

**Status Values**:
- `pending`: Waiting for DNS configuration
- `verified`: DNS verified, certificate provisioning
- `live`: Domain active with SSL
- `failed`: Configuration error

#### Redirects

Redirect www to apex (or vice versa) using Render's automatic redirects:
1. Add both domains (`example.com` and `www.example.com`)
2. Configure redirect in service settings

Or handle in application code:
```javascript
// Express.js example
app.use((req, res, next) => {
  if (req.hostname === 'www.example.com') {
    return res.redirect(301, `https://example.com${req.url}`);
  }
  next();
});
```

---

### Environment Management

#### Projects

Projects group related services and databases:
```bash
curl -X POST https://api.render.com/v1/projects \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "ownerId": "owner-id"
  }'
```

#### Environment Variable Management

List all env vars:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/env-vars
```

Add/update env vars (bulk):
```bash
curl -X PUT https://api.render.com/v1/services/{serviceId}/env-vars \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[
    {"key": "NEW_VAR", "value": "new-value"},
    {"key": "EXISTING_VAR", "value": "updated-value"}
  ]'
```

**Note**: PUT replaces all env vars. To update individual vars, GET first, modify, then PUT.

#### Variable Inheritance

Environment variables set on services are not inherited by other services. To share configuration:
1. Use blueprint environment variable groups
2. Store in database/KV store
3. Duplicate across services

---

### One-Off Jobs

Run one-time commands (like database migrations) on service infrastructure:

```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/jobs \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "startCommand": "npm run migrate",
    "planId": "starter"
  }'
```

**Use Cases**:
- Database migrations
- Data import/export
- One-time scripts
- Database seeding

**Job Lifecycle**:
1. Job starts in isolated container
2. Has access to all service environment variables
3. Has access to persistent disks (if any)
4. Runs to completion or times out
5. Logs available via jobs API

#### Checking Job Status

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/jobs/{jobId}
```

#### Job Logs

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/jobs/{jobId}/logs
```

---

### Webhooks & Notifications

Receive HTTP notifications for Render events.

#### Creating a Webhook

```bash
curl -X POST https://api.render.com/v1/webhooks \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook",
    "events": ["deploy_succeeded", "deploy_failed"],
    "serviceId": "service-id"
  }'
```

#### Webhook Events

**Deploy Events**:
- `deploy_started`: Deployment initiated
- `deploy_succeeded`: Deployment completed successfully
- `deploy_failed`: Deployment failed
- `deploy_canceled`: Deployment canceled

**Service Events**:
- `service_updated`: Service configuration changed
- `service_suspended`: Service suspended (billing issue)
- `service_resumed`: Service resumed

**Build Events**:
- `build_started`: Build started
- `build_succeeded`: Build completed
- `build_failed`: Build failed

#### Webhook Payload

Example payload for `deploy_succeeded`:
```json
{
  "event": "deploy_succeeded",
  "service": {
    "id": "service-id",
    "name": "my-service",
    "type": "web_service"
  },
  "deploy": {
    "id": "deploy-id",
    "commitId": "abc123",
    "commitMessage": "Fix bug",
    "status": "live",
    "createdAt": "2024-01-01T12:00:00Z",
    "finishedAt": "2024-01-01T12:05:00Z"
  }
}
```

#### Verifying Webhooks

Render signs webhooks with HMAC-SHA256. Verify signature:
```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
}
```

---

### Audit Logs

View account activity and changes:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/owners/{ownerId}/events?limit=100"
```

**Event Types**:
- Service creation/deletion
- Configuration changes
- Deploy triggers
- Team member actions
- Billing events

**Use Cases**:
- Compliance auditing
- Security monitoring
- Change tracking
- Debugging unexpected changes

---

### API Basics

#### Base URL
```
https://api.render.com/v1
```

#### Authentication

All requests require `Authorization` header:
```
Authorization: Bearer your_api_key
```

Get API key: https://dashboard.render.com/settings/api-keys

#### Request Format

**Content-Type**: `application/json`

```bash
curl -X POST https://api.render.com/v1/... \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

#### Response Format

Responses are JSON:
```json
{
  "id": "resource-id",
  "name": "resource-name",
  ...
}
```

#### Pagination

List endpoints use cursor-based pagination:
```bash
curl "https://api.render.com/v1/services?limit=20&cursor=eyJpZCI6ImFiYzEyMyJ9"
```

**Parameters**:
- `limit`: Results per page (default: 20, max: 100)
- `cursor`: Pagination cursor from previous response

**Response**:
```json
{
  "data": [...],
  "cursor": "next_cursor_value"
}
```

Continue pagination while `cursor` is present.

#### Rate Limits

**Limits**:
- 300 requests per 5 minutes
- Applies per API key

**Headers**:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1640995200
```

**Handling Rate Limits**:
Implement exponential backoff when receiving 429 responses.

---

## Troubleshooting

### Authentication Errors

#### 401 Unauthorized

**Symptoms**:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

**Causes**:
1. Missing `Authorization` header
2. Invalid API key
3. Expired API key

**Solutions**:
```bash
# Verify API key is set
echo $RENDER_API_KEY

# Test authentication
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/owners

# Generate new API key if needed
# Visit: https://dashboard.render.com/settings/api-keys
```

#### 403 Forbidden

**Symptoms**:
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions"
}
```

**Causes**:
1. API key lacks required permissions
2. Trying to access another account's resources
3. Account suspended

**Solutions**:
- Verify you own the resource (check `ownerId`)
- Check account status in dashboard
- Ensure API key has appropriate permissions

---

### Rate Limiting

#### 429 Too Many Requests

**Symptoms**:
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Try again in X seconds."
}
```

**Causes**:
Exceeded 300 requests per 5-minute window

**Solutions**:

**1. Implement Exponential Backoff**:
```python
import time
import requests

def api_request_with_backoff(url, headers, max_retries=5):
    for i in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code != 429:
            return response

        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
        wait_time = 2 ** i
        print(f"Rate limited. Waiting {wait_time}s...")
        time.sleep(wait_time)

    raise Exception("Max retries exceeded")
```

**2. Check Rate Limit Headers**:
```bash
curl -I -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services
```

Look for:
```
X-RateLimit-Remaining: 250
X-RateLimit-Reset: 1640995200
```

**3. Batch Operations**:
Instead of making 100 individual requests, use list endpoints with pagination.

**4. Cache Results**:
Cache responses that don't change frequently.

---

### Resource Errors

#### 404 Not Found

**Symptoms**:
```json
{
  "error": "Not found",
  "message": "Service not found"
}
```

**Causes**:
1. Invalid resource ID
2. Resource was deleted
3. Typo in endpoint URL

**Solutions**:
```bash
# List all services to find correct ID
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services

# Verify service exists
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}
```

#### 409 Conflict

**Symptoms**:
```json
{
  "error": "Conflict",
  "message": "Resource with name 'my-service' already exists"
}
```

**Causes**:
1. Duplicate name
2. Resource in invalid state for operation
3. Concurrent modifications

**Solutions**:
- Use unique names
- Check resource state before operations
- Implement optimistic locking for concurrent updates

#### 503 Service Unavailable

**Symptoms**:
```json
{
  "error": "Service unavailable",
  "message": "Temporary server error"
}
```

**Causes**:
Temporary Render API outage or maintenance

**Solutions**:
1. Check Render status: https://status.render.com
2. Implement retry logic with exponential backoff
3. Wait and retry

---

### Service Issues

#### Build Failures

**Symptoms**:
Deploy status shows `build_failed`

**Debugging**:
```bash
# Get build logs
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?type=build&tail=500"
```

**Common Causes**:

**1. Missing Dependencies**:
```
# Solution: Update package manager files
npm install --save missing-package
pip install missing-package && pip freeze > requirements.txt
```

**2. Build Command Fails**:
```
# Solution: Test build locally
npm run build
# Fix errors, then commit
```

**3. Out of Memory**:
```
# Solution: Increase build resources or optimize
# Upgrade plan or reduce build memory usage
```

**4. Timeout**:
```
# Solution: Build times out after 20 minutes
# Optimize build process or cache dependencies
```

#### Deploy Failures

**Symptoms**:
Deploy status shows `update_failed`

**Debugging**:
```bash
# Get deploy logs
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?type=deploy&tail=500"
```

**Common Causes**:

**1. Service Won't Start**:
```
# Check start command is correct
# Verify PORT binding:
const port = process.env.PORT || 10000;
app.listen(port, '0.0.0.0');  # Bind to 0.0.0.0, not localhost
```

**2. Health Check Failing**:
```
# Ensure health endpoint returns 200 OK
app.get('/health', (req, res) => res.sendStatus(200));
```

**3. Missing Environment Variables**:
```bash
# Verify all required env vars are set
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/env-vars
```

#### Port Binding Issues

**Symptoms**:
Service fails to start, logs show "Address already in use" or similar

**Solution**:
Always use `PORT` environment variable:
```javascript
// Node.js
const PORT = process.env.PORT || 10000;
app.listen(PORT, '0.0.0.0');  // Bind to 0.0.0.0, not 127.0.0.1

# Python
port = int(os.environ.get('PORT', 10000))
app.run(host='0.0.0.0', port=port)

// Go
port := os.Getenv("PORT")
if port == "" {
    port = "10000"
}
http.ListenAndServe(":"+port, handler)
```

#### Memory/CPU Limits

**Symptoms**:
Service crashes or becomes unresponsive under load

**Debugging**:
```bash
# Check metrics
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/metrics"
```

**Solutions**:
1. **Upgrade Plan**: Move to larger instance type
2. **Optimize Code**: Reduce memory footprint
3. **Enable Auto-Scaling**: Distribute load across instances
4. **Add Caching**: Reduce compute requirements

---

### Database Connection Issues

#### Connection Refused

**Symptoms**:
```
Error: connect ECONNREFUSED
FATAL: no pg_hba.conf entry for host
```

**Causes**:
1. Wrong connection string
2. Database not linked to service
3. Using external connection from internal service

**Solutions**:
```bash
# Verify connection string
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres/{postgresId}

# Use internal connection for services in same account
# Internal: postgres://...@host.render-internal.com/db
# External: postgres://...@host.render.com/db
```

#### SSL/TLS Errors

**Symptoms**:
```
Error: SSL SYSCALL error: EOF detected
Error: server does not support SSL
```

**Causes**:
Missing or incorrect SSL configuration

**Solutions**:
```javascript
// Node.js with pg
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false  // Required for Render Postgres
  }
});

# Python with psycopg2
import psycopg2
conn = psycopg2.connect(
    os.environ['DATABASE_URL'],
    sslmode='require'
)
```

#### Connection Pool Exhaustion

**Symptoms**:
```
Error: remaining connection slots are reserved
Error: too many connections
```

**Causes**:
Too many concurrent connections

**Solutions**:
1. **Implement Connection Pooling**: See `RESOURCES.md`
2. **Reduce Pool Size**: Match to database plan limits
3. **Close Connections**: Always close when done
4. **Upgrade Database Plan**: More connections available on higher plans

---

### Blueprint Issues

#### YAML Validation Errors

**Symptoms**:
Blueprint sync fails with "Invalid YAML"

**Debugging**:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('render.yaml'))"
```

**Common Issues**:
- Incorrect indentation (use 2 spaces, not tabs)
- Missing quotes around special characters
- Invalid enum values

#### Blueprint Not Syncing

**Causes**:
1. `autoDeploy` disabled
2. Wrong branch tracked
3. Blueprint not connected to repo

**Solutions**:
```bash
# Check blueprint configuration
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/blueprints/{blueprintId}

# Manually trigger sync
curl -X POST https://api.render.com/v1/blueprints/{blueprintId}/sync \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

---

### Performance Issues

#### Slow Builds

**Solutions**:
1. **Cache Dependencies**: Don't clear cache unless necessary
2. **Optimize Package Manager**: Use `npm ci` instead of `npm install`
3. **Remove Unused Dependencies**: Audit and remove unused packages
4. **Use Build Matrix**: Parallelize tests if applicable

#### High Latency

**Solutions**:
1. **Choose Closer Region**: Match region to user base
2. **Add CDN**: Use Cloudflare or similar
3. **Enable Caching**: Cache API responses
4. **Database Optimization**: Add indexes, optimize queries
5. **Use Redis**: Cache frequently accessed data

#### Auto-Scaling Not Triggering

**Causes**:
1. Not on Standard plan or higher
2. Thresholds not reached
3. Already at max instances

**Solutions**:
```bash
# Check current scaling configuration
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}

# Adjust thresholds
curl -X PATCH https://api.render.com/v1/services/{serviceId} \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -d '{
    "autoscaling": {
      "enabled": true,
      "min": 1,
      "max": 10,
      "targetCPU": 60
    }
  }'
```

---

### Debugging Strategies

#### 1. Check Logs First

Always start with logs:
```bash
# Recent runtime logs
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?type=runtime&tail=500"
```

#### 2. Verify Environment Variables

Missing or incorrect env vars cause many issues:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/env-vars
```

#### 3. Test Locally

Reproduce issues locally with same configuration:
```bash
export NODE_ENV=production
export DATABASE_URL=postgresql://...
npm start
```

#### 4. Check Service Status

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}
```

Look for `suspended`, `update_failed`, or error states.

#### 5. Review Recent Deploys

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/deploys?limit=5"
```

Identify when issues started.

#### 6. Consult Render Status

Check for platform-wide issues: https://status.render.com

#### 7. Contact Support

For issues you can't resolve:
- Email: support@render.com
- Include: service ID, logs, steps to reproduce
- Check community forum: https://community.render.com

---

This guide covers most operational scenarios and common issues. For service configuration details, see `RESOURCES.md`. For workflow examples, see `EXAMPLES.md`.
