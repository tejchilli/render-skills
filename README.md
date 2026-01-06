# Render Skills for Claude Code

A comprehensive skill for managing Render cloud infrastructure through Claude Code. This plugin provides complete guidance and automation for working with the Render.com hosting platform.

## Features

- **Service Management**: Create and configure web services, background workers, cron jobs, and static sites
- **Deployment Control**: Trigger deployments, monitor status, view logs, and manage rollbacks
- **Datastore Operations**: Set up and manage PostgreSQL, Redis, and Key-Value stores
- **Environment Configuration**: Manage environment variables and secrets
- **Infrastructure as Code**: Work with Render blueprints for declarative infrastructure
- **Monitoring & Troubleshooting**: Access logs, metrics, and diagnostic tools
- **API Discovery**: Built-in search tool for finding relevant API endpoints

## Installation

### Via Plugin Marketplace

Add this marketplace to your Claude Code configuration:

```bash
claude plugin add https://raw.githubusercontent.com/YOUR_USERNAME/render-skills/main/.claude-plugin/marketplace.json
```

Then install the skill:

```bash
claude plugin install render
```

### Manual Installation

Clone and symlink:

```bash
git clone https://github.com/YOUR_USERNAME/render-skills.git
ln -s $(pwd)/render-skills ~/.config/claude-code/skills/render
```

## Usage

Once installed, invoke the skill in Claude Code using `/render`:

```
/render help me create a web service with Node.js
/render show me how to deploy my application
/render configure a postgres database
/render check the logs for my service
```

## Quick Start

1. **Set your Render API key**:
   ```bash
   export RENDER_API_KEY="your_api_key_here"
   ```
   Get your API key from: https://dashboard.render.com/settings/api-keys

2. **Use the skill** in Claude Code to manage your infrastructure

3. **Search the API** using the built-in search tool:
   ```bash
   python3 scripts/search-api.py "postgres"
   ```

## Requirements

- Python 3.8+
- curl
- jq
- Internet access for API calls
- Render API key

## Documentation

- **SKILL.md**: Main skill documentation with examples
- **references/RESOURCES.md**: Detailed service types and datastore configurations
- **references/OPERATIONS-GUIDE.md**: Advanced operations and troubleshooting
- **references/BLUEPRINTS.md**: Infrastructure-as-code guide
- **references/EXAMPLES.md**: End-to-end workflow examples

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

Apache-2.0

## Support

- Render Documentation: https://render.com/docs
- Render API Reference: https://api-docs.render.com
- Render Status: https://status.render.com
