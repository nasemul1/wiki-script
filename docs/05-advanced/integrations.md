# Integrations

wiki-script can be integrated into larger workflows and systems.

## As a Python Library

The most powerful integration method. Import and use directly in your Python code.

### Basic Usage

```python
from wiki_cli import WikiJSClient, PagesManager, Page

client = WikiJSClient()
pages = PagesManager(client)

# All operations available
page = pages.get_by_id(5)
pages.update(page)
```

### With Custom Configuration

```python
from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient(
    url="https://wiki.example.com/graphql",
    api_key="your-api-key",
)
pages = PagesManager(client)
```

### Error Handling

```python
from wiki_cli import WikiJSClient, PagesManager, WikiJSError

client = WikiJSClient()
pages = PagesManager(client)

try:
    page = pages.get_by_id(999)
except WikiJSError as e:
    print(f"Error: {e}")
    # Handle gracefully
```

## Git Integration

### Auto-Commit Documentation Changes

```python
#!/usr/bin/env python3
"""Export wiki pages and commit changes."""

import subprocess
from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

# Export all pages
for page in pages.list_all(order_by="PATH"):
    filename = f"docs/{page.path.replace('/', '_')}.md"
    pages.export_to_file(page.id, filename)

# Commit changes
subprocess.run(["git", "add", "docs/"])
subprocess.run(["git", "commit", "-m", "Update wiki documentation"])
subprocess.run(["git", "push"])
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for broken wiki links
python -c "
from wiki_cli import WikiJSClient, PagesManager
client = WikiJSClient()
pages = PagesManager(client)
all_paths = {p.path for p in pages.list_all()}

# Check for references to non-existent pages
import re
for page in pages.list_all():
    full = pages.get_by_id(page.id)
    links = re.findall(r'\[.*?\]\((.*?)\)', full.content)
    for link in links:
        if link.startswith('/') and link[1:] not in all_paths:
            print(f'Warning: {page.path} links to non-existent {link}')
"
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/update-docs.yml
name: Update Wiki Documentation

on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  update-wiki:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install wiki-script
        run: pip install wiki-script

      - name: Update wiki
        env:
          WIKIJS_URL: ${{ secrets.WIKIJS_URL }}
          WIKIJS_API_KEY: ${{ secrets.WIKIJS_API_KEY }}
        run: |
          python -c "
          from wiki_cli import WikiJSClient, PagesManager
          import os, glob

          client = WikiJSClient()
          pages = PagesManager(client)

          for md_file in glob.glob('docs/**/*.md', recursive=True):
              with open(md_file) as f:
                  content = f.read()

              path = md_file.replace('docs/', '').replace('.md', '').replace('/', '-')
              title = content.split('\n')[0].lstrip('# ').strip()

              existing = pages.search(path)
              if existing:
                  page = pages.get_by_id(existing[0].id)
                  page.content = content
                  pages.update(page)
              else:
                  page = Page(path=path, title=title, content=content)
                  pages.create(page)
          "
```

### GitLab CI

```yaml
# .gitlab-ci.yml
update-wiki:
  stage: deploy
  script:
    - pip install wiki-script
    - python scripts/sync-wiki.py
  only:
    - main
  variables:
    WIKIJS_URL: $WIKIJS_URL
    WIKIJS_API_KEY: $WIKIJS_API_KEY
```

## Webhook Integration

### Flask Webhook Handler

```python
from flask import Flask, request, jsonify
from wiki_cli import WikiJSClient, PagesManager, Page

app = Flask(__name__)
client = WikiJSClient()
pages = PagesManager(client)

@app.route("/webhook/page-update", methods=["POST"])
def handle_page_update():
    data = request.json

    path = data.get("path")
    content = data.get("content")
    title = data.get("title")

    if not path or not content:
        return jsonify({"error": "path and content required"}), 400

    existing = pages.search(path)
    if existing:
        page = pages.get_by_id(existing[0].id)
        page.content = content
        if title:
            page.title = title
        pages.update(page)
        return jsonify({"status": "updated", "id": page.id})
    else:
        page = Page(path=path, title=title or path, content=content)
        result = pages.create(page)
        return jsonify({"status": "created", "id": result.page.id})
```

## Monitoring Integration

### Health Check Script

```python
#!/usr/bin/env python3
"""Wiki.js health check for monitoring systems."""

import sys
from wiki_cli import WikiJSClient, PagesManager, WikiJSError

def check_wiki():
    try:
        client = WikiJSClient()
        pages = PagesManager(client)
        page_list = pages.list_all()

        print(f"wiki_pages_total {len(page_list)}")
        print(f"wiki_status 1")  # 1 = healthy
        return 0
    except WikiJSError as e:
        print(f"wiki_status 0")  # 0 = unhealthy
        print(f"wiki_error \"{e}\"", file=sys.stderr)
        return 1

sys.exit(check_wiki())
```

### Prometheus Metrics

```python
from prometheus_client import Gauge, start_http_server
from wiki_cli import WikiJSClient, PagesManager

wiki_pages_total = Gauge('wiki_pages_total', 'Total number of wiki pages')
wiki_status = Gauge('wiki_status', 'Wiki.js connection status')

def collect_metrics():
    try:
        client = WikiJSClient()
        pages = PagesManager(client)
        page_list = pages.list_all()
        wiki_pages_total.set(len(page_list))
        wiki_status.set(1)
    except Exception:
        wiki_status.set(0)

# Start metrics server
start_http_server(8000)
collect_metrics()
```
