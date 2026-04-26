"""Plan domain class — typed wrapper for task plan YAML data.

Replaces the raw dict[str, Any] threading in task_plan_sync.py
with a cohesive domain object that owns its own persistence and
mutation logic.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _get_branch() -> str:
    from dev10x.domain.git_context import GitContext

    return GitContext().branch


def _extract_task_id(tool_result: str) -> str | None:
    match = re.search(r"Task #(\d+)", tool_result)
    return match.group(1) if match else None


@dataclass
class Plan:
    metadata: dict[str, Any] = field(default_factory=dict)
    tasks: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls, *, path: Path) -> Plan:
        if path.exists():
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError):
                data = {}
        else:
            data = {}
        return cls(
            metadata=data.get("plan", {}),
            tasks=data.get("tasks", []),
        )

    def save(self, *, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        plan_data = self._to_dict()
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=".plan-",
            suffix=".yaml.tmp",
        )
        try:
            with os.fdopen(fd, "w") as f:
                yaml.dump(
                    plan_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            os.rename(tmp_path, str(path))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.metadata:
            result["plan"] = self.metadata
        if self.tasks:
            result["tasks"] = self.tasks
        return result

    def ensure_metadata(self) -> None:
        if not self.metadata:
            self.metadata = {
                "created_at": _now_iso(),
                "branch": _get_branch(),
                "status": "in_progress",
            }
        self.metadata["last_synced"] = _now_iso()

    @property
    def is_new(self) -> bool:
        return not self.metadata

    def handle_task_create(
        self,
        *,
        tool_input: dict[str, Any],
        tool_result: str,
    ) -> bool:
        task_id = _extract_task_id(tool_result)
        if not task_id:
            return False

        task_entry: dict[str, Any] = {
            "id": task_id,
            "subject": tool_input.get("subject", ""),
            "status": "pending",
            "created_at": _now_iso(),
        }
        description = tool_input.get("description")
        if description:
            task_entry["description"] = description
        metadata = tool_input.get("metadata")
        if metadata:
            task_entry["metadata"] = metadata

        existing_ids = {t.get("id") for t in self.tasks}
        if task_id not in existing_ids:
            self.tasks.append(task_entry)
            return True
        return False

    def handle_task_update(self, *, tool_input: dict[str, Any]) -> None:
        task_id = tool_input.get("taskId")
        if not task_id:
            return

        status = tool_input.get("status")
        if status == "deleted":
            self.tasks = [t for t in self.tasks if t.get("id") != task_id]
            return

        for task in self.tasks:
            if task.get("id") != task_id:
                continue
            if status:
                task["status"] = status
                if status == "completed":
                    task["completed_at"] = _now_iso()
                elif status == "in_progress":
                    task["started_at"] = _now_iso()
            if "subject" in tool_input:
                task["subject"] = tool_input["subject"]
            if "description" in tool_input:
                task["description"] = tool_input["description"]
            if "metadata" in tool_input:
                existing_meta = task.get("metadata", {})
                for k, v in tool_input["metadata"].items():
                    if v is None:
                        existing_meta.pop(k, None)
                    else:
                        existing_meta[k] = v
                if existing_meta:
                    task["metadata"] = existing_meta
            break

    def check_all_completed(self) -> None:
        all_statuses = [t.get("status") for t in self.tasks]
        if all_statuses and all(s == "completed" for s in all_statuses):
            self.metadata["status"] = "completed"
            self.metadata["completed_at"] = _now_iso()

    def set_context(self, *, key: str, value: str) -> None:
        context = self.metadata.setdefault("context", {})
        _set_nested(d=context, dotpath=key, value=value)


def _set_nested(*, d: dict[str, Any], dotpath: str, value: str) -> None:
    keys = dotpath.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    try:
        d[keys[-1]] = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        d[keys[-1]] = value
