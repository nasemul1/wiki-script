# Contributing

Guide for contributing to wiki-script.

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- A running Wiki.js instance (for integration testing)

### Clone and Install

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[ai,dev]"
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific feature
pytest tests/test_create_page.py -v

# With coverage
pytest tests/ --cov=wiki_cli --cov-report=term-missing
```

## Project Structure

```
wiki_cli/
├── __init__.py          # Package exports
├── __main__.py          # python -m entry point
├── client.py            # GraphQL transport
├── models.py            # Pydantic data models
├── utils.py             # CLI helpers
├── exceptions.py        # Custom exceptions
├── cli_main.py          # Main menu loop
├── cli_pages.py         # Page CLI handlers
├── cli_history.py       # History CLI handlers
├── cli_system.py        # System CLI handlers
├── pages/
│   ├── manager.py       # Business logic
│   ├── queries.py       # GraphQL queries
│   └── history.py       # History queries
└── ai/
    ├── config.py        # Provider configuration
    ├── agent.py         # AI agent
    ├── tools.py         # Tool schemas
    └── cli.py           # AI chat UI
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Use Pydantic models for data structures
- Keep functions focused and small
- Use descriptive variable names

### CLI Output

- Use ANSI color codes for formatting
- Use Unicode box-drawing for tree views
- Keep output clean and readable
- Validate all user input

### AI Tools

- Each tool maps to a `PagesManager` method
- Tool schemas go in `tools.py`
- Tool handlers go in `agent.py`
- Always log tool calls

## Adding a New Feature

### 1. Add the GraphQL Query

In `wiki_cli/pages/queries.py` or `history.py`:

```python
MY_QUERY = """
query MyQuery($id: Int!) {
  pages {
    myOperation(id: $id) {
      field1
      field2
    }
  }
}
"""
```

### 2. Add the PagesManager Method

In `wiki_cli/pages/manager.py`:

```python
def my_method(self, id: int) -> MyResult:
    result = self.client.execute(MY_QUERY, variable_values={"id": id})
    # Parse and return
```

### 3. Add the CLI Handler

In `wiki_cli/cli_pages.py` or appropriate file:

```python
def my_handler(pages: PagesManager) -> None:
    raw = input("ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    result = pages.my_method(int(raw))
    # Display result
```

### 4. Register in Menu

In `wiki_cli/cli_main.py`:

```python
from wiki_cli.cli_pages import my_handler

handlers = {
    ...
    "18": ("My Feature", lambda: my_handler(pages)),
}
```

Update the `MENU` string.

### 5. Add AI Tool (Optional)

In `wiki_cli/ai/tools.py`:

```python
{
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "Description for the LLM",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Item ID"}
            },
            "required": ["id"]
        }
    }
}
```

In `wiki_cli/ai/agent.py`:

```python
"my_tool": self._tool_my_method,
```

```python
def _tool_my_method(self, args: dict) -> Any:
    return self.pages.my_method(args["id"])
```

### 6. Add Tests

Create `tests/test_my_feature.py`:

```python
from my_feature.success import test_my_feature_success as _success
from my_feature.validation import test_my_feature_validation as _validation

def test_my_feature_success(mock_manager, capsys):
    _success(mock_manager, capsys)

def test_my_feature_validation(mock_manager, capsys):
    _validation(mock_manager, capsys)
```

Create `tests/my_feature/success.py`:

```python
from unittest.mock import patch
from wiki_cli.cli_pages import my_handler

def test_my_feature_success(mock_manager, capsys):
    mock_result = Mock()
    mock_manager.my_method.return_value = mock_result

    with patch("builtins.input", side_effect=["1"]):
        my_handler(mock_manager)

    captured = capsys.readouterr()
    assert "expected output" in captured.out
```

## Commit Messages

Use clear, descriptive commit messages:

```
Add export page feature
Fix tree view for single-segment paths
Update AI tool schemas for create_page
Add tests for move/rename validation
```

## Pull Requests

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and add tests
3. Run all tests: `pytest tests/ -v`
4. Commit with a clear message
5. Push and create a pull request

### PR Checklist

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] No new warnings
- [ ] Code follows project style
- [ ] New features have tests
- [ ] Documentation updated if needed
- [ ] CHANGELOG updated for notable changes

## Reporting Issues

When reporting bugs, include:

1. Python version (`python --version`)
2. OS and terminal
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Error output (if any)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
