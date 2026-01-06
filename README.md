# Render Skills Marketplace

A Claude Code plugin marketplace providing comprehensive tools for managing Render cloud infrastructure.

## Installation

### From GitHub

Once published, users can install from your GitHub repository:

```bash
# Add the marketplace
/plugin marketplace add <your-github-username>/render-skills

# Install the render plugin
/plugin install render@render-skills-marketplace
```

### Local Installation (for testing)

```bash
# Add the marketplace locally
/plugin marketplace add /Users/tej/Desktop/Code/render-skills

# Install the plugin
/plugin install render@render-skills-marketplace
```

## Plugins

### render

Complete toolkit for managing Render cloud infrastructure via API:

- Create and configure services (web, workers, cron jobs)
- Manage deployments and environment variables
- Configure datastores (Postgres, Redis, Key-Value stores)
- Work with infrastructure-as-code blueprints
- Monitor logs and metrics
- Troubleshoot common issues

See the [plugin README](./plugins/render/README.md) for detailed usage instructions.

## Publishing

To publish this marketplace:

1. Push to GitHub:
   ```bash
   git push origin main
   ```

2. Users can then add your marketplace:
   ```bash
   /plugin marketplace add your-username/render-skills
   ```

## License

Apache-2.0
