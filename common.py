"""
Common utilities for the agent demo.
Includes logging configuration, colored terminal output, and conversation logging.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

# Logger name -> color mapping
LOGGER_COLORS = {
    "main": Colors.BLUE,           # main.py 主逻辑
    "main2": Colors.BLUE,          # main2.py 主逻辑
    "main3": Colors.BLUE,          # main3.py 主逻辑
    "agent_loop": Colors.MAGENTA,  # agent_loop 循环
    "tool": Colors.YELLOW,         # 工具调用
    "default": Colors.GREEN,       # 默认
}

# Color mapping for log levels
LEVEL_COLORS = {
    logging.DEBUG: Colors.GRAY,
    logging.INFO: Colors.GREEN,
    logging.WARNING: Colors.YELLOW,
    logging.ERROR: Colors.RED,
    logging.CRITICAL: Colors.BOLD + Colors.RED,
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors based on logger name and level."""
    def format(self, record):
        # Determine color based on logger name
        logger_color = Colors.RESET
        for logger_name, color in LOGGER_COLORS.items():
            if record.name.startswith(logger_name) or logger_name in record.name:
                logger_color = color
                break
        else:
            logger_color = LOGGER_COLORS["default"]

        # Add color to levelname
        level_color = LEVEL_COLORS.get(record.levelno, Colors.RESET)
        original_levelname = record.levelname
        record.levelname = f"{level_color}{original_levelname}{Colors.RESET}"

        # Add color to logger name
        original_name = record.name
        record.name = f"{logger_color}{original_name}{Colors.RESET}"

        result = super().format(record)

        # Restore originals
        record.levelname = original_levelname
        record.name = original_name

        return result

class ConversationLogger:
    """Logs conversation messages to a file for review in JSON format."""

    def __init__(self, log_dir: str = ".logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_file: Optional[Path] = None
        self.session_start = datetime.now()
        self._init_session_file()

    def _init_session_file(self):
        """Initialize the session log file with timestamp."""
        timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
        self.current_file = self.log_dir / f"conversation_{timestamp}.log"
        self._write_separator("SESSION START")
        self._write_line(f"Session started at: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_separator()

    def _write_separator(self, label: str = ""):
        """Write a separator line with optional label."""
        sep = "=" * 80
        if label:
            padding = (80 - len(label) - 2) // 2
            sep = "=" * padding + f" {label} " + "=" * (80 - padding - len(label) - 2)
        self._write_line(sep)

    def _write_line(self, line: str):
        """Write a line to the log file."""
        if self.current_file:
            with open(self.current_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _serialize_content(self, content):
        """Serialize content to JSON-serializable format."""
        if content is None:
            return None
        if isinstance(content, (str, int, float, bool, dict)):
            return content
        if isinstance(content, list):
            result = []
            for item in content:
                if hasattr(item, '__dict__'):
                    # Convert object to dict
                    result.append({
                        k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                        for k, v in item.__dict__.items()
                        if not k.startswith('_')
                    })
                elif hasattr(item, 'type'):
                    # Handle anthropic message blocks
                    obj = {"type": item.type}
                    for k in dir(item):
                        if not k.startswith('_') and hasattr(item, k):
                            v = getattr(item, k)
                            if not callable(v):
                                obj[k] = str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                    result.append(obj)
                else:
                    result.append(str(item))
            return result
        return str(content)

    def log_user_message(self, content: str, query_num: int = 0):
        """Log a user message."""
        self._write_separator(f"USER QUERY #{query_num}")
        self._write_line(f"[{datetime.now().strftime('%H:%M:%S')}] -> TO LLM (user):")
        self._write_line(json.dumps({
            "role": "user",
            "content": content
        }, ensure_ascii=False, indent=2))
        self._write_line("")

    def log_assistant_message(self, content, stop_reason: str = None):
        """Log an assistant message."""
        self._write_line(f"[{datetime.now().strftime('%H:%M:%S')}] <- FROM LLM (assistant):")
        if stop_reason:
            self._write_line(f"[Stop reason: {stop_reason}]")

        serialized = self._serialize_content(content)
        self._write_line(json.dumps({
            "role": "assistant",
            "content": serialized
        }, ensure_ascii=False, indent=2))
        self._write_line("")

    def log_tool_result(self, tool_name: str, result: str, tool_id: str = None):
        """Log a tool execution result (full content, no truncation)."""
        self._write_line(f"[{datetime.now().strftime('%H:%M:%S')}] -> TO LLM (tool_result):")
        data = {
            "type": "tool_result",
            "tool_name": tool_name,
            "content": result
        }
        if tool_id:
            data["tool_use_id"] = tool_id
        self._write_line(json.dumps(data, ensure_ascii=False, indent=2))
        self._write_line("")

    def log_messages_sent(self, messages: list, iteration: int = None):
        """Log all messages sent to LLM (full content in JSON)."""
        prefix = f" [Iteration {iteration}]" if iteration else ""
        self._write_line(f"[{datetime.now().strftime('%H:%M:%S')}] -> TO LLM{prefix}:")
        serialized = self._serialize_content(messages)
        self._write_line(json.dumps(serialized, ensure_ascii=False, indent=2))
        self._write_line("")

    def log_llm_request(self, messages_count: int, iteration: int = None):
        """Log an LLM request."""
        prefix = f"[Iteration {iteration}] " if iteration else ""
        self._write_line(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix}LLM REQUEST ({messages_count} messages)")

    def end_query(self, query_num: int = 0):
        """Mark the end of a query."""
        self._write_separator(f"END QUERY #{query_num}")
        self._write_line("")

    def get_log_path(self) -> str:
        """Get the current log file path."""
        return str(self.current_file) if self.current_file else ""

# Global conversation logger instance
_conversation_logger: Optional[ConversationLogger] = None

def get_conversation_logger() -> ConversationLogger:
    """Get or create the global conversation logger."""
    global _conversation_logger
    if _conversation_logger is None:
        _conversation_logger = ConversationLogger()
    return _conversation_logger

def setup_logging(level=logging.INFO, use_colors=True, log_dir: str = ".logs"):
    """Setup logging with optional colored output and conversation logging."""
    # Console handler with colors
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ) if use_colors else logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # File handler for all logs (no colors)
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir_path / f"app_{timestamp}.log"

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Remove existing handlers
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Initialize conversation logger
    conv_logger = get_conversation_logger()

    logger = logging.getLogger("main")
    logger.info(f"Application log: {log_file}")
    logger.info(f"Conversation log: {conv_logger.get_log_path()}")

    return logger

def get_logger(name: str = None):
    """Get a logger instance."""
    return logging.getLogger(name)

# Colored print utilities
def print_info(msg: str):
    """Print info message in cyan."""
    print(f"{Colors.CYAN}{msg}{Colors.RESET}")

def print_success(msg: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}{msg}{Colors.RESET}")

def print_warning(msg: str):
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}{msg}{Colors.RESET}")

def print_error(msg: str):
    """Print error message in red."""
    print(f"{Colors.RED}{msg}{Colors.RESET}")

def print_command(cmd: str):
    """Print shell command in yellow."""
    print(f"{Colors.YELLOW}$ {cmd}{Colors.RESET}")

def print_prompt(text: str = ">> "):
    """Print interactive prompt in cyan."""
    return input(f"{Colors.CYAN}{text}{Colors.RESET}")
