"""AI agent that translates natural language prompts into Wiki.js operations."""

from __future__ import annotations

import json
from typing import Any

from wiki_cli import WikiJSClient, WikiJSError
from wiki_cli.models import Page
from wiki_cli.pages import PagesManager
from wiki_cli.ai.config import AIConfig
from wiki_cli.ai.tools import TOOLS

# ── ANSI ─────────────────────────────────────────────────────────────

R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
C = "\033[36m"
G = "\033[32m"
Y = "\033[33m"
X = "\033[90m"

TOOL_LABELS = {
    "create_page":     "Creating page",
    "fetch_page":      "Fetching page",
    "update_page":     "Updating page",
    "delete_page":     "Deleting page",
    "list_pages":      "Listing pages",
    "search_pages":    "Searching pages",
    "browse_tree":     "Browsing tree",
    "move_page":       "Moving page",
    "move_pages":      "Moving pages",
    "clone_page":      "Cloning page",
    "export_page":     "Exporting page",
    "import_page":     "Importing page",
    "view_history":    "Viewing history",
    "view_revision":   "Viewing revision",
    "diff_revisions":  "Diffing revisions",
    "restore_revision": "Restoring revision",
    "test_connection": "Testing connection",
    "jira_test_connection": "Jira: Testing connection",
    "jira_list_projects":   "Jira: Listing projects",
    "jira_search_issues":   "Jira: Searching issues",
    "jira_get_issue":       "Jira: Getting issue",
    "jira_get_comments":    "Jira: Getting comments",
    "jira_get_changelog":   "Jira: Getting changelog",
    "jira_get_transitions": "Jira: Getting transitions",
}

MAX_CONTEXT_TOKENS = 100_000

SYSTEM_PROMPT = """You are a Wiki.js and Jira assistant. You manage wiki pages and Jira issues using the tools provided.

Rules:
- Always confirm with the user before performing destructive actions (delete, restore, move).
- When creating or updating pages, generate high-quality Markdown content when the user provides a topic.
- If a tool returns an error, explain it to the user and suggest fixes.
- For searches or lists, summarize results in a readable format instead of dumping raw data.
- Never fabricate page IDs, issue keys, or paths. Always fetch first if unsure.
- For Jira, never attempt write operations (create, edit, comment). Only read data.
- When showing Jira issues, group by status or priority for clarity.
"""


