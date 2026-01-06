---
name: render
description: Complete toolkit for managing Render cloud infrastructure via API - create and configure services (web, workers, cron jobs), manage deployments, configure environments, handle datastores (Postgres, Redis, KV), work with blueprints for infrastructure-as-code, monitor logs and metrics, and troubleshoot common issues. Use this when working with Render.com hosting platform.
license: Apache-2.0
compatibility: Requires Python 3.8+, curl, jq. Internet access needed for API calls and schema updates.
metadata:
  version: "1.0.0"
  api-version: "1.0"
---

# Render API Skill

This skill provides comprehensive guidance for managing Render cloud infrastructure through the Render API. Use it to create services, manage deployments, configure databases, and work with infrastructure-as-code blueprints.

## Quick Start

### Authentication Setup

All Render API requests require an API key for authentication. Set your API key as an environment variable:

```bash
export RENDER_API_KEY="your_api_key_here"
```

Get your API key from: https://dashboard.render.com/settings/api-keys

### Your First API Call

Test your setup by listing all services:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services
```

### Finding API Endpoints

Use the search tool to find relevant endpoints without loading the full schema:

```bash
# Search for postgres-related endpoints
python3 scripts/search-api.py "postgres"

# Search with category filter
python3 scripts/search-api.py "deploy" --category services

# List all available endpoints
python3 scripts/search-api.py --list-endpoints

# Show API statistics
python3 scripts/search-api.py --stats
```

## Core Concepts

### Services

Render supports multiple service types, each optimized for different workloads:

- **Web Services**: HTTP services with auto-scaling and custom domains
- **Background Workers**: Long-running processes for background tasks
- **Cron Jobs**: Scheduled tasks that run on a defined schedule
- **Static Sites**: Static content hosting with CDN
- **Private Services**: Internal services not exposed to the internet

All services share common configuration options:
- Runtime environment (Node, Python, Go, Rust, Ruby, Docker, etc.)
- Environment variables and secrets
- Health check configuration
- Auto-deploy from Git
- Resource allocation (instance type, scaling)

**For detailed service configurations**, see `references/RESOURCES.md`.

### Datastores

Render provides managed datastores:

- **Postgres**: Fully managed PostgreSQL databases with high availability
- **Redis**: In-memory data store for caching and real-time features
- **Key-Value Stores**: Simple persistent key-value storage

Connection strings are automatically injected as environment variables into your services.

**For datastore configuration details**, see `references/RESOURCES.md`.

### Blueprints

Blueprints are infrastructure-as-code definitions that let you:
- Define entire application stacks in YAML
- Version control your infrastructure
- Create preview environments for pull requests
- Sync infrastructure state from Git repositories

**For complete blueprint guide**, see `references/BLUEPRINTS.md`.

### Deployments

Deployments can be triggered:
- **Automatically**: On Git push (auto-deploy)
- **Manually**: Via API or dashboard
- **Scheduled**: For cron jobs

Each deployment can:
- Clear build cache
- Run pre-deploy and post-deploy hooks
- Send notifications via webhooks
- Be rolled back if needed

## Common Operations

All examples use curl with the `RENDER_API_KEY` environment variable. Replace with your preferred HTTP client.

### Creating a Web Service

```bash
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web_service",
    "name": "my-api",
    "ownerId": "your-owner-id",
    "repo": "https://github.com/username/repo",
    "autoDeploy": "yes",
    "branch": "main",
    "rootDir": "./",
    "runtime": "node",
    "buildCommand": "npm install",
    "startCommand": "npm start",
    "envVars": [
      {
        "key": "NODE_ENV",
        "value": "production"
      }
    ]
  }'
```

**Note**: Get your `ownerId` by listing owners:
```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/owners
```

### Managing Environment Variables

List environment variables for a service:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/env-vars
```

Update environment variables:

```bash
curl -X PUT https://api.render.com/v1/services/{serviceId}/env-vars \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "key": "DATABASE_URL",
      "value": "postgresql://..."
    },
    {
      "key": "API_SECRET",
      "value": "secret-value"
    }
  ]'
```

### Triggering a Deployment

Manually trigger a deployment:

```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clearCache": "clear"
  }'
```

Check deployment status:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/deploys/{deployId}
```

### Viewing Logs

Stream service logs:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?tail=100"
```

Filter logs by type:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/{serviceId}/logs?type=build"
```

### Creating a Postgres Database

```bash
curl -X POST https://api.render.com/v1/postgres \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-database",
    "ownerId": "your-owner-id",
    "plan": "starter",
    "region": "oregon",
    "databaseName": "mydb",
    "databaseUser": "myuser"
  }'
```

Get connection info:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/postgres/{postgresId}
```

The response includes:
- Internal connection string (for services in same account)
- External connection string (for external access)
- Connection parameters (host, port, database, user)

### Scaling a Service

