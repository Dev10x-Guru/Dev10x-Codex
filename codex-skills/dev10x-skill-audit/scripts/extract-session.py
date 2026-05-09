#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Extract Codex JSONL session transcript into readable markdown.

Usage:
    extract-session.py <jsonl-path> [output.md]

If output.md is omitted, writes to stdout.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

CORRECTION_PATTERNS = re.compile(
    r"(?im)"
    r"^no[,.][ ]|"
    r"^actually[, ]|"
    r"\bi meant\b|"
    r"\bthat'?s wrong\b|"
    r"\bnot what i\b|"
    r"\bdon'?t do that\b|"
    r"\bplease don'?t\b|"
    r"\bi said\b|"
    r"\bwrong\b.{0,20}\binstead\b|"
    r"^use .+ instead\b"
)

MAX_TOOL_RESULT_LEN = 500
MAX_TOOL_INPUT_LEN = 300


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [{len(text) - limit} chars truncated]"


def extract_text_from_content(content: list | str) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") in {
            "input_text",
            "output_text",
            "text",
        }:
            parts.append(block.get("text", ""))
    return "\n".join(parts)


def summarize_arguments(arguments: object) -> str:
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return truncate(arguments, MAX_TOOL_INPUT_LEN)
    else:
        parsed = arguments

    if isinstance(parsed, dict):
        summary_parts = []
        for key, value in parsed.items():
            summary_parts.append(f"{key}={truncate(str(value), MAX_TOOL_INPUT_LEN)}")
        return ", ".join(summary_parts)
    return truncate(str(parsed), MAX_TOOL_INPUT_LEN)


def check_correction(text: str) -> bool:
    return bool(CORRECTION_PATTERNS.search(text))


def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        return ts or "?"


def process_jsonl(jsonl_path: str, out: TextIO) -> None:
    path = Path(jsonl_path)
    if not path.exists():
        print(f"Error: {jsonl_path} does not exist", file=sys.stderr)
        sys.exit(1)

    session_id = None
    cwd = None
    turn_num = 0

    out.write("# Session Transcript\n\n")

    messages = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    for msg in messages:
        if msg.get("type") == "session_meta":
            payload = msg.get("payload", {})
            session_id = payload.get("id")
            cwd = payload.get("cwd", "unknown")
            break

    first_ts = ""
    for msg in messages:
        if msg.get("timestamp"):
            first_ts = msg["timestamp"]
            break

    out.write(f"- **Session**: `{session_id or 'unknown'}`\n")
    out.write(f"- **Project**: `{cwd or 'unknown'}`\n")
    out.write(f"- **Started**: {first_ts}\n")
    out.write(f"- **Source**: `{jsonl_path}`\n")
    out.write("\n---\n\n")

    for msg in messages:
        if msg.get("type") != "response_item":
            continue

        payload = msg.get("payload", {})
        payload_type = payload.get("type", "")
        ts = format_timestamp(msg.get("timestamp", ""))

        if payload_type == "message":
            raw_role = payload.get("role", "")
            if raw_role not in {"user", "assistant"}:
                continue
            role = raw_role.upper()
            text = extract_text_from_content(payload.get("content", []))

            if text.strip():
                turn_num += 1
                correction = role == "USER" and check_correction(text.strip())
                marker = " **[CORRECTION]**" if correction else ""
                out.write(f"## Turn {turn_num} [{ts}] {role}{marker}\n\n")
                out.write(f"{text.strip()}\n\n")

        elif payload_type == "function_call":
            turn_num += 1
            out.write(f"## Turn {turn_num} [{ts}] ASSISTANT\n\n")

            out.write(f"**Tool: `{payload.get('name', 'unknown')}`**\n")
            arguments = summarize_arguments(payload.get("arguments", ""))
            if arguments:
                out.write(f"```\n{arguments}\n```\n")
            out.write("\n")

        elif payload_type == "function_call_output":
            call_id = payload.get("call_id", "")
            output = truncate(str(payload.get("output", "")), MAX_TOOL_RESULT_LEN)
            out.write(
                f"<details><summary>Tool result ({call_id[:12]}...)</summary>\n\n"
            )
            out.write(f"```\n{output}\n```\n")
            out.write("</details>\n\n")

    out.write(f"\n---\n*Extracted {turn_num} turns from `{path.name}`*\n")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    jsonl_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        with open(output_path, "w") as f:
            process_jsonl(jsonl_path=jsonl_path, out=f)
        print(f"Extracted to {output_path}", file=sys.stderr)
    else:
        process_jsonl(jsonl_path=jsonl_path, out=sys.stdout)


if __name__ == "__main__":
    main()
