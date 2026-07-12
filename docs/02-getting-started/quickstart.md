# Quick Start

Get up and running in 5 minutes.

## Step 1: Install

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure

```bash
cp .env.example .env
```

Edit `.env` with your Wiki.js URL and API key:

```env
WIKIJS_URL=https://wiki.example.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

## Step 3: Test Connection

```bash
wiki-cli
```

Select option **16** (Test Connection) to verify everything works.

```
Select an option: 16

--- Test Connection ---
URL: https://wiki.example.com/graphql
Pages found: 42
Most recent: Getting Started (updated 2025-01-15)
Connection OK.

Press Enter to continue...
```

## Step 4: Try the CLI

```bash
wiki-cli
```

### Create Your First Page

```
Select an option: 1

--- Create Page ---
Path (e.g. docs/intro): my-docs/hello
Title: Hello World
Content (Markdown, press Enter when done):
# Hello World

This is my first page created with wiki-script.

Description: A test page
Tags (comma-separated): test, demo
Locale [en]:
Private? (y/n) [n]:
Published? (y/n) [y]:

Created page 1: my-docs/hello
```

### Browse Your Wiki

```
Select an option: 7

--- Browse Pages (tree) ---
/ (root)
├── my-docs/
│   └── hello (id=1)
├── docs/
│   ├── getting-started (id=2)
│   └── api (id=3)

View page by ID (or press Enter to skip):
```

## Step 5: Try the AI Assistant

```bash
# Install AI dependencies first
pip install -e ".[ai]"

# Start the AI assistant
wiki-ai
```

On first run, select a provider:

```
  available providers:

    1    OpenAI
    2    OpenRouter
    3    Groq
    4    Mistral
    5    Ollama (Local)
    6    Ollama Cloud (Remote)

  > 2

  OpenRouter API Key:
  > sk-or-v1-your-key-here
  saved
```

Then pick a model and start chatting:

```
  provider:  OpenRouter
  model:     meta-llama/llama-4-scout:free

  > list all pages

  ▸ Listing pages
  ✓ 42 pages found

  There are 42 pages in your wiki. Here's a summary...
```

## What's Next

- Read the [Basic Usage Guide](../03-guides/basic-usage.md) for detailed feature walkthroughs
- See the [AI Prompts Guide](../03-guides/ai-prompts.md) for example prompts
- Check the [Commands Reference](../04-commands/reference.md) for the full list of operations
