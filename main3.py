#!/usr/bin/env python3
"""
s03_todo_write.py - TodoWrite
The model tracks its own progress via a TodoManager. A nag reminder
forces it to keep updating when it forgets.
    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> | Tools   |
    |  prompt  |      |       |      | + todo  |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                                |
                    +-----------+-----------+
                    | TodoManager state     |
                    | [ ] task A            |
                    | [>] task B <- doing   |
                    | [x] task C            |
                    +-----------------------+
                                |
                    if rounds_since_todo >= 3:
                      inject <reminder>
Key insight: "The agent can track its own progress -- and I can see it."
"""
import os
import subprocess
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from common import (
    setup_logging, get_logger, print_command, Colors,
    get_conversation_logger
)

# Configure logging with colors and file output
setup_logging()
main_logger = get_logger("main3")
agent_logger = get_logger("agent_loop")
tool_logger = get_logger("tool")
conv_logger = get_conversation_logger()

load_dotenv(override=True)
main_logger.info("Environment loaded")
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    main_logger.info("Using custom ANTHROPIC_BASE_URL")

WORKDIR = Path.cwd()
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]
SYSTEM = f"""You are a coding agent at {WORKDIR}.
Use the todo tool to plan multi-step tasks. Mark in_progress before starting, completed when done.
Prefer tools over prose."""
main_logger.info(f"Agent initialized at {WORKDIR} with model {MODEL}")

# -- TodoManager: structured state the LLM writes to --
class TodoManager:
    def __init__(self):
        self.items = []
        main_logger.info("TodoManager initialized")

    def update(self, items: list) -> str:
        tool_logger.info(f"Updating todos with {len(items)} items")
        if len(items) > 20:
            tool_logger.warning(f"Too many todos: {len(items)}")
            raise ValueError("Max 20 todos allowed")
        validated = []
        in_progress_count = 0
        for i, item in enumerate(items):
            text = str(item.get("text", "")).strip()
            status = str(item.get("status", "pending")).lower()
            item_id = str(item.get("id", str(i + 1)))
            if not text:
                tool_logger.warning(f"Item {item_id}: text required")
                raise ValueError(f"Item {item_id}: text required")
            if status not in ("pending", "in_progress", "completed"):
                tool_logger.warning(f"Item {item_id}: invalid status '{status}'")
                raise ValueError(f"Item {item_id}: invalid status '{status}'")
            if status == "in_progress":
                in_progress_count += 1
            validated.append({"id": item_id, "text": text, "status": status})
        if in_progress_count > 1:
            tool_logger.warning(f"Multiple tasks in_progress: {in_progress_count}")
            raise ValueError("Only one task can be in_progress at a time")
        self.items = validated
        tool_logger.info(f"Todos updated: {len([t for t in validated if t['status'] == 'completed'])}/{len(validated)} completed")
        return self.render()

    def render(self) -> str:
        if not self.items:
            return "No todos."
        lines = []
        for item in self.items:
            marker = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}[item["status"]]
            lines.append(f"{marker} #{item['id']}: {item['text']}")
        done = sum(1 for t in self.items if t["status"] == "completed")
        lines.append(f"\n({done}/{len(self.items)} completed)")
        return "\n".join(lines)

TODO = TodoManager()

# -- Tool implementations --
def safe_path(p: str) -> Path:
    tool_logger.debug(f"Resolving path: {p}")
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        tool_logger.warning(f"Path escapes workspace: {p}")
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_bash(command: str) -> str:
    tool_logger.info(f"Executing bash command: {command}")
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        tool_logger.warning(f"Dangerous command blocked: {command}")
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        tool_logger.info(f"Command completed with return code: {r.returncode}")
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        tool_logger.error("Command timed out after 120s")
        return "Error: Timeout (120s)"

def run_read(path: str, limit: int = None) -> str:
    tool_logger.info(f"Reading file: {path} (limit={limit})")
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        result = "\n".join(lines)[:50000]
        tool_logger.info(f"Read {len(result)} bytes from {path}")
        return result
    except Exception as e:
        tool_logger.error(f"Error reading {path}: {e}")
        return f"Error: {e}"

