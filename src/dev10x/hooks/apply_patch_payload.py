from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

APPLY_PATCH_TOOL_NAME = "apply_patch"

_BEGIN_PATCH = "*** Begin Patch"
_END_PATCH = "*** End Patch"
_ADD_FILE = "*** Add File: "
_DELETE_FILE = "*** Delete File: "
_UPDATE_FILE = "*** Update File: "
_MOVE_TO = "*** Move to: "
_END_OF_FILE = "*** End of File"
_ENVIRONMENT_ID = "*** Environment ID: "
_CHANGE_CONTEXT = "@@"
_HEREDOC_OPENERS = frozenset({"<<EOF", "<<'EOF'", '<<"EOF"'})
_MIN_HEREDOC_LINES = 4


class MalformedPatchError(ValueError):
    pass


class PatchOperationKind(StrEnum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"


@dataclass(frozen=True)
class PatchOperation:
    kind: PatchOperationKind
    path: str
    added_lines: tuple[str, ...] = ()
    move_to: str | None = None

    @property
    def content(self) -> str:
        return "\n".join(self.added_lines)

    def touched_paths(self) -> tuple[str, ...]:
        if self.move_to:
            return (self.path, self.move_to)
        return (self.path,)


@dataclass
class _OpenHunk:
    kind: PatchOperationKind
    path: str
    added_lines: list[str]
    move_to: str | None = None
    has_changes: bool = False

    def close(self) -> PatchOperation:
        if self.kind is PatchOperationKind.UPDATE and not self.has_changes:
            raise MalformedPatchError(f"update hunk for {self.path!r} is empty")
        return PatchOperation(
            kind=self.kind,
            path=self.path,
            added_lines=tuple(self.added_lines),
            move_to=self.move_to,
        )


_HEADERS = (
    (_ADD_FILE, PatchOperationKind.ADD),
    (_DELETE_FILE, PatchOperationKind.DELETE),
    (_UPDATE_FILE, PatchOperationKind.UPDATE),
)


def _strip_boundaries(text: str) -> list[str]:
    lines = text.strip().splitlines()
    if (
        len(lines) >= _MIN_HEREDOC_LINES
        and lines[0].strip() in _HEREDOC_OPENERS
        and lines[-1].strip().endswith("EOF")
    ):
        lines = lines[1:-1]
    if not lines or lines[0].strip() != _BEGIN_PATCH:
        raise MalformedPatchError(f"first line must be {_BEGIN_PATCH!r}")
    if len(lines) < 2 or lines[-1].strip() != _END_PATCH:
        raise MalformedPatchError(f"last line must be {_END_PATCH!r}")
    return lines[1:-1]


def _open_hunk(trimmed: str) -> _OpenHunk | None:
    for marker, kind in _HEADERS:
        bare_marker = marker.rstrip()
        if trimmed == bare_marker or trimmed.startswith(marker):
            path = trimmed[len(bare_marker) :].strip()
            if not path:
                raise MalformedPatchError(f"{marker.strip()} header has no path")
            return _OpenHunk(kind=kind, path=path, added_lines=[])
    return None


def _feed_update_line(hunk: _OpenHunk, line: str) -> None:
    body = line.rstrip()
    if not hunk.has_changes and hunk.move_to is None and body.startswith(_MOVE_TO):
        hunk.move_to = body[len(_MOVE_TO) :].strip()
        return
    if body.strip() == _END_OF_FILE:
        return
    if body.startswith(_CHANGE_CONTEXT):
        hunk.has_changes = True
        return
    if line.startswith("+"):
        hunk.added_lines.append(line[1:])
        hunk.has_changes = True
        return
    if not body or line.startswith(("-", " ")):
        hunk.has_changes = True
        return
    raise MalformedPatchError(f"unexpected line in update hunk for {hunk.path!r}: {line!r}")


def parse_apply_patch(text: str) -> tuple[PatchOperation, ...]:
    operations: list[PatchOperation] = []
    hunk: _OpenHunk | None = None
    for line in _strip_boundaries(text):
        trimmed = line.strip()
        if hunk is None and not operations and trimmed.startswith(_ENVIRONMENT_ID):
            continue
        opened = _open_hunk(trimmed)
        if opened is not None:
            if hunk is not None:
                operations.append(hunk.close())
            hunk = opened
            continue
        if hunk is None or hunk.kind is PatchOperationKind.DELETE:
            if trimmed:
                raise MalformedPatchError(f"line outside a file hunk: {line!r}")
            continue
        if hunk.kind is PatchOperationKind.ADD:
            if not line.startswith("+"):
                raise MalformedPatchError(f"add-file line must start with '+': {line!r}")
            hunk.added_lines.append(line[1:])
            continue
        _feed_update_line(hunk, line)
    if hunk is not None:
        operations.append(hunk.close())
    return tuple(operations)


def _absolute(path: str, *, cwd: str) -> str:
    if os.path.isabs(path) or not cwd:
        return path
    return os.path.normpath(os.path.join(cwd, path))


def _payload(
    base: dict[str, Any], *, tool_name: str, file_path: str, content_key: str, content: str
) -> dict[str, Any]:
    return {
        **base,
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path, content_key: content},
    }


def to_edit_write_payloads(*, data: dict[str, Any], cwd: str) -> list[dict[str, Any]]:
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        raise MalformedPatchError("tool_input is not an object")
    patch = tool_input.get("command")
    if not isinstance(patch, str) or not patch.strip():
        raise MalformedPatchError("tool_input.command is missing or empty")
    base = {key: value for key, value in data.items() if key not in ("tool_name", "tool_input")}
    payloads: list[dict[str, Any]] = []
    for op in parse_apply_patch(patch):
        source = _absolute(op.path, cwd=cwd)
        if op.kind is PatchOperationKind.ADD:
            payloads.append(
                _payload(
                    base,
                    tool_name="Write",
                    file_path=source,
                    content_key="content",
                    content=op.content,
                )
            )
            continue
        payloads.append(
            _payload(
                base,
                tool_name="Edit",
                file_path=source,
                content_key="new_string",
                content=op.content,
            )
        )
        if op.move_to:
            payloads.append(
                _payload(
                    base,
                    tool_name="Write",
                    file_path=_absolute(op.move_to, cwd=cwd),
                    content_key="content",
                    content=op.content,
                )
            )
    return payloads
