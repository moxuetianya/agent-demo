#!/usr/bin/env python3
"""
s01_agent_loop.py - The Agent Loop
The entire secret of an AI coding agent in one pattern:
    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results
    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)
This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
"""
import os
import subprocess
import sys
from anthropic import Anthropic
from dotenv import load_dotenv
from common import (
    setup_logging, get_logger, print_command, Colors,
    get_conversation_logger
)

# Configure logging with colors and file output
setup_logging()
main_logger = get_logger("main")
agent_logger = get_logger("agent_loop")
tool_logger = get_logger("tool")
conv_logger = get_conversation_logger()

load_dotenv(override=True)
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."
TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]

def run_bash(command: str) -> str:
    tool_logger.info(f"Executing bash command: {command}")
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        tool_logger.warning(f"Dangerous command blocked: {command}")
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        tool_logger.info(f"Command completed with return code: {r.returncode}")
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        tool_logger.error("Command timed out after 120s")
        return "Error: Timeout (120s)"

# -- The core pattern: a while loop that calls tools until the model stops --
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

        # If the model didn't call a tool, we're done
        if response.stop_reason != "tool_use":
            agent_logger.info("Agent loop completed - no tool use")
            return

        # Execute each tool call, collect results
        results = []
        tool_count = 0
        for block in response.content:
            if block.type == "tool_use":
                tool_count += 1
                tool_logger.info(f"Executing tool call {tool_count}: {block.name}")
                print_command(block.input['command'])
                output = run_bash(block.input["command"])
                print(output[:200])
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": output})
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
            query = input(f"{Colors.CYAN}s01 >> {Colors.RESET}")
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