class WikiAgent:
    """AI agent that uses LLM tool calling to execute Wiki.js operations.

    Attributes:
        pages: The PagesManager instance for executing operations.
        config: The AI provider configuration.
        client: The underlying LLM client (OpenAI-compatible).
    """

    def __init__(
        self,
        config: AIConfig | None = None,
        wiki_client: WikiJSClient | None = None,
        wiki_name: str | None = None,
    ) -> None:
        self.config = config or AIConfig()
        if wiki_client is None:
            from wiki_cli.wikis import get_active_client

            self.wiki_client = get_active_client()
        else:
            self.wiki_client = wiki_client
        self.pages = PagesManager(self.wiki_client)
        self.client = self.config.get_client()
        self.wiki_name = wiki_name
        self._warned_at_80pct = False
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.quiet = False

        # Jira (optional — gracefully unavailable if not configured)
        self.jira_manager = None
        try:
            from wiki_cli.jira.client import JiraClient
            from wiki_cli.jira.manager import JiraManager

            jira_client = JiraClient()
            self.jira_manager = JiraManager(jira_client)
        except Exception:
            pass

    def run(self, user_prompt: str) -> str:
        """Process a user prompt and return the AI's response.

        Maintains conversation history across calls so the LLM retains context.
        Persists history to disk after each response when wiki_name is set.
        """
        result = self._run_openai(user_prompt)
        if self.wiki_name:
            try:
                from wiki_cli.ai.sessions import save_session

                save_session(self.wiki_name, self.messages)
            except Exception:
                pass  # non-fatal
        return result

    def clear_history(self) -> None:
        """Reset conversation history, keeping only the system prompt.
        Also deletes the on-disk session file if wiki_name is set.
        """
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self._warned_at_80pct = False
        if self.wiki_name:
            try:
                from wiki_cli.ai.sessions import delete_session

                delete_session(self.wiki_name)
            except Exception:
                pass

    def _check_token_warning(self) -> None:
        """Print a one-time warning when token estimate crosses 80% of MAX_CONTEXT_TOKENS."""
        if self._warned_at_80pct:
            return
        estimated = self._estimate_tokens(self.messages)
        threshold = int(MAX_CONTEXT_TOKENS * 0.8)
        if estimated >= threshold:
            import sys

            print(
                f"\n⚠ context approaching {MAX_CONTEXT_TOKENS // 1000}k limit "
                f"(~{estimated // 1000}k tokens). Older messages will be trimmed.",
                file=sys.stderr,
            )
            self._warned_at_80pct = True

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        total = 0
        for m in messages:
            content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
            if content:
                total += len(content) // 4
            args = getattr(m, "arguments", None) or (m.get("arguments", "") if isinstance(m, dict) else "")
            if args:
                total += len(args) // 4
        return total

    def _trim_history(self) -> None:
        self._check_token_warning()
        if self._estimate_tokens(self.messages) <= MAX_CONTEXT_TOKENS:
            return

        system = self.messages[:1]
        rest = self.messages[1:]

        while rest and self._estimate_tokens(system + rest[2:]) > MAX_CONTEXT_TOKENS:
            rest.pop(0)

        if rest:
            rest.insert(0, {
                "role": "user",
                "content": f"{D}[context trimmed — last {len(rest)} messages kept]{R}",
            })

        self.messages = system + rest

    def _run_openai(self, user_prompt: str) -> str:
        """Tool-calling loop for OpenAI-compatible APIs.

        Works with all supported providers (openai, openrouter, groq, mistral,
        ollama, ollama-cloud) since they all use the same chat completions API.
        """
        self.messages.append({"role": "user", "content": user_prompt})

        self._trim_history()

        while True:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                self.messages.append({"role": "assistant", "content": msg.content or ""})
                return msg.content or ""

            self.messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tool_call in msg.tool_calls:
                result = self._execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

    def _execute_tool(self, name: str, arguments_json: str) -> dict[str, Any]:
        """Execute a tool call and return a structured result.

        Args:
            name: The tool/function name.
            arguments_json: JSON string of arguments from the LLM.

        Returns:
            A dict with 'success' and 'data' or 'error' keys.
        """
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON arguments: {e}"}

        self._log_tool(name, args)

        dispatch = {
            "create_page": self._tool_create_page,
            "fetch_page": self._tool_fetch_page,
            "update_page": self._tool_update_page,
            "delete_page": self._tool_delete_page,
            "list_pages": self._tool_list_pages,
            "search_pages": self._tool_search_pages,
            "browse_tree": self._tool_browse_tree,
            "move_page": self._tool_move_page,
            "move_pages": self._tool_move_pages,
            "clone_page": self._tool_clone_page,
            "export_page": self._tool_export_page,
            "import_page": self._tool_import_page,
            "view_history": self._tool_view_history,
            "view_revision": self._tool_view_revision,
            "diff_revisions": self._tool_diff_revisions,
            "restore_revision": self._tool_restore_revision,
            "test_connection": self._tool_test_connection,
            "jira_test_connection": self._tool_jira_test_connection,
            "jira_list_projects": self._tool_jira_list_projects,
            "jira_search_issues": self._tool_jira_search_issues,
            "jira_get_issue": self._tool_jira_get_issue,
            "jira_get_comments": self._tool_jira_get_comments,
            "jira_get_changelog": self._tool_jira_get_changelog,
            "jira_get_transitions": self._tool_jira_get_transitions,
        }

        handler = dispatch.get(name)
        if not handler:
            return {"success": False, "error": f"Unknown tool: {name}"}

        try:
            result = handler(args)
            self._log_result(name, result)
            if hasattr(result, "model_dump"):
                return {"success": True, "data": result.model_dump()}
            return {"success": True, "data": result}
        except WikiJSError as e:
            self._log_error(name, str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            self._log_error(name, str(e))
            return {"success": False, "error": f"Unexpected error: {e}"}

    def _log_tool(self, name: str, args: dict) -> None:
        if self.quiet:
            return
        label = TOOL_LABELS.get(name, name)
        detail = self._summarize_args(name, args)
        print(f"  {X}▸{R} {D}{label}{R}{detail}")

    def _log_result(self, name: str, result: Any) -> None:
        if self.quiet:
            return
        summary = self._summarize_result(name, result)
        print(f"  {G}✓{R} {D}{summary}{R}")

    def _log_error(self, name: str, error: str) -> None:
        if self.quiet:
            return
        print(f"  {Y}✗{R} {D}{error}{R}")

    def _summarize_args(self, name: str, args: dict) -> str:
        if name == "create_page":
            return f"  {C}{args.get('path', '')}{R}"
        if name == "fetch_page":
            key = args.get("page_id") or args.get("path", "")
            return f"  {C}{key}{R}"
        if name == "update_page":
            return f"  {C}id={args.get('page_id', '')}{R}"
        if name == "delete_page":
            return f"  {C}id={args.get('page_id', '')}{R}"
        if name == "search_pages":
            return f"  {C}\"{args.get('query', '')}\"{R}"
        if name == "move_page":
            return f"  {C}id={args.get('page_id', '')} → {args.get('new_path', '')}{R}"
        if name == "move_pages":
            moves = args.get("moves", [])
            return f"  {C}{len(moves)} pages{R}"
        if name == "clone_page":
            return f"  {C}id={args.get('source_id', '')} → {args.get('new_path', '')}{R}"
        if name == "export_page":
            return f"  {C}id={args.get('page_id', '')} → {args.get('filename', '')}{R}"
        if name == "import_page":
            return f"  {C}{args.get('filename', '')}{R}"
        if name == "view_history":
            return f"  {C}page_id={args.get('page_id', '')}{R}"
        if name == "view_revision":
            return f"  {C}page={args.get('page_id', '')} v={args.get('version_id', '')}{R}"
        if name == "diff_revisions":
            return f"  {C}page={args.get('page_id', '')} v{args.get('version_id_1', '')}→v{args.get('version_id_2', '')}{R}"
        if name == "restore_revision":
            return f"  {C}page={args.get('page_id', '')} → v{args.get('version_id', '')}{R}"
        if name == "jira_test_connection":
            return ""
        if name == "jira_list_projects":
            return ""
        if name == "jira_search_issues":
            if args.get("jql"):
                return f"  {C}jql: {args['jql'][:50]}{R}"
            parts = []
            for key in ("project", "status", "assignee", "priority", "issue_type"):
                if args.get(key):
                    parts.append(f"{key}={args[key]}")
            return f"  {C}{', '.join(parts)}{R}" if parts else ""
        if name == "jira_get_issue":
            return f"  {C}{args.get('issue_key', '')}{R}"
        if name == "jira_get_comments":
            return f"  {C}{args.get('issue_key', '')}{R}"
        if name == "jira_get_changelog":
            return f"  {C}{args.get('issue_key', '')}{R}"
        if name == "jira_get_transitions":
            return f"  {C}{args.get('issue_key', '')}{R}"
        return ""

    def _summarize_result(self, name: str, result: Any) -> str:
        if name == "create_page":
            pid = getattr(result, "page", None)
            pid = pid.id if pid else "?"
            return f"page created (id={pid})"
        if name == "fetch_page":
            return f"fetched \"{getattr(result, 'title', '?')}\" (id={getattr(result, 'id', '?')})"
        if name == "update_page":
            return "page updated"
        if name == "delete_page":
            return "page deleted"
        if name == "list_pages":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} pages found"
        if name == "search_pages":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} results"
        if name == "browse_tree":
            return "tree built"
        if name == "move_page":
            return "page moved"
        if name == "move_pages":
            if isinstance(result, dict):
                return f"{result.get('succeeded', 0)}/{result.get('total', 0)} pages moved"
            return "pages moved"
        if name == "clone_page":
            return "page cloned"
        if name == "export_page":
            msg = result.get("message", "exported") if isinstance(result, dict) else "exported"
            return msg
        if name == "import_page":
            pid = getattr(result, "page", None)
            pid = pid.id if pid else "?"
            return f"page imported (id={pid})"
        if name == "view_history":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} revisions"
        if name == "view_revision":
            return f"version {getattr(result, 'versionId', '?')}"
        if name == "diff_revisions":
            return "diff computed"
        if name == "restore_revision":
            return "version restored"
        if name == "test_connection":
            if isinstance(result, dict) and result.get("status") == "connected":
                return f"connected ({result.get('total_pages', '?')} pages)"
            return "connection failed"
        if name == "jira_test_connection":
            if isinstance(result, dict) and "displayName" in result:
                return f"connected as {result['displayName']}"
            return result.get("error", "connection failed")
        if name == "jira_list_projects":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} projects"
        if name == "jira_search_issues":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} issues found"
        if name == "jira_get_issue":
            return f"issue {getattr(result, 'key', result.get('key', '?'))}" if isinstance(result, dict) else "issue fetched"
        if name == "jira_get_comments":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} comments"
        if name == "jira_get_changelog":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} changes"
        if name == "jira_get_transitions":
            total = result.get("total", "?") if isinstance(result, dict) else "?"
            return f"{total} transitions"
        return "done"

    # ── Tool Handlers ─────────────────────────────────────────────────

    def _tool_create_page(self, args: dict) -> Any:
        page = Page(
            path=args["path"],
            title=args["title"],
            content=args["content"],
            description=args.get("description", ""),
            tags=args.get("tags", []),
            isPublished=args.get("isPublished", True),
            isPrivate=args.get("isPrivate", False),
            locale=args.get("locale", "en"),
        )
        return self.pages.create(page)

    def _tool_fetch_page(self, args: dict) -> Any:
        if "page_id" in args and args["page_id"] is not None:
            return self.pages.get_by_id(args["page_id"])
        elif "path" in args and args["path"] is not None:
            return self.pages.get_by_path(args["path"], args.get("locale", "en"))
        return {"error": "Provide either page_id or path"}

    def _tool_update_page(self, args: dict) -> Any:
        page_id = args["page_id"]
        existing = self.pages.get_by_id(page_id)

        if "title" in args and args["title"] is not None:
            existing.title = args["title"]
        if "content" in args and args["content"] is not None:
            existing.content = args["content"]
        if "description" in args and args["description"] is not None:
            existing.description = args["description"]
        if "tags" in args and args["tags"] is not None:
            existing.tags = args["tags"]
        if "isPublished" in args and args["isPublished"] is not None:
            existing.isPublished = args["isPublished"]
        if "isPrivate" in args and args["isPrivate"] is not None:
            existing.isPrivate = args["isPrivate"]

        return self.pages.update(existing)

    def _tool_delete_page(self, args: dict) -> Any:
        self.pages.delete(args["page_id"])
        return {"message": f"Page {args['page_id']} deleted successfully"}

    def _tool_list_pages(self, args: dict) -> Any:
        pages = self.pages.list_all(order_by=args.get("order_by", "TITLE"))
        return {
            "total": len(pages),
            "pages": [
                {
                    "id": p.id,
                    "path": p.path,
                    "title": p.title,
                    "isPublished": p.isPublished,
                    "tags": p.tags,
                }
                for p in pages
            ],
        }

    def _tool_search_pages(self, args: dict) -> Any:
        pages = self.pages.search(args["query"], args.get("locale", "en"))
        return {
            "total": len(pages),
            "results": [
                {"id": p.id, "path": p.path, "title": p.title, "description": p.description}
                for p in pages
            ],
        }

    def _tool_browse_tree(self, args: dict) -> Any:
        result = self.pages.list_all(order_by="PATH")
        if not result:
            return {"tree": "(no pages found)"}

        tree: dict = {}
        for p in result:
            parts = p.path.split("/")
            node = tree
            for part in parts[:-1]:
                child = node.get(part)
                if child is None:
                    node[part] = {}
                    node = node[part]
                elif isinstance(child, dict):
                    node = child
                else:
                    node[part] = {}
                    node = node[part]
            node[parts[-1]] = p

        lines: list[str] = []

        def _build(d: dict, prefix: str = "") -> None:
            items = sorted(d.items(), key=lambda x: (not isinstance(x[1], dict), x[0]))
            for i, (name, value) in enumerate(items):
                last = i == len(items) - 1
                connector = "└── " if last else "├── "
                if isinstance(value, dict):
                    lines.append(f"{prefix}{connector}{name}/")
                    extension = "    " if last else "│   "
                    _build(value, prefix + extension)
                else:
                    pub = " [draft]" if not value.isPublished else ""
                    lines.append(f"{prefix}{connector}{name} (id={value.id}{pub})")

        _build(tree)
        return {"tree": "/ (root)\n" + "\n".join(lines)}

    def _tool_move_page(self, args: dict) -> Any:
        return self.pages.move_or_rename(args["page_id"], args["new_path"])

    def _tool_move_pages(self, args: dict) -> Any:
        moves = args.get("moves", [])
        results = []
        for move in moves:
            page_id = move["page_id"]
            new_path = move["new_path"]
            try:
                self.pages.move_or_rename(page_id, new_path)
                results.append({"page_id": page_id, "new_path": new_path, "success": True})
            except WikiJSError as e:
                results.append({"page_id": page_id, "new_path": new_path, "success": False, "error": str(e)})
        succeeded = sum(1 for r in results if r["success"])
        failed = len(results) - succeeded
        return {"total": len(results), "succeeded": succeeded, "failed": failed, "results": results}

    def _tool_clone_page(self, args: dict) -> Any:
        return self.pages.clone_page(
            args["source_id"], args["new_path"], args["new_title"]
        )

    def _tool_export_page(self, args: dict) -> Any:
        page = self.pages.get_by_id(args["page_id"])
        filename = args["filename"]

        with open(filename, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"title: {page.title}\n")
            f.write(f"path: {page.path}\n")
            f.write(f"description: {page.description}\n")
            f.write(f"tags: [{', '.join(page.tags)}]\n")
            f.write(f"published: {page.isPublished}\n")
            f.write(f"private: {page.isPrivate}\n")
            f.write(f"locale: {page.locale}\n")
            f.write("---\n\n")
            f.write(page.content)

        return {"message": f"Exported page {page.id} to {filename}"}

    def _tool_import_page(self, args: dict) -> Any:
        filename = args["filename"]
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        meta: dict[str, str] = {}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                frontmatter = content[3:end].strip()
                for line in frontmatter.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meta[key.strip()] = value.strip()
                content = content[end + 3 :].strip()

        path = args.get("path") or meta.get("path", "")
        title = args.get("title") or meta.get("title", "")
        if not path or not title:
            return {"error": "path and title are required"}

        tags_str = meta.get("tags", "")
        tags = (
            [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
            if tags_str
            else []
        )

        page = Page(
            path=path,
            title=title,
            content=content,
            description=meta.get("description", ""),
            locale=meta.get("locale", "en"),
            isPublished=meta.get("published", "true").lower() == "true",
            isPrivate=meta.get("private", "false").lower() == "true",
            tags=tags,
        )
        return self.pages.create(page)

    def _tool_view_history(self, args: dict) -> Any:
        entries, total = self.pages.get_history(
            args["page_id"],
            offset_page=args.get("offset_page", 0),
            offset_size=args.get("offset_size", 100),
        )
        return {
            "total": total,
            "entries": [
                {
                    "versionId": h.versionId,
                    "versionDate": h.versionDate,
                    "authorName": h.authorName,
                    "actionType": h.actionType,
                }
                for h in entries
            ],
        }

    def _tool_view_revision(self, args: dict) -> Any:
        return self.pages.get_version(args["page_id"], args["version_id"])

    def _tool_diff_revisions(self, args: dict) -> Any:
        import difflib

        v1 = self.pages.get_version(args["page_id"], args["version_id_1"])
        v2 = self.pages.get_version(args["page_id"], args["version_id_2"])

        old_lines = v1.content.splitlines(keepends=True)
        new_lines = v2.content.splitlines(keepends=True)
        diff = "".join(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"v{v1.versionId}",
                tofile=f"v{v2.versionId}",
            )
        )
        return {
            "version_1": v1.versionId,
            "version_2": v2.versionId,
            "diff": diff or "No differences found",
        }

    def _tool_restore_revision(self, args: dict) -> Any:
        self.pages.restore_version(args["page_id"], args["version_id"])
        return {
            "message": f"Page {args['page_id']} restored to version {args['version_id']}"
        }

    def _tool_test_connection(self, args: dict) -> Any:
        try:
            pages = self.pages.list_all(order_by="CREATED")
            return {
                "status": "connected",
                "url": self.wiki_client.url,
                "total_pages": len(pages),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    # ── Jira Tool Handlers ───────────────────────────────────────────

    def _tool_jira_test_connection(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured. Set JIRA_SERVER, JIRA_EMAIL, and JIRA_API_TOKEN."}
        return self.jira_manager.test_connection()

    def _tool_jira_list_projects(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured."}
        projects = self.jira_manager.list_projects()
        return {
            "total": len(projects),
            "projects": [p.model_dump() for p in projects],
        }

    def _tool_jira_search_issues(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured."}
        issues = self.jira_manager.search_issues(
            jql=args.get("jql"),
            project=args.get("project"),
            status=args.get("status"),
            assignee=args.get("assignee"),
            priority=args.get("priority"),
            issue_type=args.get("issue_type"),
        )
        return {
            "total": len(issues),
            "issues": [i.model_dump() for i in issues],
        }

    def _tool_jira_get_issue(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured."}
        issue = self.jira_manager.get_issue(args["issue_key"])
        return issue.model_dump()

    def _tool_jira_get_comments(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured."}
        comments = self.jira_manager.get_comments(args["issue_key"])
        return {
            "total": len(comments),
            "comments": [c.model_dump() for c in comments],
        }

    def _tool_jira_get_changelog(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured."}
        entries = self.jira_manager.get_changelog(args["issue_key"])
        return {
            "total": len(entries),
            "entries": [e.model_dump() for e in entries],
        }

    def _tool_jira_get_transitions(self, args: dict) -> Any:
        if not self.jira_manager:
            return {"error": "Jira is not configured."}
        transitions = self.jira_manager.get_transitions(args["issue_key"])
        return {
            "total": len(transitions),
            "transitions": [t.model_dump() for t in transitions],
        }
