# wiki-script

Python automation toolkit for managing a Wiki.js instance via its GraphQL API.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

## Scripts

Each operation is a standalone script. Run with `--help` for options.

### Create a page

```bash
python create_page.py "projects/alpha/overview" "Project Alpha" "# Hello World" \
    --description "Overview page" --tags "project,alpha"
```

### Fetch a page

```bash
python fetch_page.py --id 15
python fetch_page.py --path projects/alpha/overview
```

### Update a page

```bash
python update_page.py --id 15 --title "New Title" --append-content "\n\n## New Section"
```

### Delete a page

```bash
python delete_page.py 15
```

### Upload an asset

```bash
python upload_asset.py document.pdf --folder-id 0
```

## As a library

```python
from urllib.parse import urlparse
from wiki_script import WikiJSClient, Page, PagesManager, AssetsManager

client = WikiJSClient()
pages = PagesManager(client)

# Create
page = Page(path="docs/intro", title="Intro", content="# Hi", description="Intro page")
resp = pages.create(page)

# Fetch
fetched = pages.get_by_id(resp.page.id)

# Update
fetched.content += "\n\nUpdated."
pages.update(fetched)

# Upload asset (uses REST /u endpoint)
parsed = urlparse(client.url)
assets = AssetsManager(f"{parsed.scheme}://{parsed.netloc}", client.api_key)
assets.upload("photo.png", folder_id=0)

# Delete
pages.delete(resp.page.id)
```

## Project Structure

```
wiki-script/
├── wiki_script/
│   ├── __init__.py
│   ├── exceptions.py          # WikiJSError
│   ├── models.py              # Page, Asset, PageResponse (Pydantic)
│   ├── wiki_client.py         # WikiJSClient (gql transport)
│   └── operations/
│       ├── __init__.py
│       ├── pages.py           # PagesManager (GraphQL CRUD)
│       └── assets.py          # AssetsManager (REST upload)
├── create_page.py             # Create a page
├── fetch_page.py              # Fetch a page
├── update_page.py             # Update a page
├── delete_page.py             # Delete a page
├── upload_asset.py            # Upload a file
├── requirements.txt
└── .env.example
```