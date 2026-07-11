"""AI agent that translates natural language prompts into Wiki.js operations."""

from __future__ import annotations

import json
from typing import Any

from wiki_cli import WikiJSClient, WikiJSError
from wiki_cli.models import Page
from wiki_cli.pages import PagesManager
from wiki_cli.ai.config import AIConfig
from wiki_cli.ai.tools import TOOLS

SYSTEM_PROMPT = """You are a Wiki.js assistant. You manage wiki pages using the tools provided.

Rules:
- Always confirm with the user before performing destructive actions (delete, restore, move).
- When creating or updating pages, generate high-quality Markdown content when the user provides a topic.
- If a tool returns an error, explain it to the user and suggest fixes.
- For searches or lists, summarize results in a readable format instead of dumping raw data.
- Never fabricate page IDs or paths. Always fetch first if unsure.
"""


class WikiAgent:
    """AI agent that uses LLM tool calling to execute Wiki.js operations.

    Attributes:
        pages: The PagesManager instance for executing operations.
        config: The AI provider configuration.
        client: The underlying LLM client (OpenAI-compatible).
    """

    def __init__(self, config: AIConfig | None = None) -> None:
        self.config = config or AIConfig()
        self.wiki_client = WikiJSClient()
        self.pages = PagesManager(self.wiki_client)
        self.client = self.config.get_client()

    def run(self, user_prompt: str) -> str:
        """Process a user prompt and return the AI's response.

        This is the main entry point. It handles the full loop:
        1. Send prompt to LLM
        2. If LLM wants to call tools, execute them and send results back
        3. Repeat until LLM produces a text response

        Args:
            user_prompt: The user's natural language request.

        Returns:
            The AI's text response.
        """
        return self._run_openai(user_prompt)

    def _run_openai(self, user_prompt: str) -> str:
        """Tool-calling loop for OpenAI-compatible APIs.

        Works with all supported providers (openai, openrouter, groq, mistral,
        ollama, ollama-cloud) since they all use the same chat completions API.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            messages.append(msg)

            for tool_call in msg.tool_calls:
                result = self._execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                messages.append(
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

        dispatch = {
            "create_page": self._tool_create_page,
            "fetch_page": self._tool_fetch_page,
            "update_page": self._tool_update_page,
            "delete_page": self._tool_delete_page,
            "list_pages": self._tool_list_pages,
            "search_pages": self._tool_search_pages,
            "browse_tree": self._tool_browse_tree,
            "move_page": self._tool_move_page,
            "clone_page": self._tool_clone_page,
            "export_page": self._tool_export_page,
            "import_page": self._tool_import_page,
            "view_history": self._tool_view_history,
            "view_revision": self._tool_view_revision,
            "diff_revisions": self._tool_diff_revisions,
            "restore_revision": self._tool_restore_revision,
            "test_connection": self._tool_test_connection,
        }

        handler = dispatch.get(name)
        if not handler:
            return {"success": False, "error": f"Unknown tool: {name}"}

        try:
            result = handler(args)
            if hasattr(result, "model_dump"):
                return {"success": True, "data": result.model_dump()}
            return {"success": True, "data": result}
        except WikiJSError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}

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
                node = node.setdefault(part, {})
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
