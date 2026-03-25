#!/usr/bin/env python3
"""
s02_tool_use.py - Tools
The agent loop from s01 didn't change. We just added tools to the array
and a dispatch map to route calls.
    +----------+      +-------+      +------------------+
    |   User   | ---> |  LLM  | ---> | Tool Dispatch    |
    |  prompt  |      |       |      | {                |
    +----------+      +---+---+      |   bash: run_bash |
                          ^          |   read: run_read |
                          |          |   write: run_wr  |
                          +----------+   edit: run_edit |
                          tool_result| }                |
                                     +------------------+
Key insight: "The loop didn't change at all. I just added tools."
"""
import os
import subprocess
import sys
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from common import (
    setup_logging, get_logger, print_command, Colors,
    get_conversation_logger
)

# Configure logging with colors and file output
setup_logging()
main_logger = get_logger("main2")
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
SYSTEM = f"You are a coding agent at {WORKDIR}. Use tools to solve tasks. Act, don't explain."
main_logger.info(f"Agent initialized at {WORKDIR} with model {MODEL}")

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
        text = safe_path(path).read_text()
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        result = "\n".join(lines)[:50000]
        tool_logger.info(f"Read {len(text)} bytes from {path}")
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
        return f"Wrote {len(content)} bytes to {path}"
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

# -- The dispatch map: {tool_name: handler} --
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
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
]

def agent_loop(messages: list, query_num: int = 0):
    loop_count = 0
    agent_logger.info("Starting agent loop")
    conv_logger.log_llm_request(len(messages), iteration=loop_count)

    while True:
        loop_count += 1
        agent_logger.info(f"Agent loop iteration {loop_count}, calling LLM with {len(messages)} messages")
        conv_logger.log_llm_request(len(messages), iteration=loop_count)
        # Log full messages being sent to LLM
        conv_logger.log_messages_sent(messages, iteration=loop_count)

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
        tool_count = 0
        for block in response.content:
            if block.type == "tool_use":
                tool_count += 1
                handler = TOOL_HANDLERS.get(block.name)
                tool_logger.info(f"Executing tool call {tool_count}: {block.name}")
                output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                print_command(f"{block.name}: {output[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
                conv_logger.log_tool_result(block.name, output, tool_id=block.id)

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
            query = input(f"{Colors.CYAN}s02 >> {Colors.RESET}")
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
