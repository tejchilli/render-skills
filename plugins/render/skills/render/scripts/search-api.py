#!/usr/bin/env python3
"""
Search the Render API schema efficiently without loading the full schema.

Usage:
  python3 scripts/search-api.py "postgres"
  python3 scripts/search-api.py "deploy" --category services
  python3 scripts/search-api.py --list-endpoints
  python3 scripts/search-api.py --help
"""

import json
import sys
import re
import argparse
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent

PROJECT_ROOT = get_project_root()
SCHEMA_FILE = PROJECT_ROOT / "assets/schema/render-api-schema.json"
INDEX_FILE = PROJECT_ROOT / "assets/schema/endpoints-index.json"

def load_index():
    """Load pre-processed endpoint index"""
    if not INDEX_FILE.exists():
        print(f"Error: Index file not found at {INDEX_FILE}", file=sys.stderr)
        print("Run ./scripts/fetch-schema.sh to download schema and generate index", file=sys.stderr)
        sys.exit(1)

    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in index file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading index file: {e}", file=sys.stderr)
        sys.exit(1)

def search_endpoints(query, category=None, exact=False):
    """
    Search endpoints by keyword

    Args:
        query: Search term
        category: Optional category filter (tag name)
        exact: If True, use exact matching instead of regex

    Returns:
        List of matching endpoints
    """
    index = load_index()
    results = []

    # Create search pattern
    if exact:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
    else:
        pattern = re.compile(query, re.IGNORECASE)

    for endpoint in index['endpoints']:
        # Skip deprecated endpoints by default
        if endpoint.get('deprecated', False):
            continue

        # Build searchable string from endpoint data
        searchable_parts = [
            endpoint['path'],
            endpoint['method'],
            endpoint['summary'],
            endpoint.get('description', ''),
            endpoint.get('operationId', ''),
            ' '.join(endpoint.get('tags', []))
        ]
        searchable = ' '.join(searchable_parts)

        # Check if pattern matches
        if pattern.search(searchable):
            # Apply category filter if specified
            if category is None or category.lower() in [t.lower() for t in endpoint.get('tags', [])]:
                results.append(endpoint)

    return results

def format_endpoint(ep, show_description=True):
    """Format endpoint for display"""
    lines = []
    lines.append(f"{ep['method']:7} {ep['path']}")

    if ep.get('summary'):
        lines.append(f"        Summary: {ep['summary']}")

    if show_description and ep.get('description') and ep['description'] != ep.get('summary'):
        # Truncate long descriptions
        desc = ep['description']
        if len(desc) > 100:
            desc = desc[:97] + "..."
        lines.append(f"        Description: {desc}")

    if ep.get('tags'):
        lines.append(f"        Tags: {', '.join(ep['tags'])}")

    # Additional metadata
    meta = []
    if ep.get('security_required'):
        meta.append("Auth required")
    if ep.get('parameters_count', 0) > 0:
        meta.append(f"{ep['parameters_count']} params")
    if ep.get('has_requestBody'):
        meta.append("Has request body")
    if ep.get('deprecated'):
        meta.append("DEPRECATED")

    if meta:
        lines.append(f"        {' | '.join(meta)}")

    return '\n'.join(lines)

def list_endpoints(filter_tag=None):
    """List all endpoints, optionally filtered by tag"""
    index = load_index()

    endpoints = index['endpoints']
    if filter_tag:
        endpoints = [ep for ep in endpoints if filter_tag.lower() in [t.lower() for t in ep.get('tags', [])]]

    print(f"API: {index.get('title', 'Render API')} v{index.get('version', 'unknown')}")
    print(f"Total endpoints: {len(endpoints)}\n")

    for ep in endpoints:
        deprecated_marker = " [DEPRECATED]" if ep.get('deprecated') else ""
        print(f"{ep['method']:7} {ep['path']}{deprecated_marker}")

def show_stats():
    """Show statistics about the API"""
    index = load_index()

    endpoints = index['endpoints']

    # Count by method
    methods = {}
    tags = {}

    for ep in endpoints:
        method = ep['method']
        methods[method] = methods.get(method, 0) + 1

        for tag in ep.get('tags', ['Untagged']):
            tags[tag] = tags.get(tag, 0) + 1

    print(f"API: {index.get('title', 'Render API')} v{index.get('version', 'unknown')}\n")
    print(f"Total Endpoints: {len(endpoints)}\n")

    print("By Method:")
    for method, count in sorted(methods.items()):
        print(f"  {method:7} {count}")

    print("\nBy Category (Tag):")
    for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag:30} {count}")

def main():
    parser = argparse.ArgumentParser(
        description='Search Render API endpoints efficiently',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "postgres"                    # Search for postgres-related endpoints
  %(prog)s "deploy" --category services  # Search deployments in services category
  %(prog)s --list-endpoints              # List all endpoints
  %(prog)s --list-endpoints --tag Owner  # List endpoints with 'Owner' tag
  %(prog)s --stats                       # Show API statistics
        """
    )

    parser.add_argument('query', nargs='?', help='Search term')
    parser.add_argument('--category', '--tag', dest='category', help='Filter by category/tag')
    parser.add_argument('--list-endpoints', '-l', action='store_true', help='List all endpoints')
    parser.add_argument('--exact', '-e', action='store_true', help='Use exact matching')
    parser.add_argument('--limit', '-n', type=int, default=10, help='Maximum results to show (default: 10)')
    parser.add_argument('--all', '-a', action='store_true', help='Show all results (no limit)')
    parser.add_argument('--stats', '-s', action='store_true', help='Show API statistics')

    args = parser.parse_args()

    # Show stats
    if args.stats:
        show_stats()
        return

    # List all endpoints
    if args.list_endpoints:
        list_endpoints(args.category)
        return

    # Search mode requires a query
    if not args.query:
        parser.print_help()
        sys.exit(1)

    # Search for endpoints
    results = search_endpoints(args.query, args.category, args.exact)

    limit = None if args.all else args.limit

    # Display results
    print(f"\nFound {len(results)} endpoint(s) matching '{args.query}'")
    if args.category:
        print(f"  (filtered by category: {args.category})")
    print()

    if not results:
        print("No matching endpoints found. Try:")
        print("  - Different search terms")
        print("  - Broader search (remove --category filter)")
        print("  - List all endpoints: python3 scripts/search-api.py --list-endpoints")
        return

    # Show results
    display_results = results[:limit] if limit else results

    for i, ep in enumerate(display_results, 1):
        print(format_endpoint(ep, show_description=True))
        if i < len(display_results):
            print()  # Blank line between results

    # Show truncation message
    if limit and len(results) > limit:
        print(f"\n... and {len(results) - limit} more result(s).")
        print(f"Use --all to see all results, or refine your search.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
