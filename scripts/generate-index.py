#!/usr/bin/env python3
"""
Generate searchable index from Render API OpenAPI schema.
Called automatically by fetch-schema.sh
"""

import json
import sys
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent

PROJECT_ROOT = get_project_root()
SCHEMA_FILE = PROJECT_ROOT / "assets/schema/render-api-schema.json"
INDEX_FILE = PROJECT_ROOT / "assets/schema/endpoints-index.json"

def generate_index():
    """Parse OpenAPI schema and create searchable index"""

    if not SCHEMA_FILE.exists():
        print(f"Error: Schema file not found at {SCHEMA_FILE}", file=sys.stderr)
        print("Run ./scripts/fetch-schema.sh first", file=sys.stderr)
        sys.exit(1)

    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading schema file: {e}", file=sys.stderr)
        sys.exit(1)

    index = {
        'version': schema.get('info', {}).get('version', 'unknown'),
        'title': schema.get('info', {}).get('title', 'Render API'),
        'endpoints': []
    }

    # Check if schema has security definitions
    has_global_security = 'security' in schema or 'securitySchemes' in schema.get('components', {})

    paths = schema.get('paths', {})
    if not paths:
        print("Warning: No paths found in schema", file=sys.stderr)

    for path, path_item in paths.items():
        for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
            if method not in path_item:
                continue

            operation = path_item[method]

            # Extract endpoint information
            endpoint = {
                'path': path,
                'method': method.upper(),
                'summary': operation.get('summary', ''),
                'description': operation.get('description', ''),
                'tags': operation.get('tags', []),
                'operationId': operation.get('operationId', ''),
                'security_required': 'security' in operation or has_global_security,
                'parameters_count': len(operation.get('parameters', [])),
                'has_requestBody': 'requestBody' in operation,
                'deprecated': operation.get('deprecated', False)
            }

            index['endpoints'].append(endpoint)

    # Sort endpoints by path and method for consistent output
    index['endpoints'].sort(key=lambda x: (x['path'], x['method']))

    # Write index to file
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        print(f"✓ Generated index with {len(index['endpoints'])} endpoints")
        print(f"  Index saved to: {INDEX_FILE}")
        return True

    except Exception as e:
        print(f"Error writing index file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    try:
        generate_index()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
