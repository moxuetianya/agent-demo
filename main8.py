#!/usr/bin/env python3
# Harness: background execution -- the model thinks while the harness waits.
"""
s08_background_tasks.py - Background Tasks

Run commands in background threads. A notification queue is drained
before each LLM call to deliver results.

    Main thread                Background thread
    +-----------------+        +-----------------+
    | agent loop      |        | task executes   |
    | ...             |        | ...             |
    | [LLM call] <---+------- | enqueue(result) |
    |  ^drain queue   |        +-----------------+
    +-----------------+

    Timeline:
    Agent ----[spawn A]----[spawn B]----[other work]----
                 |              |
                 v              v
              [A runs]      [B runs]        (parallel)
                 |              |
                 +-- notification queue --> [results injected]

Key insight: "Fire and forget -- the agent doesn't block while the command runs."
"""

import os
import subprocess
import threading
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from common import (
    setup_logging, get_logger, Colors,
    get_conversation_logger
)

# Configure logging with colors and file output
setup_logging()
main_logger = get_logger("main8")
agent_logger = get_logger("agent_loop")
tool_logger = get_logger("tool")
bg_logger = get_logger("background")
conv_logger = get_conversation_logger()

load_dotenv(override=True)
main_logger.info("Environment loaded")
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    main_logger.info("Using custom ANTHROPIC_BASE_URL")

WORKDIR = Path.cwd()
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]
main_logger.info(f"Agent initialized at {WORKDIR} with model {MODEL}")

SYSTEM = f"You are a coding agent at {WORKDIR}. Use background_run for long-running commands."


# -- BackgroundManager: threaded execution + notification queue --
class BackgroundManager:
    def __init__(self):
        self.tasks = {}  # task_id -> {status, result, command}
        self._notification_queue = []  # completed task results
        self._lock = threading.Lock()
        bg_logger.info("BackgroundManager initialized")

    def run(self, command: str) -> str:
        """Start a background thread, return task_id immediately."""
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {"status": "running", "result": None, "command": command}
        bg_logger.info(f"Starting background task {task_id}: {command[:80]}")
        thread = threading.Thread(
            target=self._execute, args=(task_id, command), daemon=True
        )
        thread.start()
        return f"Background task {task_id} started: {command[:80]}"

    def _execute(self, task_id: str, command: str):
        """Thread target: run subprocess, capture output, push to queue."""
        bg_logger.info(f"Task {task_id} executing: {command[:80]}")
        try:
            r = subprocess.run(
                command, shell=True, cwd=WORKDIR,
                capture_output=True, text=True, timeout=300
            )
            output = (r.stdout + r.stderr).strip()[:50000]
            status = "completed"
            bg_logger.info(f"Task {task_id} completed with return code {r.returncode}")
        except subprocess.TimeoutExpired:
            output = "Error: Timeout (300s)"
            status = "timeout"
            bg_logger.warning(f"Task {task_id} timed out after 300s")
        except Exception as e:
            output = f"Error: {e}"
            status = "error"
            bg_logger.error(f"Task {task_id} failed: {e}")
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["result"] = output or "(no output)"
        with self._lock:
            self._notification_queue.append({
                "task_id": task_id,
                "status": status,
                "command": command[:80],
                "result": (output or "(no output)")[:500],
            })
        bg_logger.info(f"Task {task_id} notification queued")

    def check(self, task_id: str = None) -> str:
        """Check status of one task or list all."""
        if task_id:
            t = self.tasks.get(task_id)
            if not t:
                bg_logger.warning(f"Unknown task {task_id} check requested")
                return f"Error: Unknown task {task_id}"
            return f"[{t['status']}] {t['command'][:60]}\n{t.get('result') or '(running)' }"
        lines = []
        for tid, t in self.tasks.items():
            lines.append(f"{tid}: [{t['status']}] {t['command'][:60]}")
        bg_logger.info(f"Listing {len(lines)} background tasks")
        return "\n".join(lines) if lines else "No background tasks."

    def drain_notifications(self) -> list:
        """Return and clear all pending completion notifications."""
        with self._lock:
            notifs = list(self._notification_queue)
            self._notification_queue.clear()
        if notifs:
            bg_logger.info(f"Drained {len(notifs)} notifications")
        return notifs


BG = BackgroundManager()


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
        c = fp.read_text()
        if old_text not in c:
            tool_logger.warning(f"Text not found in {path}")
            return f"Error: Text not found in {path}"
        fp.write_text(c.replace(old_text, new_text, 1))
        tool_logger.info(f"Edited {path}")
        return f"Edited {path}"
    except Exception as e:
        tool_logger.error(f"Error editing {path}: {e}")
        return f"Error: {e}"


TOOL_HANDLERS = {
    "bash":             lambda **kw: run_bash(kw["command"]),
    "read_file":        lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file":       lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":        lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
    "background_run":   lambda **kw: BG.run(kw["command"]),
    "check_background": lambda **kw: BG.check(kw.get("task_id")),
}

TOOLS = [
    {"name": "bash", "description": "Run a shell command (blocking).",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
    {"name": "background_run", "description": "Run command in background thread. Returns task_id immediately.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "check_background", "description": "Check background task status. Omit task_id to list all.",
     "input_schema": {"type": "object", "properties": {"task_id": {"type": "string"}}}},
]


def agent_loop(messages: list, query_num: int = 0):
    loop_count = 0
    agent_logger.info("Starting agent loop")

    while True:
        loop_count += 1
        agent_logger.info(f"Agent loop iteration {loop_count}")

        # Drain background notifications and inject as system message before LLM call
        notifs = BG.drain_notifications()
        if notifs and messages:
            notif_text = "\n".join(
                f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifs
            )
            agent_logger.info(f"Injecting {len(notifs)} background notifications")
            messages.append({"role": "user", "content": f"<background-results>\n{notif_text}\n</background-results>"})
            messages.append({"role": "assistant", "content": "Noted background results."})

        conv_logger.log_llm_request(len(messages), iteration=loop_count)
        conv_logger.log_messages_sent(messages, iteration=loop_count)

        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        agent_logger.info(f"LLM response received, stop_reason: {response.stop_reason}")

        messages.append({"role": "assistant", "content": response.content})
        conv_logger.log_assistant_message(response.content, stop_reason=response.stop_reason)

        if response.stop_reason != "tool_use":
            agent_logger.info("Agent loop completed - no tool use")
            return

        results = []
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
                print(f"> {block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
                conv_logger.log_tool_result(block.name, str(output), tool_id=block.id)

        agent_logger.info(f"Executed {tool_count} tool(s), appending results to messages")
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    main_logger.info("Starting agent demo application")
    history = []
    query_count = 0
    while True:
        query_count += 1
        main_logger.info(f"Waiting for user input (query #{query_count})")
        try:
            query = input(f"{Colors.CYAN}s08 >> {Colors.RESET}")
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
