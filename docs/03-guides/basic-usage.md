# Basic Usage

This guide covers the everyday operations you'll use most often.

## Starting the CLI

```bash
wiki-cli
```

You'll see the main menu:

```
========================================
       Wiki.js Manager
========================================
  --- Pages ---
  1. Create Page
  2. Fetch Page
  ...
  0. Exit
========================================

Select an option:
```

Type a number and press Enter.

## Creating Pages

Select option **1**:

```
Select an option: 1

--- Create Page ---
Path (e.g. docs/intro): docs/getting-started
Title: Getting Started
Content (Markdown, press Enter when done):
# Getting Started

Welcome to our documentation.

Description: Quick start guide
Tags (comma-separated): docs, intro
Locale [en]:
Private? (y/n) [n]:
Published? (y/n) [y]:

Created page 1: docs/getting-started
```

**Tips:**
- Path determines the URL: `docs/getting-started` → `your-wiki.com/docs/getting-started`
- Leave optional fields blank to use defaults
- Tags help with organization and filtering

## Viewing Pages

Select option **2**:

```
Select an option: 2

--- Fetch Page ---
Fetch by:
  1. ID
  2. Path
Choose [1]:

Page ID: 1

ID:        1
Path:      docs/getting-started
Title:     Getting Started
Description: Quick start guide
Published: True
Private:   False
Locale:    en
Tags:      docs, intro
---
# Getting Started

Welcome to our documentation.
```

## Updating Pages

Select option **3**:

```
Select an option: 3

--- Update Page ---
Page ID: 1

Current title: Getting Started
New title [Getting Started]: Getting Started Guide

Current description: Quick start guide
New description [Quick start guide]:

Content options:
  1. Replace
  2. Append
  3. Keep current
Choice [3]: 2

Append content (Markdown, press Enter when done):

## Next Steps

Check out the API reference.

Tags (comma-separated) [docs, intro]: docs, intro, guide
Published? (y/n) [y]:

Updated page 1.
```

## Deleting Pages

Select option **4**:

```
Select an option: 4

--- Delete Page ---
Page ID: 5

This will permanently delete page 5.
Continue? (yes/no): yes

Deleted page 5.
```

**Note:** Deletion requires typing `yes` to confirm.

## Listing Pages

Select option **5**:

```
Select an option: 5

Sort by:
  1. Title
  2. Path
  3. Created
  4. Updated
Choice [1]: 2

  ID  Path                     Title               Published
  --  ----                     -----               ---------
   1  docs/getting-started     Getting Started     Yes
   2  docs/api/reference       API Reference       Yes
   3  docs/faq                 FAQ                 No
  ...

Filter by tag (or press Enter to skip): docs

  ID  Path                     Title               Published
  --  ----                     -----               ---------
   1  docs/getting-started     Getting Started     Yes
   2  docs/api/reference       API Reference       Yes

Showing 2 of 2 pages. Press Enter for next page or 'q' to quit.
```

## Searching Pages

Select option **6**:

```
Select an option: 6

--- Search Pages ---
Query: authentication
Locale (or press Enter for any):

  ID  Path                     Title               Description
  --  ----                     -----               -----------
   8  docs/security/auth       Authentication      User auth guide
  12  docs/api/auth-tokens     Auth Tokens         API token usage

Found 2 result(s).
```

## Browsing the Tree

Select option **7**:

```
Select an option: 7

--- Browse Pages (tree) ---
/ (root)
├── docs/
│   ├── getting-started (id=1)
│   ├── api/
│   │   ├── reference (id=2)
│   │   └── auth-tokens (id=12)
│   └── faq (id=3) [draft]
├── guides/
│   ├── installation (id=4)
│   └── configuration (id=5)

View page by ID (or press Enter to skip): 2
```

## Moving and Renaming

Select option **8**:

```
Select an option: 8

--- Move/Rename Page ---
Page ID: 2

Current path: docs/api/reference
Current title: API Reference
New path (leave blank to keep) [docs/api/reference]: docs/api/v2-reference
New title (leave blank to keep) [API Reference]: API Reference v2

This will move/rename:
  docs/api/reference  ->  docs/api/v2-reference
  Title: API Reference  ->  API Reference v2

Continue? (yes/no): yes

Moved page 2 to: docs/api/v2-reference
```

## Working with Files

### Export a Page

```
Select an option: 10

--- Export Page ---
Page ID: 1
Filename [docs_getting-started.md]:

Exported page 1 to docs_getting-started.md
```

The exported file includes YAML frontmatter:

```yaml
---
title: Getting Started
path: docs/getting-started
description: Quick start guide
tags: [docs, intro]
published: true
private: false
locale: en
---

# Getting Started

Welcome to our documentation.
```

### Import a Page

```
Select an option: 11

--- Import Page ---
Filename: my-page.md

Imported page 15: docs/imported-page
```

The importer reads YAML frontmatter automatically. If no frontmatter is found, it prompts for path and title.
