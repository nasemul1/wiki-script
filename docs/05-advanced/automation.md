# Automation

Automate wiki management tasks with scripts, cron jobs, and workflows.

## Batch Operations

### Create Multiple Pages

```python
#!/usr/bin/env python3
"""Create documentation pages from a CSV file."""

import csv
from wiki_cli import WikiJSClient, PagesManager, Page

client = WikiJSClient()
pages = PagesManager(client)

with open("pages.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        page = Page(
            path=row["path"],
            title=row["title"],
            content=row["content"],
            description=row.get("description", ""),
            tags=row.get("tags", "").split(",") if row.get("tags") else [],
        )
        result = pages.create(page)
        print(f"Created: {row['path']} (id={result.page.id})")
```

CSV format:

```csv
path,title,content,description,tags
docs/intro,Introduction,# Welcome,Getting started,docs intro
docs/api,API Reference,# API Docs,API documentation,api reference
docs/faq,FAQ,# Frequently Asked Questions,Common questions,faq
```

### Update Pages in Bulk

```python
#!/usr/bin/env python3
"""Add a footer to all pages under docs/."""

from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

FOOTER = "\n\n---\n*Last updated: 2025*"

for page in pages.list_all():
    if page.path.startswith("docs/"):
        full = pages.get_by_id(page.id)
        if FOOTER not in full.content:
            full.content += FOOTER
            pages.update(full)
            print(f"Updated: {page.path}")
```

### Tag Cleanup

```python
#!/usr/bin/env python3
"""Standardize tags across all pages."""

from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

TAG_MAP = {
    "doc": "docs",
    "documentation": "docs",
    "api-docs": "api",
    "howto": "guide",
    "how-to": "guide",
}

for page in pages.list_all():
    full = pages.get_by_id(page.id)
    original_tags = list(full.tags)

    new_tags = []
    for tag in full.tags:
        normalized = TAG_MAP.get(tag.lower(), tag.lower())
        new_tags.append(normalized)

    new_tags = list(set(new_tags))  # deduplicate

    if new_tags != original_tags:
        full.tags = new_tags
        pages.update(full)
        print(f"Retagged: {page.path}: {original_tags} → {new_tags}")
```

## Scheduled Tasks

### Daily Backup (cron)

```bash
# /etc/cron.d/wiki-backup
0 2 * * * user /path/to/backup-wiki.py
```

```python
#!/usr/bin/env python3
"""Daily wiki backup script."""

import os
import json
from datetime import datetime
from wiki_cli import WikiJSClient, PagesManager

BACKUP_DIR = "/backups/wiki"
DATE = datetime.now().strftime("%Y-%m-%d")

client = WikiJSClient()
pages = PagesManager(client)

backup_path = os.path.join(BACKUP_DIR, DATE)
os.makedirs(backup_path, exist_ok=True)

# Export all pages
for page in pages.list_all(order_by="PATH"):
    filename = f"{page.path.replace('/', '_')}.md"
    filepath = os.path.join(backup_path, filename)
    pages.export_to_file(page.id, filepath)

# Save metadata
metadata = []
for page in pages.list_all():
    metadata.append({
        "id": page.id,
        "path": page.path,
        "title": page.title,
        "tags": page.tags,
        "published": page.isPublished,
    })

with open(os.path.join(backup_path, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Backed up {len(metadata)} pages to {backup_path}")
```

### Weekly Audit

```python
#!/usr/bin/env python3
"""Weekly wiki audit report."""

from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

all_pages = pages.list_all()

# Stats
total = len(all_pages)
published = sum(1 for p in all_pages if p.isPublished)
private = sum(1 for p in all_pages if p.isPrivate)
drafts = total - published

# Pages with no tags
no_tags = [p for p in all_pages if not p.tags]

# Pages with no description
no_desc = [p for p in all_pages if not p.description]

print(f"=== Wiki Audit Report ===")
print(f"Total pages: {total}")
print(f"Published: {published}")
print(f"Drafts: {drafts}")
print(f"Private: {private}")
print(f"")
print(f"Pages without tags: {len(no_tags)}")
for p in no_tags:
    print(f"  - {p.path}")
print(f"")
print(f"Pages without description: {len(no_desc)}")
for p in no_desc:
    print(f"  - {p.path}")
```

### Auto-Publish Drafts

```python
#!/usr/bin/env python3
"""Auto-publish drafts older than 7 days."""

from datetime import datetime, timedelta
from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

cutoff = datetime.now() - timedelta(days=7)

for page in pages.list_all():
    if not page.isPublished:
        full = pages.get_by_id(page.id)
        # Check if draft is old enough to publish
        # (simplified - you'd check versionDate in real usage)
        full.isPublished = True
        pages.update(full)
        print(f"Published draft: {page.path}")
```

## Monitoring Scripts

### Broken Link Checker

```python
#!/usr/bin/env python3
"""Check for broken internal links."""

import re
from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

# Build path index
all_pages = pages.list_all()
path_index = {p.path: p for p in all_pages}

# Check links
broken = []
for page in all_pages:
    full = pages.get_by_id(page.id)
    # Find markdown links: [text](path)
    links = re.findall(r'\[.*?\]\((/.*?)\)', full.content)
    for link in links:
        if link not in path_index:
            broken.append((page.path, link))

if broken:
    print(f"Found {len(broken)} broken links:")
    for page_path, link in broken:
        print(f"  {page_path} → {link}")
else:
    print("No broken links found.")
```

### Content Staleness Checker

```python
#!/usr/bin/env python3
"""Find potentially outdated pages."""

from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

OUTDATED_KEYWORDS = ["TODO", "FIXME", "deprecated", "old version", "coming soon"]

for page in pages.list_all():
    full = pages.get_by_id(page.id)
    content_lower = full.content.lower()

    found = [kw for kw in OUTDATED_KEYWORDS if kw.lower() in content_lower]
    if found:
        print(f"{page.path}: {', '.join(found)}")
```
