from __future__ import annotations
import shlex
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional

from volt.models.tool import ExecutionRecord, Tool
from volt.storage.database import add_history


def build_command(tool: Tool, extra_args: str = "") -> str:
    cmd = tool.command
    if extra_args:
        cmd = f"{cmd} {extra_args}"
    return cmd


def execute_tool(tool: Tool, extra_args: str = "") -> ExecutionRecord:
    cmd = build_command(tool, extra_args)

    start = time.time()
    exit_code = 0

    try:
        shell_cmd = shlex.split(cmd) if sys.platform != "win32" else cmd
        result = subprocess.run(
            shell_cmd,
            shell=(sys.platform == "win32"),
            timeout=300,
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    except FileNotFoundError:
        exit_code = 127
    except Exception:
        exit_code = 1

    duration = time.time() - start
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = ExecutionRecord(
        tool_name=tool.name,
        command=cmd,
        timestamp=now,
        exit_code=exit_code,
        duration=duration,
    )

    add_history(record)
    return record


def execute_tool_interactive(tool: Tool) -> ExecutionRecord:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = ExecutionRecord(
        tool_name=tool.name,
        command=tool.command,
        timestamp=now,
        exit_code=0,
        duration=0.0,
    )

    add_history(record)
    return record