def run_write(path: str, content: str) -> str:
    tool_logger.info(f"Writing file: {path} ({len(content)} bytes)")
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        tool_logger.info(f"Wrote {len(content)} bytes to {path}")
        return f"Wrote {len(content)} bytes"
    except Exception as e:
        tool_logger.error(f"Error writing {path}: {e}")
        return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    tool_logger.info(f"Editing file: {path}")
    try:
        fp = safe_path(path)
        content = fp.read_text()
        if old_text not in content:
            tool_logger.warning(f"Text not found in {path}")
            return f"Error: Text not found in {path}"
        fp.write_text(content.replace(old_text, new_text, 1))
        tool_logger.info(f"Edited {path}")
        return f"Edited {path}"
    except Exception as e:
        tool_logger.error(f"Error editing {path}: {e}")
        return f"Error: {e}"

TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
    "todo":       lambda **kw: TODO.update(kw["items"]),
}
TOOLS = [
    {"name": "bash", "description": "Run a shell command.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
    {"name": "todo", "description": "Update task list. Track progress on multi-step tasks.",
     "input_schema": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}, "required": ["id", "text", "status"]}}}, "required": ["items"]}},
]

# -- Agent loop with nag reminder injection --
def agent_loop(messages: list, query_num: int = 0):
    rounds_since_todo = 0
    loop_count = 0
    agent_logger.info("Starting agent loop with todo tracking")
    conv_logger.log_llm_request(len(messages), iteration=loop_count)

    while True:
        loop_count += 1
        agent_logger.info(f"Agent loop iteration {loop_count}, rounds_since_todo={rounds_since_todo}")
        conv_logger.log_llm_request(len(messages), iteration=loop_count)
        # Log full messages being sent to LLM
        conv_logger.log_messages_sent(messages, iteration=loop_count)

        # Nag reminder is injected below, alongside tool results
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        agent_logger.info(f"LLM response received, stop_reason: {response.stop_reason}")

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})
        conv_logger.log_assistant_message(response.content, stop_reason=response.stop_reason)

        if response.stop_reason != "tool_use":
            agent_logger.info("Agent loop completed - no tool use")
            return

        results = []
        used_todo = False
        tool_count = 0
        for block in response.content:
            if block.type == "tool_use":
                tool_count += 1
                handler = TOOL_HANDLERS.get(block.name)
                tool_logger.info(f"Executing tool call {tool_count}: {block.name}")
                try:
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                except Exception as e:
                    tool_logger.error(f"Tool execution error: {e}")
                    output = f"Error: {e}"
                print_command(f"{block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
                conv_logger.log_tool_result(block.name, str(output), tool_id=block.id)
                if block.name == "todo":
                    used_todo = True

        rounds_since_todo = 0 if used_todo else rounds_since_todo + 1
        agent_logger.info(f"Executed {tool_count} tool(s), used_todo={used_todo}, rounds_since_todo={rounds_since_todo}")

        if rounds_since_todo >= 3:
            agent_logger.warning(f"Injecting todo reminder after {rounds_since_todo} rounds without todo update")
            results.insert(0, {"type": "text", "text": "<reminder>Update your todos.</reminder>"})

        messages.append({"role": "user", "content": results})

if __name__ == "__main__":
    main_logger.info("Starting agent demo application")
    history = []
    query_count = 0
    while True:
        query_count += 1
        main_logger.info(f"Waiting for user input (query #{query_count})")
        try:
            query = input(f"{Colors.CYAN}s03 >> {Colors.RESET}")
            main_logger.info(f"User input received: {query}")
        except (EOFError, KeyboardInterrupt):
            main_logger.info("Interrupted, exiting")
            break
        if query.strip().lower() in ("q", "exit", ""):
            main_logger.info("Exit command received, shutting down")
            break

        history.append({"role": "user", "content": query})
        conv_logger.log_user_message(query, query_num=query_count)
        main_logger.info(f"Processing query, history now has {len(history)} messages")

        agent_loop(history, query_num=query_count)

        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    main_logger.info(f"Assistant response: {block.text[:100]}...")
                    print(block.text)
        print()
        conv_logger.end_query(query_num=query_count)

    main_logger.info("Agent demo application stopped")
    main_logger.info(f"Conversation log saved to: {conv_logger.get_log_path()}")
