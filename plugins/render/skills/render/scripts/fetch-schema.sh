#!/bin/bash
# Fetches the latest Render API OpenAPI schema and generates search index
# Usage: ./scripts/fetch-schema.sh

set -e  # Exit on error

SCHEMA_URL="https://api-docs.render.com/openapi/render-public-api-1.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEMA_DIR="$PROJECT_ROOT/assets/schema"
SCHEMA_FILE="$SCHEMA_DIR/render-api-schema.json"
METADATA_FILE="$SCHEMA_DIR/schema-metadata.json"

# Create schema directory if it doesn't exist
mkdir -p "$SCHEMA_DIR"

echo "Fetching Render API schema from $SCHEMA_URL..."
curl -s "$SCHEMA_URL" -o "$SCHEMA_FILE"

if [ ! -s "$SCHEMA_FILE" ]; then
    echo "Error: Failed to download schema or file is empty"
    exit 1
fi

echo "Schema downloaded successfully"

# Check if jq is available for parsing JSON
if command -v jq &> /dev/null; then
    SCHEMA_VERSION=$(jq -r '.info.version // "unknown"' "$SCHEMA_FILE")
else
    SCHEMA_VERSION="unknown (jq not installed)"
fi

# Generate metadata
echo "Creating metadata file..."
cat > "$METADATA_FILE" <<EOF
{
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "source": "$SCHEMA_URL",
  "version": "$SCHEMA_VERSION"
}
EOF

echo "Metadata created"

# Generate search index using Python script
echo "Generating search index..."
if command -v python3 &> /dev/null; then
    python3 "$SCRIPT_DIR/generate-index.py"
    echo "✓ Schema fetch complete!"
    echo "  - Schema: $SCHEMA_FILE"
    echo "  - Metadata: $METADATA_FILE"
    echo "  - Index: $SCHEMA_DIR/endpoints-index.json"
else
    echo "Warning: python3 not found. Skipping index generation."
    echo "Install Python 3.8+ and run: python3 scripts/generate-index.py"
fi