Update service configuration to change instance type or count:

```bash
curl -X PATCH https://api.render.com/v1/services/{serviceId} \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "standard",
    "numInstances": 3
  }'
```

Available plans:
- `free`: Limited resources, sleeps after inactivity
- `starter`: Basic production tier
- `standard`: More resources, better performance
- `pro`: High performance
- `pro_plus`: Maximum resources

### Managing Custom Domains

Add a custom domain:

```bash
curl -X POST https://api.render.com/v1/services/{serviceId}/custom-domains \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example.com"
  }'
```

Render automatically provisions SSL/TLS certificates via Let's Encrypt.

List custom domains:

```bash
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/{serviceId}/custom-domains
```

**For advanced operations** (webhooks, one-off jobs, monitoring), see `references/OPERATIONS-GUIDE.md`.

## API Discovery

### Using the Search Tool

The search tool helps you find relevant endpoints without loading the entire API schema:

```bash
# Find all postgres-related endpoints
python3 scripts/search-api.py "postgres"

# Search for deployment endpoints
python3 scripts/search-api.py "deploy"

# Filter by category
python3 scripts/search-api.py "env" --category services

# Show all results (no limit)
python3 scripts/search-api.py "service" --all
```

### Interpreting Search Results

Search results show:
- **Method and Path**: The HTTP verb and endpoint URL
- **Summary**: Brief description of what the endpoint does
- **Tags**: Categories the endpoint belongs to
- **Auth Required**: Whether authentication is needed
- **Parameters**: Number of query/path parameters
- **Request Body**: Whether the endpoint accepts a request body

Example output:
```
GET     /v1/services/{serviceId}
        Summary: Retrieve service
        Tags: Services
        Auth required | 1 params
```

### Refreshing the API Schema

Update to the latest API schema:

```bash
./scripts/fetch-schema.sh
```

This downloads the latest OpenAPI schema and regenerates the search index. Run this periodically to stay up-to-date with API changes.

## Troubleshooting

### Common Errors

**401 Unauthorized**
- Cause: Invalid or missing API key
- Solution: Verify your `RENDER_API_KEY` environment variable is set correctly
- Get a new key: https://dashboard.render.com/settings/api-keys

**429 Too Many Requests**
- Cause: Rate limit exceeded
- Solution: Implement exponential backoff; wait before retrying
- Rate limits are returned in response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

**404 Not Found**
- Cause: Invalid resource ID or resource doesn't exist
- Solution: Verify the service/database/resource ID is correct
- List resources to find the correct ID

**503 Service Unavailable**
- Cause: Temporary Render API outage
- Solution: Retry with exponential backoff
- Check status: https://status.render.com

### Quick Fixes

**Build Failing**:
1. Check build logs: `curl ... /v1/services/{serviceId}/logs?type=build`
2. Verify build command is correct
3. Check environment variables are set
4. Try clearing build cache in next deployment

**Service Not Starting**:
1. Check runtime logs: `curl ... /v1/services/{serviceId}/logs?type=deploy`
2. Verify start command is correct
3. Check health check configuration
4. Ensure port binding is correct (use `PORT` environment variable)

**For comprehensive troubleshooting**, see `references/OPERATIONS-GUIDE.md`.

## Working with Blueprints

Blueprints enable infrastructure-as-code for Render. Define your entire stack in a `render.yaml` file:

```yaml
services:
  - type: web
    name: my-api
    runtime: node
    buildCommand: npm install
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production

databases:
  - name: my-db
    plan: starter
```

### Blueprint Benefits

- **Version Control**: Infrastructure definitions live in your repo
- **Preview Environments**: Automatic environments for pull requests
- **Consistency**: Same configuration across environments
- **Git Sync**: Infrastructure updates via Git push

### Creating from Blueprint

```bash
curl -X POST https://api.render.com/v1/blueprints/sync \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "https://github.com/username/repo",
    "branch": "main"
  }'
```

**For complete blueprint guide and examples**, see `references/BLUEPRINTS.md`.
**For workflow examples**, see `references/EXAMPLES.md`.

## Additional Resources

- **references/RESOURCES.md**: Detailed service types, configurations, and datastore guides
- **references/OPERATIONS-GUIDE.md**: Advanced operations, monitoring, and troubleshooting
- **references/BLUEPRINTS.md**: Complete infrastructure-as-code guide
- **references/EXAMPLES.md**: End-to-end workflow examples
- **assets/templates/blueprint-example.yaml**: Sample blueprint template

## API Reference

- **Base URL**: `https://api.render.com/v1`
- **Authentication**: Bearer token in `Authorization` header
- **Response Format**: JSON
- **Pagination**: Cursor-based (see `cursor` field in responses)
- **Rate Limiting**: Limits returned in response headers

For detailed API information, use the search tool or see `references/OPERATIONS-GUIDE.md`.
